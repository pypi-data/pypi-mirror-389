from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, List, Callable

import modal

PI_SCORER_APP_NAME = "dynamic-batching"
PI_SCORER_CLASS_NAME = "ScorerModel"
PI_SCORER_ENVIRONMENT = "prod"


class PiScorerClient():
    _function: Callable[..., Any]

    def __init__(
        self,
    ) -> None:
        cls = modal.Cls.from_name(PI_SCORER_APP_NAME, PI_SCORER_CLASS_NAME, environment_name=PI_SCORER_ENVIRONMENT)
        obj = cls()
        self._function = obj.direct.remote.aio

    async def score(
        self,
        llm_input: str,
        llm_output: str,
        scoring_spec: List[Mapping[str, Any]],
        model_name: str | None = None,
    ) -> dict[str, float]:
        total_weight = sum([item["weight"] for item in scoring_spec])
        resp = await self._function(
            model_name=model_name if model_name else "pi-scorer-bert",
            request={
                "inputs": llm_input,
                "response": llm_output,
                "questions": [s["question"] for s in scoring_spec],
            })
        scores = resp["response"]
        question_scores = {
            s["label"]: score for s, score in zip(scoring_spec, scores)
        }
        question_scores["total_score"] = sum(
            [score * (s["weight"] / total_weight) for s, score in zip(scoring_spec, scores)]
        )
        return question_scores
