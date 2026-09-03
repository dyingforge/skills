# Project State for Codex

Project State is a local-first Codex plugin that keeps a compact, validated description of a Git worktree outside the conversation. When you discard an old task and start a new one, the new Codex task receives the latest committed project and current-work state without loading chat history or the event log.

It does not modify Codex compaction and does not restore an old conversation. It gives a fresh task a small, current source of project facts.

## What it stores

- `.project-state/project-state.json`: durable project facts; intended to be tracked in Git.
- `.project-state/current-work.json`: current task and exact next action; ignored by default.
- `.project-state/events.jsonl`: cold audit history; ignored and not loaded during normal startup.
- Plugin-private data: signed activation receipts, immutable generations, commit pointer, health records, and turn checkpoints.

The generated `.project-state/.gitignore` tracks only `.gitignore` and `project-state.json` by default. State rejects credential-like strings, unknown fields, oversized content, raw command output, and instruction-shaped extra fields.

## Install for local testing

The plugin source is this directory. Register it in a local Codex marketplace, install `project-state` from that marketplace, and start a new Codex task so its Skill and Hooks are discovered. A typical personal marketplace keeps the plugin at `~/plugins/project-state`, references it from `~/.agents/plugins/marketplace.json`, and installs it with:

```sh
codex plugin add project-state@personal
```

Before enabling a repository, inspect the plugin's exact Hook definitions with `/hooks` and approve them only if they match `hooks/hooks.json`.

## Enable one worktree

In the target Git worktree:

1. Send the exact prompt `$project-state enable`.
2. Review the returned goal/next-action preview and preview hash.
3. Send `$project-state confirm-enable`.
4. Discard that conversation and start a normal new Codex task in the same worktree.

There is no custom “clear” command. Starting a fresh task is the intended recovery boundary. Once active, the SessionStart Hook reads only the current committed generation and injects a bounded recovery capsule. The history log is read only for an explicit audit or repair.

Other controls are `$project-state status`, `$project-state validate`, `$project-state repair`, and `$project-state disable`.

## Integrity model

Each active turn receives a nonce-bound request path. Before the turn ends, the Agent submits either a complete `patch` or a verified `no-change` request. The Stop Hook validates the nonce, revision, schema, safety rules, worktree binding, and fingerprint.

Material changes are written as immutable signed generations. A single signed pointer publishes the generation, after which event and visible projections are rolled forward idempotently. Projection replacement uses an atomic exchange where the platform/filesystem provides one; otherwise the visible file is left untouched and marked for manual reconciliation. Human edits and concurrent changes are quarantined rather than overwritten.

Activation is worktree-local and follows `inactive → pending → confirmed → health-verified → active`. A confirming task cannot provide its own fresh-session health receipt.

## Current support and limits

- Codex only; one advancing Agent per Git worktree.
- Git worktrees are the parallelism boundary.
- Python 3.9+ and Git are required by the Hook runtime.
- Atomic projection exchange is implemented for Darwin `renamex_np` and Linux `renameat2`. Unsupported filesystems/platforms safely degrade to manual reconciliation for existing projections.
- Hook trust and administrator policy cannot be proven from inside a Hook; status reports that limitation and records only observed runtime receipts.
- Mechanical checkpoints can detect stale or missing state, but the active model can still omit a semantic fact. Provenance, visible snapshots, repair, and practical use are the correction loop.

## Verify the source

```sh
PYTHONPYCACHEPREFIX=/tmp/project-state-pycache python3 -m unittest discover -s tests -v
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
python3 /path/to/skill-creator/scripts/quick_validate.py skills/project-state
```
