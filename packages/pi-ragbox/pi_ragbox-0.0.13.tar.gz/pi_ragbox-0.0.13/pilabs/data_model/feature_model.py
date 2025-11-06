from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .document_model import Document
    from .query_model import SearchQuery


class QueryDerivedFeature(BaseModel):
    """
    Defines a rule for computing a derived feature from a SearchQuery.
    Each rule is a named function that takes a SearchQuery and returns a value.
    The function can be synchronous or asynchronous.
    """

    name: str = Field(..., description="The name of the derived feature to add.")

    fn: Callable[[SearchQuery], Any] = Field(
        ..., description="A callable that computes the feature from the query."
    )

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)


class DocDerivedFeature(BaseModel):
    """
    Defines a rule for computing a derived feature from a Document.
    Each rule is a named function that takes a Document and returns a value.
    The function can be synchronous or asynchronous.
    """

    name: str = Field(..., description="The name of the derived feature to add.")

    fn: Callable[[Document], Any] = Field(
        ..., description="A callable that computes the feature from the document."
    )

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)


class FeatureNotPopulatedError(RuntimeError):
    """Raised when a PiPrompt-backed feature is accessed before populate()."""

    pass


class PiPrompt(BaseModel):
    name: Optional[str] = None
    prompt: str
    weight: float = 1.0

    def __init__(self, *args: Any, **data: Any) -> None:
        # Support PiPrompt("some prompt") sugar
        if args:
            if len(args) == 1 and not data and isinstance(args[0], str):
                data = {"prompt": args[0]}
            else:
                raise TypeError(
                    f"{self.__class__.__name__}() only accepts a single string positional argument "
                    f"or keyword arguments; got args={args!r}, kwargs={data!r}"
                )
        super().__init__(**data)


class CrossEncoderPrompt(BaseModel):
    name: Optional[str] = None
    instruction: Optional[str] = None
    hotswaps: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    def __init__(self, *args: Any, **data: Any) -> None:
        if args:
            if (
                len(args) == 1
                and "instruction" not in data
                and isinstance(args[0], str)
            ):
                data["instruction"] = args[0]
            else:
                raise TypeError(
                    f"{self.__class__.__name__}() only accepts a single string positional argument "
                    f"or keyword arguments; got args={args!r}, kwargs={data!r}"
                )
        super().__init__(**data)
