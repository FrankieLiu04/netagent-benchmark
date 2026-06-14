# NetConfEval Reproduction Framework

本目录是本项目维护的 NetConfEval 复现实验框架。它和
`research/netconfeval/` 的关系是：

- `research/netconfeval/`：上游论文仓库快照，作为 reference path，默认不提交到本仓库。
- `research/netconfeval_repro/`：本项目自己的可维护复现代码，尽量复用上游采样、prompt、评分和验证逻辑，但避免让 LangChain 成为实验主流程的单点故障。

## 目录边界

```text
research/netconfeval_repro/
├── adapters/     # LLM provider 适配层
├── datasets/     # 数据读取、采样和样本转换
├── runners/      # 可执行实验流程
├── scorers/      # 输出解析和评分
├── verifiers/    # Step 2/Step 3 验证器边界，后续逐步迁入
└── paths.py      # 上游仓库路径和 import path 管理
```

当前已迁入的是 Step 1 faithful translation runner。旧入口仍保留：

```bash
uv run --extra research python research/netconfeval_step1_faithful.py --help
```

新的模块入口也可以直接运行：

```bash
uv run --extra research python -m research.netconfeval_repro.runners.step1_translation --help
```

如果安装为 editable package，还可以使用脚本入口：

```bash
uv run --extra research netconfeval-step1 --help
```

## 依赖分层

基础 Step 1 复现只需要：

```bash
uv run --extra research python -m research.netconfeval_repro.runners.step1_translation
```

LangChain 兼容路径单独安装：

```bash
uv run --extra research --extra netconfeval-langchain python ...
```

Kathara/Docker/向量库仿真路径单独安装：

```bash
uv run --extra research --extra netconfeval-sim python ...
```

注意：上游脚本曾用较旧的 `langchain-openai==0.1.25` 跑通过 probe，但该版本和
本项目主依赖 `openai>=2.0.0` 不能长期放在同一个 locked extra 中。需要最大程度贴近
上游旧脚本时，可以继续使用临时 `uv --with ...` 命令；长期维护路径应优先使用本目录的
adapter 抽象。

## 后续迁移计划

Step 2 应优先迁移 verifier 边界：

- 复用上游 prompt 和测试资产。
- 将代码生成的 LLM 调用放在 `adapters/` 后面。
- 将 pytest verifier 独立为 `verifiers/step2.py`，不要和 LangChain chain 绑定。

Step 3 应优先拆出仿真后端：

- Docker/Kathara/FRR 调用独立为 backend。
- RIFT parser 和 config scorer 独立成纯 Python scorer。
- RAG/embedding 作为可选模式，不进入基础 runner 的依赖链。
