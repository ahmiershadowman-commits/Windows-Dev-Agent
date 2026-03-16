---
description: Plan any development task before executing it. Use when given a feature request, bug to fix, refactor, or any multi-step task. Always generates a structured plan with safety classifications before touching code or running commands.
---

When planning a development task:

## Phase 1 — Understand
- Restate the task in your own words
- Identify: what type of task is this? (feature, bugfix, refactor, environment, research)
- Identify: what's the success condition?
- Identify: what could go wrong?

## Phase 2 — Inspect
- Call `env_inspect` to confirm runtime and tool availability
- Check if the project has a `CLAUDE.md` or `.clinerules` with project-specific instructions
- Note the project language, build system, test framework

## Phase 3 — Brainstorm
- Generate 2-4 approaches
- For each: note the Windows-native path, any WSL fallback, pros/cons
- Prefer the most native, most auditable path

## Phase 4 — Write the plan
Structure as numbered phases, each with:
```
## Phase N: <name>
Entry criteria: <what must be true>
Steps:
  1. <specific command or action> [safety: autonomous|approval-required|checkpoint]
  2. ...
Exit criteria: <how to verify success>
Rollback: <how to undo>
```

## Phase 5 — Present and confirm
Show the full plan. Do not proceed until confirmed.

## After confirmation
Execute phase by phase. After each phase: verify exit criteria before continuing.
If a phase fails: stop, report, do not attempt the next phase without re-planning.
