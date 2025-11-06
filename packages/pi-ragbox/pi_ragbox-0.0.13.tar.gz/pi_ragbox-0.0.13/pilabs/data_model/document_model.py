from __future__ import annotations

import ast
import asyncio
import inspect
import json
import linecache
import traceback
from enum import Enum
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Set,
    TypeVar,
)

from executing import Source
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    PrivateAttr,
    field_serializer,
    field_validator,
)
from pydantic_core import core_schema

from .feature_model import (
    CrossEncoderPrompt,
    DocDerivedFeature,
    FeatureNotPopulatedError,
    PiPrompt,
)
from .query_model import SearchQuery
from .request_context_model import get_ctx

# ---- Model definitions ----


class _PromptAccessor:
    def __init__(self, results: "SearchResults", name: str):
        self._results = results
        self._name = name

    # --- internals ---
    def _is_prompt(self) -> bool:
        results_facade = getattr(self._results, "_features", None)
        if results_facade is None:
            return False
        prompt_names = set(getattr(results_facade, "_prompts", {}).keys())
        prompt_names.update(
            getattr(results_facade, "_cross_encoder_prompts", {}).keys()
        )
        return self._name in prompt_names

    def _get_from_doc(self, doc: "Document"):
        if self._is_prompt():
            if self._name not in doc.features:
                raise FeatureNotPopulatedError(
                    f"Feature '{self._name}' is a PiPrompt and has not been populated yet. "
                    f"Call: `await results.features.populate()` before reading it."
                )
            return float(doc.features[self._name])  # prompt scores are numeric
        # Non-PiPrompt path: return raw value (any type), or None if missing
        return doc.features.get(self._name, None)

    # --- public API ---
    def __iter__(self):
        for d in self._results.results:
            yield self._get_from_doc(d)

    def __getitem__(self, key):
        if isinstance(key, int):
            doc = self._results.results[key]
            return self._get_from_doc(doc)
        # assume Document-like
        return self._get_from_doc(key)

    def map(self) -> Dict[PiDocId, Any]:
        # Will raise FeatureNotPopulatedError on first missing prompt value
        return {d.docid: self._get_from_doc(d) for d in self._results.results}

    def first(self, default=None):
        try:
            return next(iter(self))
        except StopIteration:
            return default

    def __call__(self, doc: "Document"):
        return self._get_from_doc(doc)


