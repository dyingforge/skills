from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parents[1]
HOOK = PLUGIN_ROOT / "hooks" / "project_state_hook.py"


class HookProtocolTests(unittest.TestCase):
    def run_hook(self, event: dict, env: dict) -> dict:
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(event),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=True,
        )
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout) if result.stdout else {}

    def test_non_git_directory_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            event = {
                "hook_event_name": "SessionStart",
                "cwd": str(root),
                "session_id": "session",
                "source": "startup",
            }
            env = dict(os.environ, PLUGIN_ROOT=str(PLUGIN_ROOT), PLUGIN_DATA=str(data), PYTHONPYCACHEPREFIX=str(root / "pycache"))
            result = subprocess.run(
                ["python3", str(HOOK)],
                input=json.dumps(event),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=True,
            )
            self.assertEqual(result.stdout, "")

    def test_inactive_git_worktree_is_silent_and_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
            data = Path(temp) / "data"
            env = dict(os.environ, PLUGIN_ROOT=str(PLUGIN_ROOT), PLUGIN_DATA=str(data), PYTHONPYCACHEPREFIX=str(Path(temp) / "pycache"))
            result = subprocess.run(
                ["python3", str(HOOK)],
                input=json.dumps({
                    "hook_event_name": "UserPromptSubmit", "cwd": str(root),
                    "session_id": "session", "turn_id": "turn", "prompt": "normal work",
                }),
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=True,
            )
            self.assertEqual(result.stdout, "")
            self.assertFalse(data.exists())
            self.assertFalse((root / ".project-state").exists())

    def test_invalid_hook_json_returns_warning_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, PLUGIN_ROOT=str(PLUGIN_ROOT), PLUGIN_DATA=str(Path(temp) / "data"), PYTHONPYCACHEPREFIX=str(Path(temp) / "pycache"))
            result = subprocess.run(
                ["python3", str(HOOK)],
                input="[]",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=True,
            )
            output = json.loads(result.stdout)
            self.assertIn("warning", output["systemMessage"].lower())
            self.assertEqual(result.stderr, "")

    def test_enable_handshake_through_hook_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test User"], check=True)
            (root / "app.txt").write_text("hello\n")
            subprocess.run(["git", "-C", str(root), "add", "app.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)
            env = dict(
                os.environ,
                PLUGIN_ROOT=str(PLUGIN_ROOT),
                PLUGIN_DATA=str(Path(temp) / "data"),
                PYTHONPYCACHEPREFIX=str(Path(temp) / "pycache"),
            )

            def event(name: str, session: str, turn: str, **extra) -> dict:
                return {"hook_event_name": name, "cwd": str(root), "session_id": session, "turn_id": turn, **extra}

            submitted = self.run_hook(event("UserPromptSubmit", "s1", "t1", prompt="$project-state enable"), env)
            instructions = submitted["hookSpecificOutput"]["additionalContext"]
            nonce = re.search(r"Nonce: ([A-Za-z0-9_-]+)", instructions).group(1)
            request_path = Path(re.search(r"Write exactly one JSON request to: (.+)", instructions).group(1))
            request_path.write_text(json.dumps({"schema_version": 1, "type": "enable", "nonce": nonce}))
            stopped = self.run_hook(event("Stop", "s1", "t1"), env)
            self.assertIn("pending", stopped["systemMessage"].lower())

            submitted = self.run_hook(event("UserPromptSubmit", "s1", "t2", prompt="$project-state confirm-enable"), env)
            instructions = submitted["hookSpecificOutput"]["additionalContext"]
            nonce = re.search(r"Nonce: ([A-Za-z0-9_-]+)", instructions).group(1)
            preview_hash = re.search(r"preview_hash=([a-f0-9]{64})", instructions).group(1)
            request_path = Path(re.search(r"Write exactly one JSON request to: (.+)", instructions).group(1))
            request_path.write_text(json.dumps({
                "schema_version": 1, "type": "confirm-enable", "nonce": nonce, "preview_hash": preview_hash,
            }))
            stopped = self.run_hook(event("Stop", "s1", "t2"), env)
            self.assertIn("fresh", stopped["systemMessage"].lower())
            started = self.run_hook(event("SessionStart", "s2", "start", source="startup"), env)
            self.assertIn("PROJECT STATE RECOVERY CAPSULE", started["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
