# 开发记录：从设计到第一次自动修复

| 项 | 值 |
|---|---|
| 时间 | 2026-11-23 ~ 2026-11-24 |
| 仓库 | https://github.com/u7465990/java-repair-agent |
| 阶段 | v0.1 设计 → v0.2 骨架 → v0.3 首次真模型修复 |
| 结果 | Lang-1 由 qwen-plus 在 2 次尝试内修复，独立验证通过 |

本文记录三件事：**改了什么、为什么改、怎么排出来的**。最后一节是名词表，方便回看。

---

## 0. 摘要

- 起点是一份"有界工具调用"方案：3 轮 × 8 次工具调用、自研 JSON 协议、StubLLM。
- 中途推翻，改成 **LangGraph 自由 ReAct Agent + 确定性验证壳**。
- 真正的难点不在 Agent 代码，而在 **D4J 环境**：632 MB 仓库包、JDK 8/11 冲突、缺失的 Perl 与 Ant 组件。
- 用 **CI 当调试器**，8 轮迭代把 D4J 跑通；再用轨迹（trajectory）定位 Agent 失败原因。
- 最终：qwen-plus 第 1 次补丁失败，第 2 次用 BigInteger 改法通过验证，仅改生产代码。

---

## 1. 时间线

| 时间 | 事件 | 结果 |
|---|---|---|
| 11-23 下午 | 第一版设计（有界 harness） | 被判定结构怪异，推翻 |
| 11-23 晚 | 新设计：LangGraph + MCP + Skills | 文档定稿 |
| 11-23 晚 | 仓库初始化、CI、沙箱抽象 | 24 个文件，CI 14 秒绿 |
| 11-23 深夜 | D4J 镜像 8 轮排查 | d4j-smoke 成功，baseline 3 个失败 |
| 11-24 上午 | Agent 本体 + 工具 + 验证器 | 15 个测试绿 |
| 11-24 中午 | qwen-flash 尝试 | 失败：0 补丁 |
| 11-24 中午 | 看轨迹，发现 rg 缺失 / cwd 错误 | 修复并重跑 |
| 11-24 12:54 | qwen-plus 第 2 次尝试 | **修复成功** |

---

## 2. 为什么推翻第一版

第一版的核心是"有界"：

- 最多 3 轮修复，每轮最多 8 次工具调用；
- 自己定义 JSON 协议（`{"action":"tool",...}`）；
- 用 StubLLM 回放测试。

问题：

1. **策略被写死。** "读几个文件、要不要搜、什么时候停"是工程常量，不是模型判断，Agent 退化成一个在格子里选动作的组件。
2. **没有生态。** 自研协议接不了原生 tool calling，更接不了 MCP；技能、持久化、可观测全部要从零写。
3. **目标错位。** 它是为 Defects4J 定制的评测脚手架，不是一个能放进仓库干活的 Agent。

新方案把职责拆成三层：

| 层 | 负责 | 不负责 |
|---|---|---|
| 模型 | 读什么、搜什么、改什么、何时停 | 不能直接碰文件系统 |
| 基础设施 | 预算、权限、沙箱、超时、回滚 | 不决定探索顺序 |
| 验证 | 独立重跑构建与测试 | 不信模型自述 |

一句话：**策略归模型，边界归基础设施，验证归确定性代码。**

名词：harness、ReAct、tool calling、baseline。

---

## 3. 选型：为什么是 Python + LangGraph

- **LangGraph**：需要持久化、中断审批、崩溃恢复、时间旅行；这些自己写容易做错。图只编排生命周期，Agent 内部仍是自由循环。
- **LangChain 工具层**：```tool` + 原生 function calling，后面接 MCP 时工具同构。
- **Python 而不是 TypeScript**：框架首发在 Python；评测与数据分析在 Python；Java 工具链走子进程/LSP/MCP，不需要 JVM 内嵌。
- **Docker 沙箱**：Agent 会执行任意命令，必须隔离；镜像同时装 JDK 8/11、Ant、Maven、Perl、D4J。
- **uv**：Python 依赖与锁文件，CI 用 `uv sync --frozen` 保证一致。

