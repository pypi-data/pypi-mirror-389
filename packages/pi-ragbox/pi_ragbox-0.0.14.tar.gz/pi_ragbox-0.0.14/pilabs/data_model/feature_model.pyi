from .document_model import Document as Document
from .query_model import SearchQuery as SearchQuery
from _typeshed import Incomplete
from pydantic import BaseModel
from typing import Any, Callable

class QueryDerivedFeature(BaseModel):
    name: str
    fn: Callable[[SearchQuery], Any]
    model_config: Incomplete

class DocDerivedFeature(BaseModel):
    name: str
    fn: Callable[[Document], Any]
    model_config: Incomplete

class FeatureNotPopulatedError(RuntimeError): ...

class PiPrompt(BaseModel):
    name: str | None
    prompt: str
    weight: float
    def __init__(self, *args: Any, **data: Any) -> None: ...

class CrossEncoderPrompt(BaseModel):
    name: str | None
    instruction: str | None
    hotswaps: str | None
    model_config: Incomplete
    def __init__(self, *args: Any, **data: Any) -> None: ...