class _FeaturesFacade:
    """
    Dict-like facade:
        results.features["foo"] = "Is this about foo?"
        await results.features.populate()
        score0 = results.features["foo"][0]
    """

    def __init__(self, results: "SearchResults"):
        self.__dict__["_results"] = results
        self.__dict__["_prompts"]: Dict[str, PiPrompt] = {}
        self.__dict__["_cross_encoder_prompts"]: Dict[str, CrossEncoderPrompt] = {}
        self.__dict__["_pi_input_builder"]: Optional[DocFunction[str]] = None
        self.__dict__["_pi_input_builder_kwargs"]: Dict[str, Any] = {}
        self.__dict__["_ce_passage_builder"]: Optional[DocFunction[str]] = None
        self.__dict__["_ce_passage_builder_kwargs"]: Dict[str, Any] = {}
        self.__dict__["_ce_hotswaps"]: Optional[str] = None
        self.__dict__["_overwrite"]: bool = True

    def __setitem__(self, name: str, value) -> None:
        """
        Assign either:
        - a PiPrompt (deferred population via PiScorer)
        - a callable (DocFunction) to compute a derived feature immediately
        - a literal value (bool/float/str/etc.) to apply to every document
        """

        # --- Case 1: PiPrompt-backed feature ---
        if isinstance(value, PiPrompt):
            if value.name is None:
                value = value.model_copy(update={"name": name})
            self._prompts[name] = value
            return

        # --- Case 1b: CrossEncoderPrompt-backed feature ---
        if isinstance(value, CrossEncoderPrompt):
            if value.name is None:
                value = value.model_copy(update={"name": name})
            self._cross_encoder_prompts[name] = value
            return

        # --- Case 2: Callable (lambda doc: ...) derived feature ---
        if callable(value):
            updated_docs = []
            for d in self._results.results:
                computed_value = value(d)
                if inspect.isawaitable(computed_value):
                    # Avoid race conditions / background tasks in an async handler.
                    # Keep the old API for async callables.
                    raise TypeError(
                        f"features['{name}'] = <async callable> is not supported. "
                        f"Use: await results.add_features({name}=your_async_fn)"
                    )
                feats = dict(d.features)
                feats[name] = computed_value
                updated_docs.append(
                    d.model_copy(update={"features": MappingProxyType(feats)})
                )
            object.__setattr__(self._results, "results_data", updated_docs)
            return

        # --- Case 3: Plain literal value ---
        ow = self._overwrite
        updated_docs = []
        for d in self._results.results:
            feats = dict(d.features)
            if ow or name not in feats:
                feats[name] = value
            updated_docs.append(
                d.model_copy(update={"features": MappingProxyType(feats)})
            )
        object.__setattr__(self._results, "results_data", updated_docs)

    def __getitem__(self, name: str) -> _PromptAccessor:
        # Always return an accessor to read per-doc values for this feature,
        # regardless of whether it's a prompt-backed feature or a raw value.
        return _PromptAccessor(self._results, name)

    def keys(self) -> Iterable[str]:
        return list(self._prompts.keys()) + list(self._cross_encoder_prompts.keys())

    def declared(self) -> Dict[str, object]:
        declared: Dict[str, object] = dict(self._prompts)
        declared.update(self._cross_encoder_prompts)
        return declared

    async def populate(
        self,
        query,
        *,
        pi_input_builder: Optional[DocFunction[str]] = None,
        pi_input_builder_kwargs: Optional[Dict[str, Any]] = None,
        overwrite: Optional[bool] = None,
        cross_encoder_passage_builder: Optional[DocFunction[str]] = None,
        cross_encoder_passage_builder_kwargs: Optional[Dict[str, Any]] = None,
        cross_encoder_hotswaps: Optional[str] = None,
    ) -> "SearchResults":
        pi_prompts = list(self._prompts.values())
        ce_prompts = list(self._cross_encoder_prompts.values())
        if not pi_prompts and not ce_prompts:
            return self._results

        # inherit previously configured values if present
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
        if cross_encoder_passage_builder is None:
            cross_encoder_passage_builder = self._ce_passage_builder
        if cross_encoder_passage_builder_kwargs is None:
            cross_encoder_passage_builder_kwargs = (
                dict(self._ce_passage_builder_kwargs)
                if self._ce_passage_builder_kwargs
                else {}
            )
        if cross_encoder_hotswaps is None:
            cross_encoder_hotswaps = self._ce_hotswaps

        if pi_input_builder is None:
            # default builder: {"input": <query string>, "response": <doc.content>}
            def _default_builder(doc: "Document", *, query: str = "") -> str:
                return json.dumps({"input": query, "response": doc.content}, indent=2)

            pi_input_builder = _default_builder

        q_str = getattr(query, "query", query)
        if not isinstance(q_str, str):
            q_str = str(q_str)
        if pi_prompts:
            pi_input_builder_kwargs.setdefault("query", q_str)

            await self._results._populate_pi_features_from_prompts(
                prompts=pi_prompts,
                pi_input_builder=pi_input_builder,
                pi_input_builder_kwargs=pi_input_builder_kwargs,
                overwrite=overwrite,
            )

        if ce_prompts:
            await self._results._populate_cross_encoder_features_from_prompts(
                prompts=ce_prompts,
                query=q_str,
                passage_builder=cross_encoder_passage_builder,
                passage_builder_kwargs=cross_encoder_passage_builder_kwargs,
                hotswaps=cross_encoder_hotswaps,
                overwrite=overwrite,
            )
        return self._results


