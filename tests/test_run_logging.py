"""增强版 run_logging 测试 — 验证 step trace 结构能正确序列化和脱敏。"""

from __future__ import annotations

import json

from fyp_agent.run_logging import start_run_log, write_run_log


def test_run_log_stores_step_trace(tmp_path):
    """验证 step trace 能正确写入 run.json。"""
    run_log = start_run_log("list all labs", root=tmp_path)
    path = write_run_log(
        run_log,
        {
            "run_id": run_log.run_id,
            "user_task": "list all labs",
            "steps": 2,
            "steps_trace": [
                {
                    "step": 0,
                    "tool_calls": [{"id": "call-0", "name": "get_cml_labs", "arguments": {}}],
                    "tool_results": [{"success": True, "result": "[{\"id\": \"lab-001\"}]"}],
                    "tool_audit": [
                        {
                            "step": 0,
                            "tool_call_id": "call-0",
                            "tool_name": "get_cml_labs",
                            "arguments": {},
                            "mutating": False,
                            "success": True,
                            "elapsed_seconds": 0.12,
                            "result_size_chars": 19,
                        }
                    ],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 20},
                },
                {
                    "step": 1,
                    "tool_calls": [],
                    "usage": {"prompt_tokens": 200, "completion_tokens": 80},
                },
            ],
            "tool_audit_summary": {
                "total_calls": 1,
                "mutating_calls": 0,
                "read_only_calls": 1,
                "failed_calls": 0,
                "successful_calls": 1,
                "tool_names": ["get_cml_labs"],
            },
            "total_prompt_tokens": 300,
            "total_completion_tokens": 100,
            "final_answer": "Found 1 lab.",
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["steps"] == 2
    assert len(payload["steps_trace"]) == 2
    assert payload["steps_trace"][0]["tool_calls"][0]["name"] == "get_cml_labs"
    assert payload["steps_trace"][0]["tool_audit"][0]["success"] is True
    assert payload["tool_audit_summary"]["total_calls"] == 1
    assert payload["total_prompt_tokens"] == 300
    assert payload["total_completion_tokens"] == 100


def test_run_log_does_not_write_secret_fields(tmp_path):
    run_log = start_run_log("Show me labs", root=tmp_path)
    path = write_run_log(
        run_log,
        {
            "run_id": run_log.run_id,
            "OPENAI_API_KEY": "secret",
            "DEEPSEEK_API_KEY": "secret",
            "nested": {"CML_PASSWORD": "secret", "deepseek_api_key": "secret"},
            "tool_audit": [
                {
                    "tool_name": "create_cml_user",
                    "arguments": {"username": "alice", "password": "secret", "api_token": "secret"},
                }
            ],
            "final_answer": "ok",
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "OPENAI_API_KEY" not in payload
    assert "DEEPSEEK_API_KEY" not in payload
    assert "CML_PASSWORD" not in payload["nested"]
    assert "deepseek_api_key" not in payload["nested"]
    assert payload["tool_audit"][0]["arguments"] == {"username": "alice"}
    assert payload["final_answer"] == "ok"
