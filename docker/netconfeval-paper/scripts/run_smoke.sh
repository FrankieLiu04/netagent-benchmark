#!/usr/bin/env bash
set -euo pipefail

repo_root="${REPO_ROOT:-/workspace}"

"${repo_root}/docker/netconfeval-paper/scripts/run_step1_translation.sh" \
  --max-chunks-per-batch "${STEP1_SMOKE_MAX_CHUNKS_PER_BATCH:-1}"

"${repo_root}/docker/netconfeval-paper/scripts/run_step1_function_call.sh"
"${repo_root}/docker/netconfeval-paper/scripts/run_step2_code_gen.sh"
