# Level 3 Summary: Step 2 Code Generation

## Goal

Run the NetConfEval Step 2 code-generation task as an independent small-sample experiment, then compare DeepSeek V4 Flash under four thinking configurations:

- A: default thinking behavior.
- B: thinking enabled with `reasoning_effort=high`.
- C: thinking enabled with `reasoning_effort=max`.
- D: thinking disabled.

## Outcome

Level 3 passed.

The paper-faithful baseline completed successfully:

- Policy: `shortest_path`
- Prompt style: `basic`
- Feedback: disabled
- Result CSV rows: `1`
- `feedback_num`: `0`
- `format_error_num`: `0`
- `syntax_error_num`: `0`
- `test_error_num`: `0`
- Prompt/completion tokens: `807 + 941`
- Verifier: all 3 `path_tests` passed.

The A-D thinking probe also completed successfully:

| Variant | Thinking | Effort | Pass | Time (s) | Reasoning chars | Content chars | Prompt tokens | Completion tokens | Total tokens |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A_default | default | default | yes | 12.718 | 1699 | 2113 | 814 | 890 | 1704 |
| B_enabled_high | enabled | high | yes | 11.122 | 2610 | 1821 | 814 | 1050 | 1864 |
| C_enabled_max | enabled | max | yes | 83.994 | 37805 | 1692 | 893 | 9340 | 10233 |
| D_disabled | disabled | default | yes | 6.616 | 0 | 2275 | 814 | 603 | 1417 |

## Artifacts

- Paper-faithful run log: `03_level3_paper_faithful_step2.log`
- Paper-faithful result CSV: `paper_faithful_results/result-deepseek-v4-flash-shortest_path-basic-without_feedback-20260625-162536.csv`
- Paper-faithful generated code: `paper_faithful_results/generated_code.py`
- Thinking probe log: `03_level3_thinking_probe.log`
- Thinking probe CSV: `thinking_probe/variant_results.csv`
- Prompt messages: `thinking_probe/prompt_messages.json`
- Per-variant outputs: `thinking_probe/variants/<variant>/`

## Interpretation

All current Level 3 variants pass the basic shortest-path verifier. This means the earlier Level 0 Step 2 interface failure was not deterministic: in this Level 3 run, both the paper-faithful LangChain route and all direct A-D API probes produced two-argument-compatible functions.

The main observed tradeoff is cost/latency:

- `D_disabled` is fastest and cheapest for this simple task.
- `A_default` and `B_enabled_high` both save non-empty reasoning traces and pass.
- `C_enabled_max` saves much longer reasoning and costs far more tokens/time without improving this small verifier outcome.

