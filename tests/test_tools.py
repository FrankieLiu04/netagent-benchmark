from __future__ import annotations

from fyp_agent.tools import SAFE_CML_TOOLS, filter_tool_names, is_allowed_tool


def test_tool_allowlist_accepts_safe_tools():
    assert is_allowed_tool("get_cml_labs")
    assert "get_cml_status" in SAFE_CML_TOOLS


def test_tool_allowlist_filters_mutating_tools():
    tool_names = [
        "get_cml_labs",
        "delete_cml_lab",
        "configure_cml_node",
        "send_cli_command",
        "get_console_log",
    ]

    assert filter_tool_names(tool_names) == ["get_cml_labs", "get_console_log"]
