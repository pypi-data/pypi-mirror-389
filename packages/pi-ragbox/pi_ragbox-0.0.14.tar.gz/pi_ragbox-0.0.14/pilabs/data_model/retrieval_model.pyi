from .document_model import SearchResults as SearchResults
from .query_model import SearchQuery as SearchQuery
from .request_context_model import get_ctx as get_ctx
from typing import Any, Mapping, Sequence

async def pi_parallel_retrieval(base_query: SearchQuery, query_param_list: Sequence[Mapping[str, Any]], *, require_success: bool = True, max_concurrency: int | None = None) -> SearchResults: ...
