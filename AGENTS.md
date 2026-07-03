# AGENTS.md

## Project Shape

`netagent-benchmark` is a Java benchmark harness for LLM-driven Cisco Modeling
Labs experiments. It is aligned with the adjacent Spring Boot workbench and no
longer contains a repository-local Python implementation.

- Java runtime code lives in `src/main/java`.
- Java tests live in `src/test/java`.
- Research context lives in `research/`.
- Public project notes live in `docs/`.
- Generated run logs live under `experiments/runs/` and are git-ignored.

The Java runtime may start an external CML MCP server over stdio. The default
external command is still `python -m cml_mcp` because Cisco's `cml-mcp` package
is distributed for Python, but that process is an external dependency rather
than repository implementation code.

## Development Commands

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

## Runtime Configuration

Configuration is read from process environment variables, following common Java
deployment practice. Use `.env.example` only as a local template for shells,
IDEs, Docker, or deployment tooling that injects environment variables. The
application should not implement its own `.env` parser.

Never commit real CML hosts, usernames, passwords, API keys, production logs,
or unsanitized network artifacts.

- Java runtime settings are represented by `NetagentSettings`.
- Add new runtime knobs in `NetagentSettings` and mirror safe placeholders in
  `.env.example`.
- Treat copied legacy `.env` files as untrusted input: keep only variables that
  the current Java runtime reads, then load them through your shell, IDE, or
  deployment tooling.
- Runtime limits such as max turns, timeouts, and token caps are operational
  budgets. Raise them only when a concrete run needs the extra budget and the
  cost or failure mode is understood.

## Code Guidelines

- Use Java 25 and Spring Boot 4.1.x.
- Keep Java dependency changes in `pom.xml`.
- Keep dependency caches outside the repository in normal user/global caches
  such as Maven or IDE caches.
- Prefer current stable dependency releases. Avoid speculative major upgrades
  unless tests pass and the migration surface is small enough to review clearly.
- Write comments in English, and add them only for domain assumptions, artifact
  contracts, or non-obvious control flow.

## Long-Term Build Style

- Optimize for fast iteration and human readability: write the simplest code
  that directly serves the requested behavior.
- Avoid framework scaffolding, defensive layers, or generic abstractions before
  repeated need appears.
- Keep feature changes small and focused.
- Keep functions short; split only when the extracted helper has a clear name
  and is reused or independently testable.
- Add tests for explicit behavior. Prefer a few focused tests over broad
  matrices unless a previous bug or paper requirement makes the matrix useful.
- Avoid redundant fallback paths, retries, broad validation layers, or
  compatibility shims unless a named failure has already been observed or is
  required by an external contract.
- Keep test fixtures small. Inline tiny fixtures, and move fixtures to files
  only when they are reused or represent a real artifact shape.

## Architecture Notes

- Workbench-compatible artifact records live under
  `src/main/java/com/frankliu/netagent/artifact`.
- The Java agent core lives behind typed `LlmClient` and `CmlMcpClient`
  interfaces.
- Keep provider-specific OpenAI-compatible, MCP SDK, or future Spring AI code in
  adapters instead of baking those details into the loop.
- `CmlMcpServerSpec` is the single place for CML MCP stdio command and
  environment construction.
- Each run writes a sanitized `run.json` through `RunLogService`.
- `RunArtifact` defines stable fields imported by `agent-eval-workbench`; avoid
  breaking that schema casually.
- Workbench import IDs come from `NETAGENT_WORKBENCH_EXPERIMENT_ID` and
  `NETAGENT_WORKBENCH_AGENT_CONFIG_ID`; do not hard-code local database IDs.

## Documentation Rules

- Keep public-facing Markdown in English.
- Keep documentation compact; prefer updating `README.md`, `AGENTS.md`, or
  existing files before adding new docs.
- Archive stale presentation material instead of keeping it in the main docs
  path as current documentation.

## Verification

Run Java tests before handing off code changes:

```bash
mvn test
```
