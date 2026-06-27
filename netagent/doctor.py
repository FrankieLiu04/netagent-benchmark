# EN: Doctor checks for LLM provider and CML MCP connectivity.
# CN: 检查 LLM provider 和 CML MCP 的连通性。

from __future__ import annotations

from .config import ConfigError, load_settings
from .mcp_client import list_agent_tools


async def run_doctor() -> tuple[int, list[str]]:
    # EN: Check the runtime environment and return exit code plus messages.
    # CN: 逐项检查运行环境，并返回退出码和消息列表。
    messages: list[str] = []

    # EN: Load runtime configuration before probing external services.
    # CN: 先加载运行配置，再探测外部服务。
    try:
        settings = load_settings()
        messages.append("OK: loaded .env configuration")
    except ConfigError as exc:
        return 1, [str(exc)]

    # EN: Fail early if the local MCP package is unavailable.
    # CN: 本地 MCP 包不可用时提前失败。
    try:
        import cml_mcp  # noqa: F401
        messages.append("OK: cml-mcp package is importable")
    except ImportError:
        messages.append("FAIL: cml-mcp is not installed. Run: pip install cml-mcp[pyats]")
        return 1, messages

    # EN: Validate only the key required by the selected provider.
    # CN: 只校验当前 provider 所需的 key。
    if settings.provider_api_key:
        key_name = "OPENAI_API_KEY" if settings.llm_provider == "openai" else "DEEPSEEK_API_KEY"
        messages.append(f"OK: {key_name} is set")
        messages.append(f"OK: using {settings.llm_provider} model {settings.model_name}")
    else:
        key_name = "OPENAI_API_KEY" if settings.llm_provider == "openai" else "DEEPSEEK_API_KEY"
        messages.append(f"FAIL: {key_name} is missing")
        return 1, messages

    # EN: Start MCP once to verify CML reachability and tool discovery.
    # CN: 启动一次 MCP，验证 CML 可达性和工具发现。
    try:
        tools = await list_agent_tools(settings)
    except Exception as exc:
        # EN: list_agent_tools covers the MCP subprocess and remote CML reachability.
        # CN: list_agent_tools 覆盖 MCP 子进程和远端 CML 可达性。
        messages.append(f"FAIL: could not start or query CML MCP server: {type(exc).__name__}: {exc}")
        return 1, messages

    messages.append(f"OK: CML MCP server started and exposed {len(tools)} tools")
    for tool in tools:
        messages.append(f"  - {tool}")
    return 0, messages
