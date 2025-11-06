from __future__ import annotations

import json
import os
from contextlib import AbstractAsyncContextManager

import httpx
from pilabs.data_model import SearchQuery, SearchResults

DEFAULT_RETRIEVAL_SERVICE_URL = "https://ragbox-retrieval.withpi.ai"


class RetrievalClient(AbstractAsyncContextManager["RetrievalClient"]):
    _base_url: str
    _timeout: float | httpx.Timeout | None
    _client: httpx.AsyncClient | None

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | httpx.Timeout | None = 10.0,
    ) -> None:
        self._base_url = base_url or os.getenv(
            "RETRIEVAL_SERVICE_URL",
            DEFAULT_RETRIEVAL_SERVICE_URL,
        )
        self._timeout = timeout
        self._client = None

    async def retrieve(self, query: SearchQuery) -> SearchResults:
        if self._client is None:
            raise RuntimeError(
                "RetrievalClient must be used as an async context manager. "
                "Use 'async with RetrievalClient(...) as client:'"
            )

        try:
            response = await self._client.post(
                "/retrieve",
                json=query.model_dump(),
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

        results = SearchResults.model_validate(response.json())
        # Tag the results with the query.
        results._add_retrieval_query(query)
        return results

    async def __aenter__(self) -> RetrievalClient:
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._client is not None:
            await self._client.aclose()
