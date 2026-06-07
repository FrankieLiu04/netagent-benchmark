"""工具白名单 — 控制 Agent 可以调用哪些 CML MCP 工具。

当前处于 Phase 1（read-only），仅允许 8 个只读工具。
后续 Phase 会逐步开放更多工具。
"""

from __future__ import annotations

# 只读 CML MCP 工具白名单（Phase 1: 仅查询，禁止修改）
SAFE_CML_TOOLS: frozenset[str] = frozenset(
    {
        "get_cml_information",   # 获取 CML 服务器信息（版本、主机名等）
        "get_cml_status",        # 获取 CML 系统健康状态
        "get_cml_labs",          # 列出所有 lab
        "get_cml_lab_by_title",  # 按标题搜索 lab
        "get_nodes_for_cml_lab", # 获取 lab 中的节点列表
        "get_interfaces_for_node", # 获取节点的网络接口
        "get_all_links_for_lab", # 获取 lab 中的所有链路
        "get_console_log",       # 获取节点控制台日志
    }
)


def is_allowed_tool(tool_name: str, allowed_tools: set[str] | frozenset[str] = SAFE_CML_TOOLS) -> bool:
    return tool_name in allowed_tools


def filter_tool_names(tool_names: list[str], allowed_tools: set[str] | frozenset[str] = SAFE_CML_TOOLS) -> list[str]:
    return sorted(name for name in tool_names if is_allowed_tool(name, allowed_tools))
