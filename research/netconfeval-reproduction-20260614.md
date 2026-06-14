# NetConfEval 复现实验记录（2026-06-14）

## 目标

尽量完整复现 NetConfEval 中与本 FYP 相关的实验流程，并使用
DeepSeek V4 Flash 作为 OpenAI-compatible 模型进行验证。

本次环境不依赖 CUHK IE 内网；所有 CML 相关验证未纳入本复现实验。

## 上游仓库状态

- 上游仓库目录：`research/netconfeval/`
- 上游来源：`https://github.com/RedHatResearch/conext24-NetConfEval.git`
- 本地上游 commit：`24edc15b6f94e1b5805ae904cc05676eca2f02fe`
- 本地修改：`netconfeval/common/model_configs.py` 增加了 `deepseek-v4-flash`
  模型配置，用于 OpenAI-compatible API。

## 本仓库新增/使用的复现框架

- `research/netconfeval_repro/`
- `research/netconfeval_step1_faithful.py`

Step 1 faithful runner 已从单文件脚本迁入
`research/netconfeval_repro/`。旧的
`research/netconfeval_step1_faithful.py` 保留为兼容入口。

该框架绕过原仓库 LangChain 运行时，但复用 NetConfEval 的 Step 1
采样、自然语言转换、expected spec 和 per-requirement 评分逻辑。
相比早期 `research/netconfeval_runner.py`，这个脚本更接近论文的
Step 1 评估方式：

- 保留原始 batch/chunk 机制。
- 保留 `compare_result()` 的逐 requirement accuracy。
- 额外记录 `strict_exact_match` 和 `DeepDiff`，用于区分格式差异和语义错误。
- 将模型调用收敛到 `adapters/`，目前实现 `OpenAICompatibleAdapter`，
  后续 LangChain、OpenRouter、本地模型都可以作为 adapter 加入。

新的模块入口：

```bash
uv run --extra research python -m research.netconfeval_repro.runners.step1_translation --help
```

兼容旧入口：

```bash
uv run --extra research python research/netconfeval_step1_faithful.py --help
```

## 已完成：Step 1 Formal Specification Translation

运行命令：

```bash
uv run python research/netconfeval_step1_faithful.py \
  --n-runs 1 \
  --results-dir research/netconfeval/results_spec_translation_faithful
```

结果文件：

```text
research/netconfeval/results_spec_translation_faithful/result-deepseek-v4-flash-step1-faithful-20260614-223035.csv
```

汇总结果：

| Policy Types | Rows | Mean Requirement Accuracy | Strict Exact Match | Errors |
|---|---:|---:|---:|---:|
| reachability | 188 | 1.0000 | 0 / 188 | 0 |
| reachability + waypoint | 93 | 0.9839 | 0 / 93 | 1 |
| reachability + waypoint + loadbalancing | 48 | 1.0000 | 48 / 48 | 0 |
| **Overall** | **329** | **0.9954** | **48 / 329** | **1** |

关键观察：

- 早期 smoke runner 得到的 25% strict accuracy 低估了模型能力。
- 在 NetConfEval 原始 per-requirement 评分下，DeepSeek V4 Flash 在完整
  `n_runs=1` Step 1 translation 中达到 99.54% mean accuracy。
- strict exact-match 仍很低，原因主要是模型会保留额外空 section，例如
  reachability-only 时仍输出空的 `waypoint` / `loadbalancing`。
- 唯一完整失败行是 `reachability waypoint` 的 `batch_size=50`，模型输出
  JSON 截断，报 `JSONDecodeError: Unterminated string`。
- 另有一行 `batch_size=1` 的 waypoint key 格式错误：
  `("budapest","100.0.29.0/24")` 与期望 `(budapest,100.0.29.0/24)` 不一致，
  该行 per-requirement accuracy 为 0.5。

## 已探测：Step 1 Ad-hoc Function Call

运行命令：

```bash
cd research/netconfeval/netconfeval
set -a && source ../../../.env && set +a
OPENAI_API_KEY="$DEEPSEEK_API_KEY" \
OPENAI_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}" \
OPENAI_API_BASE="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}" \
uv run --project ../../.. --extra research --with 'langchain-openai==0.1.25' \
  --with 'requests-toolbelt>=1.0.0' \
  --with 'tiktoken>=0.7.0' \
  python step_1_function_call.py \
  --model deepseek-v4-flash \
  --n_runs 1 \
  --policy_file ../assets/step_1_policies.csv \
  --policy_types reachability \
  --batch_size 1 \
  --adhoc \
  --results_path ../results_function_call_probe
```

结果文件：

```text
research/netconfeval/results_function_call_probe/result-deepseek-v4-flash-adhoc-reachability-function-20260614-223429.csv
```

最小 probe 结果：

- `accuracy=1.0`
- `success=1`
- `fail=0`
- `wrong=0`

这只验证了 ad-hoc function-call 路线可以运行，不代表完整 function-call
benchmark 已完成。

## 已探测：Step 2 Code Generation

运行命令：

