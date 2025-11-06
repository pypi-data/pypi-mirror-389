from __future__ import annotations

import statistics

from pilabs.data_model import (
    Params,
    PiPrompt,
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
        "verticals": [
            "recipes",
            "travel/tourism, sightseeing, or things to do",
            "movies",
            "events",
            "educational content",
            "podcasts",
        ]
    }
)
async def search_nlweb_newapi(
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

    # QUERY CLASSIFICATION
    for vertical in ranking_params.verticals:
        query.features[vertical] = PiPrompt(f"Is the query about {vertical}?")

    await query.features.populate()

    query.features["is_vertical_query"] = any(
        query.features.get(k, 0.0) > ranking_params.query_classification_threshold
        for k in ranking_params.verticals
    )
    query.features["selected_verticals"] = [
        v
        for v in ranking_params.verticals
        if query.features.get(v, 0.0) > ranking_params.query_classification_threshold
    ]

    # --- New dict-based Features API ---
    # Always compute generic Relevance
    search_results.features["Relevance"] = PiPrompt(
        "Is the response relevant to the input?"
    )

    if query.features["is_vertical_query"]:
        # Add one feature per selected vertical, using the *human* label as the key
        pi_score_features = []
        for selected_vertical in query.features["selected_verticals"]:
            search_results.features[selected_vertical] = PiPrompt(
                f"Is the response about {selected_vertical} or a {selected_vertical} website?"
            )
            pi_score_features.append(selected_vertical)
        # Also compute product-store features
        search_results.features["is_product_store"] = PiPrompt(
            "Is this website a store that sells products?"
        )
    else:
        # Shopping-oriented features
        search_results.features["is_shop_relevant"] = PiPrompt(
            "Is the shop relevant to the query?"
        )
        search_results.features["is_product_sold"] = PiPrompt(
            "Does the shop sell the product explicitly mentioned in the query?"
        )
        search_results.features["is_equipment_sold"] = PiPrompt(
            "Does the shop sell the equipments that are being asked for in the query?"
        )
        search_results.features["are_products_appropriate"] = PiPrompt(
            "Are the products appropriate for the audience mentioned in the query?"
        )
        pi_score_features = [
            "is_shop_relevant",
            "is_product_sold",
            "is_equipment_sold",
            "are_products_appropriate",
        ]

    await search_results.features.populate(query, overwrite=True)

    search_results.features["is_shopping_domain"] = (
        lambda doc: "myshopify.com" in doc.content["url"]
    )

    # FILTER AND SCORE
    # 1. Filter shopping domains and pages for vertical queries.
    if query.features["is_vertical_query"]:
        search_results.filter(lambda doc: doc.features["is_shopping_domain"] is False)
        search_results.filter(
            lambda doc: doc.features["is_product_store"]
            < ranking_params.is_product_store_threshold
        )

    # 2. If any verticals were selected, filter docs not topical at all for any of them.
    selected_verticals = query.features.get("selected_verticals", [])
    if selected_verticals:
        search_results.filter(
            lambda doc: any(
                doc.features.get(vertical, 0.0)
                > ranking_params.document_vertical_topicality_threshold
                for vertical in selected_verticals
            )
        )

    # 3. Calculate final score as Pi Score (for shopping or vertical dimensions) plus
    # a generic relevance cross-encoder score.
    def nlweb_composite_score(doc):
        ce_score = doc.features["Relevance"]
        pi_score = statistics.mean([doc.features[s] for s in pi_score_features])
        ce_weight = ranking_params.ce_final_score_weight
        return float(((pi_score + ce_weight * ce_score) / (1.0 + ce_weight)) * 100)

    search_results.score(scoring_fn=nlweb_composite_score)

    return search_results
