# Known Limitations

- Linkareer is the only complete source adapter in the packaged implementation.
- JavaScript-heavy sources require a site-specific Playwright adapter before they can be claimed as supported.
- OCR quality depends on installed Tesseract language packs and poster resolution.
- Vision parsing depends on a configured compatible model and should remain a fallback, not the sole evidence source.
- Relevance scoring is a transparent heuristic, not a trained acceptance model.
- Slack is notification-only; approval remains in Notion.
- Google Calendar creation is performed through a Timely/Composio manifest bridge.
- Scheduled Timely execution must be verified in the user’s own account and connector permissions.
