from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import MappingProxyType

import pytest
from .request_context_model import set_ctx
from .query_model import QueryClassificationPrompt, SearchQuery


def test_defaults_are_immutable_mapping_proxies():
    query = SearchQuery(query="weather update")

    assert query.limit == 10
    assert isinstance(query.query_params, MappingProxyType)
    assert isinstance(query.classification_signals, MappingProxyType)
    assert dict(query.query_params) == {}
    assert dict(query.classification_signals) == {}

    with pytest.raises(TypeError):
        query.query_params["unit"] = "metric"  # type: ignore
    with pytest.raises(TypeError):
        query.classification_signals["score"] = 1.0  # type: ignore


def test_mappings_are_coerced_to_mapping_proxies():
    query = SearchQuery(
        query="latest news",
        query_params={"page": 1, "filters": {"category": "sports"}},
        classification_signals=[("sports", 0.8), ("finance", 0.2)],  # type: ignore
    )

    assert isinstance(query.query_params, MappingProxyType)
    assert isinstance(query.classification_signals, MappingProxyType)
    assert dict(query.classification_signals) == {"sports": 0.8, "finance": 0.2}


def test_equality_and_hash_ignore_classification_signals():
    first = SearchQuery(
        query="pizza places",
        limit=5,
        query_params={"location": {"lat": 1.0, "lon": 2.0}, "tags": ["open_late"]},
    )
    second = SearchQuery(
        query="pizza places",
        limit=5,
        query_params={"tags": ["open_late"], "location": {"lon": 2.0, "lat": 1.0}},
        classification_signals={"popularity": 0.9},  # type: ignore
    )
    third = SearchQuery(query="pizza places", limit=10)

    assert first == second
    assert hash(first) == hash(second)
    assert first != third


def test_classify_updates_features_with_pi_scorer_result():
    prompts = [
        QueryClassificationPrompt(name="safety", prompt="Rate the safety"),
        QueryClassificationPrompt(name="novelty", prompt="Rate the novelty"),
    ]
    query = SearchQuery(query="best hiking trails")

    class FakePiScorerClient:
        async def score(self, *, llm_input, llm_output, scoring_spec, **kwargs):
            assert llm_input == ""
            assert "best hiking trails" in llm_output
            return {item["label"]: idx / 10 for idx, item in enumerate(scoring_spec, 1)}

    mock_client = FakePiScorerClient()

    @dataclass
    class MockAppStateHolder:
        pi_scorer_client: object = None

    set_ctx(MockAppStateHolder(pi_scorer_client=mock_client))

    async def exercise():
        result = await query.classify(query_classification_prompts=prompts)

        assert result is query
        assert isinstance(query.classification_signals, MappingProxyType)
        assert dict(query.classification_signals) == {"safety": 0.1, "novelty": 0.2}

    asyncio.run(exercise())
