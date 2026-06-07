from __future__ import annotations

import shutil

from .config import ConfigError, Settings, load_settings
from .mcp_client import list_safe_tools


async def run_doctor() -> tuple[int, list[str]]:
    messages: list[str] = []

    try:
        settings = load_settings()
        messages.append("OK: loaded .env configuration")
    except ConfigError as exc:
        return 1, [str(exc)]

    uvx_path = shutil.which(settings.uvx_command)
    if uvx_path:
        messages.append(f"OK: found {settings.uvx_command} at {uvx_path}")
    else:
        messages.append(f"FAIL: {settings.uvx_command} was not found on PATH")
        return 1, messages

    if settings.provider_api_key:
        key_name = "OPENAI_API_KEY" if settings.llm_provider == "openai" else "DEEPSEEK_API_KEY"
        messages.append(f"OK: {key_name} is set")
        messages.append(f"OK: using {settings.llm_provider} model {settings.model_name}")
    else:
        key_name = "OPENAI_API_KEY" if settings.llm_provider == "openai" else "DEEPSEEK_API_KEY"
        messages.append(f"FAIL: {key_name} is missing")
        return 1, messages

    try:
        tools = await list_safe_tools(settings)
    except Exception as exc:
        messages.append(f"FAIL: could not start or query CML MCP server: {type(exc).__name__}: {exc}")
        return 1, messages

    messages.append(f"OK: CML MCP server started and exposed {len(tools)} allowed tools")
    for tool in tools:
        messages.append(f"  - {tool}")
    return 0, messages