class PiDocId(str):
    """String-compatible document id with its own logical type."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Parse as a string, then cast to PiDocId
        return core_schema.no_info_after_validator_function(
            lambda v: v if isinstance(v, cls) else cls(v),
            core_schema.str_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core: core_schema.CoreSchema, handler):
        json_schema = handler(core)
        json_schema.setdefault("title", "PiDocId")
        json_schema["type"] = "string"
        return json_schema


class TraceOperation(str, Enum):
    NOTE = "note"
    ADD_FEATURES = "add_features"
    FILTER = "filter"
    SCORE = "score"


class TraceEntry(BaseModel):
    operation: TraceOperation
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


TraceInput = TraceEntry | Mapping[str, Any] | str


class Document(BaseModel):
    docid: PiDocId
    content: dict
    score: float = 0.0

    features: Mapping[str, Any] = Field(default_factory=lambda: MappingProxyType({}))
    retrievals: List[SearchQuery] = Field(default_factory=list)
    traces: List[TraceEntry] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)

    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))

    @field_validator("features", mode="before")
    @classmethod
    def _ensure_mapping_proxy(cls, value: Any) -> Mapping[str, Any]:
        if value is None:
            return MappingProxyType({})
        if isinstance(value, MappingProxyType):
            return value
        if isinstance(value, Mapping):
            return MappingProxyType(dict(value))
        return MappingProxyType(dict(value))  # will raise if not mapping-like

    @field_serializer("features", mode="plain")
    def _serialize_mapping_proxy(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)

    @field_validator("traces", mode="before")
    @classmethod
    def _ensure_traces(cls, value: Any) -> List[TraceEntry]:
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [cls._parse_trace_item(item) for item in value]
        return [cls._parse_trace_item(value)]

    @field_serializer("traces", mode="plain")
    def _serialize_traces(self, value: List[TraceEntry]) -> List[Dict[str, Any]]:
        return [trace.model_dump() for trace in value]

    def add_trace(self, trace: TraceInput | DocFunction[TraceInput] | None) -> Document:
        """Return a new document with an additional trace entry."""
        if trace is None:
            return self
        if callable(trace):
            trace_value = trace(self)
        else:
            trace_value = trace

        if inspect.isawaitable(trace_value):
            raise TypeError(
                "Document.add_trace does not support awaitable trace callables."
            )

        trace_entry = self._parse_trace_item(trace_value)
        self.traces.append(trace_entry)
        return self

    @staticmethod
    def _parse_trace_item(value: Any) -> TraceEntry:
        if isinstance(value, TraceEntry):
            return value
        if isinstance(value, Mapping):
            return TraceEntry.model_validate(value)
        if isinstance(value, str):
            return TraceEntry(operation=TraceOperation.NOTE, data={"note": value})
        raise TypeError(
            f"Trace must be a TraceEntry, mapping, or string, got {type(value)!r}"
        )


R = TypeVar("R")


class DocFunction(Protocol[R]):  # type: ignore[misc]
    def __call__(self, doc: Document, *args: Any, **kwargs: Any) -> R: ...


class DebugInfo(BaseModel):
    query: SearchQuery


def _predicate_expr_from_callsite() -> str | None:
    """Attempt to recover the predicate expression passed to SearchResults.filter."""
    if Source is None:
        return None

    try:
        frame_record = inspect.stack(context=0)[2]
    except IndexError:
        return None

    frame = frame_record.frame
    try:
        executing = Source.executing(frame)
        node = getattr(executing, "node", None)
        if node is None or not isinstance(node, ast.Call):
            return None

        predicate_node = None
        for keyword in getattr(node, "keywords", []):
            if keyword.arg == "predicate":
                predicate_node = keyword.value
                break
        if predicate_node is None:
            args = getattr(node, "args", ())
            if args:
                predicate_node = args[0]
        if predicate_node is None:
            return None

        src = Source.for_frame(frame)
        text = None

        get_text = getattr(src, "get_text", None)
        if callable(get_text):
            text = get_text(predicate_node)
        else:
            asttokens_obj = getattr(src, "asttokens", None)
            if callable(asttokens_obj):
                asttokens_obj = asttokens_obj()
            if asttokens_obj is not None:
                get_text = getattr(asttokens_obj, "get_text", None)
                if callable(get_text):
                    text = get_text(predicate_node)

        if text is None and hasattr(ast, "get_source_segment"):
            filename = frame.f_code.co_filename
            if filename:
                file_source = "".join(linecache.getlines(filename))
                if file_source:
                    text = ast.get_source_segment(file_source, predicate_node)

        if text and isinstance(text, str):
            return text.strip()
        return None
    except Exception:
        traceback.print_exc()
        return None
    finally:
        del frame_record
        del frame


def _predicate_debug_info(predicate: Callable[..., Any]) -> Dict[str, Any]:
    # Try to get the lambda/function source
    src = _predicate_expr_from_callsite()
    if src is None:
        try:
            src = inspect.getsource(predicate).strip()
        except OSError:
            src = repr(predicate)

    # Collect closure/free vars and their current values
    freevars = {}
    code = getattr(predicate, "__code__", None)
    closure = getattr(predicate, "__closure__", None)
    if code and closure and code.co_freevars:
        for name, cell in zip(code.co_freevars, closure):
            try:
                freevars[name] = cell.cell_contents
            except Exception as e:
                freevars[name] = f"<unreadable: {e!r}>"

    # Callsite (best effort)
    caller = inspect.stack()[2]  # 0=this func, 1=filter(), 2=caller of filter()
    file = caller.filename
    line = caller.lineno
    func = caller.function

    return {"src": src, "freevars": freevars, "file": file, "line": line, "func": func}


def _stringify_freevars(freevars: Mapping[str, Any]) -> Dict[str, str]:
    formatted: Dict[str, str] = {}
    for key, value in freevars.items():
        try:
            display_value = getattr(value, "__dict__", value)
        except Exception:
            display_value = value
        formatted[key] = repr(display_value)
    return formatted


class SearchResults(BaseModel):
    results_data: List[Document] = Field(default_factory=list, alias="results")

    debug_info: Optional[DebugInfo] = None

    # NEW: cache the facade (not serialized)
    _features: Optional[_FeaturesFacade] = PrivateAttr(default=None)

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    @property
    def features(self) -> _FeaturesFacade:
        # Lazy init to avoid touching immutability/layout at construction
        if self._features is None:
            object.__setattr__(self, "_features", _FeaturesFacade(self))
        return self._features

    async def _populate_pi_features_from_prompts(
        self,
        *,
        prompts: list[PiPrompt],
        pi_input_builder: Optional[DocFunction[str]] = None,
        pi_input_builder_kwargs: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        overwrite: bool = True,
    ) -> "SearchResults":
        client = get_ctx().pi_scorer_client

        def _default_builder(doc: Document) -> str:
            return json.dumps(doc.content, indent=2)

        builder = pi_input_builder or _default_builder
        builder_kwargs = pi_input_builder_kwargs or {}
        scoring_spec = [
            {"question": p.prompt, "label": p.name or "", "weight": p.weight}
            for p in prompts
        ]

        async def _score_document(doc: Document) -> Document:
            pi_scores = await client.score(
                llm_input="",
                llm_output=builder(doc, **builder_kwargs),
                scoring_spec=scoring_spec,
                model_name=model_name,
            )
            updated = dict(doc.features)
            for p in prompts:
                if overwrite or p.name not in updated:
                    updated[p.name] = pi_scores.get(p.name, 0.0)
            return doc.model_copy(
                update={"features": MappingProxyType(updated)}
            ).add_trace(
                TraceEntry(
                    operation=TraceOperation.ADD_FEATURES,
                    data={
                        "features": [
                            {
                                "name": p.name,
                                "value": pi_scores.get(p.name, 0.0),
                            }
                            for p in prompts
                        ],
                        "source": "pi",
                        "overwrite": overwrite,
                    },
                )
            )

        updated_docs = await asyncio.gather(
            *(_score_document(d) for d in self.results_data)
        )
        object.__setattr__(self, "results_data", list(updated_docs))
        return self

    async def _populate_cross_encoder_features_from_prompts(
        self,
        *,
        prompts: list[CrossEncoderPrompt],
        query: str,
        passage_builder: Optional[DocFunction[str]] = None,
        passage_builder_kwargs: Optional[Dict[str, Any]] = None,
        hotswaps: Optional[str] = None,
        overwrite: bool = True,
    ) -> "SearchResults":
        if not prompts or not self.results_data:
            return self

        ctx = get_ctx()
        client = getattr(ctx, "cross_encoder_client", None)
        if client is None:
            raise RuntimeError(
                "CrossEncoderClient is not available in the current request context."
            )

        def _default_passage_builder(doc: Document) -> str:
            content = doc.content
            if isinstance(content, str):
                return content
            if isinstance(content, Mapping):
                preferred_keys = (
                    "snippet",
                    "content",
                    "body",
                    "text",
                    "raw_text",
                    "description",
                    "summary",
                )
                for key in preferred_keys:
                    value = content.get(key)
                    if isinstance(value, str) and value.strip():
                        return value
                collected = [
                    value.strip()
                    for value in content.values()
                    if isinstance(value, str) and value.strip()
                ]
                if collected:
                    return "\n".join(collected)
                return json.dumps(content, indent=2)
            return str(content)

        builder = passage_builder or _default_passage_builder
        builder_kwargs = passage_builder_kwargs or {}

        async def _build_passages() -> list[str]:
            passages: list[str] = []
            for doc in self.results_data:
                passage = builder(doc, **builder_kwargs)
                if inspect.isawaitable(passage):
                    passage = await passage
                if not isinstance(passage, str):
                    passage = str(passage)
                passages.append(passage)
            return passages

        def _extract_scores(
            response: Any, expected_length: int, prompt_name: str
        ) -> list[float]:
            candidates: list[float] | None = None
            if isinstance(response, Mapping):
                scores_candidate = response.get("scores")
                if isinstance(scores_candidate, Sequence) and not isinstance(
                    scores_candidate, (str, bytes)
                ):
                    candidates = [float(score) for score in scores_candidate]
                elif "results" in response and isinstance(
                    response["results"], Sequence
                ):
                    results_seq = response["results"]
                    if all(
                        isinstance(item, Mapping) and "score" in item
                        for item in results_seq
                    ):
                        candidates = [
                            float(item["score"])  # type: ignore[index]
                            for item in results_seq
                        ]
                elif "passages" in response and isinstance(
                    response["passages"], Sequence
                ):
                    passages_seq = response["passages"]
                    if all(
                        isinstance(item, Mapping) and "score" in item
                        for item in passages_seq
                    ):
                        candidates = [
                            float(item["score"])  # type: ignore[index]
                            for item in passages_seq
                        ]
                elif response and all(
                    isinstance(value, (int, float)) for value in response.values()
                ):
                    candidates = [float(value) for value in response.values()]
            elif isinstance(response, Sequence) and not isinstance(
                response, (str, bytes)
            ):
                if all(isinstance(item, (int, float)) for item in response):
                    candidates = [float(item) for item in response]
                elif all(
                    isinstance(item, Mapping) and "score" in item for item in response
                ):
                    candidates = [
                        float(item["score"]) for item in response  # type: ignore[index]
                    ]

            if candidates is None:
                raise ValueError(
                    f"Unsupported response format from CrossEncoderClient for prompt '{prompt_name}': {response!r}"
                )
            if len(candidates) != expected_length:
                raise ValueError(
                    f"CrossEncoderClient returned {len(candidates)} score(s) for prompt '{prompt_name}', "
                    f"expected {expected_length}."
                )
            return candidates

        passages_cache: list[str] | None = None
        docs = list(self.results_data)
        for prompt in prompts:
            prompt_name = prompt.name
            if not prompt_name:
                raise ValueError(
                    "CrossEncoderPrompt must have a name before populate()."
                )

            if passages_cache is None:
                passages_cache = await _build_passages()

            response = await client.score(
                query=query,
                passages=passages_cache,
                instruction=prompt.instruction,
                hotswaps=prompt.hotswaps or hotswaps,
            )
            scores = _extract_scores(response, len(docs), prompt_name)
            updated_docs: list[Document] = []
            for doc, score in zip(docs, scores):
                updated_features = dict(doc.features)
                if overwrite or prompt_name not in updated_features:
                    updated_features[prompt_name] = float(score)
                updated_doc = doc.model_copy(
                    update={"features": MappingProxyType(updated_features)}
                ).add_trace(
                    TraceEntry(
                        operation=TraceOperation.ADD_FEATURES,
                        data={
                            "features": [{"name": prompt_name, "value": score}],
                            "source": "cross_encoder",
                            "overwrite": overwrite,
                        },
                    )
                )
                updated_docs.append(updated_doc)

            docs = updated_docs

        object.__setattr__(self, "results_data", docs)
        return self

    @property
    def results(self) -> List[Document]:
        return list(self.results_data)

    def __setattr__(self, name, value):
        if name in ("results", "results_data"):
            raise AttributeError("Direct modification of results is not allowed.")
        if name == "debug_info":
            self.__pydantic_validator__.validate_assignment(self, name, value)
            return
        super().__setattr__(name, value)

    def add_trace(
        self, trace: TraceInput | DocFunction[TraceInput] | None
    ) -> SearchResults:
        """Append a trace entry to every document in the results."""
        if trace is None:
            return self

        for doc in self.results_data:
            doc.add_trace(trace)

        return self

    def filter(
        self,
        *args,
        predicate: DocFunction[bool] = None,
        fn_kwargs: Optional[Dict[str, Any]] = None,
        trace: TraceInput | DocFunction[TraceInput] | None = None,
    ) -> SearchResults:
        if predicate is None and args:
            if len(args) == 1 and callable(args[0]):
                predicate = args[0]
            else:
                raise TypeError(
                    "filter() accepts at most one positional argument, which must be callable"
                )

        if predicate is None:
            raise TypeError("filter() missing required argument: predicate")

        fn_kwargs = fn_kwargs or {}
        filtered = []

        info_cache: Optional[dict[str, Any]] = None

        def _filter_debug_info() -> dict[str, Any]:
            nonlocal info_cache
            if info_cache is None:
                info_cache = _predicate_debug_info(predicate)
                info_cache["formatted_freevars"] = _stringify_freevars(
                    info_cache["freevars"]
                )
            return info_cache

        def _make_filter_trace(payload: TraceInput | None, kept: bool) -> TraceEntry:
            base_entry: TraceEntry | None = None
            if payload is not None:
                base_entry = Document._parse_trace_item(payload)
            data = dict(base_entry.data) if base_entry else {}
            data["kept"] = kept

            info = _filter_debug_info()
            data.setdefault(
                "location", f"{info['file']}:{info['line']} ({info['func']})"
            )
            data.setdefault("predicate_source", info["src"])
            data.setdefault("freevars", info["formatted_freevars"])

            return TraceEntry(
                operation=TraceOperation.FILTER,
                data=data,
            )

        if trace is None:

            def auto_trace(doc: Document) -> TraceEntry:
                # We don’t re-run predicate; we *already* know the result per loop iteration,
                # so we’ll fill it right after calling predicate below.
                return TraceEntry(
                    operation=TraceOperation.NOTE,
                    data={},
                )

            trace_fn: Optional[Callable[[Document], TraceInput]] = auto_trace
        else:
            if callable(trace):
                trace_fn = trace
            else:
                parsed = Document._parse_trace_item(trace)
                trace_fn = lambda _doc, entry=parsed: entry

        for doc in self.results_data:
            ok = predicate(doc, **fn_kwargs)
            if ok:
                payload = trace_fn(doc) if trace_fn else None
                if callable(getattr(doc, "add_trace", None)):
                    doc = doc.add_trace(
                        lambda d, p=payload: _make_filter_trace(p, True)  # type: ignore
                    )
                filtered.append(doc)
            else:
                # Optionally log rejections too (comment out if too noisy)
                if callable(getattr(doc, "add_trace", None)):
                    if trace_fn:
                        rej_payload = trace_fn(doc)
                    else:
                        info = _filter_debug_info()
                        rej_payload = (
                            f"filter@{info['file']}:{info['line']}: {info['src']}"
                            if info
                            else "filter(rejected)"
                        )
                    doc = doc.add_trace(
                        lambda d, p=rej_payload: _make_filter_trace(p, False)
                    )  # type: ignore
                # Not appended

        object.__setattr__(self, "results_data", filtered)
        return self

    def score(
        self,
        scoring_fn: DocFunction[float],
        fn_kwargs: Optional[Dict[str, Any]] = None,
        trace: TraceInput | DocFunction[TraceInput] | None = None,
    ) -> SearchResults:
        fn_kwargs = fn_kwargs or {}
        scored_docs: List[Document] = []

        info_cache: Optional[dict[str, Any]] = None

        def _score_debug_info() -> dict[str, Any]:
            nonlocal info_cache
            if info_cache is None:
                info_cache = _predicate_debug_info(scoring_fn)
                info_cache["formatted_freevars"] = _stringify_freevars(
                    info_cache["freevars"]
                )
            return info_cache

        def _make_score_trace(
            payload: TraceInput | None, score_value: float
        ) -> TraceEntry:
            base_entry: TraceEntry | None = (
                Document._parse_trace_item(payload) if payload is not None else None
            )
            data = dict(base_entry.data) if base_entry else {}
            data["score"] = score_value

            info = _score_debug_info()
            data.setdefault(
                "location", f"{info['file']}:{info['line']} ({info['func']})"
            )
            data.setdefault("function_source", info["src"])
            data.setdefault("freevars", info["formatted_freevars"])

            return TraceEntry(
                operation=TraceOperation.SCORE,
                data=data,
            )

        if trace is None:

            def auto_trace(doc: Document) -> TraceEntry:
                return TraceEntry(
                    operation=TraceOperation.NOTE,
                    data={},
                )

            for doc in self.results_data:
                doc_score = scoring_fn(doc, **fn_kwargs)
                updated_doc = doc.model_copy(update={"score": doc_score})
                msg = auto_trace(updated_doc)
                updated_doc = updated_doc.add_trace(
                    lambda d, m=msg, val=doc_score: _make_score_trace(m, val)
                )
                scored_docs.append(updated_doc)
        else:
            if callable(trace):
                trace_fn: Callable[[Document], TraceInput] = trace
            else:
                parsed = Document._parse_trace_item(trace)

                def trace_fn(_doc: Document, entry=parsed) -> TraceEntry:
                    return entry

            for doc in self.results_data:
                doc_score = scoring_fn(doc, **fn_kwargs)
                updated_doc = doc.model_copy(update={"score": doc_score}).add_trace(
                    lambda d, fn=trace_fn, val=doc_score: _make_score_trace(fn(d), val)
                )
                scored_docs.append(updated_doc)

        scored_docs.sort(key=lambda d: d.score, reverse=True)
        object.__setattr__(self, "results_data", scored_docs)

        return self

    # Back-compat wrapper (unchanged signature)
    async def add_pi_features(
        self,
        prompts: list[PiPrompt],
        pi_input_builder: DocFunction[str] | None = None,
        pi_input_builder_kwargs: Optional[Dict[str, Any]] = None,
        overwrite: bool = True,
    ) -> "SearchResults":
        prompts_v2: list[PiPrompt] = [
            PiPrompt(name=p.name, prompt=p.prompt, weight=p.weight) for p in prompts
        ]
        return await self._populate_pi_features_from_prompts(
            prompts=prompts_v2,
            pi_input_builder=pi_input_builder,
            pi_input_builder_kwargs=pi_input_builder_kwargs,
            overwrite=overwrite,
        )

    async def add_features(
        self,
        features: (
            Sequence[DocDerivedFeature] | Mapping[str, Callable[[Document], Any]]
        ) = (),
        *,
        overwrite: bool = True,
        # Support kwargs format via named_features
        **named_features: Callable[[Document], Any],
    ) -> SearchResults:
        """
        Adds features derived from the SearchResults.

        Can be called as:
            await results.add_features([
                DocDerivedFeature(name="is_shopping_doc", fn=my_fn)
            ])

        Or more succinctly as:
            await results.add_features(
                is_shopping_doc=my_fn,
            )
        """
        # Normalize all inputs into a flat list of DocDerivedFeature
        normalized: list[DocDerivedFeature] = []
        if isinstance(features, Mapping):
            normalized.extend(
                DocDerivedFeature(name=k, fn=v) for k, v in features.items()
            )
        else:
            normalized.extend(features or [])
        if named_features:
            normalized.extend(
                DocDerivedFeature(name=k, fn=v) for k, v in named_features.items()
            )

        async def _run_one_feature_fn(
            doc: Document, s: DocDerivedFeature
        ) -> tuple[str, Any]:
            value = s.fn(doc)
            if inspect.isawaitable(value):
                value = await value
            return s.name, value

        async def _run_all_for_document(doc: Document) -> Document:
            updated_features = dict(doc.features)
            results = await asyncio.gather(
                *(_run_one_feature_fn(doc, r) for r in normalized)
            )

            feature_names = [s.name for s in normalized]
            for name, value in results:
                if overwrite or name not in updated_features:
                    updated_features[name] = value

            return doc.model_copy(
                update={"features": MappingProxyType(updated_features)}
            ).add_trace(
                TraceEntry(
                    operation=TraceOperation.ADD_FEATURES,
                    data={
                        "features": feature_names,
                        "overwrite": overwrite,
                    },
                )
            )

        updated_docs = await asyncio.gather(
            *(_run_all_for_document(doc) for doc in self.results_data)
        )

        object.__setattr__(self, "results_data", list(updated_docs))

        return self

    def _add_retrieval_query(
        self,
        retrieval: SearchQuery,
    ) -> SearchResults:
        """
        Annotate documents with a query for tracing purposes.
        """

        def _add_query_to_doc(doc: Document) -> Document:
            updated_retrievals = list(doc.retrievals)
            if retrieval is not None:
                updated_retrievals.append(retrieval)
            return doc.model_copy(update={"retrievals": updated_retrievals})

        updated_docs = [_add_query_to_doc(doc) for doc in self.results_data]

        object.__setattr__(self, "results_data", list(updated_docs))

        return self

    @staticmethod
    def _merge_doc_features_and_metadata(
        merge_into: Document, merge_from: Document
    ) -> None:
        if merge_into is merge_from:
            return

        if merge_from.features:
            merged_features = dict(merge_into.features)
            merged_features.update(merge_from.features)
            if merged_features != merge_into.features:
                object.__setattr__(merge_into, "features", merged_features)

        if merge_from.retrievals:
            merged_retrievals = list(merge_into.retrievals)
            for retrieval in merge_from.retrievals:
                if retrieval not in merged_retrievals:
                    merged_retrievals.append(retrieval)
            if merged_retrievals != merge_into.retrievals:
                object.__setattr__(merge_into, "retrievals", merged_retrievals)

    def merge(self, other: SearchResults) -> SearchResults:
        seen: Set[PiDocId] = set()
        merged_docs: Dict[PiDocId, Document] = dict()

        for doc in (*self.results_data, *other.results_data):
            if doc.docid in seen:
                self._merge_doc_features_and_metadata(merged_docs[doc.docid], doc)
                continue
            merged_docs[doc.docid] = doc
            seen.add(doc.docid)

        object.__setattr__(self, "results_data", list(merged_docs.values()))

        return self


DocDerivedFeature.model_rebuild()
