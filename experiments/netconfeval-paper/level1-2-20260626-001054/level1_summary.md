# Level 1 Summary: Step 1 Faithful Translation

## Goal

Run the Step 1 formal-spec translation path as a standalone small-sample Docker experiment, using the paper-compatible container and DeepSeek OpenAI-compatible endpoint.

## Command

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_translation.sh \
  --max-chunks-per-batch 1
```

## Outcome

Level 1 passed.

- Upstream NetConfEval snapshot was ready at `24edc15b6f94e1b5805ae904cc05676eca2f02fe`.
- The script completed with exit code `0`.
- Result CSV contains 17 logical rows.
- Mean requirement accuracy: `0.8824`.
- Strict exact match: `3/17 = 17.65%`.
- Errored rows: `2`.
- Prompt/completion tokens recorded in CSV: `15405 + 27213`.

## Artifacts

- Run log: `01_level1_translation.log`
- Result CSV copy: `level1_translation_results/result-deepseek-v4-flash-step1-faithful-20260625-161524.csv`
- Original generated path: `research/netconfeval/results_spec_translation_faithful/result-deepseek-v4-flash-step1-faithful-20260625-161524.csv`

## Non-Perfect Rows

- Row 4: policy types `loadbalancing reachability waypoint`, batch size `33`, accuracy `0`, model error.
- Row 17: policy type `reachability`, batch size `100`, accuracy `0`, model error.

These failures are model-output or parser-facing experiment results, not Docker or API connectivity failures.

