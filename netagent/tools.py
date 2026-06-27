# EN: Tool exposure and audit policy for CML MCP tools.
# CN: 控制 agent 可见的 CML MCP 工具与审计判断。

from __future__ import annotations

ToolAllowlist = frozenset[str] | None

# EN: None keeps the MCP server as the single source of visible tools.
# CN: None 表示以 MCP server 动态列出的工具为准。
ALL_CML_TOOLS: ToolAllowlist = None

MUTATING_TOOL_PREFIXES = (
    "add_",
    "apply_",
    "clone_",
    "configure_",
    "connect_",
    "create_",
    "delete_",
    "modify_",
    "send_",
    "set_",
    "start_",
    "stop_",
    "wipe_",
)

def is_allowed_tool(tool_name: str, allowed_tools: ToolAllowlist = ALL_CML_TOOLS) -> bool:
    if allowed_tools is None:
        return True
    return tool_name in allowed_tools


def filter_tool_names(tool_names: list[str], allowed_tools: ToolAllowlist = ALL_CML_TOOLS) -> list[str]:
    if allowed_tools is None:
        return sorted(tool_names)
    return sorted(name for name in tool_names if is_allowed_tool(name, allowed_tools))


def is_mutating_tool(tool_name: str) -> bool:
    # EN: Detect likely CML mutations from cml-mcp tool names.
    # CN: 根据 cml-mcp 工具名判断是否可能修改 CML 状态。
    return tool_name.startswith(MUTATING_TOOL_PREFIXES)
