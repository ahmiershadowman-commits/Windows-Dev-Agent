"""
Safety gate — classifies tool calls and enforces approval requirements.
Called by hooks before execution.
"""

import argparse
import json
import re
import sys

SAFETY_CLASSES = {
    "read-only":        0,  # autonomous
    "reversible":       1,  # autonomous + audit
    "approval-required": 2,  # show + wait
    "checkpoint":       3,  # stop + explain risk
    "forbidden":        4,  # never without explicit human command
}

# Patterns → safety class
BASH_RULES = [
    (re.compile(r"(rm\s+-rf|del\s+/[sf]|format\s+[a-z]:)", re.I), "checkpoint"),
    (re.compile(r"(reg\s+(add|delete)|Set-ItemProperty.*HKLM)", re.I), "checkpoint"),
    (re.compile(r"(winget\s+install|choco\s+install|scoop\s+install)", re.I), "approval-required"),
    (re.compile(r"(npm\s+install|pip\s+install|cargo\s+install|go\s+get)", re.I), "approval-required"),
    (re.compile(r"(Enable-WindowsOptionalFeature|Install-WindowsFeature)", re.I), "approval-required"),
    (re.compile(r"(git\s+push|gh\s+pr\s+create|gh\s+release)", re.I), "approval-required"),
    (re.compile(r"(git\s+(status|log|diff|show)|Get-|Select-|Format-|Where-|Sort-)", re.I), "read-only"),
    (re.compile(r"(pytest|cargo\s+test|go\s+test|npm\s+test)", re.I), "reversible"),
]


def classify_bash(command: str) -> str:
    for pattern, cls in BASH_RULES:
        if pattern.search(command):
            return cls
    return "reversible"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True)
    parser.add_argument("--args", default="{}")
    args = parser.parse_args()

    try:
        tool_args = json.loads(args.args)
    except json.JSONDecodeError:
        tool_args = {"raw": args.args}

    if args.tool == "bash":
        command = tool_args.get("command", "")
        safety_class = classify_bash(command)
    elif args.tool == "package_install":
        safety_class = "approval-required"
    else:
        safety_class = "reversible"

    level = SAFETY_CLASSES.get(safety_class, 1)

    result = {
        "tool": args.tool,
        "safety_class": safety_class,
        "level": level,
        "proceed": level < 3,  # gate blocks checkpoint and forbidden
    }

    print(json.dumps(result))
    # Exit 2 = block (hooks convention: non-zero blocks execution)
    sys.exit(0 if result["proceed"] else 2)


if __name__ == "__main__":
    main()
