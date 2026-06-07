from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from agents.mcp import MCPServerStdio, create_static_tool_filter

from .config import Settings
from .tools import SAFE_CML_TOOLS


def cml_mcp_params(settings: Settings) -> dict[str, object]:
    return {
        "command": settings.uvx_command,
        "args": ["--python", settings.mcp_python, "cml-mcp[pyats]"],
        "env": settings.cml_env(),
    }


def create_cml_mcp_server(settings: Settings) -> MCPServerStdio:
    return MCPServerStdio(
        name="Cisco Modeling Labs",
        params=cml_mcp_params(settings),
        client_session_timeout_seconds=settings.mcp_timeout_seconds,
        tool_filter=create_static_tool_filter(allowed_tool_names=list(SAFE_CML_TOOLS)),
    )


@asynccontextmanager
async def cml_mcp_server(settings: Settings) -> AsyncIterator[MCPServerStdio]:
    async with create_cml_mcp_server(settings) as server:
        yield server


async def list_safe_tools(settings: Settings) -> list[str]:
    async with cml_mcp_server(settings) as server:
        tools = await server.list_tools()
    return sorted(tool.name for tool in tools)
