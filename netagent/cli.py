from __future__ import annotations

import argparse
import asyncio
import sys

from .config import ConfigError, load_settings
from .doctor import run_doctor
from .mcp_client import list_agent_tools
from .runner import run_agent_task


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器，包含 run / tools / doctor 三个子命令。"""
    parser = argparse.ArgumentParser(prog="netagent", description="NetAgent CML benchmark harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # netagent run "task" — 执行一次 CML agent 任务
    run_parser = subparsers.add_parser("run", help="Run one CML agent task")
    run_parser.add_argument("task", help="Natural-language task for the agent")

    # netagent tools — 列出当前 Agent 可见的 CML MCP 工具
    subparsers.add_parser("tools", help="List CML MCP tools exposed to the agent")

    # netagent doctor — 诊断运行环境
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
            print(f"Failed to list CML MCP tools: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print("\n".join(tools))
        return 0

    if args.command == "run":
        try:
            result = await run_agent_task(settings, args.task)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(result.final_answer)
        print(f"\nRun log: {result.run_log_path}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main_async(argv))
