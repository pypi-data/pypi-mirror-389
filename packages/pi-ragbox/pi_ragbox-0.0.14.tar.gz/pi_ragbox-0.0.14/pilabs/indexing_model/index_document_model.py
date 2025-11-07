import hashlib
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

if TYPE_CHECKING:
    from pilabs.clients.embedding_client import OpenAIEmbedder


class CorpusIndexDocument(BaseModel):
    id: str | None = None
    corpus_domain: str
    corpus_name: str
    config: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _set_id(self) -> "CorpusIndexDocument":
        self.id = f"{self.corpus_domain}__%__{self.corpus_name}"
        return self


class IndexDocument(BaseModel):
    id: str | None = None
    text: str | None = None
    embedding: list[float] | None = None
    structured_data: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def _validate_inputs(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        text = data.get("text")
        structured_data = data.get("structured_data")

        if text is None and structured_data is None:
            raise ValueError(
                "IndexDocument requires either text or structured_data to be provided."
            )

        if text is not None and structured_data is not None:
            raise ValueError(
                "IndexDocument accepts only one of text or structured_data at creation time."
            )
        return data

    @model_validator(mode="after")
    def _normalize_text(self) -> "IndexDocument":
        if self.text is None:
            return self

        raw_text = self.text

        try:
            json.loads(self.text)
        except (TypeError, json.JSONDecodeError):
            normalized = {"text": raw_text}
            self.text = json.dumps(normalized, indent=2, ensure_ascii=False)
            return self

        return self

    def _get_structured_data(self) -> dict[str, Any]:
        if self.structured_data is not None:
            return self.structured_data

        return json.loads(self.text)

    def _get_text(self) -> str:
        if self.text is not None:
            return self.text
        return json.dumps(self.structured_data, indent=2, ensure_ascii=False)

    async def materialize(self, embedder: "OpenAIEmbedder") -> dict[str, Any]:
        """Return a fully populated document payload ready for indexing."""
        document_id = self.id or hashlib.sha256(self.text.encode("utf-8")).hexdigest()

        document_embedding = self.embedding
        if document_embedding is None:
            document_embedding = await embedder.embed(self.text)

        structured_data = self._get_structured_data()

        payload: dict[str, Any] = {
            "id": document_id,
            "text": self.text,
            "embedding": document_embedding,
        }

        if structured_data is not None:
            for key, value in structured_data.items():
                if key not in payload:
                    payload[key] = value

        return payload

    @classmethod
    async def materialize_many(
        cls,
        documents: Iterable["IndexDocument"],
        embedder: "OpenAIEmbedder",
    ) -> list[dict[str, Any]]:
        """Return fully populated document payloads ready for indexing."""
        docs = list(documents)
        if not docs:
            return []

        texts_to_embed: list[str] = []
        for document in docs:
            if document.embedding is None:
                texts_to_embed.append(document.text)

        embeddings: list[list[float]] = []
        if texts_to_embed:
            embeddings = await embedder.embed_batch(texts_to_embed)

        embedded_cursor = 0
        materialized: list[dict[str, Any]] = []
        for document in docs:
            embedding = document.embedding
            if embedding is None:
                embedding = embeddings[embedded_cursor]
                embedded_cursor += 1

            document_id = (
                document.id or hashlib.sha256(document.text.encode("utf-8")).hexdigest()
            )

            structured_data = document._get_structured_data()

            payload: dict[str, Any] = {
                "id": document_id,
                "text": document.text,
                "embedding": embedding,
            }

            if structured_data is not None:
                for key, value in structured_data.items():
                    if key not in payload:
                        payload[key] = value

            materialized.append(payload)

        if embedded_cursor != len(embeddings):
            raise RuntimeError("embed_batch returned unexpected number of embeddings")

        return materialized


class IndexingRequest(BaseModel):
    documents: list[IndexDocument]
    corpus_name: str
    config: dict[str, Any] | None = None
    doc_schema: type[BaseModel] | None = Field(default=None, exclude=True, repr=False)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _validate_documents_against_schema(self) -> "IndexingRequest":
        if self.doc_schema is None:
            return self

        if not issubclass(self.doc_schema, BaseModel):
            raise TypeError(
                "IndexingRequest.doc_schema must be a Pydantic BaseModel subclass."
            )

        for index, document in enumerate(self.documents):
            if document.structured_data is not None:
                try:
                    self.doc_schema.model_validate(document.structured_data)
                except ValidationError as exc:
                    raise ValueError(
                        f"Document at position {index} does not conform to schema "
                        f"{self.doc_schema.__name__}: {exc.errors()}"
                    ) from exc
                continue

            try:
                parsed = self.doc_schema.model_validate_json(document.text)
            except ValidationError as exc:  # pragma: no cover - defensive
                raise ValueError(
                    f"Document at position {index} does not conform to schema "
                    f"{self.doc_schema.__name__}: {exc.errors()}"
                ) from exc

            document.structured_data = parsed.model_dump()

        return self


class DeleteCorpusRequest(BaseModel):
    corpus_name: str
