"""NetConfEval Step 1 faithful runner compatibility entrypoint.

该脚本保留旧命令入口；实际实现已迁移到
`research.netconfeval_repro.runners.step1_translation`。
"""

from __future__ import annotations

from research.netconfeval_repro.runners.step1_translation import main


if __name__ == "__main__":
    main()
