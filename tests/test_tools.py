from __future__ import annotations

from fyp_agent.tools import ALL_CML_TOOLS, filter_tool_names, is_allowed_tool, is_mutating_tool


def test_default_tool_policy_accepts_all_tools():
    assert is_allowed_tool("get_cml_labs")
    assert is_allowed_tool("delete_cml_lab")
    assert ALL_CML_TOOLS is None


def test_default_tool_policy_does_not_filter_mutating_tools():
    tool_names = [
        "get_cml_labs",
        "delete_cml_lab",
        "configure_cml_node",
        "send_cli_command",
        "get_console_log",
    ]

    assert filter_tool_names(tool_names) == sorted(tool_names)


def test_explicit_tool_allowlist_can_still_filter_tools():
    tool_names = ["get_cml_labs", "delete_cml_lab", "get_console_log"]
    allowed = frozenset({"get_cml_labs", "get_console_log"})

    assert filter_tool_names(tool_names, allowed) == ["get_cml_labs", "get_console_log"]


def test_mutating_tool_classifier_uses_cml_mcp_naming_convention():
    assert is_mutating_tool("delete_cml_lab")
    assert is_mutating_tool("send_cli_command")
    assert is_mutating_tool("configure_cml_node")
    assert not is_mutating_tool("get_cml_labs")
    assert not is_mutating_tool("check_packet_capture_status")
