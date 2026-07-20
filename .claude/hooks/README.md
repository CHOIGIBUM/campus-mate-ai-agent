# Claude Code Hooks

- `guard_secrets.py` blocks Write/Edit content containing common live-token patterns.
- `log_subagent.py` appends subagent completion metadata to `_workspace/logs/subagents.jsonl`.
- `validate_workspace.py` performs a non-blocking workspace sanity check at session stop.

Hooks receive JSON on stdin. They never print or store secret values.
