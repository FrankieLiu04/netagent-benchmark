# Level 2 Summary: Step 1 Function Call

## Goal

Run the Step 1 adhoc function-call path as a standalone small-sample Docker experiment, checking that the old LangChain/OpenAI-compatible function-call route can execute against DeepSeek.

## Command

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm \
  -e STEP1_FUNCTION_RESULTS_PATH="/workspace/experiments/netconfeval-paper/level1-2-20260626-001054/level2_function_call_results" \
  netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_function_call.sh
```

## Outcome

Level 2 passed.

- Upstream NetConfEval snapshot was ready at `24edc15b6f94e1b5805ae904cc05676eca2f02fe`.
- DeepSeek API returned HTTP 200.
- The script completed with exit code `0`.
- Result CSV contains 1 logical row.
- Accuracy: `1.0`.
- Model errors: `0`.
- Format errors: `0`.
- Prompt/completion tokens recorded in CSV: `134 + 105`.

## Artifacts

- Run log: `02_level2_function_call.log`
- Result CSV: `level2_function_call_results/result-deepseek-v4-flash-adhoc-reachability-function-20260625-161545.csv`
- Upstream script log: `level2_function_call_results/log-deepseek-v4-flash-adhoc-reachability-function-20260625-161545.log`

## Observed Sample

Input requirement:

```text
100.0.4.0/24 is accessible from istanbul.
```

Expected result:

```python
{
    "reachability": {
        "istanbul": ["100.0.4.0/24"]
    },
    "waypoint": {},
    "loadbalancing": {}
}
```

Observed model result:

```python
{"reachability": {"istanbul": ["100.0.4.0/24"]}}
```

The scorer accepted this as accurate; the diff only records the removed empty `waypoint` and `loadbalancing` keys.

