# Timely bridge files

Campus Mate writes `artifacts/calendar_requests.json`. Timely reads each request and calls
`GOOGLECALENDAR_CREATE_EVENT`, then writes `artifacts/calendar_results.json` using the shape
shown in `calendar_results.example.json`.

For conflict checks, Timely normalizes Google Calendar events or free/busy results to the shape
shown in `freebusy.example.json`, then runs:

```bash
campus-mate conflicts apply --input artifacts/freebusy.json
```
