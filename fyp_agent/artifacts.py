"""Workbench artifact 结构 — 生成 Java 项目可导入的稳定 run.json 字段。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


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
    """构建 Java workbench 依赖的归一化 artifact 字段。

    该结构只保存可安全展示和导入的摘要信息；完整 trace 仍由原始 run.json 字段承载。
    """
    total_tokens = None
    if prompt_tokens is not None or completion_tokens is not None:
        total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

    audit = tool_audit_summary or {}
    return {
        "benchmark": {
            "name": "fyp-agent",
            "case_id": run_id,
            "level": "agent-run",
        },
        "agent": {
            "provider": llm_provider,
            "model": model_name,
            "reasoning_mode": "default",
        },
        "result": {
            "status": status,
            "score": None,
            "final_answer": final_answer,
            "error_message": error_message,
        },
        "metrics": {
            "duration_seconds": duration_seconds,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "tool_calls": audit.get("total_calls"),
            "mutating_tool_calls": audit.get("mutating_calls"),
            "failed_tool_calls": audit.get("failed_calls"),
        },
        "artifacts": {
            "run_log_path": str(run_log_path),
            "generated_code_path": None,
            "verifier_output_path": None,
        },
        "workbench_import": {
            "schema_version": "1.0",
            "run_id": run_id,
            "timestamp": timestamp,
            "task": task,
        },
    }
