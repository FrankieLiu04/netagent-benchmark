#!/usr/bin/env bash
set -euo pipefail

RUN_ID="level3-20260626-002509"

# Paper-faithful Step 2 shortest_path/basic/without_feedback baseline.
docker compose -f docker/netconfeval-paper/compose.yaml run --rm \
  -e STEP2_RESULTS_PATH="/workspace/experiments/netconfeval-paper/${RUN_ID}/paper_faithful_results" \
  netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step2_code_gen.sh

# A-D DeepSeek thinking-mode probe using the same Step 2 prompt and verifier.
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  python docker/netconfeval-paper/scripts/level3_thinking_probe.py \
  --output-dir "/workspace/experiments/netconfeval-paper/${RUN_ID}/thinking_probe"

