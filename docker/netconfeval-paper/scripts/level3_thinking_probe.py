"""Level 3 探针 — 对比 DeepSeek thinking 模式下的 Step 2 代码生成。

该脚本复用上游 NetConfEval 的 Step 2 prompt、测试资产和 verifier，
但绕开旧 LangChain 调用层，直接使用 OpenAI-compatible streaming API。
这样可以保存 `reasoning_content`、最终输出、生成代码和 verifier 结果。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class Variant:
    """一次 thinking 配置实验。"""

    label: str
    description: str
    thinking_type: str | None
    reasoning_effort: str | None


VARIANTS: tuple[Variant, ...] = (
    Variant("A_default", "default thinking behavior", None, None),
    Variant("B_enabled_high", "thinking enabled with high effort", "enabled", "high"),
    Variant("C_enabled_max", "thinking enabled with max effort", "enabled", "max"),
    Variant("D_disabled", "thinking disabled", "disabled", None),
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default=os.getenv("NETCONFEVAL_MODEL", "deepseek-v4-flash"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))
    parser.add_argument("--repo-root", default=os.getenv("REPO_ROOT", "/workspace"))
    return parser.parse_args()


def build_messages(repo_root: Path) -> list[dict[str, str]]:
    """构建与上游 Step 2 shortest_path/basic/without_feedback 一致的消息。"""
    import sys

    upstream_pkg = repo_root / "research" / "netconfeval"
    sys.path.append(str(upstream_pkg))
    from netconfeval.prompts.step_2_basic import (  # noqa: PLC0415
        ASK_FOR_CODE_PROMPT,
        INPUT_OUTPUT_PROMPT,
        INSTRUCTION_PROMPT,
        SETUP_PROMPT,
    )

    code_path = upstream_pkg / "assets" / "step_2_code_base" / "computing_path_empty.py"
    prompt = code_path.read_text(encoding="utf-8")

    return [
        {"role": "system", "content": SETUP_PROMPT},
        {"role": "user", "content": INPUT_OUTPUT_PROMPT},
        {"role": "user", "content": INSTRUCTION_PROMPT},
        {"role": "user", "content": prompt},
        {"role": "system", "content": ASK_FOR_CODE_PROMPT},
    ]


def stream_completion(client: OpenAI, model: str, messages: list[dict[str, str]], variant: Variant) -> tuple[str, str, dict[str, Any]]:
    """流式调用 DeepSeek，返回 thinking、final content 和 usage。"""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "response_format": {"type": "json_object"},
        "stream_options": {"include_usage": True},
    }
    extra_body: dict[str, Any] = {}
    if variant.thinking_type is not None:
        extra_body["thinking"] = {"type": variant.thinking_type}
    if extra_body:
        kwargs["extra_body"] = extra_body
    if variant.reasoning_effort is not None:
        kwargs["reasoning_effort"] = variant.reasoning_effort

    reasoning_parts: list[str] = []
    content_parts: list[str] = []
    usage: dict[str, Any] = {}

    response = client.chat.completions.create(**kwargs)
    for chunk in response:
        if getattr(chunk, "usage", None):
            usage = chunk.usage.model_dump()
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        reasoning = getattr(delta, "reasoning_content", None)
        content = getattr(delta, "content", None)
        if reasoning:
            reasoning_parts.append(reasoning)
        if content:
            content_parts.append(content)

    return "".join(reasoning_parts), "".join(content_parts), usage


def parse_result(content: str) -> tuple[str | None, str | None]:
    """从模型 JSON 输出中提取 result 代码。"""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, f"json_decode_error: {exc}"

    if not isinstance(payload, dict):
        return None, "json_payload_not_object"
    if str(payload.get("status", "")).lower() == "error":
        return None, f"model_status_error: {payload.get('reason', '')}"
    result = payload.get("result")
    if not isinstance(result, str):
        return None, "missing_string_result"
    return result, None


def verify_code(repo_root: Path, code: str) -> tuple[bool, str, str]:
    """使用上游 verifier 执行 path_tests。"""
    import sys

    upstream_pkg = repo_root / "research" / "netconfeval"
    sys.path.append(str(upstream_pkg))
    from netconfeval.verifiers.step_2_verifier_detailed import Step2VerifierDetailed  # noqa: PLC0415

    test_path = upstream_pkg / "assets" / "step_2_tests" / "path_tests"
    verifier = Step2VerifierDetailed(default_test_path=str(test_path))
    success, output = verifier.verify(
        code,
        {"extend": True, "input": "\n", "metadata": {"test_path": str(test_path)}},
    )
    output_text = output or ""
    return success, classify_failure(success, output_text), output_text


def classify_failure(success: bool, verifier_output: str) -> str:
    """把 verifier 输出归类为 Level 3 failure taxonomy。"""
    if success:
        return "pass"
    if "takes 1 positional argument but 2 were given" in verifier_output:
        return "interface_error"
    if "SyntaxError" in verifier_output or "IndentationError" in verifier_output:
        return "syntax_error"
    if "AssertionError" in verifier_output:
        return "assertion_error"
    if re.search(r"\b(TypeError|ValueError|KeyError|NameError|ImportError|ModuleNotFoundError)\b", verifier_output):
        return "runtime_error"
    return "test_error"


def write_text(path: Path, text: str) -> None:
    """写入文本文件，确保父目录存在。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    """执行 A-D variants 并写出 CSV 与文本 artifact。"""
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Set OPENAI_API_KEY or DEEPSEEK_API_KEY before running the Level 3 thinking probe.")

    repo_root = Path(args.repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=args.api_key, base_url=args.base_url)
    messages = build_messages(repo_root)
    write_text(output_dir / "prompt_messages.json", json.dumps(messages, indent=2))

    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        start = time.time()
        variant_dir = output_dir / "variants" / variant.label
        reasoning, content, usage = stream_completion(client, args.model, messages, variant)
        elapsed = time.time() - start

        write_text(variant_dir / "reasoning_content.txt", reasoning)
        write_text(variant_dir / "final_content.json", content)
        write_text(variant_dir / "usage.json", json.dumps(usage, indent=2))

        code, parse_error = parse_result(content)
        verifier_success = False
        failure_class = "format_error"
        verifier_output = parse_error or ""

        if code is not None:
            write_text(variant_dir / "generated_code.py", code)
            verifier_success, failure_class, verifier_output = verify_code(repo_root, code)
        else:
            write_text(variant_dir / "generated_code.py", "")

        write_text(variant_dir / "verifier_output.txt", verifier_output)

        rows.append(
            {
                "variant": variant.label,
                "description": variant.description,
                "thinking_type": variant.thinking_type or "default",
                "reasoning_effort": variant.reasoning_effort or "default",
                "success": int(verifier_success),
                "failure_class": failure_class,
                "parse_error": parse_error or "",
                "time": f"{elapsed:.3f}",
                "reasoning_chars": len(reasoning),
                "content_chars": len(content),
                "prompt_tokens": usage.get("prompt_tokens", ""),
                "completion_tokens": usage.get("completion_tokens", ""),
                "total_tokens": usage.get("total_tokens", ""),
            }
        )

    with (output_dir / "variant_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
