"""MCP 客户端 — 通过 mcp SDK 直连 cml-mcp 子进程（stdio transport）。

替代旧版 agents.mcp.MCPServerStdio，直接使用 mcp.ClientSession
管理 JSON-RPC 通信，暴露 list_tools / call_tool 两个核心方法。
"""

from __future__ import annotations

import sys
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, Tool

from .config import Settings
from .tools import SAFE_CML_TOOLS


@dataclass
class MCPToolDef:
    """单个 MCP 工具的定义，用于转换为 LLM function-calling schema。"""

    name: str
    description: str
    input_schema: dict[str, Any]


def _content_to_text(content_blocks: list[Any]) -> str:
    """将 MCP call_tool 返回的 content blocks 提取为纯文本。"""
    parts: list[str] = []
    for block in content_blocks:
        if isinstance(block, TextContent):
            parts.append(block.text)
        else:
            parts.append(str(block))
    return "\n".join(parts)


class CmlMcpSession:
    """封装一次 MCP 会话，提供工具列表和工具调用接口。"""

    def __init__(self, session: ClientSession, allowed: frozenset[str] = SAFE_CML_TOOLS) -> None:
        self._session = session
        self._allowed = allowed

    async def list_tools(self) -> list[MCPToolDef]:
        """列出白名单内的 MCP 工具。"""
        result = await self._session.list_tools()
        tools: list[MCPToolDef] = []
        for tool in result.tools:
            if tool.name in self._allowed:
                tools.append(
                    MCPToolDef(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema or {"type": "object", "properties": {}},
                    )
                )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """调用一个 MCP 工具，返回纯文本结果。

        如果工具不在白名单内，拒绝执行。
        """
        if name not in self._allowed:
            raise PermissionError(f"Tool '{name}' is not in the safe allowlist")

        result = await self._session.call_tool(name, arguments=arguments)
        return _content_to_text(result.content)

    async def call_raw(self, name: str, arguments: dict[str, Any]) -> Any:
        """调用工具并返回原始 MCP result（含 is_error 等元数据）。"""
        if name not in self._allowed:
            raise PermissionError(f"Tool '{name}' is not in the safe allowlist")
        return await self._session.call_tool(name, arguments=arguments)


def cml_mcp_params(settings: Settings) -> StdioServerParameters:
    """构建启动 cml-mcp 子进程的参数。"""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "cml_mcp"],
        env=settings.cml_env(),
    )


@asynccontextmanager
async def cml_mcp_session(
    settings: Settings,
    allowed: frozenset[str] = SAFE_CML_TOOLS,
) -> AsyncIterator[CmlMcpSession]:
    """启动 cml-mcp 子进程，建立 MCP 会话，yield CmlMcpSession。

    退出时自动关闭子进程和会话。
    """
    params = cml_mcp_params(settings)
    # 用 AsyncExitStack 管理嵌套的 async context managers
    async with AsyncExitStack() as stack:
        read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        yield CmlMcpSession(session, allowed=allowed)


async def list_safe_tools(settings: Settings) -> list[str]:
    """启动 MCP server 并列出白名单内的工具名称。"""
    async with cml_mcp_session(settings) as mcp:
        tools = await mcp.list_tools()
    return sorted(tool.name for tool in tools)
