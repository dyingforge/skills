#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional


PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).parents[1])
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from project_state_core import (  # noqa: E402
    StateError,
    checkpoint_for_prompt,
    load_recovery_context,
    process_stop_event,
    record_mutation_hint,
    record_session_end,
    resolve_git_context,
)


def emit(value: Optional[dict]) -> None:
    if value:
        sys.stdout.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
        sys.stdout.write("\n")


def context_output(event_name: str, text: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": text,
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise StateError("hook input must be a JSON object")
        plugin_data = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
        if not plugin_data:
            raise StateError("PLUGIN_DATA is unavailable")
        cwd = event.get("cwd")
        if not cwd:
            raise StateError("hook event has no cwd")
        try:
            ctx = resolve_git_context(cwd)
        except StateError:
            # The plugin is project-scoped and intentionally does nothing outside Git.
            return 0
        event_name = event.get("hook_event_name")
        if event_name == "SessionStart":
            context = load_recovery_context(plugin_data, ctx, event)
            if context:
                emit(context_output("SessionStart", context))
        elif event_name == "UserPromptSubmit":
            _, instructions = checkpoint_for_prompt(plugin_data, ctx, event)
            if instructions:
                emit(context_output("UserPromptSubmit", instructions))
        elif event_name == "PostToolUse":
            record_mutation_hint(plugin_data, ctx, event)
        elif event_name == "Stop":
            emit(process_stop_event(plugin_data, ctx, event))
        elif event_name == "SessionEnd":
            record_session_end(plugin_data, ctx, event)
        return 0
    except (StateError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        current_event = locals().get("event")
        event_name = current_event.get("hook_event_name", "unknown") if isinstance(current_event, dict) else "unknown"
        if event_name == "Stop":
            emit({"continue": False, "stopReason": str(exc), "systemMessage": f"Project State hook failed: {exc}"})
        else:
            emit({"systemMessage": f"Project State hook warning: {exc}"})
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
