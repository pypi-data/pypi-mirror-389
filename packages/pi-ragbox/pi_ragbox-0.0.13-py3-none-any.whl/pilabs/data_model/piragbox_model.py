from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

_PIPELINE_REGISTRY: dict[str, Callable[..., Awaitable[Any]]] = {}
_PIPELINE_DEFAULTS: dict[str, dict[str, Any]] = {}


def piragbox(
    *, params: dict[str, Any], name: str | None = None
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator that registers async ranking pipelines with default parameter values.
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("piragbox decorator expects an async function.")

        registry_name = name or func.__name__
        if registry_name in _PIPELINE_REGISTRY:
            raise ValueError(f"Pipeline '{registry_name}' already registered.")

        defaults = dict(params)
        setattr(func, "__piragbox_params__", defaults)
        setattr(func, "__piragbox_name__", registry_name)

        _PIPELINE_REGISTRY[registry_name] = func
        _PIPELINE_DEFAULTS[registry_name] = defaults

        return func

    return decorator


def get_pipeline(name: str) -> Callable[..., Awaitable[Any]]:
    """
    Retrieve a registered pipeline by name.
    """
    try:
        return _PIPELINE_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Pipeline '{name}' is not registered.") from exc


def get_pipeline_param_defaults(name: str) -> dict[str, Any]:
    """
    Retrieve the default parameter values registered for a pipeline by name.
    """
    try:
        return dict(_PIPELINE_DEFAULTS[name])
    except KeyError as exc:
        raise KeyError(f"Pipeline '{name}' is not registered.") from exc


def list_pipelines() -> list[str]:
    """
    Return the names of all registered pipelines.
    """
    return sorted(_PIPELINE_REGISTRY)