```bash
cd research/netconfeval/netconfeval
set -a && source ../../../.env && set +a
OPENAI_API_KEY="$DEEPSEEK_API_KEY" \
OPENAI_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}" \
OPENAI_API_BASE="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}" \
uv run --project ../../.. --extra research --with 'langchain-openai==0.1.25' \
  --with 'requests-toolbelt>=1.0.0' \
  --with 'tiktoken>=0.7.0' \
  python step_2_code_gen.py \
  --model deepseek-v4-flash \
  --n_runs 1 \
  --policy_types shortest_path \
  --n_retries 1 \
  --results_path ../results_code_gen_probe
```

结果文件：

```text
research/netconfeval/results_code_gen_probe/result-deepseek-v4-flash-shortest_path-basic-without_feedback-20260614-223412.csv
```

最小 probe 结果：

- 模型成功生成 Python 代码。
- verifier 成功运行 pytest。
- 首次生成失败，原因是函数签名为 `compute_routing_paths(topology)`，
  但测试调用需要 `compute_routing_paths(topology, None)`。
- CSV 中 `feedback_num=1`，说明 verifier/feedback loop 被触发。

这说明 Step 2 已经越过环境 blocker，可以继续扩展到原论文的四种 policy
和 with/without feedback 组合。

## 未完成：Step 3 Low-Level Configuration

尝试命令：

```bash
cd research/netconfeval/netconfeval
set -a && source ../../../.env && set +a
OPENAI_API_KEY="$DEEPSEEK_API_KEY" \
OPENAI_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}" \
OPENAI_API_BASE="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}" \
uv run --project ../../.. --extra research \
  --with kathara \
  --with numpy \
  --with pdfminer.six \
  --with chromadb \
  --with scikit-learn \
  --with 'langchain-openai==0.1.25' \
  --with 'requests-toolbelt>=1.0.0' \
  --with 'tiktoken>=0.7.0' \
  python step_3_low_level.py \
  --model deepseek-v4-flash \
  --n_runs 1 \
  --mode none \
  --results_path ../results_low_level_probe
```

结果：

- Python 依赖可以通过临时 `uv --with ...` 补齐。
- 真实 blocker 是 Docker daemon 未运行：
  `Kathara.exceptions.DockerDaemonConnectionError: Cannot connect to Docker Daemon`
- 因此本次没有生成 Step 3 CSV。

继续 Step 3 前需要：

1. 启动 Docker Desktop / Docker daemon。
2. 确认 Kathara 可以创建并运行 FRRouting container。
3. 再运行 `mode=none/full/idx/rag` 四个模式。
4. `mode=rag` 还需要确认 embedding API 是否可用；原论文使用 OpenAI embedding。

## 环境和依赖说明

主项目新增/整理 optional extras：

```toml
research = [
    "deepdiff>=8.0.0",
    "sortedcontainers>=2.4.0",
]

netconfeval-langchain = [
    "langchain-community>=0.2.0",
    "langchain-openai>=1.0.0",
    "requests-toolbelt>=1.0.0",
    "tiktoken>=0.7.0",
]

netconfeval-sim = [
    "chromadb>=0.5.0",
    "kathara>=3.7.0",
    "numpy>=1.26.0",
    "pdfminer.six>=20240706",
    "scikit-learn>=1.5.0",
]
```

依赖按用途分层：

- `research`：Step 1 faithful runner 的轻量依赖。
- `netconfeval-langchain`：保留 LangChain 兼容路线，用于后续对照原脚本。
- `netconfeval-sim`：Step 3 所需 Docker/Kathara/向量库/数值依赖。

原仓库旧 LangChain 依赖在当前 Python 3.13 环境下会出现兼容问题。本次早期 probe
曾通过临时覆盖 `langchain-openai==0.1.25`、`requests-toolbelt>=1.0.0`
和 `tiktoken>=0.7.0` 跑通 Step 2 和 function-call probe；但
`langchain-openai==0.1.25` 要求 `openai<2.0.0`，不能和主项目
`openai>=2.0.0` 共同锁入长期 extra。因此长期维护采用 adapter 抽象，
旧 pin 只作为临时 reference/probe 命令保留。

## 目录改造计划

当前结构：

```text
research/
├── netconfeval/                 # 上游仓库快照，默认 gitignore
├── netconfeval_repro/           # 本项目维护的复现实验框架
├── netconfeval_step1_faithful.py # 兼容入口
└── netconfeval-reproduction-20260614.md
```

`research/netconfeval_repro/` 的设计边界：

```text
adapters/   # LLM provider glue，LangChain 只是可选 adapter
datasets/   # 上游数据读取、样本选择、自然语言转换
runners/    # step1/step2/step3 实验流程
scorers/    # compare_result、strict diff、relaxed scoring
verifiers/  # pytest verifier、Kathara/FRR verifier、RIFT parser 边界
```

后续 Step 2 应优先拆出 pytest verifier 和测试资产映射；Step 3 应优先拆出
Docker/Kathara/FRR backend，并让 RAG/embedding 作为可选模式存在。

## 当前结论

本次已经完成 NetConfEval Step 1 translation 的完整一轮 faithful 复现
（`n_runs=1`，329 rows）。结果显示 DeepSeek V4 Flash 在原论文式
per-requirement accuracy 下表现很强，早期 strict exact-match smoke test
的 25% 结论不适合作为最终复现结论。

尚未完成论文建议的 `n_runs=5` 全量复现；预计调用量约为本次的 5 倍。
Step 2 和 Step 1 function-call 已完成最小 probe，Step 3 需要 Docker/Kathara
运行环境后继续。
