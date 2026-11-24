# Evaluation: Lang 1–6

| 项 | 值 |
|---|---|
| 日期 | 2026-11-24 |
| 模型 | qwen-plus（DashScope OpenAI 兼容端点） |
| 配置 | temperature 0.1，max_tokens 4096，最多 2 次尝试，每次 25 次工具调用 |
| 判据 | 编译通过 + 触发测试通过 + 无新增失败（对比 baseline） |

## 结果

| Bug | 结果 | 尝试 | 输入 token | 输出 token | 耗时 | CI run |
|---|---|---|---|---|---|---|
| Lang-1 | 修复 | 2 | n/a（统计功能上线前） | n/a | 11.6 min | 45328306512 |
| Lang-3 | 未修复 | 2 | 230,355 | 16,924 | 8.8 min | 45369381492 |
| Lang-4 | 修复 | 1 | 126,940 | 7,640 | 3.8 min | 45371098356 |
| Lang-5 | 修复 | 2 | 238,530 | 14,522 | 8.2 min | 45371104469 |
| Lang-6 | 未修复 | 2 | 188,847 | 10,693 | 6.0 min | 45371115126 |

- **Fix rate：3/5 = 60%**（按可运行 bug 计）。
- 成功样本平均尝试次数：1.67。
- 已知 4 次运行合计输入 784,672 tokens、输出 49,779 tokens（不含 Lang-1）。
- Lang-2 未纳入：D4J 2.x 已将其标记为 deprecated，checkout 直接拒绝。

## 观察

1. **上下文压缩有效**：Lang-3 在压缩前单次运行消耗 1,025,014 输入 token；压缩到最近 12 条消息 + 工具输出截断后降到 230,355，约 4.4 倍。
2. **验证器抓到了真实错误**：Lang-3 第一次尝试引入重复变量声明，编译失败，verify 如实判负，没有把"编译失败"误判成"没有失败"。
3. **失败集中在语义细节**：Lang-3 是数值精度（testStringCreateNumberEnsureNoPrecisionLoss），Lang-6 是代理对转义（testEscapeSurrogatePairs），都不是探索能力问题。
4. **Lang-4 的补丁改了额外文件**：除了 LookupTranslator.java，还改了 DateUtils.java——顺手清掉了 baseline 里两个 locale 失败。判据允许（无新增失败），但说明"最小改动"还需要 diff 审计约束。
5. **工具质量决定下限**：qwen-flash 失败的直接原因是当时镜像缺 ripgrep、工作目录错误；修好后 qwen-plus 才有发挥空间。

## 复现

```bash
gh workflow run agent-run.yml \
  -f bug=4 \
  -f model=openai:qwen-plus \
  -f attempts=2 \
  -f max_steps=25
```

产物：`work/Lang-<N>/patch.diff`、`report.md`、`trajectory-*.jsonl`。

## 下一步

- 加 diff 审计（禁止改测试/构建文件、限制改动规模）；
- 跑更多 bug（10–20 个）并报告置信区间；
- 为失败样本建立失败分类（定位错误 / 语义错误 / 编译错误）。
