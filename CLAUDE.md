# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Windows-Dev-Agent is a Claude Code plugin for Windows-native developer orchestration. It provides environment inspection, capability routing, workflow planning, package management (WinGet/Chocolatey/Scoop), and sandbox execution (Windows Sandbox, WSL, Dev Container).

## Commands

```bash
# Run all tests
python -m pytest tests/ -q

# Run a single test file
python -m pytest tests/test_safety.py -q

# Start the MCP server (stdio transport)
python -m src.mcp.server

# Install dependency
pip install pyyaml
```

## Architecture

The project has two layers:

**Plugin layer (markdown):** `commands/`, `skills/`, `agents/`, `hooks/` — These are Claude Code-readable markdown files that define slash commands (`/windows-dev-agent:env`, `/windows-dev-agent:plan`, `/windows-dev-agent:defrag`), auto-triggered context skills, and the hook system.

**Python backend (`src/`):** A JSON-RPC stdio MCP server exposing 8 tools. The server entry point is `src/mcp/server.py`.

### MCP Tool → Handler mapping

| Tool | Handler | Backend module |
|------|---------|---------------|
| `env_inspect` | `handle_env_inspect` | `src/discovery/discovery.py` + `discovery.ps1` |
| `tool_discover` | `handle_tool_discover` | `src/discovery/discovery.py` |
| `capability_run` | `handle_capability_run` | `src/graph/capability_graph.py` |
| `workflow_plan` | `handle_workflow_plan` | `src/workflow/engine.py` |
| `package_install` | `handle_package_install` | PowerShell execution layer |
| `sandbox_run` | `handle_sandbox_run` | `src/execution/powershell_executor.py` |
| `logs_query` | `handle_logs_query` | `src/observability/audit_report.py` |
| `mcp_audit` | `handle_mcp_audit` | `.mcp.json` inspection |

### Safety model

`src/safety/gate.py` classifies every bash/tool call into one of 5 tiers before execution via `hooks/hooks.json` PreToolUse hooks:

- **read-only** (autonomous): `git status`, `Get-*`, `Where-*`, query commands
- **reversible** (autonomous + audit): tests, build commands
- **approval-required** (confirmation): `winget install`, `git push`, `npm install`, `gh pr create`
- **checkpoint** (stop + explain): `rm -rf`, `reg add`, `format`, `Enable-WindowsOptionalFeature`
- **forbidden** (never): reserved for extreme cases

### Capability routing

`capabilities.yaml` defines capabilities (e.g., `lint-python`, `create-pr`) with preferred tool + fallback (e.g., `ruff` → `pylint`). `src/graph/capability_graph.py` selects the best available tool at runtime based on the environment snapshot.

### Environment caching

`src/discovery/discovery.py` caches environment state in `.cache/environment.json` with a 5-minute TTL. The PowerShell discovery script (`src/discovery/discovery.ps1`) does the actual Windows system inspection.

### Hook execution

`hooks/hooks.json` wires three lifecycle events:
- **PreToolUse**: `python -m src.safety.gate` — blocks checkpoint/forbidden actions
- **PostToolUse**: `python -m src.observability.trace` — emits OpenTelemetry spans
- **Stop**: `python -m src.observability.audit_report` — generates session audit

### Key schemas

- `src/schemas/capability.py`: `CapabilityDefinition`, `IntentClass`, `SafetyLevel`, `DependencyCheck`
- `src/schemas/workflow.py`: `WorkflowDefinition`, `WorkflowStage`, `WorkflowStep`
- `src/models/environment.py`: `EnvironmentSnapshot`, `SystemInfo`, `VirtualizationInfo`, `Runtimes`

## Plugin manifests

- `.mcp.json` — declares the MCP server (command: `python -m src.mcp.server`)
- `.claude-plugin/plugin.json` — Claude Code plugin manifest (minClaudeCodeVersion: 1.0.33)
- `apm.yml` — APM registry manifest (targets: claude, codex, opencode)
