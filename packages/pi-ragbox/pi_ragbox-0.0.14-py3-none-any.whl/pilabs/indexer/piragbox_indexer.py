from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pilabs.indexing_client import IndexingClient
from pilabs.indexing_model import DeleteCorpusRequest, IndexDocument, IndexingRequest
from tqdm import tqdm

BATCH_SIZE = 200
MAX_INDEX_PAYLOAD_BYTES = 3 * 1024 * 1024  # 3 MiB limit per request


class PiRagBoxIndexer:
    def __init__(self) -> None:
        self._client = IndexingClient()
        self._has_active_client = False

    async def __aenter__(self) -> PiRagBoxIndexer:
        await self._client.__aenter__()
        self._has_active_client = True
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._has_active_client:
            await self._client.__aexit__(*exc_info)
            self._has_active_client = False

    def _get_client(self) -> IndexingClient:
        if not self._has_active_client:
            raise RuntimeError(
                "PiRagBoxIndexer must be used as an async context manager. "
                "Use 'async with PiRagBoxIndexer() as indexer:'"
            )
        return self._client

    async def index(
        self,
        document: IndexDocument,
        corpus_name: str,
        doc_schema: type[BaseModel] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        client = self._get_client()
        await client.index(
            IndexingRequest(
                documents=[document],
                corpus_name=corpus_name,
                doc_schema=doc_schema,
                config=config,
            )
        )

    async def index_batch(
        self,
        documents: list[IndexDocument],
        corpus_name: str,
        doc_schema: type[BaseModel] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        client = self._get_client()
        if not documents:
            return

        with tqdm(
            total=len(documents),
            desc=f"Indexing corpus {corpus_name}",
            unit="doc",
        ) as progress:

            async def send_within_limit(batch_docs: list[IndexDocument]) -> None:
                request = IndexingRequest(
                    documents=batch_docs,
                    corpus_name=corpus_name,
                    doc_schema=doc_schema,
                    config=config,
                )
                payload_size_bytes = len(request.model_dump_json().encode("utf-8"))
                if payload_size_bytes <= MAX_INDEX_PAYLOAD_BYTES:
                    await client.index(request)
                    progress.update(len(batch_docs))
                    return

                if len(batch_docs) == 1:
                    raise RuntimeError(
                        "Index request payload exceeds 3 MiB even for a single document."
                    )

                midpoint = len(batch_docs) // 2
                await send_within_limit(batch_docs[:midpoint])
                await send_within_limit(batch_docs[midpoint:])

            for start in range(0, len(documents), BATCH_SIZE):
                batch = documents[start : start + BATCH_SIZE]
                await send_within_limit(batch)

    async def index_corpus(
        self,
        documents: list[IndexDocument],
        corpus_name: str,
        doc_schema: type[BaseModel] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        Create index for the given corpus and index all provided documents.

        Args:
            documents: Iterable of index documents to index
            corpus_name: Name of the corpus (used as index name)
            config: Optional configuration overrides forwarded to the indexing service
        """
        client = self._get_client()
        await client.delete_corpus(DeleteCorpusRequest(corpus_name=corpus_name))

        await self.index_batch(
            documents,
            corpus_name,
            doc_schema=doc_schema,
            config=config,
        )

    async def delete_corpus(self, corpus_name: str) -> None:
        """
        Delete the OpenSearch index associated with the provided corpus name.

        Args:
            corpus_name: Name of the corpus (used as index name)
        """
        client = self._get_client()
        await client.delete_corpus(DeleteCorpusRequest(corpus_name=corpus_name))

    async def list_corpora(self) -> list[str]:
        client = self._get_client()
        return await client.list_corpora()
