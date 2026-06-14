from __future__ import annotations

import json
from pathlib import Path

import pytest

if not (Path(__file__).resolve().parents[2] / "research" / "netconfeval" / "netconfeval").exists():
    pytest.skip("NetConfEval upstream snapshot is not checked out.", allow_module_level=True)

from research.netconfeval_repro.adapters import ChatMessage
from research.netconfeval_repro.runners.step1_translation import call_model
from research.netconfeval_repro.scorers import parse_model_json, score_step1_result


class StubAdapter:
    """测试用 LLM 适配器。"""

    def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        timeout: float,
        max_tokens: int,
    ):
        from research.netconfeval_repro.adapters import ModelResponse

        assert messages
        assert timeout == 1.0
        assert max_tokens == 128
        payload = {
            "status": "OK",
            "result": {
                "reachability": {"a": ["10.0.0.0/24"]},
            },
        }
        return ModelResponse(content=json.dumps(payload), prompt_tokens=10, completion_tokens=5)


def test_parse_model_json_extracts_result_object() -> None:
    payload = '{"status": "OK", "result": "{\\"reachability\\": {\\"a\\": [\\"p\\"]}}"}'

    assert parse_model_json(payload) == {"reachability": {"a": ["p"]}}


def test_score_step1_result_uses_requirement_accuracy_and_strict_diff() -> None:
    expected = {"reachability": {"a": ["p"]}}
    result = {"reachability": {"a": ["p"]}, "waypoint": {}}
    row = {"total": 0, "success": 0, "fail": 0, "wrong": 0, "accuracy": 0}

    score_step1_result(expected, result, row)

    assert row["accuracy"] == 1
    assert row["strict_exact_match"] == 0
    assert "dictionary_item_added" in row["diff"]


def test_call_model_uses_adapter_boundary() -> None:
    result, error, prompt_tokens, completion_tokens, raw_output = call_model(
        adapter=StubAdapter(),
        policy_types={"reachability"},
        human_language=["a can reach 10.0.0.0/24."],
        timeout=1.0,
        max_tokens=128,
    )

    assert error == ""
    assert result == {"reachability": {"a": ["10.0.0.0/24"]}}
    assert prompt_tokens == 10
    assert completion_tokens == 5
    assert raw_output
