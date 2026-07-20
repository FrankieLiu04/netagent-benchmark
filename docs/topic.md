# YBL1: Vibe Networking — Network Engineering

- **Context**: Research prototype for LLM-driven network engineering
- **Area**: LLM agents for network engineering

## Description

This project explores the potential and capabilities of applying LLM to layer 2 (switching) and layer 3 (routing) network engineering. We adopt Cisco's Modelling Lab (CML) network emulator which has an open-source MCP server that can interface with LLM platforms.

## Research Goals

1. **LLM Benchmark for Network Configuration** — Assess existing LLMs on a small, controlled set of network configuration and troubleshooting tasks.
2. **Identify Limitations & Develop Solutions** — Compare a direct LLM baseline with a tool-assisted agent and targeted verifiers, then classify failure modes.
3. **LLM-Driven Network Troubleshooting and Repair** — Progress from replay development to real CML diagnosis, then to isolated configuration and repair experiments with post-change verification.

## Active Experimental Scope

The current implementation is intentionally narrower than the long-term topic:

1. Build deterministic replay cases and a scoring contract.
2. Validate the same agent loop against real CML with read-only observation and diagnosis tasks when the CML network path is available.
3. Add CML write operations only for explicit, resettable task cases with an enforced tool allowlist and a verification step.

RAG and multi-agent coordination are possible future methods, not baseline
requirements. They should be added only when a completed baseline experiment
establishes a concrete failure mode worth addressing.

## Additional Topics (for reference)

- **YBL2**: Vibe Networking — Network Protocol Research (autonomous design, implementation, and evaluation of transport protocols via LLM)
- **YBL3**: Vibe Networking — Network Traffic Analysis (LLM applied to log/analytics pattern discovery, anomaly detection, and performance correlation)
