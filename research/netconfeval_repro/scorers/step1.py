"""Step 1 输出解析与评分。"""

from __future__ import annotations

import json
from typing import Any

from deepdiff import DeepDiff

from research.netconfeval_repro.paths import ensure_upstream_on_path

ensure_upstream_on_path()

from netconfeval.common.utils import compare_result  # noqa: E402


def parse_model_json(content: str) -> dict[str, Any]:
    """解析模型返回的 JSON，并抽取 `result` 字段。"""
    text = content.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]

    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("model response is not a JSON object")
    if str(payload.get("status", "")).lower() == "error":
        raise ValueError(f"model returned error status: {payload.get('reason') or payload.get('result')}")
    result = payload.get("result", payload)
    if isinstance(result, str):
        result = json.loads(result)
    if not isinstance(result, dict):
        raise ValueError("result field is not a JSON object")
    return result


def normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    """复用原脚本的 key 空格清理逻辑。"""
    normalized = dict(result)
    if "waypoint" in result and isinstance(result["waypoint"], dict):
        normalized["waypoint"] = {str(k).replace(" ", ""): v for k, v in result["waypoint"].items()}
    if "loadbalancing" in result and isinstance(result["loadbalancing"], dict):
        normalized["loadbalancing"] = {
            str(k).replace(" ", ""): v for k, v in result["loadbalancing"].items()
        }
    return normalized


def score_step1_result(expected: dict[str, Any], result: dict[str, Any], row: dict[str, Any]) -> None:
    """填充 Step 1 原论文式 accuracy 和 strict diff 字段。"""
    normalized = normalize_result(result)
    compare_result(expected, normalized, row)
    diff = DeepDiff(expected, normalized, ignore_order=True)
    row["diff"] = str(diff)
    row["strict_exact_match"] = 0 if diff else 1
