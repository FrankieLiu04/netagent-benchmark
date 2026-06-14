"""LLM 调用适配器。"""

from research.netconfeval_repro.adapters.base import ChatMessage, LLMAdapter, ModelResponse
from research.netconfeval_repro.adapters.openai_compatible import OpenAICompatibleAdapter

__all__ = ["ChatMessage", "LLMAdapter", "ModelResponse", "OpenAICompatibleAdapter"]
