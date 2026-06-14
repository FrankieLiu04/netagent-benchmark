"""NetConfEval 复现实验的路径和上游导入处理。"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = REPO_ROOT / "research"
UPSTREAM_ROOT = RESEARCH_ROOT / "netconfeval"
UPSTREAM_PACKAGE_ROOT = UPSTREAM_ROOT / "netconfeval"
DEFAULT_STEP1_POLICY_FILE = UPSTREAM_ROOT / "assets" / "step_1_policies.csv"
DEFAULT_RESULTS_ROOT = UPSTREAM_ROOT


def ensure_upstream_on_path() -> None:
    """把原 NetConfEval 仓库加入 import path。"""
    upstream = str(UPSTREAM_ROOT)
    if upstream not in sys.path:
        sys.path.insert(0, upstream)
