# EN: Agent task runner for one complete run lifecycle.
# CN: 编排一次 agent run 的完整生命周期。

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .artifacts import build_workbench_artifact
from .config import Settings
from .llm import LLMClient
from .loop import agent_loop
from .mcp_client import cml_mcp_session
from .prompts import get_system_prompt
from .run_logging import start_run_log, write_run_log
from .trace import AgentLoopResult, StepHook


def summarize_tool_audit(result: AgentLoopResult) -> dict[str, object]:
    # EN: Summarize tool-call audit data for one run.
    # CN: 汇总一次 run 的工具调用审计信息。
    total_calls = len(result.tool_audit)
    mutating_calls = sum(1 for entry in result.tool_audit if entry.mutating)
    failed_calls = sum(1 for entry in result.tool_audit if not entry.success)
    return {
        "total_calls": total_calls,
        "mutating_calls": mutating_calls,
        "read_only_calls": total_calls - mutating_calls,
        "failed_calls": failed_calls,
        "successful_calls": total_calls - failed_calls,
        "tool_names": sorted({entry.tool_name for entry in result.tool_audit}),
    }


@dataclass(frozen=True)
class AgentRunResult:
    # EN: Result of one agent run.
    # CN: 一次 agent run 的结果。

    final_answer: str
    run_log_path: Path
    run_id: str


def _base_payload(settings: Settings, task: str, run_id: str, timestamp: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "user_task": task,
        "llm_provider": settings.llm_provider,
        "model_name": settings.model_name,
        "tool_exposure": "all",
    }


def _record_success(
    payload: dict[str, object],
    *,
    result: AgentLoopResult,
    settings: Settings,
    task: str,
    run_id: str,
    timestamp: str,
    run_log_path: Path,
) -> None:
    payload["final_answer"] = result.final_answer
    payload["steps"] = result.steps
    payload["total_prompt_tokens"] = result.total_prompt_tokens
    payload["total_completion_tokens"] = result.total_completion_tokens
    payload["duration_seconds"] = round(result.duration_seconds, 3)
    payload["steps_trace"] = [t.to_dict() for t in result.traces]
    payload["tool_audit_summary"] = summarize_tool_audit(result)
    payload["tool_audit"] = [entry.to_dict() for entry in result.tool_audit]
    payload.update(
        build_workbench_artifact(
            run_id=run_id,
            timestamp=timestamp,
            task=task,
            llm_provider=settings.llm_provider,
            model_name=settings.model_name,
            run_log_path=run_log_path,
            status="completed",
            final_answer=result.final_answer,
            duration_seconds=result.duration_seconds,
            prompt_tokens=result.total_prompt_tokens,
            completion_tokens=result.total_completion_tokens,
            tool_audit_summary=payload["tool_audit_summary"],
        )
    )


def _record_failure(
    payload: dict[str, object],
    *,
    exc: Exception,
    settings: Settings,
    task: str,
    run_id: str,
    timestamp: str,
    run_log_path: Path,
) -> None:
    payload["error_message"] = f"{type(exc).__name__}: {exc}"
    payload.update(
        build_workbench_artifact(
            run_id=run_id,
            timestamp=timestamp,
            task=task,
            llm_provider=settings.llm_provider,
            model_name=settings.model_name,
            run_log_path=run_log_path,
            status="failed",
            error_message=payload["error_message"],
        )
    )


async def _execute_agent_run(
    settings: Settings,
    task: str,
    payload: dict[str, object],
    hooks: list[StepHook] | None,
) -> AgentLoopResult:
    async with cml_mcp_session(settings) as mcp:
        # EN: Record the exact MCP tool surface exposed to this run.
        # CN: 记录本次运行实际暴露的 MCP 工具面。
        tools = await mcp.list_tools()
        payload["enabled_tool_names"] = sorted(tool.name for tool in tools)

        llm = LLMClient.from_settings(settings)
        return await agent_loop(
            task=task,
            system_prompt=get_system_prompt("full_access"),
            llm=llm,
            mcp=mcp,
            tools=tools,
            max_steps=settings.max_turns,
            hooks=hooks,
        )


async def run_agent_task(
    settings: Settings,
    task: str,
    hooks: list[StepHook] | None = None,
) -> AgentRunResult:
    # EN: Execute one agent task and return its result.
    # CN: 执行一次 agent 任务并返回结果。
    run_log = start_run_log(task)
    run_log_path = run_log.run_dir / "run.json"
    payload = _base_payload(settings, task, run_log.run_id, run_log.timestamp)

    try:
        result = await _execute_agent_run(settings, task, payload, hooks)
        _record_success(
            payload,
            result=result,
            settings=settings,
            task=task,
            run_id=run_log.run_id,
            timestamp=run_log.timestamp,
            run_log_path=run_log_path,
        )

        log_path = write_run_log(run_log, payload)
        return AgentRunResult(
            final_answer=result.final_answer,
            run_log_path=log_path,
            run_id=run_log.run_id,
        )
    except Exception as exc:
        # EN: Run-level failures cover startup, discovery, LLM calls, and log writes.
        # CN: run 级失败覆盖启动、发现、LLM 调用和日志写入。
        _record_failure(
            payload,
            exc=exc,
            settings=settings,
            task=task,
            run_id=run_log.run_id,
            timestamp=run_log.timestamp,
            run_log_path=run_log_path,
        )
        log_path = write_run_log(run_log, payload)
        raise RuntimeError(
            f"Agent run failed. Run log written to {log_path}: {exc}"
        ) from exc
