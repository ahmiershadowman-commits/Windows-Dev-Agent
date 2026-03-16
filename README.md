# Windows Dev Agent

A Claude Code plugin for Windows-native developer orchestration.

**Install:**
```
/plugin install windows-dev-agent
```

**Or with APM:**
```
apm install windows-dev-agent
```

---

## What it does

- `/windows-dev-agent:env` — Full environment snapshot: OS, runtimes, WSL, Dev Drive, package managers, editors
- `/windows-dev-agent:plan <task>` — Structured execution plan before touching anything. Entry criteria, steps, exit criteria, rollback, safety classifications.
- `/windows-dev-agent:defrag` — Scan existing agent infrastructure (VS Code extensions, MCP servers, agent configs) and choose to absorb, route, or clean house.

## How it works

Two layers:

**Plugin layer (markdown)** — read directly by Claude Code, no build step:
- `commands/` — slash commands
- `skills/` — auto-triggered context skills
- `agents/` — orchestration agent
- `hooks/` — pre/post tool safety gates

**Python backend** — MCP stdio server invoked by Claude Code:
- Environment discovery via PowerShell/WMI
- Safety gate classifying every shell command before execution
- Audit trail at end of every session

## Tool routing priority

1. PowerShell native
2. WinGet
3. WMI/CIM
4. MSBuild / .NET
5. WSL (fallback, not default)
6. Windows Sandbox / Hyper-V (isolation)

## Safety model

| Class | Behavior |
|---|---|
| `read-only` | Autonomous |
| `reversible` | Autonomous + audit log |
| `approval-required` | Show command, wait for yes |
| `checkpoint` | Explain risk, require confirmation |
| `forbidden` | Never without direct human command |

## Requirements

- Claude Code 1.0.33+
- Python 3.9+
- `pip install pyyaml`
- Windows 10/11 (PowerShell 5.1+)

## Architecture

See `docs/superpowers/specs/` for design documents.
