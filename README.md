# Codex Skills

这个仓库收录了两个用于 Codex 的个人技能：一个负责对 vibe coding 产物进行独立、只读的多视角审查，另一个负责为长期项目维护可追溯的唯一事实源。

## Skills

| Skill | 用途 | 主要内容 |
|---|---|---|
| [`vibecoding-review`](./vibecoding-review/) | 审查当前任务中的 AI 代码改动，核对用户需求覆盖、正确性、运行风险、复杂度与测试证据 | `SKILL.md`、Codex UI 元数据 |
| [`project-to-act`](./project-to-act/) | 为跨会话、长期项目维护目标、范围、进度、版本、功能和验收证据 | `SKILL.md`、初始化/迁移/验证脚本、五份项目账本模板、Codex UI 元数据 |

## 安装

克隆仓库后，把需要的技能目录复制到 Codex 的个人 skills 目录：

```bash
git clone git@github.com:dyingforge/skills.git
mkdir -p ~/.codex/skills
cp -R skills/vibecoding-review ~/.codex/skills/
cp -R skills/project-to-act ~/.codex/skills/
```

重启 Codex 或开始一个新任务，使技能清单重新加载。

## 使用

直接在请求中点名技能：

```text
使用 $vibecoding-review 审查本次改动。
```

```text
使用 $project-to-act 为这个长期项目建立并维护项目账本。
```

`project-to-act` 不会因为技能被加载就自动写入文件。它会先检查项目中是否已有管理文档，并在初始化、采用或迁移前执行预览和验证。

## 仓库结构

```text
skills/
├── README.md
├── project-to-act/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── scripts/init_project_management.py
│   └── assets/templates/
└── vibecoding-review/
    ├── SKILL.md
    └── agents/openai.yaml
```

每个一级目录都是一个可独立安装的 Codex skill。技能说明与触发条件位于对应的 `SKILL.md`，`agents/openai.yaml` 提供技能列表中的展示信息。

## 维护与验证

修改技能后，可使用 Codex 自带的 skill validator 检查目录名、YAML frontmatter 和必填字段。`project-to-act` 的脚本也可以独立执行只读检查：

```bash
python project-to-act/scripts/init_project_management.py \
  --project-root /path/to/project \
  --check
```

除非你明确选择初始化、采用或迁移，建议先使用 `--check` 或 `--dry-run`。
