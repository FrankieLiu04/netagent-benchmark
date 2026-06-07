from __future__ import annotations

import json

from fyp_agent.run_logging import start_run_log, write_run_log


def test_run_log_does_not_write_secret_fields(tmp_path):
    run_log = start_run_log("Show me labs", root=tmp_path)
    path = write_run_log(
        run_log,
        {
            "run_id": run_log.run_id,
            "OPENAI_API_KEY": "secret",
            "DEEPSEEK_API_KEY": "secret",
            "nested": {"CML_PASSWORD": "secret", "deepseek_api_key": "secret"},
            "final_answer": "ok",
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "OPENAI_API_KEY" not in payload
    assert "DEEPSEEK_API_KEY" not in payload
    assert "CML_PASSWORD" not in payload["nested"]
    assert "deepseek_api_key" not in payload["nested"]
    assert payload["final_answer"] == "ok"
