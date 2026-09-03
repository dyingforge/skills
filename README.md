# Codex Skills

这个仓库收录了三个用于 Codex 的个人能力包：代码审查 Skill、项目治理 Skill，以及带生命周期 Hooks 的 Project State 插件式 Skill。

## Skills

| Skill | 用途 | 主要内容 |
|---|---|---|
| [`vibecoding-review`](./vibecoding-review/) | 审查当前任务中的 AI 代码改动，核对用户需求覆盖、正确性、运行风险、复杂度与测试证据 | `SKILL.md`、Codex UI 元数据 |
| [`project-to-act`](./project-to-act/) | 为跨会话、长期项目维护目标、范围、进度、版本、功能和验收证据 | `SKILL.md`、初始化/迁移/验证脚本、五份项目账本模板、Codex UI 元数据 |
| [`project-state`](./project-state/) | 在新的 Codex 任务之间恢复紧凑、经过验证且与 Git worktree 绑定的项目状态 | Skill、生命周期 Hooks、JSON schemas、状态引擎、测试 |

## 安装

克隆仓库后，可以把两个独立 Skill 复制到 Codex 的个人 skills 目录：

```bash
git clone git@github.com:dyingforge/skills.git
mkdir -p ~/.codex/skills
cp -R skills/vibecoding-review ~/.codex/skills/
cp -R skills/project-to-act ~/.codex/skills/
```

重启 Codex 或开始一个新任务，使技能清单重新加载。

`project-state` 依赖生命周期 Hooks，必须按插件安装，不能只复制其中的 `SKILL.md`。完整安装和启用步骤见 [`project-state/README.md`](./project-state/README.md)。

## 使用

直接在请求中点名技能：

```text
使用 $vibecoding-review 审查本次改动。
```

```text
使用 $project-to-act 为这个长期项目建立并维护项目账本。
```

```text
$project-state enable
```

`project-to-act` 不会因为技能被加载就自动写入文件。它会先检查项目中是否已有管理文档，并在初始化、采用或迁移前执行预览和验证。

`project-state` 默认禁止隐式调用。首次启用需要检查预览并执行 `$project-state confirm-enable`，随后在同一 worktree 中开启新的 Codex 任务进行健康检查。

## 仓库结构

```text
skills/
├── README.md
├── project-state/
│   ├── .codex-plugin/plugin.json
│   ├── skills/project-state/
│   ├── hooks/
│   ├── schemas/
│   ├── scripts/
│   └── tests/
├── project-to-act/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── scripts/init_project_management.py
│   └── assets/templates/
└── vibecoding-review/
    ├── SKILL.md
    └── agents/openai.yaml
```

`vibecoding-review` 和 `project-to-act` 是可独立安装的 Skill；`project-state` 是插件根目录，其 Skill 位于 `project-state/skills/project-state/`。技能说明与触发条件位于对应的 `SKILL.md`，`agents/openai.yaml` 提供技能列表中的展示信息。

## 维护与验证

修改技能后，可使用 Codex 自带的 skill validator 检查目录名、YAML frontmatter 和必填字段。`project-to-act` 的脚本也可以独立执行只读检查：

```bash
python project-to-act/scripts/init_project_management.py \
  --project-root /path/to/project \
  --check
```

除非你明确选择初始化、采用或迁移，建议先使用 `--check` 或 `--dry-run`。

验证 `project-state` 时运行其单元测试，并分别检查插件清单与嵌套 Skill：

```bash
PYTHONPYCACHEPREFIX=/tmp/project-state-pycache \
  python3 -m unittest discover -s project-state/tests -v
python3 /path/to/plugin-creator/scripts/validate_plugin.py project-state
python3 /path/to/skill-creator/scripts/quick_validate.py \
  project-state/skills/project-state
```
