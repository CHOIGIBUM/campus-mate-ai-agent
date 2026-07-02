import json
import sys

from calendar_scheduler_agent import CalendarSchedulerAgent


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = CalendarSchedulerAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
