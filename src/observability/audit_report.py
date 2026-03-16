"""
Generate end-of-session audit report from agent.log.
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

LOG_FILE = Path(__file__).parent.parent.parent / "agent.log"


def generate_report():
    if not LOG_FILE.exists():
        print("No session log found.")
        return

    events = []
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not events:
        print("Session log is empty.")
        return

    event_types = Counter(e.get("event") for e in events)
    print("\n=== Windows Dev Agent — Session Audit Report ===")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total events logged: {len(events)}")
    print("\nEvent breakdown:")
    for event, count in event_types.most_common():
        print(f"  {event}: {count}")
    print("\n" + "=" * 48)


if __name__ == "__main__":
    generate_report()
