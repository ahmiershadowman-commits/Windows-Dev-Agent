"""
Minimal trace logger. Writes JSONL events to agent.log.
Full OpenTelemetry integration is a future phase.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent.parent / "agent.log"


def log_event(event_type: str, data: dict):
    entry = {
        "ts": datetime.now().isoformat(),
        "event": event_type,
        **data
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--input", default="{}")
    parser.add_argument("--output", default="{}")
    args = parser.parse_args()
    log_event(args.event, {"input": args.input[:500], "output": args.output[:500]})


if __name__ == "__main__":
    main()
