"""Step 1 数据集加载和样本转换封装。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sortedcontainers import SortedSet

from research.netconfeval_repro.paths import ensure_upstream_on_path

ensure_upstream_on_path()

from netconfeval.common.utils import (  # noqa: E402
    chunk_list,
    convert_to_human_language,
    load_csv,
    pick_sample,
    transform_sample_to_expected,
)


def load_step1_dataset(policy_file: Path, policy_types: SortedSet[str]) -> list[dict[str, Any]]:
    """按原 NetConfEval 逻辑读取 Step 1 policy CSV。"""
    return load_csv(str(policy_file), policy_types)


def pick_step1_sample(
    max_n_requirements: int,
    dataset: list[dict[str, Any]],
    iteration: int,
    policy_types: SortedSet[str],
) -> list[dict[str, Any]]:
    """按原 NetConfEval 固定 seed 逻辑选择样本。"""
    return pick_sample(max_n_requirements, dataset, iteration, policy_types)


__all__ = [
    "chunk_list",
    "convert_to_human_language",
    "load_step1_dataset",
    "pick_step1_sample",
    "transform_sample_to_expected",
]
