from _typeshed import Incomplete
from collections.abc import Mapping as Mapping
from pilabs.clients.embedding_client import OpenAIEmbedder as OpenAIEmbedder
from pydantic import BaseModel
from typing import Any, Iterable

class CorpusIndexDocument(BaseModel):
    id: str | None
    corpus_domain: str
    corpus_name: str
    config: dict[str, Any] | None
    def _set_id(self) -> CorpusIndexDocument: ...

class IndexDocument(BaseModel):
    id: str | None
    text: str | None
    embedding: list[float] | None
    structured_data: dict[str, Any] | None
    @classmethod
    def _validate_inputs(cls, data: Any) -> Any: ...
    def _normalize_text(self) -> IndexDocument: ...
    def _get_structured_data(self) -> dict[str, Any]: ...
    def _get_text(self) -> str: ...
    async def materialize(self, embedder: OpenAIEmbedder) -> dict[str, Any]: ...
    @classmethod
    async def materialize_many(cls, documents: Iterable['IndexDocument'], embedder: OpenAIEmbedder) -> list[dict[str, Any]]: ...

class IndexingRequest(BaseModel):
    documents: list[IndexDocument]
    corpus_name: str
    config: dict[str, Any] | None
    doc_schema: type[BaseModel] | None
    model_config: Incomplete
    def _validate_documents_against_schema(self) -> IndexingRequest: ...

class DeleteCorpusRequest(BaseModel):
    corpus_name: str
