# netagent-benchmark

`netagent-benchmark` is a Java CLI for repeatable LLM network-engineering
experiments. It connects an agent loop to Cisco Modeling Labs (CML) through
Cisco's MCP server, or to a local replay environment during development, and
writes one sanitized `run.json` per run.

The repository is an experiment harness, not a generic agent platform and not
a web service. Its long-term research path is:

1. develop repeatable cases with replayed network observations;
2. validate observation and diagnosis against real CML when campus access is
   available;
3. run isolated, resettable CML configuration and repair experiments with an
   explicit per-task tool policy.

## What works today

- Java 25 Maven CLI with a real OpenAI-compatible LLM adapter (DeepSeek by
  default).
- A CML MCP stdio adapter built on the official MCP Java SDK.
- A replay network environment and scripted LLM adapter for deterministic
  local tests and smoke runs.
- A typed agent loop with tool traces, token counts, duration, and tool audit
  records.
- Sanitized, benchmark-owned `run.json` artifacts under `experiments/runs/`.
- CML diagnostics and tool-discovery commands for use once the internal
  network is reachable.

Real CML execution is intentionally not claimed as validated until `doctor`,
`tools`, and a real `run` have completed in the target environment.

## Architecture

```text
CLI
  -> experiment/ExperimentRunner
  -> agent/AgentLoop
  -> ports/llm + ports/network
  -> adapters/llm/openai and adapters/network/{replay,cml}
  -> artifact/run.json
```

The core depends only on the two small ports:

- `LlmClient`: asks a model to respond to messages and exposed tools.
- `NetworkEnvironment`: lists and calls network tools.

`ReplayNetworkEnvironment` and `CmlMcpEnvironment` implement the same network
port. This lets local regression tests exercise the same agent loop that later
talks to real CML.

## Repository layout

```text
src/main/java/com/frankliu/netagent/
├── cli/          # Picocli entry point and CML diagnostics
├── experiment/   # Runtime settings and ExperimentRunner orchestration
├── agent/        # Agent loop, prompts, and tool-call audit policy
├── ports/        # Stable LLM and network interfaces
├── adapters/     # OpenAI-compatible, replay, and CML MCP implementations
└── artifact/     # run.json schema, redaction, trace, and file writing

src/test/java/    # Mirrors production package boundaries
experiments/runs/ # Generated, sanitized run artifacts; git-ignored
research/         # Literature and benchmark context
docs/             # Public project notes
```

## Quick start

`mise.toml` pins Java and Maven. Run Maven through mise when Maven is not on
your shell `PATH`:

```bash
mise exec -- mvn test
mise exec -- mvn package
```

The packaged CLI is:

```bash
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar --help
```

### Local, deterministic checks

```bash
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar artifact-smoke "list all CML labs"
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar loop-smoke "list all CML labs"
```

`loop-smoke` uses replay adapters only. It never contacts an LLM or CML.

### Real LLM, then real CML

Copy `.env.example` and let your shell, IDE, or container inject its values.
The application deliberately does not parse `.env` itself.

```bash
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar llm-smoke "summarize OSPF in one sentence"
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar doctor
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar tools
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar run "list all CML labs"
```

Use `doctor` and `tools` before `run` after any CML, campus-network, VPN, or
MCP configuration change.

## Run artifacts

Every run writes:

```text
experiments/runs/<run-id>-<task-slug>/run.json
```

`run.json` is the source of truth for a benchmark run. It contains its schema
version, task, agent identity, result, metrics, full tool trace, tool audit,
and artifact path. Secret-like fields are removed before it is written.

The adjacent `agent-eval-workbench` is not a runtime dependency. If later
analysis needs a database, add an explicit import transformer from this schema
rather than changing the runner to fit a workbench API.

## Scope boundaries

- Do not add a web server, database, queue, dashboard, or workbench client to
  this repository without a concrete experiment that requires it.
- Do not add a second LLM adapter unless it is an explicit model-comparison
  variable in an experiment.
- Do not treat replay results as proof of CML behaviour.
- Before enabling CML write operations, introduce task cases with explicit
  allowed tools, isolated/resettable labs, and post-change verification.

## Research context

- [Project topic summary](docs/topic.md)
- [Literature review](research/literature-review.md)
- [NetConfBench IETF Draft](https://datatracker.ietf.org/doc/draft-cui-nmrg-llm-benchmark/01/)
