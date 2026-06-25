# NetConfEval Paper-Compatible Docker

这个 Docker 环境只服务 NetConfEval Step 1/Step 2 论文复现，不作为主项目
`fyp_agent` 的运行环境。它把旧 LangChain/OpenAI SDK 依赖隔离在容器里，避免和
主项目 `openai>=2` 的 CML/MCP agent 环境互相影响。

## 合规运行边界

如果公司内网环境下使用 Docker Desktop 需要单独采购正版授权，不要在公司开发机上用
Docker Desktop 跑这个环境。

推荐路径：

- 在个人/学校机器上运行 Docker Desktop，前提是符合对应授权和网络政策。
- 在 Linux VM、实验服务器或云主机上使用 Docker Engine / Docker Compose plugin。
- 在公司环境内使用已经获批的容器运行平台或远程 Linux 开发机。

本文档里的 `docker compose` 命令不要求 Docker Desktop 本身；在 Linux 上安装 Docker
Engine 和 compose plugin 后同样可运行。

## 构建

```bash
docker compose -f docker/netconfeval-paper/compose.yaml build
```

第一次运行时，如果本地没有 `research/netconfeval/`，脚本会 clone 上游仓库并 checkout
固定 commit：

```text
24edc15b6f94e1b5805ae904cc05676eca2f02fe
```

如果本地已有 `research/netconfeval/`，脚本会直接复用该快照。

## 环境变量

容器默认读取仓库根目录 `.env`。至少需要设置其中之一：

```bash
OPENAI_API_KEY=...
# 或
DEEPSEEK_API_KEY=...
```

DeepSeek/OpenAI-compatible endpoint 可以通过这些变量覆盖：

```bash
OPENAI_BASE_URL=...
DEEPSEEK_BASE_URL=...
NETCONFEVAL_MODEL=deepseek-v4-flash
```

## Smoke 验收

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_smoke.sh
```

`run_smoke.sh` 会依次运行：

- Step 1 faithful translation，默认每个 batch 只取 1 个 chunk。
- Step 1 ad-hoc function-call probe。
- Step 2 code-generation probe。

## 单独运行 Step 1 Translation

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_translation.sh
```

跑论文口径的 `n_runs=5`：

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm \
  -e NETCONFEVAL_N_RUNS=5 \
  netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_translation.sh
```

## 单独运行 Step 1 Function Call

默认 probe 等价于之前跑通过的最小命令：

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_function_call.sh
```

扩展 policy/batch：

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm \
  -e STEP1_FUNCTION_POLICY_TYPES="reachability waypoint" \
  -e STEP1_FUNCTION_BATCH_SIZE=5 \
  netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step1_function_call.sh
```

## 单独运行 Step 2 Code Generation

默认 probe 使用 `shortest_path`：

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step2_code_gen.sh
```

扩展 policy/retry：

```bash
docker compose -f docker/netconfeval-paper/compose.yaml run --rm \
  -e STEP2_POLICY_TYPES="shortest_path" \
  -e STEP2_N_RETRIES=3 \
  netconfeval-paper \
  bash docker/netconfeval-paper/scripts/run_step2_code_gen.sh
```

## 当前边界

- 这个环境暂时不包含 Step 3 Kathara/FRR 仿真依赖。
- Step 1 faithful translation 使用本项目维护的 adapter runner。
- Step 1 function-call 和 Step 2 仍调用上游脚本，因此脚本会对上游
  `model_configs.py` 做一个最小 DeepSeek model-name 兼容 patch。
