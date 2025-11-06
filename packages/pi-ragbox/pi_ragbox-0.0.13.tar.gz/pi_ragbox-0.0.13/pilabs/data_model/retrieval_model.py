import asyncio
from typing import Any, Mapping, Optional, Sequence

from .document_model import SearchResults
from .query_model import SearchQuery
from .request_context_model import get_ctx


async def pi_parallel_retrieval(
    base_query: SearchQuery,
    query_param_list: Sequence[Mapping[str, Any]],
    *,
    require_success: bool = True,
    max_concurrency: Optional[int] = None,
) -> SearchResults:
    """
    Send N retrievals in parallel (built from base_query + each query_params),
    then merge their SearchResults in the same order as query_param_list.
    """
    retrieval_client = get_ctx().retrieval_client

    # Optional concurrency gate
    semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else None

    async def run_retrieve(params: Mapping[str, Any]):
        q = base_query.model_copy(update={"query_params": params})
        if semaphore:
            async with semaphore:
                return await retrieval_client.retrieve(q)
        return await retrieval_client.retrieve(q)

    coroutines = [run_retrieve(p) for p in query_param_list]

    if require_success:
        # All-or-nothing: if one fails, others are cancelled.
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for c in coroutines:
                tasks.append(tg.create_task(c))
        results = [t.result() for t in tasks]
    else:
        # Keep successes, skip failures.
        results = await asyncio.gather(*coroutines, return_exceptions=True)

    search_results = SearchResults(results=[])
    for r in results:
        if isinstance(r, Exception):
            continue
        assert isinstance(r, SearchResults)
        search_results.merge(r)
    return search_results
