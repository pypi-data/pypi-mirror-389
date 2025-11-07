from __future__ import annotations

from pilabs.data_model import (
    Params,
    PiPrompt,
    CrossEncoderPrompt,
    SearchQuery,
    SearchResults,
    pi_parallel_retrieval,
)
from pilabs.data_model.piragbox_model import piragbox


@piragbox(params={"corpus_names": "monday"})
async def search_simple(
    query: SearchQuery,
    ranking_params: Params,
) -> SearchResults:
    corpora = [
        corpus.strip()
        for corpus in ranking_params.corpus_names.split(",")
        if corpus.strip()
    ]

    query_param_list = [
        {"kind": kind, "corpus": corpus}
        for corpus in corpora
        for kind in ("keyword", "dense")
    ]

    search_results = await pi_parallel_retrieval(
        query,
        query_param_list=query_param_list,
        require_success=True,
    )

    search_results.features["pi_relevance"] = PiPrompt(
        "Is the response relevant to the input search query?"
    )
    search_results.features["ce_relevance"] = CrossEncoderPrompt(
        "Given a web search query, retrieve relevant passages that answer the query"
    )
    await search_results.features.populate(query, overwrite=True)

    search_results.score(
        scoring_fn=lambda doc: doc.features["pi_relevance"]
        + doc.features["ce_relevance"]
    )

    return search_results
