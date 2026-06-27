# EN: MCP client using the MCP SDK to reach cml-mcp over stdio.
# CN: 通过 MCP SDK 以 stdio 直连 cml-mcp 子进程。

from __future__ import annotations

import sys
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, Tool

from .config import Settings
from .tools import ALL_CML_TOOLS, ToolAllowlist


@dataclass
class MCPToolDef:
    # EN: Single MCP tool definition for LLM function-calling schemas.
    # CN: 单个 MCP 工具定义，用于转换为 LLM function-calling schema。

    name: str
    description: str
    input_schema: dict[str, Any]


def _content_to_text(content_blocks: list[Any]) -> str:
    # EN: Extract plain text from MCP call_tool content blocks.
    # CN: 从 MCP call_tool content blocks 中提取纯文本。
    parts: list[str] = []
    for block in content_blocks:
        if isinstance(block, TextContent):
            parts.append(block.text)
        else:
            parts.append(str(block))
    return "\n".join(parts)


class CmlMcpSession:
    # EN: Wrap one MCP session with tool listing and tool calls.
    # CN: 封装一次 MCP 会话，提供工具列表和工具调用接口。

    def __init__(self, session: ClientSession, allowed: ToolAllowlist = ALL_CML_TOOLS) -> None:
        self._session = session
        self._allowed = allowed

    async def list_tools(self) -> list[MCPToolDef]:
        # EN: List MCP tools currently exposed to the agent.
        # CN: 列出当前暴露给 agent 的 MCP 工具。
        result = await self._session.list_tools()
        tools: list[MCPToolDef] = []
        for tool in result.tools:
            if self._allowed is None or tool.name in self._allowed:
                tools.append(
                    MCPToolDef(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema or {"type": "object", "properties": {}},
                    )
                )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        # EN: Call one MCP tool and return a plain-text result.
        # CN: 调用一个 MCP 工具，并返回纯文本结果。
        if self._allowed is not None and name not in self._allowed:
            raise PermissionError(f"Tool '{name}' is not in the configured tool allowlist")

        result = await self._session.call_tool(name, arguments=arguments)
        return _content_to_text(result.content)

    async def call_raw(self, name: str, arguments: dict[str, Any]) -> Any:
        # EN: Call a tool and return the raw MCP result metadata.
        # CN: 调用工具并返回原始 MCP result 元数据。
        if self._allowed is not None and name not in self._allowed:
            raise PermissionError(f"Tool '{name}' is not in the configured tool allowlist")
        return await self._session.call_tool(name, arguments=arguments)


def cml_mcp_params(settings: Settings) -> StdioServerParameters:
    # EN: Build parameters for starting the cml-mcp subprocess.
    # CN: 构建启动 cml-mcp 子进程的参数。
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "cml_mcp"],
        env=settings.cml_env(),
    )


@asynccontextmanager
async def cml_mcp_session(
    settings: Settings,
    allowed: ToolAllowlist = ALL_CML_TOOLS,
) -> AsyncIterator[CmlMcpSession]:
    # EN: Start cml-mcp and yield an initialized MCP session.
    # CN: 启动 cml-mcp 并返回已初始化的 MCP 会话。
    params = cml_mcp_params(settings)
    # EN: AsyncExitStack keeps both stdio and MCP sessions closed together.
    # CN: AsyncExitStack 统一关闭 stdio 与 MCP 会话。
    async with AsyncExitStack() as stack:
        read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        yield CmlMcpSession(session, allowed=allowed)


async def list_agent_tools(settings: Settings) -> list[str]:
    # EN: Start the MCP server and list tool names visible to the agent.
    # CN: 启动 MCP server 并列出 agent 可见的工具名称。
    async with cml_mcp_session(settings) as mcp:
        tools = await mcp.list_tools()
    return sorted(tool.name for tool in tools)
