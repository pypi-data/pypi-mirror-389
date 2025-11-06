from __future__ import annotations

import pytest

from .param_model import Params


def test_register_and_access_params():
    params = Params()
    params.register("timeout", 30)
    params.register({"retries": 3})

    assert params.get("timeout") == 30

    params.set("timeout", 45)

    assert params.get("timeout") == 45
    assert params.all() == {"timeout": 45, "retries": 3}
    assert params.defaults() == {"timeout": 30, "retries": 3}


def test_register_duplicate_name_raises_value_error():
    params = Params()
    params.register("retry", 3)

    with pytest.raises(ValueError, match="already registered"):
        params.register("retry", 5)


def test_get_or_set_unknown_parameter_raises_key_error():
    params = Params()

    with pytest.raises(KeyError, match="not registered"):
        params.get("missing")

    with pytest.raises(KeyError, match="not registered"):
        params.set("missing", "value")


def test_copy_produces_isolated_registry():
    params = Params()
    params.register(
        {
            "threshold": 0.5,
            "options": {"flags": ["default"]},
        }
    )
    params.set("options", {"flags": ["original"]})

    cloned = params.copy()
    cloned.set("threshold", 0.9)
    cloned.get("options")["flags"].append("clone-only")

    assert params.get("threshold") == 0.5
    assert params.get("options")["flags"] == ["original"]

    params.get("options")["flags"].append("base-only")

    assert cloned.get("threshold") == 0.9
    assert cloned.get("options")["flags"] == ["original", "clone-only"]
    assert params.get("options")["flags"] == ["original", "base-only"]


def test_reset_restores_default_value():
    params = Params()
    params.register("feature_flag", False)
    params.set("feature_flag", True)

    param = params.get_param("feature_flag")
    param.reset()

    assert param.value() is False
