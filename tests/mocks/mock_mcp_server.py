"""Mock MCP server — 用 mcp SDK 实现的本地假 CML server，用于无内网环境下的测试。

通过 stdio transport 启动，模拟 cml-mcp 的工具列表和返回值。
真实 cml-mcp 启动方式是 `python -m cml_mcp`，这个 mock 启动方式是
`python -m tests.mocks.mock_mcp_server`。
"""

from __future__ import annotations

import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

MOCK_TOOLS: list[Tool] = [
    Tool(
        name="get_cml_information",
        description="Get CML server information (version, hostname, etc.)",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_cml_status",
        description="Get CML system health status",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_cml_labs",
        description="List all labs on the CML server",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_cml_lab_by_title",
        description="Search for a lab by its title",
        inputSchema={
            "type": "object",
            "properties": {"title": {"type": "string", "description": "Lab title to search for"}},
            "required": ["title"],
        },
    ),
    Tool(
        name="get_nodes_for_cml_lab",
        description="Get the list of nodes in a lab",
        inputSchema={
            "type": "object",
            "properties": {"lab_id": {"type": "string", "description": "Lab ID"}},
            "required": ["lab_id"],
        },
    ),
    Tool(
        name="get_interfaces_for_node",
        description="Get network interfaces for a node",
        inputSchema={
            "type": "object",
            "properties": {
                "lab_id": {"type": "string"},
                "node_id": {"type": "string"},
            },
            "required": ["lab_id", "node_id"],
        },
    ),
    Tool(
        name="get_all_links_for_lab",
        description="Get all links in a lab",
        inputSchema={
            "type": "object",
            "properties": {"lab_id": {"type": "string"}},
            "required": ["lab_id"],
        },
    ),
    Tool(
        name="get_console_log",
        description="Get console log for a node",
        inputSchema={
            "type": "object",
            "properties": {"lab_id": {"type": "string"}, "node_id": {"type": "string"}},
            "required": ["lab_id", "node_id"],
        },
    ),
]


MOCK_RESPONSES: dict[str, str] = {
    "get_cml_information": json.dumps(
        {"version": "2.9.1", "hostname": "mock-cml.example", "ready": True}
    ),
    "get_cml_status": json.dumps({"status": "healthy", "clusters": 1}),
    "get_cml_labs": json.dumps(
        [
            {"id": "lab-001", "title": "OSPF-Demo", "state": "STARTED"},
            {"id": "lab-002", "title": "BGP-Lab", "state": "STOPPED"},
        ]
    ),
}

server = Server("mock-cml")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return MOCK_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name in MOCK_RESPONSES:
        text = MOCK_RESPONSES[name]
    elif name == "get_cml_lab_by_title":
        title = arguments.get("title", "")
        if "OSPF" in title.upper():
            text = json.dumps([{"id": "lab-001", "title": "OSPF-Demo", "state": "STARTED"}])
        else:
            text = json.dumps([])
    elif name == "get_nodes_for_cml_lab":
        lab_id = arguments.get("lab_id", "")
        text = json.dumps(
            [
                {"id": f"{lab_id}-n1", "label": "R1", "type": "router"},
                {"id": f"{lab_id}-n2", "label": "R2", "type": "router"},
            ]
        )
    else:
        text = json.dumps({"result": "ok", "tool": name, "args": arguments})

    return [TextContent(type="text", text=text)]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
