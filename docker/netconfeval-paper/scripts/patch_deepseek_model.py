"""Best-effort patch for using DeepSeek through upstream NetConfEval scripts.

The maintained Step 1 runner does not need this patch. The original LangChain
scripts look up model names through netconfeval/common/model_configs.py, so the
Docker wrapper appends a tiny compatibility block when the upstream snapshot has
not already been patched locally.
"""

from __future__ import annotations

import sys
from pathlib import Path


PATCH_MARKER = "# FYP_DEEPSEEK_MODEL_PATCH"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_deepseek_model.py PATH_TO_MODEL_CONFIGS")

    path = Path(sys.argv[1])
    if not path.exists():
        raise SystemExit(f"model config file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if PATCH_MARKER in text or "deepseek-v4-flash" in text:
        return

    patch = f'''

{PATCH_MARKER}
try:
    _fyp_base_config = {{}}
    for _fyp_name in ("gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"):
        if _fyp_name in MODEL_CONFIGS:
            _fyp_base_config = dict(MODEL_CONFIGS[_fyp_name])
            break
    _fyp_base_config.update({{
        "model": "deepseek-v4-flash",
        "model_name": "deepseek-v4-flash",
        "name": "deepseek-v4-flash",
    }})
    MODEL_CONFIGS["deepseek-v4-flash"] = _fyp_base_config
except Exception:
    pass
'''
    path.write_text(text.rstrip() + patch + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
