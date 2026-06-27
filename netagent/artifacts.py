# EN: Stable run.json artifact fields for the Java workbench.
# CN: 生成 Java workbench 可导入的稳定 run.json 字段。

from __future__ import annotations

from pathlib import Path
from typing import Any


def _total_tokens(prompt_tokens: int | None, completion_tokens: int | None) -> int | None:
    if prompt_tokens is None and completion_tokens is None:
        return None
    return (prompt_tokens or 0) + (completion_tokens or 0)


def _metrics(
    *,
    duration_seconds: float | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    tool_audit_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    audit = tool_audit_summary or {}
    return {
        "duration_seconds": duration_seconds,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": _total_tokens(prompt_tokens, completion_tokens),
        "tool_calls": audit.get("total_calls"),
        "mutating_tool_calls": audit.get("mutating_calls"),
        "failed_tool_calls": audit.get("failed_calls"),
    }


def _result(status: str, final_answer: str | None, error_message: str | None) -> dict[str, Any]:
    return {
        "status": status,
        "score": None,
        "final_answer": final_answer,
        "error_message": error_message,
    }


def _artifact_paths(run_log_path: Path) -> dict[str, Any]:
    return {
        "run_log_path": str(run_log_path),
        "generated_code_path": None,
        "verifier_output_path": None,
    }


def _workbench_import(run_id: str, timestamp: str, task: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "timestamp": timestamp,
        "task": task,
    }


def build_workbench_artifact(
    *,
    run_id: str,
    timestamp: str,
    task: str,
    llm_provider: str,
    model_name: str,
    run_log_path: Path,
    status: str,
    final_answer: str | None = None,
    error_message: str | None = None,
    duration_seconds: float | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    tool_audit_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # EN: Build normalized artifact fields consumed by the Java workbench.
    # CN: 构建 Java workbench 依赖的归一化 artifact 字段。
    return {
        "benchmark": {
            "name": "netagent",
            "case_id": run_id,
            "level": "agent-run",
        },
        "agent": {
            "provider": llm_provider,
            "model": model_name,
            "reasoning_mode": "default",
        },
        "result": _result(status, final_answer, error_message),
        "metrics": _metrics(
            duration_seconds=duration_seconds,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tool_audit_summary=tool_audit_summary,
        ),
        "artifacts": _artifact_paths(run_log_path),
        "workbench_import": _workbench_import(run_id, timestamp, task),
    }
