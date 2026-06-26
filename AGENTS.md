# AGENTS.md

## Project Shape

`netagent-benchmark` is a Python research prototype for LLM-driven network
engineering agents and CML/MCP benchmark experiments.

- Runtime code lives in `fyp_agent/`.
- Tests live in `tests/`.
- Research context lives in `research/`.
- Public project notes live in `docs/`.
- Generated run logs live under `experiments/runs/` and are git-ignored.

## Development Commands

```bash
uv sync --extra dev
uv run python -m pytest tests/ -v
uv run python -m fyp_agent doctor
uv run python -m fyp_agent tools
uv run python -m fyp_agent run "list all CML labs"
```

## Runtime Configuration

Configuration is loaded from `.env`; use `.env.example` as the template.
Never commit real CML hosts, usernames, passwords, API keys, production logs,
or unsanitized network artifacts.

## Code Guidelines

- Use Python `>=3.12,<3.14`.
- Keep complete type annotations on new functions.
- Keep `from __future__ import annotations` in Python modules.
- Follow the current top-level `fyp_agent/` package layout.
- Use Pydantic models for runtime configuration.
- Keep dependency changes in both `pyproject.toml` and `uv.lock`.

## Architecture Notes

- LLM calls use the OpenAI-compatible `openai` SDK directly.
- The agent loop is a local ReAct-style loop in `fyp_agent/loop.py`.
- MCP communication uses `mcp.ClientSession` over stdio.
- `ALL_CML_TOOLS = None` means the agent accepts the tool list exposed by the
  MCP server.
- Each run writes a sanitized `run.json` through `fyp_agent/run_logging.py`.
- `fyp_agent/artifacts.py` defines stable fields imported by
  `agent-eval-workbench`; avoid breaking that schema casually.

## Documentation Rules

- Keep public-facing Markdown in English.
- Keep documentation compact; prefer updating `README.md`, `AGENTS.md`, or
  existing files before adding new docs.
- Archive stale presentation material instead of keeping it in the main docs
  path as current documentation.

## Verification

Run tests before handing off code changes:

```bash
uv run python -m pytest tests/ -v
```
