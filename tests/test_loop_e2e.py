"""端到端 agent loop 测试 — 使用 mock MCP server + mock LLM，无需内网/API key。

验证：
1. agent_loop 能正确驱动 LLM → MCP tool call → LLM → final answer 的循环
2. trace 数据结构完整
3. token 计数正确
4. messages 历史正确
"""

from __future__ import annotations

import sys
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from fyp_agent.llm import LLMResponse, ToolCall
from fyp_agent.loop import agent_loop
from fyp_agent.mcp_client import CmlMcpSession, MCPToolDef
from fyp_agent.prompts import get_system_prompt

# 确保能导入 tests.mocks
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mocks.mock_llm import MockLLMClient  # noqa: E402
from tests.mocks.mock_mcp_server import MOCK_TOOLS  # noqa: E402

MOCK_SERVER_PATH = str(Path(__file__).parent / "mocks" / "mock_mcp_server.py")


@asynccontextmanager
async def mock_mcp_session() -> AsyncIterator[CmlMcpSession]:
    """启动 mock MCP server，yield CmlMcpSession，退出时自动清理。"""
    params = StdioServerParameters(
        command=sys.executable,
        args=[MOCK_SERVER_PATH],
    )
    async with AsyncExitStack() as stack:
        read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        yield CmlMcpSession(session)


def _mock_tool_defs() -> list[MCPToolDef]:
    return [
        MCPToolDef(
            name=t.name,
            description=t.description or "",
            input_schema=t.inputSchema or {"type": "object", "properties": {}},
        )
        for t in MOCK_TOOLS
    ]


async def test_agent_loop_e2e():
    """完整测试 agent loop：2 次 tool call + 1 次最终回答。"""
    mock_llm = MockLLMClient()

    async with mock_mcp_session() as mcp:
        result = await agent_loop(
            task="List all CML labs and show server info",
            system_prompt=get_system_prompt("read_only"),
            llm=mock_llm,  # type: ignore[arg-type]
            mcp=mcp,
            tools=_mock_tool_defs(),
            max_steps=10,
        )

        # 3 步：2 tool calls + 1 final answer
        assert result.steps == 3
        assert "OSPF-Demo" in result.final_answer
        assert "2.9.1" in result.final_answer

        # 验证 trace
        assert len(result.traces) == 3
        step0 = result.traces[0]
        assert len(step0.llm_response.tool_calls) == 1
        assert step0.llm_response.tool_calls[0].name == "get_cml_labs"
        assert len(step0.tool_results) == 1
        assert step0.tool_results[0]["success"] is True

        step1 = result.traces[1]
        assert step1.llm_response.tool_calls[0].name == "get_cml_information"

        step2 = result.traces[2]
        assert step2.llm_response.tool_calls == []
        assert step2.llm_response.finish_reason == "stop"

        # 验证 token 统计
        assert result.total_prompt_tokens > 0
        assert result.total_completion_tokens > 0
        assert result.total_prompt_tokens == sum(t.llm_response.prompt_tokens for t in result.traces)
        assert result.total_completion_tokens == sum(
            t.llm_response.completion_tokens for t in result.traces
        )

        # 验证 messages 历史
        assert result.messages[0]["role"] == "user"
        # tool-call steps 会追加 assistant message + tool result message
        # final step（无 tool_call）不会追加 assistant message
        assistant_msgs = [m for m in result.messages if m["role"] == "assistant"]
        tool_msgs = [m for m in result.messages if m["role"] == "tool"]
        assert len(assistant_msgs) == 2  # 2 tool-call steps
        assert len(tool_msgs) == 2


async def test_agent_loop_max_steps():
    """测试 max_steps 限制：LLM 一直调用工具不回答时应该被截断。"""
    infinite_script = [
        LLMResponse(
            content="checking...",
            tool_calls=[ToolCall(id=f"call-{i}", name="get_cml_labs", arguments={})],
            finish_reason="tool_calls",
            prompt_tokens=50,
            completion_tokens=10,
            raw_message={},
        )
        for i in range(100)
    ]
    mock_llm = MockLLMClient(script=infinite_script)

    async with mock_mcp_session() as mcp:
        result = await agent_loop(
            task="infinite loop test",
            system_prompt="test",
            llm=mock_llm,  # type: ignore[arg-type]
            mcp=mcp,
            tools=_mock_tool_defs(),
            max_steps=3,
        )

        assert result.steps == 3
        # loop 耗尽时，final_answer 取自最后一次 response.content
        assert result.final_answer == "checking..."


async def test_agent_loop_tool_error_handling():
    """测试工具调用失败时的错误处理（白名单拒绝）。"""
    mock_llm = MockLLMClient(
        script=[
            LLMResponse(
                content="Let me delete this lab.",
                tool_calls=[ToolCall(id="call-0", name="delete_cml_lab", arguments={"lab_id": "x"})],
                finish_reason="tool_calls",
                prompt_tokens=50,
                completion_tokens=10,
                raw_message={},
            ),
            LLMResponse(
                content="I could not delete the lab as this is a read-only agent.",
                tool_calls=[],
                finish_reason="stop",
                prompt_tokens=100,
                completion_tokens=30,
                raw_message={},
            ),
        ]
    )

    async with mock_mcp_session() as mcp:
        result = await agent_loop(
            task="delete a lab",
            system_prompt="test",
            llm=mock_llm,  # type: ignore[arg-type]
            mcp=mcp,
            tools=_mock_tool_defs(),
            max_steps=5,
        )

        # 第一步工具调用应该失败（PermissionError），但 loop 应该继续
        step0 = result.traces[0]
        assert len(step0.tool_results) == 1
        assert step0.tool_results[0]["success"] is False
        assert "PermissionError" in step0.tool_results[0]["error"]

        # loop 应该继续到第二步并给出最终答案
        assert result.steps == 2
        assert "read-only" in result.final_answer.lower()


async def test_agent_loop_with_hook():
    """测试 StepHook 系统：hook 每步都被调用。"""
    hook_calls: list[int] = []

    def counting_hook(messages, trace, step):
        hook_calls.append(step)
        return messages

    mock_llm = MockLLMClient(
        script=[
            LLMResponse(
                content="checking...",
                tool_calls=[ToolCall(id="call-0", name="get_cml_labs", arguments={})],
                finish_reason="tool_calls",
                prompt_tokens=50,
                completion_tokens=10,
                raw_message={},
            ),
            LLMResponse(
                content="Done. Found 2 labs.",
                tool_calls=[],
                finish_reason="stop",
                prompt_tokens=100,
                completion_tokens=30,
                raw_message={},
            ),
        ]
    )

    async with mock_mcp_session() as mcp:
        result = await agent_loop(
            task="list labs",
            system_prompt="test",
            llm=mock_llm,  # type: ignore[arg-type]
            mcp=mcp,
            tools=_mock_tool_defs(),
            max_steps=5,
            hooks=[counting_hook],
        )

        assert len(hook_calls) == 2  # 2 steps
        assert hook_calls == [0, 1]
        assert "2 labs" in result.final_answer