---

## 4. 最难的其实是环境

### 4.1 先探测，不猜

在 Windows 上检查：

- WSL 已安装，但只有 Docker Desktop 自带的 `docker-desktop`，**没有 Ubuntu**；
- Docker CLI 存在，但 daemon 没启动；
- `uv`、`git` 有，`java` 没有（不影响，Java 在镜像里）。

网络测速（这决定了后面所有方案）：

| 目标 | 实测 | 结论 |
|---|---|---|
| PyPI | ~150 KB/s | 能装，但要等 |
| GitHub raw | 连接失败 | 不能直接下文件 |
| Docker Hub | 连接失败 | 必须用镜像站 |
| defects4j.org 仓库包 | 8.5 KB/s，632 MB | 约 20 小时，不可行 |

### 4.2 关键决策：不做"完整 D4J 镜像"

D4J 官方的 `init.sh` 会：

1. 下载 632 MB 的项目仓库压缩包；
2. 下载 Major、EvoSuite、Randoop；
3. 准备 Gradle 发行版。

在 8.5 KB/s 的网络下，这条路直接堵死。于是改成：

- 对 D4J 框架做 **sparse + blobless clone**（只取 `framework/bin`、`core`、`util`、`lib`、`projects/Lang`、`projects/lib`，约 10 MB）；
- 只保留 **commons-lang 一个仓库**，并用 `git fetch --depth 1` 只取两个提交（约 2 MB）；
- 用目录占位满足 D4J 启动时的校验（Major 的 ant、testgen 目录、gradle 目录、`project_repos/README`）。

名词：sparse checkout、blobless clone、shallow fetch、bind mount。

### 4.3 8 轮 CI 排查

CI 在这里不是"交付门禁"，而是**唯一能跑通 Linux + Docker 的调试器**。

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| 1 | `Java 11 is required!` | 把 JDK 8 放到了 PATH 最前 | PATH 保留 JDK 11，另设 `JAVA_HOME` 给 Ant |
| 2 | Docker build 退出码 2 | 写 README 时 `project_repos` 目录还不存在 | 先 `mkdir -p` |
| 3 | `Can't locate String/Interpolate.pm` | 缺 D4J 的 Perl 依赖 | 装 `libdbi-perl`、`libjson-parse-perl` 等 |
| 4 | `unable to read tree (d1a45e9)` | D4J 先检出 **fixed** 再反向打补丁，仓库里只有 buggy | 同时 fetch fixed 与 buggy 两个 SHA |
| 5 | `Unable to locate package ant-junit` | 新版 Ubuntu 没有这个包名 | 改用 `ant-optional` |
| 6 | `Cannot run tests!` + `Total time: 0 seconds` | Ant 缺 junit 任务，测试根本没跑 | 装 `ant-optional`（提供 junit task） |
| 7 | `baseline failing: 0` 但命令成功 | 我们把"测试没跑起来"误判成"没有失败" | 增加守卫：退出码非 0 且无失败 → 抛错 |
| 8 | 成功 | — | compile ok / trigger 1 / failing 3 |

其中第 6、7 条是最危险的：**测试没跑，但 CI 是绿的**。如果只看"success"，会以为评测通过。修法不是改解析，而是让"跑不起来"显式失败。

### 4.4 排查方法

- **先看日志最后 20 行**，错误通常在那里；开头只是 apt 安装噪声。
- **区分"测试失败"与"测试没跑"**：前者有 `Failing tests:`，后者是 `Cannot run tests!`。
- **读源码而不是猜**：D4J 的行为来自 `Project.pm`、`Constants.pm`、`d4j-checkout`，直接看就能知道它要 fixed 提交、要 Major 的 ant、要 README。
- **最小复现**：单独跑 `defects4j checkout/compile/test`，再套 CLI。

---

## 5. Agent 本体的实现

### 5.1 结构

