# EN: Agent trace and result data structures.
# CN: Agent trace 和 result 数据结构。

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .llm import LLMResponse


@dataclass
class ToolAuditEntry:
    # EN: Audit record for one MCP tool call.
    # CN: 单次 MCP 工具调用的审计记录。

    step: int
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    mutating: bool
    success: bool
    elapsed_seconds: float
    result_size_chars: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "step": self.step,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "mutating": self.mutating,
            "success": self.success,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "result_size_chars": self.result_size_chars,
        }
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass
class StepTrace:
    # EN: Complete record for one agent step.
    # CN: 单个 agent step 的完整记录。

    step: int
    llm_response: LLMResponse
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    tool_audit: list[ToolAuditEntry] = field(default_factory=list)
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
            "tool_audit": [entry.to_dict() for entry in self.tool_audit],
            "usage": {
                "prompt_tokens": self.llm_response.prompt_tokens,
                "completion_tokens": self.llm_response.completion_tokens,
            },
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


@dataclass
class AgentLoopResult:
    # EN: Complete result of one agent loop.
    # CN: 一次 agent loop 的完整结果。

    final_answer: str
    steps: int
    traces: list[StepTrace]
    tool_audit: list[ToolAuditEntry]
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
            "tool_audit": [entry.to_dict() for entry in self.tool_audit],
        }


@dataclass
class LoopState:
    # EN: Mutable state for the agent loop.
    # CN: Agent loop 的可变状态。

    messages: list[dict[str, Any]]
    traces: list[StepTrace] = field(default_factory=list)
    tool_audit: list[ToolAuditEntry] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    final_answer: str = ""


class StepHook(Protocol):
    # EN: Step-end hook that may return updated messages.
    # CN: 每步结束后的回调，可返回更新后的 messages。

    def __call__(
        self,
        messages: list[dict[str, Any]],
        trace: StepTrace,
        step: int,
    ) -> list[dict[str, Any]]:
        ...
