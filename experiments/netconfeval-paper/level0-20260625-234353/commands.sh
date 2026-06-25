#!/usr/bin/env bash
set -euo pipefail

# Build the paper-compatible Docker image.
docker compose -f docker/netconfeval-paper/compose.yaml build

# Run the Level 0 smoke baseline.
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_smoke.sh

