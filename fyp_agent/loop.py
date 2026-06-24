"""核心 agent loop — 自定义 ReAct 循环，替代 OpenAI Agents SDK Runner。

设计目标：
- 完全控制每一步的 LLM 调用、工具执行和状态流转
- 可插拔的 StepHook 系统，Phase 3 可注入 verification / reflection / RAG
- 完整的 step-level trace，用于 benchmark 分析
- 不依赖 openai-agents SDK，直接用 openai chat completions + mcp SDK

循环逻辑：
  user task → LLM (with tools) → tool_calls? → execute via MCP → append results → repeat
                                      ↓ no
                                   done → final answer
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from .llm import LLMClient, LLMResponse
from .mcp_client import CmlMcpSession, MCPToolDef

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trace 数据结构
# ---------------------------------------------------------------------------

@dataclass
class StepTrace:
    """单个 agent step 的完整记录。"""

    step: int
    llm_response: LLMResponse
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "finish_reason": self.llm_response.finish_reason,
            "content": self.llm_response.content,
            "tool_calls": [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in self.llm_response.tool_calls
            ],
            "tool_results": self.tool_results,
            "usage": {
                "prompt_tokens": self.llm_response.prompt_tokens,
                "completion_tokens": self.llm_response.completion_tokens,
            },
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


@dataclass
class AgentLoopResult:
    """一次 agent loop 的完整结果。"""

    final_answer: str
    steps: int
    traces: list[StepTrace]
    total_prompt_tokens: int
    total_completion_tokens: int
    duration_seconds: float
    messages: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_answer": self.final_answer,
            "steps": self.steps,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "duration_seconds": round(self.duration_seconds, 3),
            "steps_trace": [t.to_dict() for t in self.traces],
        }


# ---------------------------------------------------------------------------
# Hook 系统
# ---------------------------------------------------------------------------

class StepHook(Protocol):
    """每步结束后的回调，可修改 messages 并返回新 messages。

    Phase 1 不挂任何 hook。Phase 3 可插：
    - VerificationHook: agent 产出配置后自动验证
    - ReflectionHook: 每 N 步注入反思消息
    - RAGHook: 检测到需要知识时自动检索
    """

    def __call__(
        self,
        messages: list[dict[str, Any]],
        trace: StepTrace,
        step: int,
    ) -> list[dict[str, Any]]:
        ...


# ---------------------------------------------------------------------------
# 核心 agent loop
# ---------------------------------------------------------------------------

async def agent_loop(
    task: str,
    system_prompt: str,
    llm: LLMClient,
    mcp: CmlMcpSession,
    tools: list[MCPToolDef],
    max_steps: int = 20,
    hooks: list[StepHook] | None = None,
) -> AgentLoopResult:
    """执行一次完整的 agent loop。

    Args:
        task: 用户的自然语言任务。
        system_prompt: 系统提示词。
        llm: LLM 客户端。
        mcp: MCP 会话（已初始化）。
        tools: 可用工具列表。
        max_steps: 最大迭代次数。
        hooks: 每步结束后的回调列表。

    Returns:
        AgentLoopResult，包含最终答案、完整 trace 和 token 统计。
    """
    openai_tools = LLMClient.mcp_tools_to_openai(tools)

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": task},
    ]

    traces: list[StepTrace] = []
    total_prompt = 0
    total_completion = 0
    final_answer = ""
    loop_start = time.monotonic()

    for step in range(max_steps):
        step_start = time.monotonic()

        # 1. LLM 决策
        response = await llm.chat(system_prompt, messages, tools=openai_tools or None)

        total_prompt += response.prompt_tokens
        total_completion += response.completion_tokens

        # 2. 如果没有 tool_calls → LLM 给出最终回答
        if not response.tool_calls:
            elapsed = time.monotonic() - step_start
            trace = StepTrace(
                step=step,
                llm_response=response,
                elapsed_seconds=elapsed,
            )

            # 执行 hooks
            for hook in hooks or []:
                messages = hook(messages, trace, step)

            traces.append(trace)
            final_answer = response.content or ""
            logger.info("Agent loop finished at step %d (no tool_calls)", step)
            break

        # 3. 执行 tool calls
        # 先把 assistant message（含 tool_calls）加入 messages
        assistant_msg: dict[str, Any] = {
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
        messages.append(assistant_msg)

        tool_results: list[dict[str, Any]] = []
        for tc in response.tool_calls:
            logger.info("Step %d: calling tool %s(%s)", step, tc.name, tc.arguments)
            try:
                result_text = await mcp.call_tool(tc.name, tc.arguments)
                tool_results.append(
                    {
                        "tool_call_id": tc.id,
                        "tool_name": tc.name,
                        "success": True,
                        "result": result_text,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    }
                )
            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                logger.warning("Tool %s failed: %s", tc.name, error_msg)
                tool_results.append(
                    {
                        "tool_call_id": tc.id,
                        "tool_name": tc.name,
                        "success": False,
                        "error": error_msg,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": f"Error: {error_msg}",
                    }
                )

        elapsed = time.monotonic() - step_start
        trace = StepTrace(
            step=step,
            llm_response=response,
            tool_results=tool_results,
            elapsed_seconds=elapsed,
        )

        # 4. 执行 hooks
        for hook in hooks or []:
            messages = hook(messages, trace, step)

        traces.append(trace)
    else:
        # max_steps 耗尽
        logger.warning("Agent loop hit max_steps=%d without finishing", max_steps)
        final_answer = response.content or "[Agent loop reached max steps without a final answer]"

    duration = time.monotonic() - loop_start

    return AgentLoopResult(
        final_answer=final_answer,
        steps=len(traces),
        traces=traces,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        duration_seconds=duration,
        messages=messages,
    )