```text
CLI run
  └─ run_repair
       ├─ run_baseline        checkout + compile + test + export trigger
       ├─ build_react_agent   LangGraph: agent ⇄ tools
       ├─ verify              compile + test + 对比 baseline
       └─ reset / retry       失败回滚，带报告重来
```

### 5.2 工具

9 个：`read_file` `write_file` `edit_file` `list_files` `search_code` `run_tests` `bash` `git_diff` `finish`。

设计要点：

- **路径锁定**：`posixpath.normpath` 后必须仍在 `/workspace/repo` 下；
- **错误即字符串**：工具失败返回 `ERROR: ...`，不抛异常炸掉整轮；
- **统一 cwd**：所有 shell 命令在仓库根执行（这条是后来踩坑补的）；
- **finish 不代表成功**：它只是让循环停下，是否修好由 verify 决定。

### 5.3 验证

`verify` 独立重跑 `defects4j compile` 和 `defects4j test`，判定：

1. 编译通过；
2. 触发测试通过（`failing ∩ trigger = ∅`）；
3. 没有新增失败（`failing ⊆ baseline_failing`）。

为什么不用"全绿"：Lang-1 的 baseline 里有 2 个 locale 相关的 `DateUtilsTest` 失败，与本 bug 无关。要求全绿会把可修的 bug 判成不可修。

名词：trigger test、F2P、P2P、baseline failing set。

---

## 6. 第一次真模型尝试：qwen-flash 为什么失败

现象：

```text
not fixed after 2 attempt(s)
compile_ok=True
failing=3
trigger_failing=[...TestLang747]
patch.diff  0 字节
```

**没有补丁**说明模型从头到尾没改过文件。

排查方式：不换模型，先看轨迹。

1. CI 上传 `trajectory-*.jsonl`（每条消息一行）；
2. 下载 artifact，按 `role` 和 `tool_calls` 展开；
3. 发现两个问题：
   - 所有 `search_code` / `list_files` 返回 `bash: rg: command not found`（镜像没装 ripgrep）；
   - `bash` 的工作目录是 `/workspace`，模型 `ls` 看到的是 `repo/` 子目录，一直在绕路。

修法：

- Dockerfile 加 `ripgrep`；
- 所有工具统一 `cwd=/workspace/repo`；
- 顺手把 baseline 测试输出（含栈）放进 prompt 尾部。

教训：**先看轨迹，再怀疑模型。** 工具坏了，换再贵的模型也没用。

---

## 7. qwen-plus 成功

qwen-plus 第 1 次尝试：在 hex 分支里加 `try/catch` 回退，验证失败。
第 2 次尝试：用 `BigInteger.bitLength()` 判断范围，通过。

```text
fixed in 2 attempt(s)
compile_ok=True
failing=2
new_failures=[]
trigger_failing=[]
```

补丁只改了 `NumberUtils.java`，没有动测试与构建文件。耗时 11 分 38 秒。

模型对比：

| 模型 | 结果 | 说明 |
|---|---|---|
| qwen-flash | 未修复 | 预算花在探索，未定位 |
| qwen-plus | 修复 | 2 次尝试 |
| qwen-max | 未试 | 备选 |
| qwen3-coder-plus | 404 | 端点不提供 |

---

## 8. 提交地图

| commit | 内容 |
|---|---|
| `49334f4` | 仓库初始化：沙箱、D4J 适配、CLI、测试 |
| `d0bb82e` | 瘦身 D4J 镜像 + smoke workflow |
| `20f5592` | 修 init 校验（JDK 11 在 PATH） |
| `030ed0f` | 先建 `project_repos` 再写 README |
| `3c59359` | 补 Perl 依赖 |
| `a1ab064` | 同时取 fixed/buggy 提交 + patch 工具 |
| `62b7fe2` | 尝试 `ant-junit`（失败） |
| `0e338df` | 改用 `ant-optional` |
| `e415acb` | 测试跑不起来时显式报错 |
| `e6a59bd` | LangGraph ReAct + 工具 + 验证器 |
| `08495b6` | OpenAI 兼容端点支持 |
| `4145ee1` | `agent-run` workflow |
| `d75f443` | 轨迹落盘 + prompt 加失败输出 |
| `1686bff` | 装 ripgrep |
| `a98bd0d` | 工具统一在仓库根执行 |
| `5267e47` | README 记录首次修复 |

