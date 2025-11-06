from __future__ import annotations

import os
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any

import httpx

DEFAULT_CROSS_ENCODER_URL = "https://api.withpi.ai/v1/search/query_to_passage/score"
DEFAULT_CROSS_ENCODER_HOTSWAPS = "pi-cross-encoder-small:pi-cross-encoder-qwen"
DEFAULT_INSTRUCTION = (
    "Given a web search query, retrieve relevant passages that answer the query"
)


class CrossEncoderClient(AbstractAsyncContextManager["CrossEncoderClient"]):
    _score_url: str
    _api_key: str
    _timeout: float | httpx.Timeout | None
    _client: httpx.AsyncClient | None
    _hotswaps: str

    def __init__(
        self,
        score_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float | httpx.Timeout | None = 10.0,
        hotswaps: str | None = None,
    ) -> None:
        self._score_url = score_url or DEFAULT_CROSS_ENCODER_URL
        self._api_key = api_key or os.getenv("WITHPI_API_KEY", "")
        self._timeout = timeout
        self._hotswaps = hotswaps or DEFAULT_CROSS_ENCODER_HOTSWAPS
        self._client = None

    async def score(
        self,
        query: str,
        passages: Sequence[str],
        *,
        instruction: str | None = None,
        hotswaps: str | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError(
                "CrossEncoderClient must be used as an async context manager. "
                "Use 'async with CrossEncoderClient(...) as client:'"
            )

        headers = {
            "x-api-key": self._api_key,
            "x-hotswaps": hotswaps or self._hotswaps,
            "Content-Type": "application/json",
        }

        response = await self._client.post(
            self._score_url,
            headers=headers,
            json={
                "query": query,
                "passages": list(passages),
                "instruction": instruction or DEFAULT_INSTRUCTION,
            },
        )
        response.raise_for_status()
        return response.json()

    async def __aenter__(self) -> CrossEncoderClient:
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            http2=True,
            limits=httpx.Limits(
                max_connections=200,
                keepalive_expiry=60,
                max_keepalive_connections=200,
            ),
        )
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._client is not None:
            await self._client.aclose()
