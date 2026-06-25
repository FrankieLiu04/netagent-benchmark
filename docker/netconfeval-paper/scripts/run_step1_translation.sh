#!/usr/bin/env bash
set -euo pipefail

repo_root="${REPO_ROOT:-/workspace}"
model="${NETCONFEVAL_MODEL:-deepseek-v4-flash}"
n_runs="${NETCONFEVAL_N_RUNS:-1}"
results_dir="${STEP1_TRANSLATION_RESULTS_DIR:-${repo_root}/research/netconfeval/results_spec_translation_faithful}"

"${repo_root}/docker/netconfeval-paper/scripts/ensure_upstream.sh"

cd "${repo_root}"
python -m research.netconfeval_repro.runners.step1_translation \
  --model "${model}" \
  --n-runs "${n_runs}" \
  --results-dir "${results_dir}" \
  "$@"
