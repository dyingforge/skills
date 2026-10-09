import argparse
import hashlib
import os
import sys
from pathlib import Path

FILES = ["SKILL.md", "PLAN.md", "REVIEW.md"]

MARKERS = {
    "SKILL.md": [
        "## 铁律",
        "## 省调用、省上下文",
        "## 1. 启动",
        "## 4. 准备 worker",
        "## 6. worker 异常",
        "## 8. STATE.md",
        "只有这些情况才停下找用户",
    ],
    "PLAN.md": [
        "plan.md 是用户亲手写的权威来源",
        ".loop/tasks/tNN.md",
        "分配原则：所有实现都派给 worker",
    ],
    "REVIEW.md": [
        "每轮一次调用取齐证据",
        "结论写入 `.loop/reviews/tNN-rK.md`",
        "同一任务最多 3 轮",
        "对照 plan 逐条核对",
    ],
}


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def check_repo(repo_root):
    skill_dir = Path(repo_root) / "loop"
    errors = []
    texts = {}
    for name in FILES:
        path = skill_dir / name
        if not path.is_file():
            errors.append(f"缺少文件：{path}")
            continue
        content = read_text(path)
        if not content.strip():
            errors.append(f"文件内容为空：{path}")
            continue
        texts[name] = content
    if errors:
        return errors
    if "PLAN.md" not in texts["SKILL.md"]:
        errors.append("SKILL.md 没有引用 PLAN.md")
    if "REVIEW.md" not in texts["SKILL.md"]:
        errors.append("SKILL.md 没有引用 REVIEW.md")
    for name, markers in MARKERS.items():
        for marker in markers:
            holders = [candidate for candidate in FILES if marker in texts[candidate]]
            if holders != [name]:
                errors.append(f"标记 {marker!r} 应当只出现在 {name}，实际出现在 {holders}")
    return errors


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_installed(repo_root, installed_dir):
    skill_dir = Path(repo_root) / "loop"
    installed_dir = Path(installed_dir)
    errors = []
    for name in FILES:
        source = skill_dir / name
        target = installed_dir / name
        if not target.is_file():
            errors.append(f"安装副本缺少文件：{target}")
            continue
        if digest(source) != digest(target):
            errors.append(f"安装副本与仓库不一致：{target}")
    return errors


def main():
    default_repo = Path(__file__).resolve().parent.parent
    codex_home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(default_repo))
    parser.add_argument("--installed", default=str(Path(codex_home) / "skills" / "loop"))
    args = parser.parse_args()
    errors = check_repo(args.repo_root) + check_installed(args.repo_root, args.installed)
    for error in errors:
        print(error)
    if errors:
        return 1
    print("检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
