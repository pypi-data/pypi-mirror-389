from __future__ import annotations

import json

from pilabs.data_model import (
    Params,
    PiPrompt,
    QueryClassificationPrompt,
    SearchQuery,
    SearchResults,
    pi_parallel_retrieval,
)
from pilabs.data_model.piragbox_model import piragbox


@piragbox(
    params={
        "query_classification_threshold": 0.5,
        "recipe_doc_threshold": 0.5,
    }
)
async def search_demo(
    query: SearchQuery,
    ranking_params: Params,
) -> SearchResults:
    """
    Execute the ranking pipeline for a given query.
    """
    fanout_queries = await query.fanout_queries()
    print(fanout_queries)

    query = await query.classify(
        query_classification_prompts=[
            QueryClassificationPrompt(
                name="recipes",
                prompt="Is this query about recipes?",
            ),
            QueryClassificationPrompt(
                name="podcasts",
                prompt="Is this query about podcasts?",
            ),
        ],
    )

    print(f"{query.model_dump_json(indent=2)=}")

    search_results = await pi_parallel_retrieval(
        query,
        query_param_list=[
            {"kind": "keyword", "corpus": "nlweb"},
            {"kind": "dense", "corpus": "nlweb"},
        ],
        require_success=True,
    )

    await search_results.add_pi_features(
        prompts=[
            PiPrompt(
                name="recipes",
                prompt="Is the response about recipes?",
            ),
            PiPrompt(
                name="podcasts",
                prompt="Is the response about podcasts?",
            ),
            PiPrompt(
                name="Relevance",
                prompt="Is the response relevant to the input?",
            ),
        ],
        pi_input_builder=lambda doc, query: json.dumps(
            {"input": query, "response": doc.content}, indent=2
        ),
        pi_input_builder_kwargs={"query": query.query},
    )

    if query.features["recipes"] > ranking_params.query_classification_threshold:
        search_results.filter(
            predicate=lambda doc: doc.features["recipes"]
            > ranking_params.recipe_doc_threshold
        )

    search_results.score(scoring_fn=lambda doc: doc.features["Relevance"])

    return search_results
