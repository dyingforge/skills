---
name: loop
description: Use when the user explicitly asks to use loop or HerdR to coordinate worker agents on a coding task. Plan, delegate implementation, independently review, and integrate work through isolated Git worktrees.
---

# 编排者手册

你是编排者：规划、指挥 worker（弱模型）、审查、合并。你运行在 herdr 里，用 `herdr` 命令操控其他 pane 的 agent。

首次在项目使用时，把本技能作为 `.loop/PLAYBOOK.md` 的版本来源，把 [`loop-worker/SKILL.md`](../loop-worker/SKILL.md) 作为 `.loop/WORKER.md` 的版本来源。项目已有运行时副本时，先核对用户对这些文件的修改，再更新副本；保留 `.loop/STATE.md` 的现有进度。

上下文被压缩或会话重启后，先重读本手册和 `.loop/STATE.md`，从断点继续。

## 铁律

1. **不提前结束回合。** 除非全部完成，或触发第 7 节停止条件，否则一直循环，不要汇报进度后停下。
2. **你不实现。** 写代码、改文档、构建、改配置一律交给 worker。你只做：规划、审查、合并、第 5 节规定的接管。
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

**plan.md 是用户亲手写的权威来源，不是草稿**：

- 保留其结构、顺序、命名、技术选择、验收标准；对应章节原文放进任务文件。
- 只做四类调整：拆小过大的步骤、补验收命令、补文件路径/上下文、纠正明显错误的依赖顺序。
- 每个任务标“来源：plan 第 X 条”，plan 每一条都要有任务覆盖。
- **不改 plan.md**，调整记入 STATE.md 的“计划变更”。
- plan 有矛盾或不可行：先推进不受影响的部分并记录；整体走不下去才按第 7 节停下。
- 每次取下一个任务前，检查 plan.md 是否被用户修改，有变化就同步任务。

只有 goal.md：自己规划并拆分。

任务文件 `.loop/tasks/tNN.md`：

```markdown
# tNN 标题
来源：plan 第 X 条（或“编排者追加：原因”）
## 目标
## 具体做法（文件、参考、接口，让 worker 无需猜测）
## 允许修改
## 验收（一条能以退出码判定成败的命令）
```

**分配原则：所有实现都派给 worker。** 需要架构判断的任务，你先做出判断并写进任务文件（接口、文件划分、约束），再派。

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

用默认等待条件（idle/done/blocked 任一返回），不要指定 `--until done`，否则会漏掉直接回到 idle 的 worker。按返回状态处理：idle/done → 审查；blocked → 第 6 节；超时 → `agent read` 看一次，正常工作就再等，卡死见第 6 节。

**审查**（每个任务必须做，每轮一次调用取齐证据）：

```bash
cd .loop/wt/w1; LOG=<主仓库绝对路径>/.loop/logs/tNN-rK.log; mkdir -p "$(dirname "$LOG")"
echo "== RESULT =="; cat RESULT.md
git add -A                                         # 暂存含新增的未跟踪文件
echo "== STATUS =="; git status --short           # 逐个看新增/删除文件：是否越界、有无截图/日志/产物/密钥
echo "== STAT ==";   git diff --cached --stat <基线>
echo "== ACCEPT =="; <验收命令> > "$LOG" 2>&1; rc=$?; echo "exit=$rc"; if [ $rc -ne 0 ]; then tail -n 30 "$LOG"; fi
```

- `<基线>`：首轮 = 派活前主分支提交；返工轮 = 上一轮的检查点提交。worker 不提交，所以不能用 `HEAD` 比较，要用 `git add -A` 后的 `git diff --cached <基线>` 读 diff（首轮全量，返工只看增量）。
- 核对：①验收退出码为 0（你亲自重跑，同轮不重跑第二遍）②只改了允许范围 ③任务目标逐条做到 ④无明显 bug、边界情况和风格问题 ⑤RESULT.md 的自查与遗留问题和你看到的相符，不符就在 STATE.md 备注该 worker 不可靠。
- 结论写入 `.loop/reviews/tNN-rK.md`，一两行即可，通过也写。

**结论**：

- **通过**：一次调用串起来，任一步失败即停：

  ```bash
  git -C .loop/wt/w1 add -A && git -C .loop/wt/w1 commit -qm "<tNN 标题>" \
  && git merge --no-ff -q -m "<tNN 标题>" loop/w1 \
  && git status --short && git show --stat --oneline HEAD \
  && git -C .loop/wt/w1 merge -q <主分支>
  ```

  合并后核对：工作区干净无冲突标记；`show --stat` 的文件与审查时一致，没多没少。**不再重跑该任务的验收**，除非出现冲突或带入了审查时没见过的改动。然后更新 STATE.md，取下一个任务。
- **需修改**：写意见到 `.loop/reviews/tNN-rK.md`；**先打检查点** `git -C .loop/wt/w1 add -A && git -C .loop/wt/w1 commit -qm "checkpoint tNN rK"`，哈希记入 STATE.md 作为下一轮基线；再派活。**同一任务最多 3 轮。**
- **接管**：仅当 3 轮仍不过。先确认任务描述是否够具体；接管后在 STATE.md 备注原因，用于改进后续任务说明。不得因为“自己做更快”而跳过派活。
- **合并冲突**：自己解决，解决不了见第 7 节。

## 6. worker 异常

- **blocked**：`herdr agent read worker1 --source recent-unwrapped --lines 40`（一次读够）。范围内的普通确认 → `herdr agent send-keys worker1 enter` 放行；涉及删数据、凭据、越界、联网下载未知内容 → 不放行，按第 7 节。
- **跑偏/卡死**：`send-keys worker1 esc` 打断，重新 `agent prompt`；多次无效就接管。
- 必要时重开 worker 会话（打断 → 回到 shell → `agent start`），任务靠文件，不丢进度。

## 7. 最终验收与停止

**最终验收**（完整模式；轻量模式只对照计划简单过一遍，几行说明每条是否完成）：

1. 主分支上全量跑一次测试/构建/lint，**这是全程唯一一次全量验证**，不逐个重跑任务级验收。
2. 对照 plan 逐条核对，写入 `.loop/FINAL_CHECK.md`：每条对应任务、证据。证据**优先引用已有审查记录和全量验证结果**，不重读所有代码，仅对有疑点的条目抽查。没有证据的条目视为未完成。
3. 有缺口 → 追加任务回到第 5 节，最多追加 2 轮，之后仍有缺口就停下汇报。
4. 全部达成 → 清理 worktree，向用户简短总结。

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
