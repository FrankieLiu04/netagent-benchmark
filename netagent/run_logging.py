"""Run 日志 — 将每次 agent 执行的结果序列化为 JSON，自动脱敏。

每次 run 在 experiments/runs/ 下创建独立目录，
写入 run.json（已过滤密钥字段）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


SECRET_FIELD_NAMES = {
    "openai_api_key",
    "deepseek_api_key",
    "cml_password",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "CML_PASSWORD",
}

SECRET_FIELD_MARKERS = (
    "api_key",
    "apikey",
    "password",
    "secret",
)


@dataclass(frozen=True)
class RunLog:
    run_id: str
    run_dir: Path
    timestamp: str


def make_slug(text: str, max_length: int = 48) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (slug or "run")[:max_length].strip("-") or "run"


def start_run_log(task: str, root: Path = Path("experiments/runs")) -> RunLog:
    """创建一次 run 的日志目录，返回 RunLog 元数据。"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{uuid4().hex[:8]}"
    run_dir = root / f"{run_id}-{make_slug(task)}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return RunLog(run_id=run_id, run_dir=run_dir, timestamp=timestamp)


def is_secret_field(field_name: str) -> bool:
    """判断字段名是否像密钥字段。"""
    normalized = field_name.lower()
    secret_names = {name.lower() for name in SECRET_FIELD_NAMES}
    return (
        normalized in secret_names
        or normalized == "token"
        or normalized.endswith("_token")
        or normalized.startswith("token_")
        or any(marker in normalized for marker in SECRET_FIELD_MARKERS)
    )


def sanitize_value(value: Any) -> Any:
    """递归移除任意 JSON-like 结构中的密钥字段。"""
    if isinstance(value, dict):
        return sanitize_payload(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """递归移除 payload 中的密钥字段（API key、密码等）。"""
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if is_secret_field(str(key)):
            continue
        clean[key] = sanitize_value(value)
    return clean


def write_run_log(run_log: RunLog, payload: dict[str, object]) -> Path:
    """将脱敏后的 payload 写入 run.json，返回文件路径。"""
    path = run_log.run_dir / "run.json"
    clean = sanitize_payload(payload)
    path.write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
