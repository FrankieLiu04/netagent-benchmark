# EN: Mock LLM client for tool-calling tests without an API.
# CN: 用于无 API 环境下测试 tool-calling 的 mock LLM 客户端。

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from netagent.llm import LLMClient, LLMResponse, ToolCall


def _make_tool_call_response(
    call_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    step: int,
) -> LLMResponse:
    return LLMResponse(
        content=f"I'll check that using {tool_name}.",
        tool_calls=[ToolCall(id=call_id, name=tool_name, arguments=arguments)],
        finish_reason="tool_calls",
        prompt_tokens=100 + step * 50,
        completion_tokens=20 + step * 10,
        raw_message={
            "role": "assistant",
            "content": f"I'll check that using {tool_name}.",
        },
    )


def _make_final_response(answer: str, step: int) -> LLMResponse:
    return LLMResponse(
        content=answer,
        tool_calls=[],
        finish_reason="stop",
        prompt_tokens=200 + step * 50,
        completion_tokens=80,
        raw_message={"role": "assistant", "content": answer},
    )


class MockLLMClient:
    # EN: Mock LLM client that returns scripted responses.
    # CN: 按脚本返回预设响应的 mock LLM 客户端。

    def __init__(self, script: list[LLMResponse] | None = None) -> None:
        if script is None:
            self._script: list[LLMResponse] = [
                _make_tool_call_response("call-0", "get_cml_labs", {}, 0),
                _make_tool_call_response("call-1", "get_cml_information", {}, 1),
                _make_final_response(
                    "I found 2 labs: OSPF-Demo (STARTED) and BGP-Lab (STOPPED). "
                    "The CML server is running version 2.9.1.",
                    2,
                ),
            ]
        else:
            self._script = script
        self._call_index = 0

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        if self._call_index >= len(self._script):
            return _make_final_response("[Mock LLM exhausted script]", self._call_index)
        response = self._script[self._call_index]
        self._call_index += 1
        return response
