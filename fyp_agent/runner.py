from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import RunConfig, Runner

from .agent import build_agent
from .config import Settings
from .mcp_client import cml_mcp_server
from .run_logging import start_run_log, write_run_log
from .tools import SAFE_CML_TOOLS


@dataclass(frozen=True)
class AgentRunResult:
    final_answer: str
    run_log_path: Path
    run_id: str


def _trace_id(result: Any) -> str | None:
    for attr in ("trace_id", "last_response_id"):
        value = getattr(result, attr, None)
        if value:
            return str(value)
    return None


async def run_agent_task(settings: Settings, task: str) -> AgentRunResult:
    run_log = start_run_log(task)
    payload: dict[str, object] = {
        "run_id": run_log.run_id,
        "timestamp": run_log.timestamp,
        "user_task": task,
        "llm_provider": settings.llm_provider,
        "model_name": settings.model_name,
        "enabled_tool_names": sorted(SAFE_CML_TOOLS),
    }

    try:
        async with cml_mcp_server(settings) as server:
            agent = build_agent(settings, server)
            result = await Runner.run(
                agent,
                task,
                max_turns=settings.max_turns,
                run_config=RunConfig(
                    workflow_name="fyp-cml-agent",
                    tracing_disabled=settings.llm_provider != "openai",
                    trace_include_sensitive_data=False,
                ),
            )
        final_answer = str(result.final_output)
        payload["final_answer"] = final_answer
        payload["sdk_trace_id"] = _trace_id(result)
        log_path = write_run_log(run_log, payload)
        return AgentRunResult(final_answer=final_answer, run_log_path=log_path, run_id=run_log.run_id)
    except Exception as exc:
        payload["error_message"] = f"{type(exc).__name__}: {exc}"
        log_path = write_run_log(run_log, payload)
        raise RuntimeError(f"Agent run failed. Run log written to {log_path}: {exc}") from exc
