#!/usr/bin/env bash
set -euo pipefail

RUN_ID="level1-2-20260626-001054"

# Level 1: Step 1 faithful translation, small-sample smoke scale.
# Note: this command writes to the upstream default results directory unless
# STEP1_TRANSLATION_RESULTS_DIR is passed through docker compose with -e.
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_translation.sh \
  --max-chunks-per-batch 1

# Level 2: Step 1 adhoc function-call, one reachability sample.
docker compose -f docker/netconfeval-paper/compose.yaml run --rm \
  -e STEP1_FUNCTION_RESULTS_PATH="/workspace/experiments/netconfeval-paper/${RUN_ID}/level2_function_call_results" \
  netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_function_call.sh

