from contextvars import ContextVar
from typing import Any

_current_ctx: ContextVar[Any] = ContextVar("current_app_state")

def set_ctx(value: Any):
    return _current_ctx.set(value)

def get_ctx() -> Any:
    return _current_ctx.get()

def reset_ctx(token) -> None:
    _current_ctx.reset(token)