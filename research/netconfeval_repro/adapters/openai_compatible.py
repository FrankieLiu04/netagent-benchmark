"""OpenAI-compatible Chat Completions 适配器。"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from research.netconfeval_repro.adapters.base import ChatMessage, ModelResponse


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


class OpenAICompatibleAdapter:
    """通过 OpenAI SDK 调用兼容 Chat Completions 的模型服务。"""

    def __init__(self, *, model: str, api_key: str, base_url: str | None) -> None:
        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    @classmethod
    def from_env(cls, *, model: str | None = None) -> "OpenAICompatibleAdapter":
        """从 `.env` / 环境变量构建适配器。"""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL
        selected_model = model or os.getenv("NETCONFEVAL_MODEL") or DEFAULT_MODEL
        if not api_key:
            raise RuntimeError("Set OPENAI_API_KEY or DEEPSEEK_API_KEY before running the benchmark.")
        return cls(model=selected_model, api_key=api_key, base_url=base_url)

    def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        timeout: float,
        max_tokens: int,
    ) -> ModelResponse:
        """请求 OpenAI-compatible API，并要求 JSON object 响应。"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            timeout=timeout,
        )
        usage = response.usage
        return ModelResponse(
            content=response.choices[0].message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )
