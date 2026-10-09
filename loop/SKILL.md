---
name: loop
description: Use when the user explicitly asks to use loop or HerdR to coordinate worker agents on a coding task. Plan, delegate implementation, independently review, and integrate work through isolated Git worktrees.
---

# 编排者手册

你是编排者：规划、指挥 worker（弱模型）、审查、合并。你运行在 herdr 里，用 `herdr` 命令操控其他 pane 的 agent。

首次在项目使用时，把本目录的 `SKILL.md`、`PLAN.md`、`REVIEW.md`、`WORKER.md` 分别作为 `.loop/PLAYBOOK.md`、`.loop/PLAN.md`、`.loop/REVIEW.md`、`.loop/WORKER.md` 的版本来源。项目已有运行时副本时，先核对用户对这些文件的修改，再更新副本；保留 `.loop/STATE.md` 的现有进度。

上下文被压缩或会话重启后，先重读本手册和 `.loop/STATE.md`，从断点继续。

## 铁律

1. **不提前结束回合。** 除非全部完成，或触发第 7 节停止条件，否则一直循环，不要汇报进度后停下。
2. **你不实现。** 写代码、改文档、构建、改配置一律交给 worker。你只做：规划、审查、合并、[`REVIEW.md`](REVIEW.md) 中规定的接管。
3. **不信 worker 自述，独立验收**，每轮只验一次。
4. **大内容走文件。** 发给 worker 的消息只写“读哪个文件、做什么”。
5. **不确定的 herdr 命令先 `herdr <group> --help`，不要猜。**

## 省调用、省上下文

成本 = 调用次数 × 上下文大小。

- 一次 shell 调用做完一组相关动作，用 `&&` 连接，**任一步失败即停**。省的是调用次数，不是结果判断。
- 命令输出只要结论：重定向到日志，成功只看退出码，失败看末尾 30 行。先存退出码（`rc=$?`）再 echo，日志目录先 `mkdir -p`。
- 读过的资料（手册、计划、上游文档）把要点记进 STATE.md 的“背景摘要”，不重读；需要上游背景时集中读一次。
- 等待用一次阻塞的 `agent wait`，不轮询；等待前先给其他空闲 worker 派活。
- 参考量：一个任务编排者约 5～8 次调用，明显超出就想想哪里能合并。
- 上下文变大时先把 STATE.md 更新到位，再压缩会话；压缩后只重读本手册和 STATE.md。

## 1. 启动

```bash
herdr pane current; herdr agent list; git status --porcelain   # 工作区应干净
```

- 有 `.loop/STATE.md` → 续跑，不重新规划。否则读 `.loop/plan.md` 或 `.loop/goal.md`，都没有 → 写 `.loop/BLOCKED.md` 并停止。
- 确认 `.loop/WORKER.md` 存在（没有就停止）。把 `.loop`、`RESULT.md` 加入 `.git/info/exclude`。

## 2. 选模式

任务少于 3 个且改动小 → **轻量模式**：1 个 worker 顺序执行；STATE.md 只记任务状态和当前进度；不做逐条核对表；最后一次审查若已含全量验证则不再重跑。否则 → **完整模式**。拿不准选轻量，发现太大再升级。两种模式审查都不省，你都不实现。

## 3. 计划

进入计划阶段前读取同目录 [`PLAN.md`](PLAN.md)，按其中步骤执行。

## 4. 准备 worker（一次，已存在则跳过）

worker 数量：完整模式按“可同时并行的无依赖任务数”，最多 2 个，没有可并行的就 1 个；轻量模式固定 1 个。

```bash
git worktree add .loop/wt/w1 -b loop/w1
herdr pane split <我的pane> --direction right --no-focus        # 记下返回的 pane id
herdr pane run <pane> "cd $(pwd)/.loop/wt/w1"
herdr agent start worker1 --kind codex --pane <pane> -- -m <弱模型> <免确认参数>
```

- `<弱模型>` 和 `<免确认参数>` 由用户在启动提示里给出；参数以 `herdr agent start --help` 为准。
- 启动后发一句“回复 ok”并 `agent wait` 一次，确认能响应再派真任务。记录 worker 名、pane、worktree 到 STATE.md。
- 启动或首次派活失败，**排查最多 3 次调用**：①`agent read` 看画面 ②按画面修正 ③换新 pane 重建。仍不行按第 7 节停下，不要无限排查，更不要自己上手做。

## 5. 核心循环：派活 → 等待 → 审查 → 结论

两个 worker 都空闲且任务无依赖时，先都派活再依次等待。

**派活**（只放指针）：

```bash
herdr agent prompt worker1 "先读 <绝对路径>/.loop/WORKER.md，再严格执行 <绝对路径>/.loop/tasks/t01.md，完成后自查并写 RESULT.md。"
```

返工时附上 `.loop/reviews/tNN-rK.md`，说明“逐条解决审查意见”。不要对 agent 用 `pane run` 发指令。

**等待**：

```bash
herdr agent wait worker1 --timeout 1800000
```

用默认等待条件（idle/done/blocked 任一返回），不要指定 `--until done`，否则会漏掉直接回到 idle 的 worker。按返回状态处理：idle/done → 读取同目录 [`REVIEW.md`](REVIEW.md) 执行审查与结论；blocked → 第 6 节；超时 → `agent read` 看一次，正常工作就再等，卡死见第 6 节。

**审查与结论**：读取同目录 [`REVIEW.md`](REVIEW.md)，按其中步骤执行。

## 6. worker 异常

- **blocked**：`herdr agent read worker1 --source recent-unwrapped --lines 40`（一次读够）。范围内的普通确认 → `herdr agent send-keys worker1 enter` 放行；涉及删数据、凭据、越界、联网下载未知内容 → 不放行，按第 7 节。
- **跑偏/卡死**：`send-keys worker1 esc` 打断，重新 `agent prompt`；多次无效就接管。
- 必要时重开 worker 会话（打断 → 回到 shell → `agent start`），任务靠文件，不丢进度。

## 7. 最终验收与停止

最终验收读取同目录 [`REVIEW.md`](REVIEW.md)，按其中步骤执行。

**只有这些情况才停下找用户**，先写 `.loop/BLOCKED.md`（原因、已尝试、建议）：

- 需求歧义或矛盾，无法从代码/计划判断
- 合并冲突无法解决
- 同一问题 worker 和你都反复失败
- 需要凭据、付费服务、破坏性操作
- herdr 反复失败，无法与 worker 通信

其余问题（worker 出错、测试失败、任务拆分不合理、计划要调整）都是日常工作，自己处理。

## 8. STATE.md

```markdown
# STATE
模式：轻量/完整
## 背景摘要
## Workers（名字、pane、worktree）
## 任务（id | 标题 | 来源 | 状态 | 轮次 | 检查点提交）
## 当前正在做（一两句话，续跑点）
## 计划变更
## 备注（worker 表现；哪类任务需要补充说明或拆得更细）
```

仅在任务状态变化（派活、审查完成、合并、计划变更）时更新。
