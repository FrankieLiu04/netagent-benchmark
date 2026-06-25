#!/usr/bin/env bash
set -euo pipefail

repo_root="${REPO_ROOT:-/workspace}"
upstream_dir="${NETCONFEVAL_UPSTREAM_DIR:-${repo_root}/research/netconfeval}"
model="${NETCONFEVAL_MODEL:-deepseek-v4-flash}"
n_runs="${NETCONFEVAL_N_RUNS:-1}"
n_retries="${STEP2_N_RETRIES:-1}"
policy_types="${STEP2_POLICY_TYPES:-shortest_path}"
results_path="${STEP2_RESULTS_PATH:-../results_code_gen_probe}"

"${repo_root}/docker/netconfeval-paper/scripts/ensure_upstream.sh"

export OPENAI_API_KEY="${OPENAI_API_KEY:-${DEEPSEEK_API_KEY:-}}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-${DEEPSEEK_BASE_URL:-https://api.deepseek.com}}"
export OPENAI_API_BASE="${OPENAI_API_BASE:-${OPENAI_BASE_URL}}"

if [[ -z "${OPENAI_API_KEY}" ]]; then
  echo "Set OPENAI_API_KEY or DEEPSEEK_API_KEY before running Step 2 code generation." >&2
  exit 2
fi

cd "${upstream_dir}/netconfeval"
python step_2_code_gen.py \
  --model "${model}" \
  --n_runs "${n_runs}" \
  --policy_types ${policy_types} \
  --n_retries "${n_retries}" \
  --results_path "${results_path}" \
  "$@"
