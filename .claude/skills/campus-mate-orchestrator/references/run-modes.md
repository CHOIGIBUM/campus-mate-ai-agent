# Orchestrator run modes

| Mode | Purpose | Default side effect |
|---|---|---|
| `status` | Inspect configuration, contracts, and recent artifacts | none |
| `onboard` | Create or update the profile through `profile-manager` | local profile write |
| `demo` | Run fixture by default; live only with explicit approval | JSON by default |
| `daily` | Collect, parse, rank, and upsert | Notion when configured |
| `brief` | Generate or send the recommendation briefing | dry-run interactively |
| `accept-sync` | Plan and apply accepted calendar items | Calendar and Notion |
| `partial:<phase>` | Targeted rerun and required downstream phases | phase dependent |

Timely schedules `daily`, `brief`, and `accept-sync`. These schedule names do not require separate Agent definitions.
