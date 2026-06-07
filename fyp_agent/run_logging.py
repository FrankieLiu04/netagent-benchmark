from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


SECRET_FIELD_NAMES = {
    "openai_api_key",
    "deepseek_api_key",
    "cml_password",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "CML_PASSWORD",
}


@dataclass(frozen=True)
class RunLog:
    run_id: str
    run_dir: Path
    timestamp: str


def make_slug(text: str, max_length: int = 48) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (slug or "run")[:max_length].strip("-") or "run"


def start_run_log(task: str, root: Path = Path("experiments/runs")) -> RunLog:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{uuid4().hex[:8]}"
    run_dir = root / f"{run_id}-{make_slug(task)}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return RunLog(run_id=run_id, run_dir=run_dir, timestamp=timestamp)


def sanitize_payload(payload: dict[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for key, value in payload.items():
        if key in SECRET_FIELD_NAMES:
            continue
        if isinstance(value, dict):
            clean[key] = sanitize_payload(value)
        else:
            clean[key] = value
    return clean


def write_run_log(run_log: RunLog, payload: dict[str, object]) -> Path:
    path = run_log.run_dir / "run.json"
    clean = sanitize_payload(payload)
    path.write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
