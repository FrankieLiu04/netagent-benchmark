"""Agent 任务执行器 — 编排一次 agent run 的完整生命周期。

流程: start_run_log → cml_mcp_session(connect) → list_tools → agent_loop → write_run_log
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .artifacts import build_workbench_artifact
from .config import Settings
from .llm import LLMClient
from .loop import AgentLoopResult, StepHook, agent_loop
from .mcp_client import cml_mcp_session
from .prompts import get_system_prompt
from .run_logging import start_run_log, write_run_log


def summarize_tool_audit(result: AgentLoopResult) -> dict[str, object]:
    """汇总一次 run 的工具调用审计信息。"""
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
    """一次 agent run 的结果。"""

    final_answer: str
    run_log_path: Path
    run_id: str


async def run_agent_task(
    settings: Settings,
    task: str,
    hooks: list[StepHook] | None = None,
) -> AgentRunResult:
    """执行一次 agent 任务，返回结果。

    Args:
        settings: 运行时配置。
        task: 用户的自然语言任务。
        hooks: 可选的 step hooks（Phase 3 扩展用）。

    Returns:
        AgentRunResult，包含最终答案和 run log 路径。
    """
    run_log = start_run_log(task)
    payload: dict[str, object] = {
        "run_id": run_log.run_id,
        "timestamp": run_log.timestamp,
        "user_task": task,
        "llm_provider": settings.llm_provider,
        "model_name": settings.model_name,
        "tool_exposure": "all",
    }

    try:
        async with cml_mcp_session(settings) as mcp:
            # 获取当前 MCP server 暴露给 agent 的全部工具定义
            tools = await mcp.list_tools()
            payload["enabled_tool_names"] = sorted(tool.name for tool in tools)

            # 构建 LLM 客户端
            llm = LLMClient.from_settings(settings)

            # 执行 agent loop
            system_prompt = get_system_prompt("full_access")
            result: AgentLoopResult = await agent_loop(
                task=task,
                system_prompt=system_prompt,
                llm=llm,
                mcp=mcp,
                tools=tools,
                max_steps=settings.max_turns,
                hooks=hooks,
            )

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
                run_id=run_log.run_id,
                timestamp=run_log.timestamp,
                task=task,
                llm_provider=settings.llm_provider,
                model_name=settings.model_name,
                run_log_path=run_log.run_dir / "run.json",
                status="completed",
                final_answer=result.final_answer,
                duration_seconds=result.duration_seconds,
                prompt_tokens=result.total_prompt_tokens,
                completion_tokens=result.total_completion_tokens,
                tool_audit_summary=payload["tool_audit_summary"],
            )
        )

        log_path = write_run_log(run_log, payload)
        return AgentRunResult(
            final_answer=result.final_answer,
            run_log_path=log_path,
            run_id=run_log.run_id,
        )
    except Exception as exc:
        payload["error_message"] = f"{type(exc).__name__}: {exc}"
        payload.update(
            build_workbench_artifact(
                run_id=run_log.run_id,
                timestamp=run_log.timestamp,
                task=task,
                llm_provider=settings.llm_provider,
                model_name=settings.model_name,
                run_log_path=run_log.run_dir / "run.json",
                status="failed",
                error_message=payload["error_message"],
            )
        )
        log_path = write_run_log(run_log, payload)
        raise RuntimeError(
            f"Agent run failed. Run log written to {log_path}: {exc}"
        ) from exc
