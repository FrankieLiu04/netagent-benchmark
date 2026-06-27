# EN: End-to-end agent loop tests with mock MCP and mock LLM.
# CN: 使用 mock MCP 和 mock LLM 的端到端 agent loop 测试。

from __future__ import annotations

import sys
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from netagent.llm import LLMResponse, ToolCall
from netagent.loop import agent_loop
from netagent.mcp_client import CmlMcpSession, MCPToolDef
from netagent.prompts import get_system_prompt

# EN: Add the repo root so local test mocks are importable.
# CN: 加入仓库根目录，确保可导入本地 test mocks。
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mocks.mock_llm import MockLLMClient  # noqa: E402
from tests.mocks.mock_mcp_server import MOCK_TOOLS  # noqa: E402

MOCK_SERVER_PATH = str(Path(__file__).parent / "mocks" / "mock_mcp_server.py")


@asynccontextmanager
async def mock_mcp_session() -> AsyncIterator[CmlMcpSession]:
    # EN: Start the mock MCP server and yield a managed session.
    # CN: 启动 mock MCP server 并返回受管理的会话。
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


async def _run_agent(
    mock_llm: MockLLMClient,
    *,
    task: str = "List all CML labs and show server info",
    system_prompt: str = "test",
    max_steps: int = 10,
    hooks=None,
):
    async with mock_mcp_session() as mcp:
        return await agent_loop(
            task=task,
            system_prompt=system_prompt,
            llm=mock_llm,  # type: ignore[arg-type]
            mcp=mcp,
            tools=_mock_tool_defs(),
            max_steps=max_steps,
            hooks=hooks,
        )


def _assert_default_trace(result) -> None:
    assert len(result.traces) == 3
    step0 = result.traces[0]
    assert len(step0.llm_response.tool_calls) == 1
    assert step0.llm_response.tool_calls[0].name == "get_cml_labs"
    assert step0.tool_results[0]["success"] is True
    assert step0.tool_audit[0].tool_name == "get_cml_labs"
    assert step0.tool_audit[0].mutating is False
    assert step0.tool_audit[0].result_size_chars > 0
    assert result.traces[1].llm_response.tool_calls[0].name == "get_cml_information"
    assert result.traces[2].llm_response.tool_calls == []


def _assert_token_totals(result) -> None:
    assert result.total_prompt_tokens > 0
    assert result.total_completion_tokens > 0
    assert result.total_prompt_tokens == sum(t.llm_response.prompt_tokens for t in result.traces)
    assert result.total_completion_tokens == sum(
        t.llm_response.completion_tokens for t in result.traces
    )


def _assert_message_history(result, expected_tool_steps: int) -> None:
    assert result.messages[0]["role"] == "user"
    assistant_msgs = [m for m in result.messages if m["role"] == "assistant"]
    tool_msgs = [m for m in result.messages if m["role"] == "tool"]
    assert len(assistant_msgs) == expected_tool_steps
    assert len(tool_msgs) == expected_tool_steps


def _delete_lab_script() -> list[LLMResponse]:
    return [
        LLMResponse(
            content="Let me delete this lab.",
            tool_calls=[ToolCall(id="call-0", name="delete_cml_lab", arguments={"lab_id": "x"})],
            finish_reason="tool_calls",
            prompt_tokens=50,
            completion_tokens=10,
            raw_message={},
        ),
        LLMResponse(
            content="The lab deletion request was sent to CML.",
            tool_calls=[],
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=30,
            raw_message={},
        ),
    ]


def _labs_then_done_script() -> list[LLMResponse]:
    return [
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


async def test_agent_loop_e2e():
    result = await _run_agent(MockLLMClient(), system_prompt=get_system_prompt("full_access"))

    assert result.steps == 3
    assert "OSPF-Demo" in result.final_answer
    assert "2.9.1" in result.final_answer
    _assert_default_trace(result)
    _assert_token_totals(result)
    _assert_message_history(result, expected_tool_steps=2)
    assert [entry.tool_name for entry in result.tool_audit] == [
        "get_cml_labs",
        "get_cml_information",
    ]


async def test_agent_loop_max_steps():
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

    result = await _run_agent(mock_llm, task="infinite loop test", max_steps=3)

    assert result.steps == 3
    # EN: Exhausted loops return the last model content.
    # CN: 循环耗尽时返回最后一次模型内容。
    assert result.final_answer == "checking..."


async def test_agent_loop_mutating_tool_is_forwarded_to_mcp():
    result = await _run_agent(
        MockLLMClient(script=_delete_lab_script()),
        task="delete a lab",
        max_steps=5,
    )

    step0 = result.traces[0]
    assert step0.tool_results[0]["success"] is True
    assert "delete_cml_lab" in step0.tool_results[0]["result"]
    assert step0.tool_audit[0].mutating is True
    assert result.tool_audit[0].arguments == {"lab_id": "x"}
    assert result.steps == 2
    assert "sent to CML" in result.final_answer


async def test_agent_loop_with_hook():
    hook_calls: list[int] = []

    def counting_hook(messages, trace, step):
        hook_calls.append(step)
        return messages

    result = await _run_agent(
        MockLLMClient(script=_labs_then_done_script()),
        task="list labs",
        max_steps=5,
        hooks=[counting_hook],
    )

    assert len(hook_calls) == 2
    assert hook_calls == [0, 1]
    assert "2 labs" in result.final_answer
