# netagent-benchmark

---

## Project Background

`netagent-benchmark` is an FYP research prototype for LLM-driven network
engineering agents and benchmarks. The project was framed around three
preparation stages:

1. Learn to program LLMs through API access and build an agent harness.
2. Build layer-3 Cisco routing knowledge at roughly CCNP Route level.
3. Connect Cisco Modeling Labs (CML) with an LLM agent through Cisco's MCP
   server, then evaluate network configuration and troubleshooting tasks.

## 项目概览

本项目探索如何将 **LLM 应用于二层/三层网络工程**，主要实验平台为
Cisco Modeling Labs（CML），通过 MCP server 让 LLM agent 与 CML 交互。

### 三个核心目标

1. 建立面向网络配置任务的 **LLM benchmark**。
2. 找出 LLM 在网络配置中的局限，并探索改进方案（RAG、多 agent、verification loop）。
3. 探索 **LLM-driven 自动网络故障排查**。

---

## 当前阶段

**Phase 1（已完成）**：Agent harness + CML MCP 集成。

- `fyp-agent doctor` — 诊断连通性
- `fyp-agent run "<task>"` — 执行 Agent 任务
- `fyp-agent tools` — 列出可用 MCP 工具

**下一步**：Phase 2（Cisco 路由知识学习）+ Phase 3（CML + LLM 深度集成）。

---

## 仓库结构

```text
netagent-benchmark/
├── fyp_agent/          # Agent harness、MCP 集成、CLI（Python 包）
├── tests/              # 单元测试
├── docs/               # Public-safe project notes and slides
├── research/           # 文献综述
├── experiments/        # Agent 运行日志（自动生成 run.json）
└── notes/              # 会议记录、学习笔记
```

---

## 快速开始

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 配置环境
cp .env.example .env   # 然后编辑 .env，填入 CML 凭据和 LLM API key

# 安装依赖
uv sync --extra dev

# 诊断
uv run python -m fyp_agent doctor

# 运行
uv run python -m fyp_agent run "列出 CML 上所有 lab"
```

每次 run 会在 `experiments/runs/<run-id>/run.json` 写入脱敏日志，并包含
`workbench_import`、`benchmark`、`agent`、`result`、`metrics`、`artifacts`
字段，供旁边的 Java workbench 导入。

> 📘 **AI coding agent 协作规范、编码约定、架构决策、已知坑位**：见 [`AGENTS.md`](AGENTS.md)。

## 参考方向

- [NetConfBench IETF Draft](https://datatracker.ietf.org/doc/draft-cui-nmrg-llm-benchmark/01/)

---

## 文献综述

详见 `research/literature-review.md`。该文件整理了 LLM 应用于网络配置和故障排查的
相关研究、benchmark、局限性和本 FYP 可以切入的研究 gap。
