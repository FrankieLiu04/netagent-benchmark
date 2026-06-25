#!/usr/bin/env bash
set -euo pipefail

repo_root="${REPO_ROOT:-/workspace}"
upstream_dir="${NETCONFEVAL_UPSTREAM_DIR:-${repo_root}/research/netconfeval}"
upstream_url="${NETCONFEVAL_UPSTREAM_URL:-https://github.com/RedHatResearch/conext24-NetConfEval.git}"
upstream_commit="${NETCONFEVAL_UPSTREAM_COMMIT:-24edc15b6f94e1b5805ae904cc05676eca2f02fe}"

mkdir -p "$(dirname "${upstream_dir}")"

if [[ ! -d "${upstream_dir}/.git" ]]; then
  echo "[netconfeval-paper] cloning upstream NetConfEval into ${upstream_dir}" >&2
  git clone "${upstream_url}" "${upstream_dir}"
fi

cd "${upstream_dir}"
current_commit="$(git rev-parse HEAD)"
if [[ "${current_commit}" != "${upstream_commit}" ]]; then
  echo "[netconfeval-paper] checking out upstream commit ${upstream_commit}" >&2
  git fetch --all --tags
  git checkout "${upstream_commit}"
fi

python "${repo_root}/docker/netconfeval-paper/scripts/patch_deepseek_model.py" \
  "${upstream_dir}/netconfeval/common/model_configs.py"

echo "[netconfeval-paper] upstream ready at $(git rev-parse HEAD)" >&2
