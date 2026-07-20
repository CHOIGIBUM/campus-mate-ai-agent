# Implementation Status

## Included and tested

- Claude Code project harness under `.claude/`
- 9 detailed agent definitions
- 18 modular skills with references/templates
- Root architecture/spec/workflow/role contracts
- Secret-guard, subagent audit, and workspace validation hooks
- Python 3.11 package and CLI
- Linkareer adapter
- HTML/JSON-LD/Next.js parsing
- Optional OCR and vision passes
- Evidence-aware merge
- Profile onboarding and relevance scoring
- JSON and Notion repositories
- Slack dry-run/delivery client
- Calendar request/result bridge
- Conflict application
- Automated unit tests and harness validation

## Requires user workspace configuration

- Live Notion write verification
- Live Slack message verification
- Timely schedule creation
- Timely/Composio Google Calendar connector execution
- OCR language-pack installation
- Vision endpoint and model configuration

## Claims boundary

Additional competition sites remain extension targets until an adapter and tests are added. External integration success must be demonstrated in the user’s own account before it is described as verified.

## Canonical runtime layout

- `.claude/agents/` and `.claude/skills/` are the canonical Claude Code discovery paths.
- `timely/` documents scheduled deployment and connector calls.
- The legacy `.pi/` tree is intentionally not duplicated, preventing two divergent sources of truth.
