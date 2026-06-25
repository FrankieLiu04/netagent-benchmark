# NetConfEval Docker Level 0 Reproduction Summary

## Goal

Confirm that the paper-compatible Docker environment can build, start, locate the pinned upstream NetConfEval snapshot, receive non-secret environment configuration, call the DeepSeek OpenAI-compatible API, and execute the existing smoke script.

## Outcome

Level 0 passed.

- Docker image build completed successfully.
- `run_smoke.sh` completed with exit code `0`.
- Upstream NetConfEval snapshot was ready at `24edc15b6f94e1b5805ae904cc05676eca2f02fe`.
- Containerized model calls reached `https://api.deepseek.com/chat/completions` and returned HTTP 200.
- Step 1 faithful translation generated a CSV result with 17 rows.
- Step 1 function-call generated a CSV/log result.
- Step 2 code-generation reached the verifier and produced a real verifier failure, which is a later-stage quality/compatibility item rather than a Level 0 environment blocker.

## Primary Artifacts

- Build log: `00_build.log`
- Smoke log: `00_smoke.log`
- Environment summary: `env_summary.md`
- Reproduction commands: `commands.sh`

## Generated Upstream Result Files

- `research/netconfeval/results_spec_translation_faithful/result-deepseek-v4-flash-step1-faithful-20260625-160027.csv`
- `research/netconfeval/results_function_call_probe/result-deepseek-v4-flash-adhoc-reachability-function-20260625-160028.csv`
- `research/netconfeval/results_function_call_probe/log-deepseek-v4-flash-adhoc-reachability-function-20260625-160028.log`
- `research/netconfeval/results_code_gen_probe/result-deepseek-v4-flash-shortest_path-basic-without_feedback-20260625-160128.csv`
- `research/netconfeval/results_code_gen_probe/log-deepseek-v4-flash-shortest_path-basic-without_feedback-20260625-160128.log`

## Notes For Level 1+

- Step 1 translation summary from smoke: 17 rows, mean requirement accuracy `0.9412`, strict exact match `4/17 = 23.53%`, errored rows `1`.
- Step 2 generated `compute_routing_paths(topo)` while the verifier called `compute_routing_paths(topology_test, None)`, causing `TypeError: compute_routing_paths() takes 1 positional argument but 2 were given`.
- The upstream `model_configs.py` was patched by `docker/netconfeval-paper/scripts/patch_deepseek_model.py` to recognize `deepseek-v4-flash`.

