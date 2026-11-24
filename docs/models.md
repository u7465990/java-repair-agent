# Model matrix

## 现状

- 百炼控制台的免费额度页列出 **136 个模型**，每个 1M token，默认状态是"未开启"。
- 账号**欠费**时，API 直接返回：

```json
{"type": "Arrearage", "message": "Access denied, please make sure your account is in good standing."}
```

- 不在免费列表里的模型返回：

```json
{"type": "AccessDenied.Unpurchased", "message": "Access to model denied."}
```

所以顺序是：**结清欠费 → 在免费额度页开启要用的模型 → 再跑 benchmark**。只开额度不结清欠费，调用仍然会被拒绝。

## 不要 136 个一起跑

按当前的量级估算：一个 bug 约 8 分钟、20 万 token。136 个模型 × 5 个 bug ≈ 90 小时、1.3 亿 token。既跑不完，也看不出结论。

建议分层：

| 层级 | 数量 | 目的 |
|---|---|---|
| Tier 1 | 5–6 个 | 编码/工具调用能力最强的模型，先跑 Lang-1 冒烟 |
| Tier 2 | 2 个 | Tier 1 里表现最好的，跑完整 5 个 bug |
| Tier 3 | 其余 | 只在需要"模型对比"素材时抽样 |

Tier 1 候选（以免费额度页实际可开启的为准）：

- `qwen3.8-max` / `qwen3.8-max-0902`
- `qwen3-coder-flash` / `qwen3-coder-plus`（若在列表里）
- `kimi-k3`
- `deepseek-v4.1-flash`
- `glm-5.3`
- `qwen3.8-plus`

## 开发期用免费模型，最终用强模型

两套用法，别混：

| 阶段 | 模型 | 预算 | 目的 |
|---|---|---|---|
| 开发冒烟 | qwen3.8-flash / deepseek-v4.1-flash / glm-5.3-flash | 1 次尝试、12 步、15 万 token | 查工具、环境、循环是否正常 |
| 最终取数 | qwen-plus / qwen3.8-max | 2 次尝试、25 步 | 产出可写进报告的 fix rate |

冒烟不要求修好，只要求**轨迹里没有工具错误**。`dev-smoke` workflow 会在结束后跑
`scripts/trajectory_health.py`，出现 `ERROR` / `command not found` / `No such file` 就判红。

超预算保护：`JAVA_AGENT_TOKEN_BUDGET` 到顶后图会主动结束，不会像之前那样一个 bug 烧掉 100 万 token。

## 跑矩阵

本地（需要镜像 + key）：

```bash
export JAVA_AGENT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_API_KEY=...
uv run python scripts/bench_matrix.py \
  --models "openai:qwen3.8-max,openai:kimi-k3" \
  --bugs "1,3,4,5,6" \
  --attempts 2 --max-steps 25
```

CI：`bench-matrix` workflow，参数是逗号分隔的 models / bugs，产物在 `bench/summary.md`。

## 判读

- 先看 Lang-1（已知可修），修不好说明模型/工具链有问题，不必浪费后面 4 个 bug；
- 再看 tokens 和耗时，便宜的模型即使通过率低也可能更划算；
- 失败样本保留 trajectory，按"定位错误 / 语义错误 / 编译错误"分类。
