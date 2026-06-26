# AGENTS.md — 本项目 AI Coding Agent 规范与背景知识

> 本文档面向在此仓库中工作的 AI coding agent（如 GitHub Copilot、Cursor、Claude Code）。
> 包含项目特有的编码规范、架构决策、已知坑位和运行指令。

---

## 构建与运行

### 环境

```bash
# 安装依赖（含 dev）
uv sync --extra dev

# 运行所有单元测试
uv run python -m pytest tests/ -v

# 诊断环境连通性
uv run python -m fyp_agent doctor

# 列出 Agent 可见的 CML MCP 工具
uv run python -m fyp_agent tools

# 执行一次 Agent 任务
uv run python -m fyp_agent run "list all CML labs"
```

### 配置

所有配置从 `.env` 加载（模板见 `.env.example`）。不要将真实密钥写入 `.env.example` 或提交到 git。

---

## 编码规范

- **Python 版本**: `>=3.12,<3.14`（当前 venv 为 3.13）
- **类型注解**: 所有函数必须有完整的类型注解，文件顶部 `from __future__ import annotations`
- **注释语言**: 函数/类的 docstring 和模块说明使用**中文**；行内注释中英文均可
- **包结构**: 顶层 `fyp_agent/` 而非 `src/` 布局（`src/` 在本地 editable install 有不稳定问题）
- **配置模型**: 使用 Pydantic `BaseModel` + `pydantic-settings`，字段校验用 `field_validator` / `model_validator`
- **测试**: `pytest`，测试文件放在 `tests/`，命名 `test_*.py`
- **依赖管理**: 使用 `uv`，新增依赖后务必同步 `uv.lock` 和 `pyproject.toml`

---

## 架构决策

### Agent Harness 设计

- **LLM 调用**: 直接使用 `openai` SDK（`AsyncOpenAI`），不依赖 OpenAI Agents SDK
- **Agent Loop**: 自定义 ReAct 循环（`fyp_agent/loop.py`），支持可插拔 `StepHook`
- **默认 LLM**: DeepSeek V4 Flash（通过 OpenAI-compatible API），切换 provider 只需改 `.env` 中 `LLM_PROVIDER`
- **MCP 通信**: 使用 `mcp` SDK（`ClientSession` + `stdio_client`），而非 `openai-agents` 的 `MCPServerStdio`
- **Agent 生命周期**: CLI → `runner.run_agent_task()` → `cml_mcp_session()` + `LLMClient.from_settings()` → `agent_loop()` → 写入 `experiments/runs/<run-id>/run.json`
- **日志脱敏**: `run_logging.py` 自动过滤 `API_KEY`、`PASSWORD` 等敏感字段
- **Trace 记录**: 每次 run 的 `run.json` 包含 step-level trace（工具调用、token 消耗、耗时）

### 当前工具暴露策略

Agent 默认暴露 `cml-mcp` server 动态列出的**全部工具**，项目调性是快速、合理的试错和迭代。
本地不再用只读白名单屏蔽 mutating tools。

工具暴露策略定义在 `fyp_agent/tools.py`。`ALL_CML_TOOLS = None` 表示信任 MCP server
返回的全部工具；如果后续需要临时收紧范围，可以传入具体 `frozenset[str]`。

### 依赖版本锁

- `virl2-client>=2.9.1,<2.10`：匹配 CML 2.9.x API。大版本升级（2.10+）需验证与 cml-mcp 的兼容性。
- `cml-mcp[pyats]>=0.28.0`：当前为 0.28.0，已验证与 CML 2.9.1 完全兼容（2026-06-14 测试通过）。

---

## 已知限制

- **网络要求**：CML 服务器通常仅限授权校园网、实验室网络或 VPN 访问；不要提交真实主机名、账号、IP 或密码。
- **CML 版本**：当前 CML 为 2.9.1，与 virl2-client 2.9.x 和 cml-mcp 0.28 兼容。若服务器升级到 2.10+，需同步更新依赖。
- **Agent 可操作 CML**：当前允许 Agent 调用 CML MCP 暴露的全部工具，包括创建、修改、配置、启动/停止、CLI、抓包等。
- **单轮对话**：`fyp-agent run` 每次执行是一次性任务，不保留对话历史（未来需支持 interactive session）。

---

## 安全约束

- `.env` 文件已被 `.gitignore`，**绝不能提交**真实密钥
- `run_logging.py` 中的 `SECRET_FIELD_NAMES` 是脱敏白名单，新增密钥字段需同步更新
- Agent System Prompt 鼓励在用户请求清晰时直接调用合适工具推进任务。工具边界由 CML 账号权限、MCP server 能力和 `mcp_client.py:CmlMcpSession` 的可选 allowlist 共同决定。
- 不要在任何文件（包括注释、docstring、测试）中硬编码 API key 或密码
