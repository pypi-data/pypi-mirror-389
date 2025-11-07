from _typeshed import Incomplete
from contextlib import asynccontextmanager
from dataclasses import dataclass
from fastapi import FastAPI, Request as Request
from pilabs.clients import CrossEncoderClient, PiScorerClient, QueryFanoutClient, RetrievalClient
from pilabs.data_model import Document as Document, SearchQuery as SearchQuery, SearchResults as SearchResults
from pydantic import BaseModel
from typing import AsyncGenerator

builtin_flows_path: Incomplete
pipelines: Incomplete

@dataclass
class AppStateHolder:
    pi_scorer_client: PiScorerClient
    retrieval_client: RetrievalClient
    cross_encoder_client: CrossEncoderClient
    fanout_query_client: QueryFanoutClient

app: Incomplete

def get_app_state() -> AppStateHolder: ...

AppState: Incomplete

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]: ...
async def profile_request(request: Request, call_next): ...
async def bind_request_state_ctx(app_state: AppState) -> AsyncGenerator[None, None]: ...
def get_pi_scorer_client(app_state: AppState) -> PiScorerClient: ...
def get_retrieval_client(app_state: AppState) -> RetrievalClient: ...
async def root(): ...
def _rewrite_doc_content(doc: Document) -> Document: ...
async def search(query: SearchQuery) -> SearchResults: ...

class SearchFlow(BaseModel):
    name: str
    params: dict

class SearchMetadata(BaseModel):
    search_flows: list[SearchFlow]
    identifier: str

async def search_metadata() -> SearchMetadata: ...