---

## 9. 当前架构

```text
Windows / CLI
   │
   ├─ LangGraph ReAct Agent（qwen-plus via DashScope）
   │      └─ 9 个工具 ── docker exec ──┐
   │                                   ▼
   │                          d4j-runner 容器
   │                          JDK 8/11 · Ant · D4J · Lang
   │
   └─ verify（独立重跑 compile/test，不信模型自述）
```

---

## 10. 下一步

1. **Token 与成本**：在每次 model call 记录 `usage_metadata`，报告里显示 token 与估算费用。
2. **5 个 bug 的评测**：Lang 1–5，得到第一份 fix rate。
3. **Skills**：`SKILL.md` 渐进披露，加入 `java-repair` 技能。
4. **持久化图**：checkpointer + interrupt，让长任务可恢复。
5. **MCP**：接 GitHub/Jira，把 Java 工具暴露成 MCP server。

---

## 11. 名词表

| 名词 | 含义 |
|---|---|
| Defects4J（D4J） | Java 缺陷数据集 + 命令行工具，提供 buggy/fixed 版本与触发测试 |
| buggy / fixed revision | 同一个 bug 的"带病"与"已修"提交 |
| F2P（fail-to-pass） | 修复前失败、修复后应通过的测试，即 trigger test |
| P2P（pass-to-pass） | 修复前后都应通过的测试，用于防回归 |
| baseline | 在 buggy 版本上跑出来的失败集合与日志 |
| trigger test | D4J 标注的、能触发该 bug 的测试 |
| checkout | 把某个 bug 的代码取到工作目录 |
| 反向补丁 | D4J 先检出 fixed，再应用补丁得到 buggy 的过程 |
| 镜像（image） | 装好环境的只读模板 |
| 容器（container） | 用镜像启动的临时实例 |
| 挂载（bind mount） | 把宿主机目录映射进容器，两边是同一份文件 |
| 命名卷（named volume） | Docker 管理的持久化存储，常用于缓存 |
| 沙箱（sandbox） | 限制 Agent 执行命令的隔离环境 |
| uv | Python 的依赖与版本管理工具，类比 npm |
| 锁文件（uv.lock） | 固定每个依赖的确切版本 |
| ReAct | 模型交替进行"推理"和"工具调用"的循环 |
| tool calling / function calling | 模型输出结构化工具调用，而不是自然语言 |
| LangGraph | 用图编排 Agent 生命周期、持久化与中断的框架 |
| StateGraph | LangGraph 的状态图，节点读写共享状态 |
| checkpointer | 把图状态持久化，支持恢复与时间旅行 |
| trajectory | 一次 Agent 运行的消息与工具调用记录 |
| harness | 包在模型外面的确定性脚手架（预算、回滚、验证） |
| verify | 独立重跑构建与测试的验证节点 |
| SKILL.md | 技能文件：frontmatter + 流程知识，按需加载 |
| MCP | Model Context Protocol，跨语言/跨进程的工具与资源协议 |
| HITL | Human-in-the-loop，危险操作前中断等待确认 |
| CI | 持续集成，这里同时充当远程调试环境 |
| artifact | CI 产出的文件（轨迹、补丁、日志） |

---

## 12. 可复用的经验

1. **先测网络，再定方案。** 632 MB 的下载计划不该在 8.5 KB/s 的网络下开始。
2. **CI 可以当调试器**，尤其当本地缺 Linux/GPU/网络时。
3. **"绿了"不等于"对了"**：测试没跑起来也会 exit 0，要显式区分。
4. **读上游源码**比搜索报错更快：D4J 的 fixed-then-patch、Major ant、README 校验都写在代码里。
5. **Agent 失败先看轨迹**：工具报错、工作目录、prompt 缺信息，比模型能力更常见。
6. **验证必须独立**：模型说完成不算，重跑才算；比较 baseline，而不是要求全绿。