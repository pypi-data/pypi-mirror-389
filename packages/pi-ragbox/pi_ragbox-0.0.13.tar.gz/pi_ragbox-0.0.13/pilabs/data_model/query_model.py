from __future__ import annotations

import asyncio
import inspect
import json
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
)

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_serializer,
    field_validator,
    model_serializer,
)

from .feature_model import PiPrompt, QueryDerivedFeature
from .param_model import Params
from .request_context_model import get_ctx


def _freeze(x: Any) -> Any:
    """Make JSON-y structures immutably hashable."""
    if isinstance(x, Mapping):
        # sort by key for stable ordering
        return tuple((k, _freeze(v)) for k, v in sorted(x.items()))
    if isinstance(x, (list, tuple)):
        return tuple(_freeze(v) for v in x)
    if isinstance(x, set):
        return frozenset(_freeze(v) for v in x)
    return x  # assume already hashable (str, int, float, None, bool, etc.)


class _FeaturesFacade(MutableMapping[str, Any]):
    """
    Dict-like facade for query.features (mirrors the doc facade):
      - query.features["X"] = PiPrompt("Is this query about X?")   # registers prompt
      - query.features["k"] = lambda q: ...                        # compute immediately (sync)
      - query.features["k"] = <literal>                            # write-through literal
      - await query.features.populate(...)                         # run PiScorer over declared prompts
      - await query.features.add(...)                              # back-compat sugar for derived fns
    """

    _owner: "SearchQuery"

    def __init__(self, owner: "SearchQuery"):
        self._owner = owner
        self._prompts: dict[str, PiPrompt] = {}
        self._pi_input_builder: Callable[..., str] | None = None
        self._pi_input_builder_kwargs: dict[str, Any] = {}
        self._overwrite: bool = True

    # --- Mapping protocol over the backing store ---
    def __getitem__(self, k: str) -> Any:
        return self._owner._features_store[k]

    def __iter__(self):
        return iter(self._owner._features_store)

    def __len__(self) -> int:
        return len(self._owner._features_store)

    def __delitem__(self, k: str) -> None:
        m = dict(self._owner._features_store)
        del m[k]
        object.__setattr__(self._owner, "_features_store", MappingProxyType(m))

    # --- assignment ---
    def __setitem__(self, name: str, value: Any) -> None:
        """
        Accept:
          - PiPrompt → register for populate()
          - callable → compute immediately (must be sync)
          - literal → write-through to store
        """
        # Case 1: PiPrompt-backed feature (no string auto-wrap)
        if isinstance(value, PiPrompt):
            if value.name is None:
                value = value.model_copy(update={"name": name})
            self._prompts[name] = value
            return

        # Case 2: callable-derived (sync only, like doc facade)
        if callable(value):
            updated = dict(self._owner._features_store)
            result = value(self._owner)
            if inspect.isawaitable(result):
                raise TypeError(
                    f"query.features['{name}'] = <async callable> is not supported. "
                    f"Use: await query.add_features({name}=your_async_fn)"
                )
            updated[name] = result
            object.__setattr__(
                self._owner, "_features_store", MappingProxyType(updated)
            )
            return

        # Case 3: literal
        updated = dict(self._owner._features_store)
        if self._overwrite or name not in updated:
            updated[name] = value
        object.__setattr__(self._owner, "_features_store", MappingProxyType(updated))

    # attribute sugar: query.features.foo
    def __getattr__(self, name: str) -> Any:
        try:
            return self._owner._features_store[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self[name] = value

    # declared prompts (optional inspection)
    def declared(self) -> dict[str, PiPrompt]:
        return dict(self._prompts)

    # back-compat sugar to run derived functions via the old path
    async def add(
        self,
        features: (
            Mapping[str, Callable[["SearchQuery"], Any]] | Sequence[QueryDerivedFeature]
        ) = (),
        *,
        overwrite: bool = True,
        **named_features: Callable[["SearchQuery"], Any],
    ) -> "SearchQuery":
        return await self._owner.add_features(
            features, overwrite=overwrite, **named_features
        )

    def update_sync(self, mapping: Mapping[str, Any]) -> None:
        m = dict(self._owner._features_store)
        m.update(mapping)
        object.__setattr__(self._owner, "_features_store", MappingProxyType(m))

    # --- PiScorer run (async), like the doc facade's populate() ---
    async def populate(
        self,
        *,
        pi_input_builder: Callable[..., str] | None = None,
        pi_input_builder_kwargs: dict[str, Any] | None = None,
        overwrite: bool | None = None,
    ) -> "SearchQuery":
        prompts = list(self._prompts.values())
        if not prompts:
            return self._owner

        # inherit configured defaults if any
        if pi_input_builder is None:
            pi_input_builder = self._pi_input_builder
        if pi_input_builder_kwargs is None:
            pi_input_builder_kwargs = (
                dict(self._pi_input_builder_kwargs)
                if self._pi_input_builder_kwargs
                else {}
            )
        if overwrite is None:
            overwrite = self._overwrite

        # default builder: {"query": <query string>}
        if pi_input_builder is None:

            def _default_builder(*, query: str = "") -> str:
                return json.dumps({"query": query}, indent=2)

            pi_input_builder = _default_builder

        # resolve query string
        q_str = self._owner.query
        pi_input_builder_kwargs.setdefault("query", q_str)

        client = get_ctx().pi_scorer_client
        pi_result = await client.score(
            llm_input="",
            llm_output=pi_input_builder(**pi_input_builder_kwargs),
            scoring_spec=[
                {"question": p.prompt, "label": p.name, "weight": p.weight}
                for p in prompts
            ],
        )

        updated = dict(self._owner._features_store)
        for p in prompts:
            if overwrite or p.name not in updated:
                updated[p.name] = pi_result.get(p.name, 0.0)
        object.__setattr__(self._owner, "_features_store", MappingProxyType(updated))
        return self._owner


class QueryClassificationPrompt(BaseModel):
    name: str
    prompt: str


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    query_params: Mapping[str, Any] = Field(
        default_factory=lambda: MappingProxyType({})
    )

    _features_facade: Optional[_FeaturesFacade] = PrivateAttr(default=None)

    # This is needed to accept features provided as features or classification_signals.
    # It is never actually serialized/returned or seen as part of the model.
    incoming_features: Mapping[str, Any] | None = Field(
        default_factory=lambda: MappingProxyType({}),
        exclude=True,
        repr=False,
        validation_alias=AliasChoices("features", "classification_signals"),
    )
    # Actual features will be stored here.
    _features_store: Mapping[str, Any] = PrivateAttr(
        default_factory=lambda: MappingProxyType({})
    )

    model_config = ConfigDict(frozen=True)

    # Public features access
    @property
    def features(self) -> _FeaturesFacade:
        fac = getattr(self, "_features_facade", None)
        if fac is None:
            fac = _FeaturesFacade(self)
            object.__setattr__(self, "_features_facade", fac)
        return fac

    @property
    def classification_signals(self) -> Mapping[str, Any]:
        return self._features_store

    def model_post_init(self, __context: Any) -> None:
        """Ensure mapping fields are stored as immutable proxies after validation."""
        object.__setattr__(
            self, "query_params", MappingProxyType(dict(self.query_params))
        )
        incoming = getattr(self, "incoming_features", None)
        if incoming is not None:
            object.__setattr__(
                self, "_features_store", MappingProxyType(dict(incoming))
            )
            object.__setattr__(self, "incoming_features", None)
        else:
            object.__setattr__(self, "_features_store", MappingProxyType({}))

    @field_validator("query_params", "incoming_features", mode="before")
    @classmethod
    def _ensure_mapping_proxy(cls, value: Any) -> MappingProxyType:
        if value is None:
            return MappingProxyType({})
        if isinstance(value, MappingProxyType):
            return value
        if isinstance(value, Mapping):
            return MappingProxyType(dict(value))
        try:
            return MappingProxyType(dict(value))
        except TypeError as exc:  # pragma: no cover - defensive guard
            raise TypeError("Expected mapping-compatible input") from exc

    @field_serializer("query_params", mode="plain")
    def _serialize_mapping_proxy(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)

    @model_serializer(mode="wrap")
    def _serialize_features(self, handler):
        out = handler(self)
        out["features"] = dict(self._features_store)
        if "incoming_features" in out:
            del out["incoming_features"]
        if "_features_store" in out:
            del out["_features_store"]
        return out

    def populate_params(self, params: Params) -> None:
        """
        Update registered params with values from this query's parameter mapping.
        """
        for key, value in self.query_params.items():
            try:
                params.set(key, value)
            except KeyError:
                continue

    async def classify(
        self,
        query_classification_prompts: list[QueryClassificationPrompt],
    ) -> "SearchQuery":
        # Back-compat implemented using the new facade
        for prompt in query_classification_prompts:
            self.features[prompt.name] = PiPrompt(prompt.prompt)
        await self.features.populate()
        return self

    async def fanout_queries(
        self,
        *,
        instruction_prompt: str | None = None,
    ) -> List["SearchQuery"]:
        """
        Generate a list of fanout queries derived from this query using the QueryFanoutClient.
        Each derived query inherits the same limit and query parameters.
        """
        app_state = get_ctx()
        client = getattr(app_state, "fanout_query_client", None)
        if client is None:
            raise RuntimeError(
                "QueryFanoutClient is not configured in the request context"
            )

        fanout_queries = await client.generate_fanout(
            self.query,
            instruction_prompt=instruction_prompt,
        )

        return [
            SearchQuery(
                query=fanout_query,
                limit=self.limit,
                query_params=self.query_params,
            )
            for fanout_query in fanout_queries
        ]

    async def add_features(
        self,
        features: (
            Sequence[QueryDerivedFeature] | Mapping[str, Callable[[SearchQuery], Any]]
        ) = (),
        *,
        overwrite: bool = True,
        # Support kwargs format via named_features
        **named_features: Callable[[SearchQuery], Any],
    ) -> SearchQuery:
        """
        Adds derived features derived from the SearchQuery (including
        any classifications already done).

        Can be called as:
            await query.add_features([
                QueryDerivedFeature(name="is_vertical_query", fn=my_fn)
            ])

        Or more succinctly as:
            await query.add_features(
                is_vertical_query=my_fn,
                top_verticals=my_other_fn,
            )
        """
        # Normalize all inputs into a flat list of QueryDerivedFeature
        normalized: list[QueryDerivedFeature] = []
        if isinstance(features, Mapping):
            normalized.extend(
                QueryDerivedFeature(name=k, fn=v) for k, v in features.items()
            )
        else:
            normalized.extend(features or [])
        if named_features:
            normalized.extend(
                QueryDerivedFeature(name=k, fn=v) for k, v in named_features.items()
            )

        updated_features = dict(self._features_store)

        async def _run(s: QueryDerivedFeature) -> tuple[str, Any]:
            value = s.fn(self)
            if inspect.isawaitable(value):
                value = await value
            return s.name, value

        results = await asyncio.gather(*(_run(r) for r in normalized))

        for name, value in results:
            if overwrite or name not in updated_features:
                updated_features[name] = value

        self.features.update_sync(updated_features)
        return self

    def _key(self) -> Tuple[Any, ...]:
        return (
            self.query,
            self.limit,
            _freeze(self.query_params),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SearchQuery):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        # safe because model_config.frozen=True
        return hash(self._key())


QueryDerivedFeature.model_rebuild()
