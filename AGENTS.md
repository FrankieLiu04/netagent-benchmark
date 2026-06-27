# AGENTS.md

## Project Shape

`netagent-benchmark` is a Python research prototype for LLM-driven network
engineering agents and CML/MCP benchmark experiments.

- Runtime code lives in `netagent/`.
- Tests live in `tests/`.
- Research context lives in `research/`.
- Public project notes live in `docs/`.
- Generated run logs live under `experiments/runs/` and are git-ignored.

## Development Commands

```bash
uv sync --extra dev
uv run python -m pytest tests/ -v
uv run python -m netagent doctor
uv run python -m netagent tools
uv run python -m netagent run "list all CML labs"
```

## Runtime Configuration

Configuration is loaded from `.env`; use `.env.example` as the template.
Never commit real CML hosts, usernames, passwords, API keys, production logs,
or unsanitized network artifacts.

- Treat copied legacy `.env` files as untrusted input: keep only variables that
  the current repo reads, document new keys in `.env.example`, and never print
  secret values in logs or handoff notes.
  将旧项目复制来的 `.env` 视为待清理输入：只保留当前仓库实际读取的变量，新变量写入 `.env.example`，不要在日志或交付说明中打印密钥值。
- Runtime limits such as max turns, timeouts, and token caps are operational
  budgets, not provider-documentation maxima. Raise them only when a concrete
  run needs the extra budget and the cost/failure mode is understood.
  最大轮数、超时和 token 上限属于运行预算，不等同于 provider 文档最大值；只有明确实验需要且理解成本和失败模式时才上调。

## Code Guidelines

- Use Python `>=3.12,<3.14`.
- Keep complete type annotations on new functions.
- Keep `from __future__ import annotations` in Python modules.
- Follow the current top-level `netagent/` package layout.
- Use Pydantic models for runtime configuration.
- Keep dependency changes in both `pyproject.toml` and `uv.lock`.
- Keep dependency caches outside the repository in the normal user/global cache
  (`uv`, pip, Maven, or IDE caches). Do not vendor downloaded packages into git
  or hide them with repo-local `.gitignore` entries unless a reproducibility
  artifact explicitly requires it.
  依赖缓存放在本机用户/全局缓存中（如 `uv`、pip、Maven 或 IDE 缓存）；不要把下载依赖放进仓库后再用本地 `.gitignore` 隐藏，除非复现实验产物明确要求。
- Prefer current stable dependency releases that satisfy the supported Python
  range. Avoid speculative major upgrades unless tests pass and the migration
  surface is small enough to review in one diff.
  优先使用符合当前 Python 范围的稳定依赖版本；避免没有测试支撑的试探性大版本升级，除非迁移面足够小且可在一个 diff 内审查。

## Long-Term Build Style

- Optimize for fast iteration and human readability: write the simplest code
  that directly serves the requested behavior, and avoid framework scaffolding,
  defensive layers, or generic abstractions before repeated need appears.
  面向快速迭代和人类可读性：只写直接服务于目标行为的最简代码，在重复需求出现前避免框架化脚手架、防御层和泛化抽象。
- Keep feature changes small: target one behavior per diff, and keep most diffs
  under 300 changed lines unless data files or generated fixtures are involved.
  保持改动小而聚焦：每个 diff 默认只解决一个行为，除数据文件或生成 fixture 外，尽量控制在 300 行变更以内。
- Keep functions short: target <= 40 logical lines per function; split only when
  the extracted helper has a clear name and is reused or independently testable.
  保持函数短小：单个函数目标不超过 40 行逻辑代码；只有当 helper 命名清晰、可复用或可独立测试时才拆分。
- Keep modules focused: if a Python module grows beyond about 400 lines, check
  whether it mixes config, I/O, agent logic, and reporting responsibilities.
  保持模块聚焦：如果 Python 模块超过约 400 行，检查它是否混合了配置、I/O、agent 逻辑和报告职责。
- Add tests only for explicit behavior: prefer 1-3 focused tests per changed
  behavior, and avoid broad regression matrices unless a previous bug or paper
  requirement makes the matrix necessary.
  只为明确行为添加测试：每个变更行为优先写 1-3 个聚焦测试，除非历史 bug 或论文要求需要矩阵，否则避免宽泛回归矩阵。
- Avoid redundant safety code: do not add fallback paths, retries, broad
  validation layers, or compatibility shims unless a named failure has already
  been observed or is required by an external contract.
  避免冗余兜底代码：不要添加 fallback、retry、宽泛校验层或兼容 shim，除非已经观察到明确失败或外部契约要求。
- Keep test fixtures small: inline tiny fixtures, and move fixtures to files only
  when they are reused by at least two tests or represent a real artifact shape.
  保持测试 fixture 小：小 fixture 直接内联；只有被至少两个测试复用或代表真实产物结构时才放入文件。
- Require justification for fallback code: every retry, broad `except`, default
  substitution, or degraded mode must name the concrete failure it handles.
  兜底代码必须说明理由：每个 retry、宽泛 `except`、默认替换或降级模式都要写明它处理的具体失败。
- Use bilingual comments sparingly: write needed Python comments as adjacent
  hashtag-style lines, `# EN:` and `# CN:`, only for domain assumptions,
  artifact contracts, or non-obvious control flow.
  谨慎使用中英对照注释：必要的 Python 注释使用相邻的 hashtag-style `# EN:` 和
  `# CN:` 两行，只解释领域假设、产物契约或非显然控制流。
- Do not use Python triple-quoted docstrings as comments. Module, class,
  function, and test explanations must use `# EN:` / `# CN:` comments instead;
  real runtime string constants may still use normal string syntax when needed.
  不使用 Python 三引号 docstring 作为注释；模块、类、函数和测试说明都改用
  `# EN:` / `# CN:` 注释；真实运行时字符串常量可按需要使用普通字符串语法。
- Keep bilingual comments concise: each `# EN:` or `# CN:` line should normally
  fit within about 100 characters and explain why the code exists, not restate
  what the next line already says.
  保持双语注释简洁：每行 `# EN:` 或 `# CN:` 通常不超过约 100 字符，只解释原因，不复述下一行代码。
- Before coding, write down the intended behavior, touched files, expected tests,
  and any threshold exception. After coding, review the diff against the same
  four items before handoff.
  写代码前写清目标行为、涉及文件、预期测试和任何阈值例外；写完后交付前用同四项复查 diff。

## Architecture Notes

- LLM calls use the OpenAI-compatible `openai` SDK directly.
- The agent loop is a local ReAct-style loop in `netagent/loop.py`.
- MCP communication uses `mcp.ClientSession` over stdio.
- `ALL_CML_TOOLS = None` means the agent accepts the tool list exposed by the
  MCP server.
- Each run writes a sanitized `run.json` through `netagent/run_logging.py`.
- `netagent/artifacts.py` defines stable fields imported by
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
