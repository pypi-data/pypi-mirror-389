from __future__ import annotations

import json
import os
from contextlib import AbstractAsyncContextManager

import httpx
from pilabs.indexing_model import DeleteCorpusRequest, IndexingRequest

DEFAULT_INDEXING_SERVICE_URL = "https://ragbox-retrieval.withpi.ai"


class IndexingClient(AbstractAsyncContextManager["IndexingClient"]):
    _base_url: str
    _timeout: float | httpx.Timeout | None
    _client: httpx.AsyncClient | None

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | httpx.Timeout | None = 180.0,
    ) -> None:
        self._base_url = base_url or os.getenv(
            "INDEXING_SERVICE_URL",
            DEFAULT_INDEXING_SERVICE_URL,
        )
        self._timeout = timeout
        self._client = None

    async def index(self, request: IndexingRequest) -> None:
        if self._client is None:
            raise RuntimeError(
                "IndexingClient must be used as an async context manager. "
                "Use 'async with IndexingClient(...) as client:'"
            )

        try:
            response = await self._client.post(
                "/index",
                json=request.model_dump(),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except ValueError:
                detail = e.response.text
            raise RuntimeError(
                f"{e}\nServer detail: {json.dumps(detail, indent=2)}"
            ) from e

    async def delete_corpus(self, request: DeleteCorpusRequest) -> None:
        if self._client is None:
            raise RuntimeError(
                "IndexingClient must be used as an async context manager. "
                "Use 'async with IndexingClient(...) as client:'"
            )

        try:
            response = await self._client.post(
                "/delete_corpus",
                json=request.model_dump(),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except ValueError:
                detail = e.response.text
            raise RuntimeError(
                f"{e}\nServer detail: {json.dumps(detail, indent=2)}"
            ) from e

    async def list_corpora(self) -> list[str]:
        if self._client is None:
            raise RuntimeError(
                "IndexingClient must be used as an async context manager. "
                "Use 'async with IndexingClient(...) as client:'"
            )

        try:
            response = await self._client.post("/list_corpora")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except ValueError:
                detail = e.response.text
            raise RuntimeError(
                f"{e}\nServer detail: {json.dumps(detail, indent=2)}"
            ) from e

    async def __aenter__(self) -> IndexingClient:
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._client is not None:
            await self._client.aclose()
