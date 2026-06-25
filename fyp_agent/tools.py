"""工具暴露与审计策略 — 控制 Agent 可以调用哪些 CML MCP 工具。

当前项目调性偏向快速、合理的试错和迭代：默认信任 cml-mcp server 暴露的全部工具。
如果后续需要收紧范围，可以把 `ALL_CML_TOOLS` 替换为具体 frozenset。
"""

from __future__ import annotations

ToolAllowlist = frozenset[str] | None

# None 表示不做本地白名单过滤：MCP server 动态列出的工具都会暴露给 agent。
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
    """根据 cml-mcp 工具命名约定判断工具是否可能修改 CML 状态。"""
    return tool_name.startswith(MUTATING_TOOL_PREFIXES)
