# Thinking Comparison

The A-D probe uses the same Step 2 `shortest_path` prompt and the same upstream `path_tests` verifier, but calls DeepSeek directly through the OpenAI-compatible streaming API so that `reasoning_content` can be saved.

## Variants

- `A_default`: no explicit `thinking` field and no explicit `reasoning_effort`.
- `B_enabled_high`: `extra_body={"thinking": {"type": "enabled"}}`, `reasoning_effort="high"`.
- `C_enabled_max`: `extra_body={"thinking": {"type": "enabled"}}`, `reasoning_effort="max"`.
- `D_disabled`: `extra_body={"thinking": {"type": "disabled"}}`.

## Results

| Variant | Result | Failure class | Reasoning saved | Notes |
| --- | --- | --- | ---: | --- |
| A_default | pass | pass | 1699 chars | Confirms default mode streams reasoning content. |
| B_enabled_high | pass | pass | 2610 chars | Slightly more reasoning than default in this run. |
| C_enabled_max | pass | pass | 37805 chars | Much larger reasoning trace and token count. |
| D_disabled | pass | pass | 0 chars | Confirms disabled mode suppresses reasoning content. |

## Files

Each variant directory contains:

- `reasoning_content.txt`
- `final_content.json`
- `generated_code.py`
- `verifier_output.txt`
- `usage.json`

Because all variants passed, `verifier_output.txt` is empty for each variant.

## Takeaway

For this shortest-path probe, thinking is not required to pass. The most useful immediate value of thinking mode is observability: it gives a trace that can be studied when future Step 2 or Step 3 cases fail. `reasoning_effort=max` is probably too expensive for routine smoke tests, but useful for occasional diagnosis.

