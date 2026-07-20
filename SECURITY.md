# Security

Campus Mate never requires credentials to be committed to the repository.

- Store Notion, Slack, model, and Google/Composio credentials in Timely Secrets or environment variables.
- Do not put tokens in Agent or Skill Markdown files.
- If a token was previously committed, revoke and reissue it; deleting the visible file is not enough.
- Run `make secret-scan` before every public push.
- Use a dedicated test Notion database, Slack workspace/channel, and Google Calendar for demonstrations.
