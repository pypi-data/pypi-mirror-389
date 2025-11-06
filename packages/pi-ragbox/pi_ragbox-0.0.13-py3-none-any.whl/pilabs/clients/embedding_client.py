import os
from typing import Any

import httpx
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, ConfigDict


class Embedder(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    dimensions: int

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError()


class OpenAIEmbedder(Embedder):
    model: str

    def model_post_init(self, __context: Any) -> None:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not azure_endpoint or not azure_api_key:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set"
            )

        self._client = AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version="2024-10-21",
        )

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            input=text,
            model=self.model,
            dimensions=self.dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self._client.embeddings.create(
            input=texts,
            model=self.model,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]


class PiEmbedder(Embedder):
    api_key: str | None = None
    embed_url: str = "https://api.withpi.ai/v1/search/embed"
    hotswaps: str = "pi-embedder-bert:pi-embedder-multilingual"
    timeout: float | httpx.Timeout | None = 10.0

    def model_post_init(self, __context: Any) -> None:
        self._api_key = self.api_key or os.getenv("WITHPI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "WITHPI_API_KEY must be provided or set in environment variables"
            )

    async def embed(self, text: str) -> list[float]:
        embeddings = await self.embed_batch([text])
        if not embeddings:
            raise ValueError("PiEmbedder returned no embedding for the provided text")
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        headers = {
            "x-api-key": self._api_key,
            "x-hotswaps": self.hotswaps,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout, http2=True) as client:
            response = await client.post(
                self.embed_url,
                headers=headers,
                json={"query": list(texts)},
            )
            response.raise_for_status()
            embeddings = response.json()

        if len(embeddings) != len(texts):
            raise ValueError(
                "PiEmbedder response embeddings count does not match input count"
            )

        for vector in embeddings:
            if len(vector) != self.dimensions:
                raise ValueError(
                    "PiEmbedder embedding dimension mismatch with configured dimensions"
                )

        return embeddings
