from __future__ import annotations

import copy
from typing import Any, Dict, Union


class _Param:
    """Encapsulates a single registered parameter with default and current value."""

    def __init__(self, name: str, default: Any):
        self.name = name
        self.default = default
        self._value = default

    def value(self) -> Any:
        return self._value

    def set(self, value: Any):
        self._value = value

    def reset(self):
        self._value = self.default

    def __repr__(self):
        return f"_Param(name={self.name!r}, value={self._value!r}, default={self.default!r})"


class Params:
    """Parameter registry that supports cloning for per-request isolation."""

    def __init__(self):
        self._registry: Dict[str, _Param] = {}

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------
    def register(self, name_or_dict: Union[str, Dict[str, Any]], default: Any = None):
        if isinstance(name_or_dict, dict):
            for name, val in name_or_dict.items():
                self._register_one(name, val)
        else:
            self._register_one(name_or_dict, default)

    def _register_one(self, name: str, default: Any):
        if name in self._registry:
            raise ValueError(f"Parameter '{name}' already registered.")
        self._registry[name] = _Param(name, default)

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------
    def _require_param(self, name: str) -> _Param:
        if name not in self._registry:
            raise KeyError(
                f"Parameter '{name}' not registered. "
                f"Call params.register('{name}', default_value) first."
            )
        return self._registry[name]

    def get(self, name: str) -> Any:
        return self._require_param(name).value()

    def get_param(self, name: str) -> _Param:
        """Access the underlying parameter wrapper for advanced operations."""
        return self._require_param(name)

    def set(self, name: str, value: Any):
        self._require_param(name).set(value)

    def __getattr__(self, name: str) -> Any:
        try:
            return self.get(name)
        except KeyError as exc:
            raise AttributeError(f"'Params' object has no attribute '{name}'") from exc

    def all(self) -> Dict[str, Any]:
        return {name: param.value() for name, param in self._registry.items()}

    def defaults(self) -> Dict[str, Any]:
        return {name: param.default for name, param in self._registry.items()}

    # -------------------------------------------------------------------------
    # Cloning for per-request usage
    # -------------------------------------------------------------------------
    def copy(self) -> Params:
        """Return a deep copy of the Params instance for per-request isolation."""
        new_instance = Params()
        new_instance._registry = copy.deepcopy(self._registry)
        return new_instance

    def __repr__(self):
        return f"Params({self.all()})"
