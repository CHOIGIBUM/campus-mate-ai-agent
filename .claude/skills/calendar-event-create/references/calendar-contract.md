# Calendar Connector Contract

Event kinds:

- `deadline`: `[마감] title`, usually 23:00 KST
- `preparation`: `[D-3 준비] title`, usually 09:00 KST
- `event`: `[행사] title`, usually 09:00 KST

Each result must preserve the request ID. A connector timeout is a failure, not an implied success. Keep event IDs in the opportunity record to avoid duplicates.
