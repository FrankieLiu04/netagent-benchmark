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

The current implementation provides a Python agent harness with:

- `netagent doctor` for local environment and connectivity checks.
- `netagent tools` for listing CML MCP tools visible to the agent.
- `netagent run "<task>"` for executing one agent task and writing a sanitized
  `run.json` artifact.

The Python package is `netagent`, and the command-line entry point is
`netagent`.

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
├── netagent/        # Python agent harness, MCP client, CLI, run logging
├── tests/            # Unit and integration-style tests with local mocks
├── docs/             # Public project notes and archived presentation material
├── research/         # Literature review and research context
├── experiments/      # Local run artifacts; generated runs are git-ignored
├── AGENTS.md         # Instructions for coding agents working in this repo
└── README.md
```

## Quick Start

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create a local environment file:

```bash
cp .env.example .env
```

Fill in the required CML and LLM credentials in `.env`, then install
dependencies:

```bash
uv sync --extra dev
```

Run checks:

```bash
uv run python -m pytest tests/ -v
uv run python -m netagent doctor
uv run python -m netagent tools
```

Run an agent task:

```bash
uv run python -m netagent run "list all CML labs"
```

## Run Artifacts

Each run writes a sanitized artifact to:

```text
experiments/runs/<run-id>/run.json
```

The artifact includes stable top-level fields for downstream ingestion:

- `workbench_import`
- `benchmark`
- `agent`
- `result`
- `metrics`
- `artifacts`

Full step traces and tool audit records are also stored in the same `run.json`
for debugging and evaluation.

## Relationship With `agent-eval-workbench`

`netagent-benchmark` owns agent execution, CML/MCP integration, and run artifact
generation. [`agent-eval-workbench`](https://github.com/FrankieLiu04/agent-eval-workbench)
owns the Java Spring Boot backend for importing artifacts, tracking
experiments, and comparing evaluation results.

## Research Notes

- [Literature review](research/literature-review.md)
- [Project topic summary](docs/topic.md)
- [NetConfBench IETF Draft](https://datatracker.ietf.org/doc/draft-cui-nmrg-llm-benchmark/01/)
