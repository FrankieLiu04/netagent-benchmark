from __future__ import annotations

import argparse
import asyncio
import sys

from .config import ConfigError, load_settings
from .doctor import run_doctor
from .mcp_client import list_agent_tools
from .runner import run_agent_task


def build_parser() -> argparse.ArgumentParser:
    # EN: Build the CLI parser for run, tools, and doctor.
    # CN: 构建包含 run、tools、doctor 的 CLI 参数解析器。
    parser = argparse.ArgumentParser(prog="netagent", description="NetAgent CML benchmark harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one CML agent task")
    run_parser.add_argument("task", help="Natural-language task for the agent")

    subparsers.add_parser("tools", help="List CML MCP tools exposed to the agent")

    subparsers.add_parser("doctor", help="Check LLM provider and CML MCP connectivity")
    return parser


async def _main_async(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        code, messages = await run_doctor()
        print("\n".join(messages))
        return code

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.command == "tools":
        try:
            tools = await list_agent_tools(settings)
        except Exception as exc:
            # EN: Collapse MCP/CML startup and query failures into one CLI error.
            # CN: 将 MCP/CML 启动和查询失败收敛为一条 CLI 错误。
            print(f"Failed to list CML MCP tools: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print("\n".join(tools))
        return 0

    if args.command == "run":
        try:
            result = await run_agent_task(settings, args.task)
        except Exception as exc:
            # EN: The runner already wrote the structured log; show only the summary.
            # CN: runner 已写入结构化日志；这里只展示摘要。
            print(str(exc), file=sys.stderr)
            return 1
        print(result.final_answer)
        print(f"\nRun log: {result.run_log_path}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main_async(argv))
