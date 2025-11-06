from __future__ import annotations

import json
import statistics

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
        "is_product_store_threshold": 0.25,
        "document_vertical_topicality_threshold": 0.1,
        "ce_final_score_weight": 0.4,
    }
)
async def search_nlweb(
    query: SearchQuery,
    ranking_params: Params,
) -> SearchResults:
    search_results = await pi_parallel_retrieval(
        query,
        query_param_list=[
            {"kind": "keyword", "corpus": "nlweb"},
            {"kind": "dense", "corpus": "nlweb"},
            {"kind": "keyword", "corpus": "nlweb_non_shopify"},
            {"kind": "dense", "corpus": "nlweb_non_shopify"},
        ],
        require_success=True,
    )

    NLWEB_VERTICALS = [
        "recipes",
        "travel/tourism, sightseeing, or things to do",
        "movies",
        "events",
        "educational content",
        "podcasts",
    ]

    # QUERY CLASSIFICATION
    query = await query.classify(
        query_classification_prompts=[
            QueryClassificationPrompt(
                name=vertical, prompt=f"Is this query about {vertical}?"
            )
            for vertical in NLWEB_VERTICALS
        ],
    )

    query.features["is_vertical_query"] = any(
        query.features.get(k, 0.0) > ranking_params.query_classification_threshold
        for k in NLWEB_VERTICALS
    )
    query.features["selected_verticals"] = [
        v
        for v in NLWEB_VERTICALS
        if query.features.get(v, 0.0) > ranking_params.query_classification_threshold
    ]

    vertical_prompts = [
        PiPrompt(
            name=selected_vertical,
            prompt=f"Is the response about {selected_vertical} or a {selected_vertical} website?",
        )
        for selected_vertical in query.features["selected_verticals"]
    ]

    is_vertical_query = query.features["is_vertical_query"]
    if is_vertical_query:
        vertical_prompts.append(
            PiPrompt(
                name="is_product_store",
                prompt="Is this website a store that sells products?",
            ),
        )
        pi_score_keys = [v for v in query.features["selected_verticals"]]
    else:
        vertical_prompts.extend(
            [
                PiPrompt(
                    name="is_shop_relevant",
                    prompt="Is the shop relevant to the query?",
                ),
                PiPrompt(
                    name="is_product_sold",
                    prompt="Does the shop sell the product explicitly mentioned in the query?",
                ),
                PiPrompt(
                    name="is_equipment_sold",
                    prompt="Does the shop sell the equipments that are being asked for in the query?",
                ),
                PiPrompt(
                    name="are_products_appropriate",
                    prompt="Are the products appropriate for the audience mentioned in the query?",
                ),
            ]
        )
        pi_score_keys = [
            "is_shop_relevant",
            "is_product_sold",
            "is_equipment_sold",
            "are_products_appropriate",
        ]

    base_prompts = [
        PiPrompt(
            name="Relevance",
            prompt="Is the response relevant to the input?",
        ),
    ]

    # ADD PI SIGNALS
    await search_results.add_pi_features(
        prompts=base_prompts + vertical_prompts,
        pi_input_builder=lambda doc, query: json.dumps(
            {"input": query, "response": doc.content}, indent=2
        ),
        pi_input_builder_kwargs={"query": query.query},
    )

    await search_results.add_features(
        is_shopping_domain=lambda doc: "myshopify.com" in doc.content["url"]
    )

    # FILTER AND SCORE
    # 1. Filter shopping domains and pages for vertical queries.
    if is_vertical_query:
        search_results.filter(
            predicate=lambda doc: doc.features.get("is_shopping_domain") is False
        )
        search_results.filter(
            predicate=lambda doc: doc.features.get("is_product_store")
            < ranking_params.is_product_store_threshold
        )

    # 2. If any verticals were selected, filter docs not topical at all for any of them.
    selected_verticals = query.features.get("selected_verticals", [])
    if selected_verticals:
        search_results.filter(
            predicate=lambda doc: any(
                doc.features.get(vertical, 0.0)
                > ranking_params.document_vertical_topicality_threshold
                for vertical in selected_verticals
            )
        )

    # 3. Calculate final score as Pi Score (for shopping or vertical dimensions) plus
    # a generic relevance cross-encoder score.
    def nlweb_composite_score(doc):
        ce_score = doc.features["Relevance"]
        pi_score = statistics.mean([doc.features[s] for s in pi_score_keys])
        ce_weight = ranking_params.ce_final_score_weight
        return float(((pi_score + ce_weight * ce_score) / (1.0 + ce_weight)) * 100)

    search_results.score(scoring_fn=nlweb_composite_score)

    return search_results
