from __future__ import annotations

import json
from pathlib import Path

from fyp_agent.llm import LLMClient, LLMResponse, ToolCall
from fyp_agent.mcp_client import MCPToolDef


def test_mcp_tools_to_openai_format():
    """验证 MCP 工具定义能正确转换为 OpenAI function tool 格式。"""
    tools = [
        MCPToolDef(
            name="get_cml_labs",
            description="List all labs",
            input_schema={"type": "object", "properties": {}},
        ),
        MCPToolDef(
            name="get_nodes_for_cml_lab",
            description="Get nodes in a lab",
            input_schema={
                "type": "object",
                "properties": {"lab_id": {"type": "string"}},
                "required": ["lab_id"],
            },
        ),
    ]

    result = LLMClient.mcp_tools_to_openai(tools)
    assert len(result) == 2
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "get_cml_labs"
    assert result[0]["function"]["description"] == "List all labs"
    assert result[1]["function"]["parameters"]["required"] == ["lab_id"]


def test_llm_response_dataclass():
    """验证 LLMResponse 数据结构。"""
    resp = LLMResponse(
        content="hello",
        tool_calls=[ToolCall(id="tc1", name="get_cml_labs", arguments={})],
        finish_reason="tool_calls",
        prompt_tokens=100,
        completion_tokens=50,
        raw_message={"role": "assistant"},
    )
    assert resp.tool_calls[0].name == "get_cml_labs"
    assert resp.prompt_tokens == 100
    assert resp.completion_tokens == 50
