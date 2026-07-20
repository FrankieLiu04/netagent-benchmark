# TODO

## Next experiment milestone

- [ ] Define a small `TaskCase` format: task input, allowed tools, expected
  evidence, and scoring rule.
- [ ] Add one deterministic replay case and one evaluator before adding a task
  suite or method comparison.
- [ ] Turn the existing mutating-call audit into an enforced per-task allowlist
  before any real CML write operation.

## CML validation milestone

- [ ] Run `doctor` and `tools` from the approved CML network path.
- [ ] Run a real read-only `run "list all CML labs"` and archive the sanitized
  artifact as experiment evidence.
- [ ] Only then design isolated/resettable CML execution and repair cases with
  post-change verification.

## Explicitly deferred

- Workbench import client or remote task submission.
- Additional LLM provider adapters.
- RAG, multi-agent coordination, dashboard, database, and web service work.
