"""LLM 适配器的公共协议。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ChatMessage:
    """单条 chat completion 消息。"""

    role: str
    content: str


@dataclass(frozen=True)
class ModelResponse:
    """模型响应及 token 统计。"""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMAdapter(Protocol):
    """隐藏具体模型提供商差异的最小接口。"""

    def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        timeout: float,
        max_tokens: int,
    ) -> ModelResponse:
        """请求模型返回 JSON 文本。"""
