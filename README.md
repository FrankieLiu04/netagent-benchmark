# netagent-benchmark

`netagent-benchmark` is a research prototype for LLM-driven network
engineering agents and benchmarks. It connects an LLM agent to Cisco Modeling
Labs (CML) through Cisco's MCP server, then records sanitized run artifacts for
network configuration and troubleshooting experiments.

## Goals

1. Build a benchmark harness for network configuration tasks.
2. Study where LLMs fail in L2/L3 network engineering workflows.
3. Explore improvement strategies such as RAG, multi-agent coordination, and
   verification loops.
4. Generate stable run artifacts that can be imported by a separate experiment
   tracking backend.

## Current Status

The benchmark harness is now implemented in Java to align with the adjacent
Spring Boot workbench. It provides:

- Java 25 / Spring Boot 4.1 Maven build metadata.
- Environment-backed Java runtime settings for model, CML, turn budget, timeout,
  and run artifact location.
- Workbench-compatible `run.json` artifact records.
- A typed Java agent loop with LLM and MCP adapter interfaces.
- A lightweight OpenAI-compatible Java LLM adapter built on JDK `HttpClient`.
- A typed CML MCP stdio adapter built on the official MCP Java SDK.
- Secret redaction and run-log writing.
- A minimal `artifact-smoke` CLI command for writing a dry-run artifact without
  calling an LLM or CML.
- A `loop-smoke` CLI command that executes the Java loop with scripted LLM and
  MCP clients, then writes a trace-bearing `run.json`.
- An `llm-smoke` CLI command that uses a real OpenAI-compatible LLM endpoint
  with no CML tools.
- A `tools` CLI command that starts `cml-mcp` through the official MCP Java SDK
  and lists tools exposed by Cisco Modeling Labs.
- A `doctor` CLI command for checking runtime configuration and CML MCP tool
  discovery.
- A `run` CLI command that executes the Java agent with a real OpenAI-compatible
  LLM and real CML MCP tools, then writes the workbench-compatible run artifact.

The repository no longer contains a Python benchmark implementation. The Java
runtime can still start an external CML MCP server over stdio; by default that
command is `python -m cml_mcp` because Cisco's `cml-mcp` package is distributed
for Python.

## Architecture

```text
CLI task
  -> runner
  -> OpenAI-compatible LLM client
  -> ReAct-style agent loop
  -> CML MCP stdio session
  -> Cisco Modeling Labs
  -> sanitized run artifact
```

## Repository Layout

```text
netagent-benchmark/
├── src/main/java/    # Java agent harness, MCP client, CLI, and run logging
├── src/test/java/    # Java unit and integration-style tests with local mocks
├── docs/             # Public project notes and archived presentation material
├── research/         # Literature review and research context
├── experiments/      # Local run artifacts; generated runs are git-ignored
├── AGENTS.md         # Instructions for coding agents working in this repo
└── README.md
```

## Quick Start

```bash
mvn test
mvn package
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar artifact-smoke "list all CML labs"
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar loop-smoke "list all CML labs"
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar llm-smoke "summarize OSPF in one sentence"
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar run "list all CML labs"
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar doctor
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar tools
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar mcp-spec
```

Use `.env.example` as a local template for shell, IDE, Docker, or deployment
environment variables:

```bash
cp .env.example .env
```

The Java runtime reads process environment variables. It does not parse `.env`
files itself. For local shell runs, export the variables before launching the
jar, or let your IDE/container tooling load them.

Install Java dependencies through Maven:

```bash
mvn package
```

Run an agent task:

```bash
java -jar target/netagent-benchmark-0.1.0-SNAPSHOT.jar run "list all CML labs"
```

## Run Artifacts

Each run writes a sanitized artifact to:

```text
experiments/runs/<run-id>/run.json
```

The artifact includes stable top-level fields for downstream ingestion:

- `experimentId` when `NETAGENT_WORKBENCH_EXPERIMENT_ID` is set
- `agentConfigId` when `NETAGENT_WORKBENCH_AGENT_CONFIG_ID` is set
- `workbench_import`
- `benchmark`
- `agent`
- `result`
- `metrics`
- `artifacts`

Full step traces and tool audit records are also stored in the same `run.json`
for debugging and evaluation.

Set `NETAGENT_WORKBENCH_EXPERIMENT_ID` before a run when the generated
`run.json` should be posted directly to the workbench FYP run import API.

## Relationship With `agent-eval-workbench`

`netagent-benchmark` owns agent execution, CML/MCP integration, and run artifact
generation. [`agent-eval-workbench`](https://github.com/FrankieLiu04/agent-eval-workbench)
owns the Java Spring Boot backend for importing artifacts, tracking
experiments, and comparing evaluation results.

## Research Notes

- [Literature review](research/literature-review.md)
- [Project topic summary](docs/topic.md)
- [NetConfBench IETF Draft](https://datatracker.ietf.org/doc/draft-cui-nmrg-llm-benchmark/01/)
