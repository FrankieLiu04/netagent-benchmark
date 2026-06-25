"""诊断工具 — 检查 LLM provider 和 CML MCP 的连通性。"""

from __future__ import annotations

from .config import ConfigError, load_settings
from .mcp_client import list_agent_tools


async def run_doctor() -> tuple[int, list[str]]:
    """逐项检查运行环境，返回 (退出码, 消息列表)。"""
    messages: list[str] = []

    # 1. 加载 .env 配置
    try:
        settings = load_settings()
        messages.append("OK: loaded .env configuration")
    except ConfigError as exc:
        return 1, [str(exc)]

    # 2. 检查 cml-mcp 包是否可导入
    try:
        import cml_mcp  # noqa: F401
        messages.append("OK: cml-mcp package is importable")
    except ImportError:
        messages.append("FAIL: cml-mcp is not installed. Run: pip install cml-mcp[pyats]")
        return 1, messages

    # 3. 检查 LLM API key
    if settings.provider_api_key:
        key_name = "OPENAI_API_KEY" if settings.llm_provider == "openai" else "DEEPSEEK_API_KEY"
        messages.append(f"OK: {key_name} is set")
        messages.append(f"OK: using {settings.llm_provider} model {settings.model_name}")
    else:
        key_name = "OPENAI_API_KEY" if settings.llm_provider == "openai" else "DEEPSEEK_API_KEY"
        messages.append(f"FAIL: {key_name} is missing")
        return 1, messages

    # 4. 检查 CML MCP server 是否能启动并列出工具
    try:
        tools = await list_agent_tools(settings)
    except Exception as exc:
        messages.append(f"FAIL: could not start or query CML MCP server: {type(exc).__name__}: {exc}")
        return 1, messages

    messages.append(f"OK: CML MCP server started and exposed {len(tools)} tools")
    for tool in tools:
        messages.append(f"  - {tool}")
    return 0, messages
