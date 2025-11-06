from __future__ import annotations

import os
from typing import Any

from openai import AsyncAzureOpenAI
from pydantic import BaseModel, ConfigDict

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_MAX_OUTPUT_TOKENS = 1024
DEFAULT_VERBOSITY = "minimal"
DEFAULT_AZURE_ENDPOINT = "https://zach-m9irbgmv-eastus2.openai.azure.com"
DEFAULT_API_VERSION = "2024-12-01-preview"

INSTRUCTION_PROMPT = (
    "I am training a query fanout model for my agent that will:\n"
    "- Take a broad, complex query expressed by a human\n"
    "- Convert it into a set of narrow, targeted information needs\n"
    "- Enable querying specific backends with these narrowed queries\n"
    "\n"
    "For each broad query you receive, generate a prioritized set of narrow fanout queries. "
    "Order them by importance, where:\n"
    "- Most important narrow queries appear first\n"
    "- Importance is determined by how much essential information from the broad query each narrow query covers\n"
    "\n"
    "Requirements for individual narrow queries:\n"
    "1. Must seek a single piece of information\n"
    "2. Must avoid compound elements (e.g., no 'look for X and Y')\n"
    "3. Must be formulated for targeted question answering\n"
    "\n"
    "Requirements for the collection of narrow queries:\n"
    "1. Must collectively cover all implicit information needs from the broad query\n"
    "2. Must be non-redundant and target specific, non-overlapping information needs\n"
    "\n"
    "Post-generation process:\n"
    "- Review all generated narrow queries\n"
    "- If any query is still too broad, decompose it further into multiple narrow queries\n"
    "- Repeat this process until all queries are appropriately narrow and specific\n"
    "\n"
    "Example input and output:\n"
    'Input broad query: "I am creating a diet for my child and want to understand how much dairy products to use"\n'
    "Output:\n"
    "{\n"
    '    "query": "I am creating a diet for my child and want to understand how much dairy products to use",\n'
    '    "fanout_queries": [\n'
    '        "Health benefits milk for kids",\n'
    '        "Nutritional value of milk",\n'
    '        "Nutritional value of cheese",\n'
    '        "Recommended calorie consumption children",\n'
    '        "Is yogurt good for kids?"\n'
    "    ]\n"
    "}\n"
    "\n"
    "Respond using structured output only, conforming to the expected schema, and keep any language outside of the structured data to a minimum."
)


class FanoutQueries(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fanout_queries: list[str]


class QueryFanoutClient:
    """Client for generating query fanouts using the OpenAI Responses API."""

    _client: AsyncAzureOpenAI
    _model: str
    _temperature: float
    _max_output_tokens: int
    _instruction_prompt: str
    _verbosity: str

    def __init__(
        self,
        *,
        client: AsyncAzureOpenAI | None = None,
        api_key: str | None = None,
        azure_endpoint: str | None = None,
        api_version: str | None = None,
        model: str = DEFAULT_MODEL,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        instruction_prompt: str = INSTRUCTION_PROMPT,
        verbosity: str = DEFAULT_VERBOSITY,
    ) -> None:
        self._client = client or self._build_client(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._instruction_prompt = instruction_prompt
        self._verbosity = verbosity

    @staticmethod
    def _build_client(
        *,
        api_key: str | None,
        azure_endpoint: str | None,
        api_version: str | None,
    ) -> AsyncAzureOpenAI:
        client_kwargs: dict[str, Any] = {
            "azure_endpoint": azure_endpoint or DEFAULT_AZURE_ENDPOINT,
            "api_version": api_version or DEFAULT_API_VERSION,
            "timeout": 240.0,
            "max_retries": 3,
        }

        resolved_api_key = api_key or os.getenv("AZURE_OPENAI_GPT_API_KEY")
        if resolved_api_key:
            client_kwargs["api_key"] = resolved_api_key

        return AsyncAzureOpenAI(**client_kwargs)

    async def generate_fanout(
        self,
        query: str,
        *,
        instruction_prompt: str | None = None,
    ) -> list[str]:
        """Generate a list of fanout queries for the supplied broad query."""
        response = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=self._build_messages(query, instruction_prompt),
            temperature=0.0,
            max_completion_tokens=self._max_output_tokens,
            response_format=FanoutQueries,
        )
        parsed = FanoutQueries.model_validate(response.choices[0].message.parsed)

        # The structured response is already validated; return the list directly.
        return list(parsed.fanout_queries)

    def _build_messages(
        self,
        query: str,
        instruction_prompt: str | None = None,
    ) -> list:
        return [
            {
                "role": "system",
                "content": instruction_prompt or self._instruction_prompt,
            },
            {
                "role": "user",
                "content": query,
            },
        ]
