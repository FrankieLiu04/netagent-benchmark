"""LLM 客户端 — 封装 OpenAI-compatible chat completions，支持 tool calling。

直接使用 openai.AsyncOpenAI，不经过 openai-agents SDK。
负责：
- 构建 LLM 请求（messages + tools schema）
- 解析响应（assistant message + tool_calls）
- 提取 token usage
- 将 MCP tool schema 转为 OpenAI function tool 格式
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI

from .config import Settings
from .mcp_client import MCPToolDef


@dataclass
class ToolCall:
    """LLM 请求调用的一个工具。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """一次 LLM 调用的结构化响应。"""

    content: str | None
    tool_calls: list[ToolCall]
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    raw_message: dict[str, Any]


@dataclass
class LLMClient:
    """OpenAI-compatible LLM 客户端。

    支持 OpenAI 和 DeepSeek（或任何 OpenAI-compatible endpoint）。
    """

    client: AsyncOpenAI
    model: str

    @classmethod
    def from_settings(cls, settings: Settings) -> LLMClient:
        """从 Settings 构建 LLM 客户端。"""
        client = AsyncOpenAI(
            api_key=settings.provider_api_key,
            base_url=settings.provider_base_url,
        )
        return cls(client=client, model=settings.model_name)

    @staticmethod
    def mcp_tools_to_openai(tools: list[MCPToolDef]) -> list[dict[str, Any]]:
        """将 MCP 工具定义转换为 OpenAI function tool 格式。"""
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
        """发起一次 chat completion 请求。

        Args:
            system_prompt: 系统提示词，作为 messages[0] 注入。
            messages: 对话历史（不含 system message）。
            tools: OpenAI function tool 列表，None 表示不提供工具。

        Returns:
            LLMResponse，包含 assistant 内容、tool_calls 和 token usage。
        """
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

        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            import json

            for tc in msg.tool_calls:
                args_str = tc.function.arguments or "{}"
                try:
                    args = json.loads(args_str)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        usage = response.usage
        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "unknown",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            raw_message=msg.model_dump(),
        )
