# AGENTS.md

## Purpose and scope

`netagent-benchmark` is a Java 25 CLI for controlled LLM network-engineering
experiments. It must remain a modular monolith: one runnable benchmark harness
with CML and replay adapters, not a web platform or a second workbench.

The durable output of a run is the sanitized
`experiments/runs/<run-id>-<task-slug>/run.json`. That schema belongs to this
repository. External systems may transform and import it, but must not control
the runner's runtime model.

## Package map

```text
cli/          Picocli commands and CML diagnostics only
experiment/   Run settings and ExperimentRunner orchestration
agent/        Agent loop, prompt text, and tool-call audit policy
ports/        Stable LlmClient and NetworkEnvironment interfaces
adapters/     Implementations for OpenAI-compatible LLMs, replay, and CML MCP
artifact/     run.json schema, traces, redaction, and file storage
```

Dependency direction is intentional:

```text
cli -> experiment -> agent -> ports
adapters -> ports
experiment -> artifact
```

Do not import an adapter into `agent/`. `agent/` must be testable with replay
implementations. Do not create an `evaluation/` package until the first real
task evaluator is implemented; empty framework packages are not architecture.

## CML and replay rules

- `ReplayNetworkEnvironment` is for deterministic local tests. It is a
  development and regression adapter, not evidence of real CML behaviour.
- `CmlMcpEnvironment` starts Cisco's Python-distributed `cml-mcp` process over
  stdio through the official MCP Java SDK.
- Run `doctor`, then `tools`, before a real CML run after any network or MCP
  change.
- The current tool policy records whether a call appears mutating. It does not
  enforce permission. Before adding CML write experiments, add explicit task
  cases, an enforced allowlist, isolated/resettable labs, and post-change
  verification in the same change.

## Runtime configuration

The runtime reads process environment variables only; it does not parse `.env`.
Use `.env.example` as a safe template for a shell, IDE, or container runtime.

Required for a real LLM run:

- `LLM_PROVIDER=deepseek` (default) with `DEEPSEEK_API_KEY`, or
  `LLM_PROVIDER=openai` with `OPENAI_API_KEY`.
- `LLM_MODEL` and the matching `*_BASE_URL` are optional overrides.

Required for real CML commands: `CML_URL`, `CML_USERNAME`, and
`CML_PASSWORD`. Never commit real hosts, credentials, API keys, production
logs, or unsanitized network artifacts.

## Development commands

`mise.toml` pins Java and Maven. Prefer:

```bash
mise exec -- mvn test
mise exec -- mvn package
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar loop-smoke "list all CML labs"
```

Use `llm-smoke`, `doctor`, `tools`, and `run` only when the relevant real
credentials and CML network path are available.

## Change discipline

- Keep public Markdown in English and update `README.md`, this file, and
  `TODO.md` whenever scope, commands, or architecture changes.
- Keep comments in English; write them only for non-obvious contracts or
  domain assumptions.
- Add focused tests alongside an explicit behaviour. Keep CML integration
  tests separate from default replay/unit tests.
- Add a second provider, a workbench client, RAG, multi-agent coordination,
  or a dashboard only after a named experiment requires it.
- Before handoff, run `mise exec -- mvn test`. Run `mise exec -- mvn package`
  whenever the CLI entry point or dependency set changes.
