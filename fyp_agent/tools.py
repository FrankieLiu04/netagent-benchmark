from __future__ import annotations

SAFE_CML_TOOLS: frozenset[str] = frozenset(
    {
        "get_cml_information",
        "get_cml_status",
        "get_cml_labs",
        "get_cml_lab_by_title",
        "get_nodes_for_cml_lab",
        "get_interfaces_for_node",
        "get_all_links_for_lab",
        "get_console_log",
    }
)


def is_allowed_tool(tool_name: str, allowed_tools: set[str] | frozenset[str] = SAFE_CML_TOOLS) -> bool:
    return tool_name in allowed_tools


def filter_tool_names(tool_names: list[str], allowed_tools: set[str] | frozenset[str] = SAFE_CML_TOOLS) -> list[str]:
    return sorted(name for name in tool_names if is_allowed_tool(name, allowed_tools))
