# 审查

编排者收到执行者交付后，以及最终验收时读取本文件。

验证职责全在编排者：worker 不运行任何验证命令，验收、测试、构建一律由你亲自执行。

## 审查（每个任务必须做，每轮一次调用取齐证据）

```bash
cd .loop/wt/w1; LOG=<主仓库绝对路径>/.loop/logs/tNN-rK.log; mkdir -p "$(dirname "$LOG")"
echo "== RESULT =="; cat RESULT.md
echo "== STATUS =="; git status --short            # worker 已提交，应为空；有残留说明漏提交
echo "== STAT ==";   git diff --stat <基线>..HEAD  # 逐个看新增/删除文件：是否越界、有无截图/日志/产物/密钥
echo "== ACCEPT =="; <验收命令> > "$LOG" 2>&1; rc=$?; echo "exit=$rc"; if [ $rc -ne 0 ]; then tail -n 30 "$LOG"; fi
git clean -fdx                                     # 清掉验收产生的中间编译产物；RESULT.md 已被 git 排除，不受影响
```

- `<基线>`：首轮 = 派活前主分支提交；返工轮 = worker 上一轮交付的提交（哈希记在 STATE.md）。worker 交付前已自行提交，直接 `git diff <基线>..HEAD` 读 diff（首轮全量，返工只看增量）。
- 核对：①验收退出码为 0（你亲自运行，同轮不重跑第二遍）②只改了允许范围 ③任务目标逐条做到 ④无明显 bug、边界情况和风格问题 ⑤RESULT.md 的自查与遗留问题和你看到的相符，不符就在 STATE.md 备注该 worker 不可靠。
- 结论写入 `.loop/reviews/tNN-rK.md`，一两行即可，通过也写。

## 结论

- **通过**：一次调用串起来，任一步失败即停：

  ```bash
  git merge --no-ff -q -m "<tNN 标题>" loop/w1 \
  && git status --short && git show --stat --oneline HEAD \
  && git -C .loop/wt/w1 merge -q <主分支>
  ```

  合并后核对：工作区干净无冲突标记；`show --stat` 的文件与审查时一致，没多没少。**不再重跑该任务的验收**，除非出现冲突或带入了审查时没见过的改动。然后更新 STATE.md，取下一个任务。
- **需修改**：写意见到 `.loop/reviews/tNN-rK.md`；记录 worker 当前提交哈希（`git -C .loop/wt/w1 rev-parse HEAD`）到 STATE.md 作为下一轮基线；再派活。**同一任务最多 3 轮。**
- **接管**：仅当 3 轮仍不过。先确认任务描述是否够具体；接管后在 STATE.md 备注原因，用于改进后续任务说明。不得因为“自己做更快”而跳过派活。
- **合并冲突**：自己解决，解决不了见 `SKILL.md` 第 7 节的停止条件。

## 最终验收

**最终验收**（完整模式；轻量模式只对照计划简单过一遍，几行说明每条是否完成）：

1. 主分支上全量跑一次测试/构建/lint，**这是全程唯一一次全量验证**，不逐个重跑任务级验收。
2. 对照 plan 逐条核对，写入 `.loop/FINAL_CHECK.md`：每条对应任务、证据。证据**优先引用已有审查记录和全量验证结果**，不重读所有代码，仅对有疑点的条目抽查。没有证据的条目视为未完成。
3. 有缺口 → 追加任务回到 `SKILL.md` 第 5 节，最多追加 2 轮，之后仍有缺口就停下汇报。
4. 全部达成 → 清理现场，向用户简短总结：

   ```bash
   git worktree remove --force .loop/wt/w1   # 每个 worker 的 worktree 都要删
   git branch -D loop/w1                      # 对应分支一并删除
   ```

   清理前确认 worktree 里没有未合并的提交。中间编译产物已在每轮审查后由 `git clean -fdx` 清理，这里再确认无残留。
