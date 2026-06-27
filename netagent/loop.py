# EN: Custom ReAct-style agent loop.
# CN: 自定义 ReAct 风格 agent loop。

from __future__ import annotations

import json
import logging
import time
from typing import Any

from .llm import LLMClient, LLMResponse, ToolCall
from .mcp_client import CmlMcpSession, MCPToolDef
from .tools import is_mutating_tool
from .trace import AgentLoopResult, LoopState, StepHook, StepTrace, ToolAuditEntry

logger = logging.getLogger(__name__)


# EN: Core agent loop helpers.
# CN: 核心 agent loop 辅助函数。

def _assistant_message(response: LLMResponse) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": response.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for tc in response.tool_calls
        ],
    }


def _apply_hooks(
    messages: list[dict[str, Any]],
    trace: StepTrace,
    step: int,
    hooks: list[StepHook] | None,
) -> list[dict[str, Any]]:
    for hook in hooks or []:
        messages = hook(messages, trace, step)
    return messages


def _tool_failure(
    *,
    step: int,
    tool_call: ToolCall,
    messages: list[dict[str, Any]],
    error_msg: str,
    elapsed_seconds: float,
) -> tuple[dict[str, Any], ToolAuditEntry]:
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": f"Error: {error_msg}",
        }
    )
    return (
        {
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.name,
            "success": False,
            "error": error_msg,
        },
        ToolAuditEntry(
            step=step,
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
            mutating=is_mutating_tool(tool_call.name),
            success=False,
            elapsed_seconds=elapsed_seconds,
            error=error_msg,
        ),
    )


def _tool_success(
    *,
    step: int,
    tool_call: ToolCall,
    messages: list[dict[str, Any]],
    result_text: str,
    elapsed_seconds: float,
) -> tuple[dict[str, Any], ToolAuditEntry]:
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result_text,
        }
    )
    return (
        {
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.name,
            "success": True,
            "result": result_text,
        },
        ToolAuditEntry(
            step=step,
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
            mutating=is_mutating_tool(tool_call.name),
            success=True,
            elapsed_seconds=elapsed_seconds,
            result_size_chars=len(result_text),
        ),
    )


async def _execute_tool_call(
    *,
    step: int,
    tool_call: ToolCall,
    mcp: CmlMcpSession,
    messages: list[dict[str, Any]],
) -> tuple[dict[str, Any], ToolAuditEntry]:
    logger.info("Step %d: calling tool %s(%s)", step, tool_call.name, tool_call.arguments)
    tool_start = time.monotonic()
    try:
        result_text = await mcp.call_tool(tool_call.name, tool_call.arguments)
    except Exception as exc:
        # EN: Return MCP/CML tool failures to the LLM as observations.
        # CN: 将 MCP/CML 工具失败作为 observation 交还给 LLM。
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.warning("Tool %s failed: %s", tool_call.name, error_msg)
        return _tool_failure(
            step=step,
            tool_call=tool_call,
            messages=messages,
            error_msg=error_msg,
            elapsed_seconds=time.monotonic() - tool_start,
        )
    return _tool_success(
        step=step,
        tool_call=tool_call,
        messages=messages,
        result_text=result_text,
        elapsed_seconds=time.monotonic() - tool_start,
    )


async def _execute_tool_calls(
    *,
    step: int,
    response: LLMResponse,
    mcp: CmlMcpSession,
    messages: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[ToolAuditEntry]]:
    messages.append(_assistant_message(response))
    tool_results: list[dict[str, Any]] = []
    step_tool_audit: list[ToolAuditEntry] = []
    for tool_call in response.tool_calls:
        result, audit_entry = await _execute_tool_call(
            step=step,
            tool_call=tool_call,
            mcp=mcp,
            messages=messages,
        )
        tool_results.append(result)
        step_tool_audit.append(audit_entry)
    return tool_results, step_tool_audit


def _record_tokens(state: LoopState, response: LLMResponse) -> None:
    state.total_prompt_tokens += response.prompt_tokens
    state.total_completion_tokens += response.completion_tokens


def _finish_without_tools(
    state: LoopState,
    response: LLMResponse,
    step: int,
    step_start: float,
    hooks: list[StepHook] | None,
) -> None:
    trace = StepTrace(
        step=step,
        llm_response=response,
        elapsed_seconds=time.monotonic() - step_start,
    )
    state.messages = _apply_hooks(state.messages, trace, step, hooks)
    state.traces.append(trace)
    state.final_answer = response.content or ""
    logger.info("Agent loop finished at step %d (no tool_calls)", step)


async def _record_tool_step(
    state: LoopState,
    *,
    response: LLMResponse,
    step: int,
    step_start: float,
    mcp: CmlMcpSession,
    hooks: list[StepHook] | None,
) -> None:
    tool_results, step_tool_audit = await _execute_tool_calls(
        step=step,
        response=response,
        mcp=mcp,
        messages=state.messages,
    )
    state.tool_audit.extend(step_tool_audit)
    trace = StepTrace(
        step=step,
        llm_response=response,
        tool_results=tool_results,
        tool_audit=step_tool_audit,
        elapsed_seconds=time.monotonic() - step_start,
    )
    state.messages = _apply_hooks(state.messages, trace, step, hooks)
    state.traces.append(trace)


def _loop_result(state: LoopState, duration_seconds: float) -> AgentLoopResult:
    return AgentLoopResult(
        final_answer=state.final_answer,
        steps=len(state.traces),
        traces=state.traces,
        tool_audit=state.tool_audit,
        total_prompt_tokens=state.total_prompt_tokens,
        total_completion_tokens=state.total_completion_tokens,
        duration_seconds=duration_seconds,
        messages=state.messages,
    )


async def agent_loop(
    task: str,
    system_prompt: str,
    llm: LLMClient,
    mcp: CmlMcpSession,
    tools: list[MCPToolDef],
    max_steps: int = 20,
    hooks: list[StepHook] | None = None,
) -> AgentLoopResult:
    # EN: Execute one complete agent loop.
    # CN: 执行一次完整的 agent loop。
    openai_tools = LLMClient.mcp_tools_to_openai(tools)
    state = LoopState(messages=[{"role": "user", "content": task}])
    loop_start = time.monotonic()
    last_response_content = ""

    for step in range(max_steps):
        step_start = time.monotonic()

        # EN: Ask the LLM for the next action.
        # CN: 请求 LLM 决定下一步。
        response = await llm.chat(system_prompt, state.messages, tools=openai_tools or None)
        _record_tokens(state, response)
        last_response_content = response.content or ""

        # EN: No tool calls means the LLM has produced the final answer.
        # CN: 没有工具调用表示 LLM 已给出最终答案。
        if not response.tool_calls:
            _finish_without_tools(state, response, step, step_start, hooks)
            break

        await _record_tool_step(
            state,
            response=response,
            step=step,
            step_start=step_start,
            mcp=mcp,
            hooks=hooks,
        )
    else:
        # EN: Preserve the last model text when max_steps is exhausted.
        # CN: max_steps 耗尽时保留最后一次模型文本。
        logger.warning("Agent loop hit max_steps=%d without finishing", max_steps)
        state.final_answer = last_response_content or "[Agent loop reached max steps without a final answer]"

    return _loop_result(state, time.monotonic() - loop_start)
