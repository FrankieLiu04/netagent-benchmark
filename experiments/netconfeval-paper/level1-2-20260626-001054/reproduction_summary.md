# NetConfEval Docker Level 1-2 Reproduction Summary

## Scope

This run completes:

- Level 1: Step 1 formal-spec translation small sample.
- Level 2: Step 1 adhoc function-call small sample.

The run builds on the Level 0 Docker baseline and reuses the already-built `fyp-netconfeval-paper:latest` image.

## Environment

- Run ID: `level1-2-20260626-001054`
- Date: `2026-06-26`
- Workspace: `/Users/frankieliu/Final_Year_Project`
- Git commit: `cc2112ecab138b695d9a7cdbd26b5d97661df9ce`
- Upstream NetConfEval commit: `24edc15b6f94e1b5805ae904cc05676eca2f02fe`
- Model: `deepseek-v4-flash`
- API endpoint observed in logs: `https://api.deepseek.com/chat/completions`

## Results

Level 1 passed with measurable model failures:

- Rows: `17`
- Mean requirement accuracy: `0.8824`
- Strict exact match: `3/17 = 17.65%`
- Errored rows: `2`

Level 2 passed:

- Rows: `1`
- Accuracy: `1.0`
- Model errors: `0`
- Format errors: `0`

## Artifacts

- `01_level1_translation.log`
- `02_level2_function_call.log`
- `level1_translation_results/result-deepseek-v4-flash-step1-faithful-20260625-161524.csv`
- `level2_function_call_results/result-deepseek-v4-flash-adhoc-reachability-function-20260625-161545.csv`
- `level2_function_call_results/log-deepseek-v4-flash-adhoc-reachability-function-20260625-161545.log`
- `level1_summary.md`
- `level2_summary.md`
- `commands.sh`

## Notes

- Level 1's two errored rows are useful research evidence for parser/model-output robustness; they do not indicate environment failure.
- Level 2's scorer accepts omission of empty `waypoint` and `loadbalancing` keys for the one-sample reachability task.
- The Level 1 command was first run without passing `STEP1_TRANSLATION_RESULTS_DIR` through `docker compose run -e`, so the CSV was generated in the upstream default results directory and then copied into this experiment directory for archival.

