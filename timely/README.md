# Timely Mapping

This folder maps the canonical `.claude` harness to the original Timely deployment model.

- Six functional roles are defined as Claude Code subagents.
- Three scheduled operations are described in `automations.yaml`.
- Timely runs the Python CLI and connector calls.
- `.claude/` remains the reusable source of orchestration truth; do not maintain a second divergent `.pi/` copy.

See `docs/timely-deployment.md` for setup and result contracts.
