# EN: OpenAI-compatible chat completions client with tool calling.
# CN: 封装 OpenAI-compatible chat completions，并支持 tool calling。

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from .config import Settings
from .mcp_client import MCPToolDef


@dataclass
class ToolCall:
    # EN: Tool requested by one LLM call.
    # CN: 一次 LLM 请求调用的工具。

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    # EN: Structured response from one LLM call.
    # CN: 一次 LLM 调用的结构化响应。

    content: str | None
    tool_calls: list[ToolCall]
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    raw_message: dict[str, Any]


def _parse_tool_calls(raw_tool_calls: Any) -> list[ToolCall]:
    # EN: Parse tool calls and isolate malformed JSON arguments.
    # CN: 解析工具调用，并隔离畸形 JSON 参数。
    parsed: list[ToolCall] = []
    if not raw_tool_calls:
        return parsed

    for tc in raw_tool_calls:
        args_str = tc.function.arguments or "{}"
        try:
            args = json.loads(args_str)
        except (json.JSONDecodeError, TypeError):
            args = {}
        parsed.append(
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=args,
            )
        )
    return parsed


@dataclass
class LLMClient:
    # EN: OpenAI-compatible LLM client.
    # CN: 支持 OpenAI、DeepSeek 或其他兼容 endpoint。

    client: AsyncOpenAI
    model: str

    @classmethod
    def from_settings(cls, settings: Settings) -> LLMClient:
        # EN: Build an LLM client from Settings.
        # CN: 从 Settings 构建 LLM 客户端。
        client = AsyncOpenAI(
            api_key=settings.provider_api_key,
            base_url=settings.provider_base_url,
        )
        return cls(client=client, model=settings.model_name)

    @staticmethod
    def mcp_tools_to_openai(tools: list[MCPToolDef]) -> list[dict[str, Any]]:
        # EN: Convert MCP tool definitions to OpenAI function tools.
        # CN: 将 MCP 工具定义转换为 OpenAI function tool。
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        # EN: Send one chat completion request.
        # CN: 发起一次 chat completion 请求。
        full_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        usage = response.usage
        return LLMResponse(
            content=msg.content,
            tool_calls=_parse_tool_calls(msg.tool_calls),
            finish_reason=choice.finish_reason or "unknown",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            raw_message=msg.model_dump(),
        )
