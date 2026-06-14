from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MAX_TURNS = 6


class Settings(BaseModel):
    """Agent 运行时配置，从 .env 文件加载。

    支持 OpenAI 和 DeepSeek 两种 LLM provider，
    通过 LLM_PROVIDER 环境变量切换。
    """

    llm_provider: Literal["openai", "deepseek"] = "deepseek"
    llm_model: str | None = None
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None
    deepseek_base_url: str = Field(default=DEFAULT_DEEPSEEK_BASE_URL, min_length=1)
    cml_url: str = Field(..., min_length=1)
    cml_username: str = Field(..., min_length=1)
    cml_password: str = Field(..., min_length=1)
    cml_verify_ssl: bool = False
    max_turns: int = Field(default=DEFAULT_MAX_TURNS, ge=1, le=20)
    # MCP server 会话超时（秒），冷启动首次可能较长
    mcp_timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)

    @model_validator(mode="after")
    def require_provider_key(self) -> "Settings":
        """确保当前 provider 对应的 API key 已设置。"""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek")
        return self

    @field_validator("cml_verify_ssl", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
        raise ValueError(f"invalid boolean value: {value!r}")

    def cml_env(self) -> dict[str, str]:
        """构建传递给 cml-mcp 子进程的环境变量。"""
        return {
            "CML_URL": self.cml_url,
            "CML_USERNAME": self.cml_username,
            "CML_PASSWORD": self.cml_password,
            "CML_VERIFY_SSL": str(self.cml_verify_ssl).lower(),
        }

    @property
    def model_name(self) -> str:
        if self.llm_model:
            return self.llm_model
        if self.llm_provider == "openai":
            return DEFAULT_OPENAI_MODEL
        return DEFAULT_DEEPSEEK_MODEL

    @property
    def provider_api_key(self) -> str:
        if self.llm_provider == "openai":
            return self.openai_api_key or ""
        return self.deepseek_api_key or ""

    @property
    def provider_base_url(self) -> str | None:
        if self.llm_provider == "deepseek":
            return self.deepseek_base_url
        return None


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


def load_settings(env_file: str | Path = ".env") -> Settings:
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
    elif str(env_file) == ".env":
        load_dotenv()

    raw = {
        "llm_provider": os.getenv("LLM_PROVIDER", "deepseek").strip().lower(),
        "llm_model": os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY"),
        "deepseek_base_url": os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
        "cml_url": os.getenv("CML_URL"),
        "cml_username": os.getenv("CML_USERNAME"),
        "cml_password": os.getenv("CML_PASSWORD"),
        "cml_verify_ssl": os.getenv("CML_VERIFY_SSL", "false"),
        "mcp_timeout_seconds": os.getenv("FYP_MCP_TIMEOUT_SECONDS", "30"),
    }

    try:
        return Settings.model_validate(raw)
    except ValidationError as exc:
        missing = []
        for error in exc.errors():
            loc = ".".join(str(part) for part in error["loc"])
            missing.append(f"{loc}: {error['msg']}")
        details = "\n".join(f"- {item}" for item in missing)
        raise ConfigError(
            "Agent configuration is incomplete. Create a .env file from "
            ".env.example and fill in the required values:\n" + details
        ) from exc
