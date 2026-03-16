# Windows Dev Agent — Wire-Up Design

**Date:** 2026-03-16
**Status:** Approved
**Phase:** Wire-up (plugin layer + repo cleanup). Skill expansion is a separate phase.

---

## Goal

Transform the current repo from a standalone Python CLI (with build artifacts committed to history) into a working Claude Code plugin. The git history is preserved intentionally — the drift from correct architecture is part of the record.

---

## Context

The repo has two layers of problems:

1. **Junk at root level** — the previous agent committed build logs, phase reports, an executor script, and its own `plugin.py` entry point. None of these belong.
2. **Missing plugin layer** — the entire Claude Code plugin surface (`.claude-plugin/`, `commands/`, `skills/`, `agents/`, `hooks/`, `.mcp.json`) does not exist.

A reference implementation exists in `windows-dev-agent.zip` (dated 2026-03-14). It has the correct plugin layer and cleaner versions of some `src/` modules. The current repo has more complete Python implementations of `discovery/`, `execution/`, `workflow/`, `graph/`, and `schemas/` than the zip.

---

## Architecture

The plugin has two distinct layers:

**Plugin layer (markdown)** — read directly by Claude Code. No build step.
```
.claude-plugin/plugin.json     ← manifest
.mcp.json                      ← MCP server declaration
commands/{defrag,env,plan}.md  ← slash commands
agents/windows-orchestrator.md ← orchestration agent
skills/*/SKILL.md              ← auto-triggered skills (×5)
hooks/hooks.json               ← pre/post tool hooks
```

**Python backend** — invoked by the MCP server and hooks.
```
src/mcp/server.py              ← stdio MCP server (exposes 8 tools)
src/safety/gate.py             ← safety classification (called by hooks)
src/observability/             ← trace.py + audit_report.py
src/discovery/                 ← PowerShell/WMI environment discovery
src/execution/                 ← PowerShell executor + command builder
src/models/                    ← environment + execution dataclasses
src/workflow/engine.py         ← workflow DSL execution engine
src/graph/capability_graph.py  ← tool selection + routing
src/schemas/                   ← capability, tool, workflow definitions
src/config/capability_loader.py← YAML parser + validator
```

---

## Changes

### Delete (junk — no longer needed)

- `agent.log`
- `build.log`
- `BUILD_PLAN.md`
- `FINAL_BUILD_REPORT.md`
- `PHASE_COMPLETION_SUMMARY.md`
- `execute_phase.sh`
- `phase_executor.py`
- `plugin.py` (root-level)
- `.build_state.json`
- `src/web/` (entire directory — no web component)

### Add from zip (plugin layer — does not exist in current repo)

- `.claude-plugin/plugin.json`
- `.mcp.json`
- `commands/defrag.md`
- `commands/env.md`
- `commands/plan.md`
- `agents/windows-orchestrator.md`
- `skills/env-inspect/SKILL.md`
- `skills/win-setup/SKILL.md`
- `skills/workflow-plan/SKILL.md`
- `skills/package-install/SKILL.md`
- `skills/sandbox-run/SKILL.md`
- `hooks/hooks.json`

### Add from zip (backend files — additive, do not replace existing)

- `src/safety/gate.py` — regex-based CLI classifier invoked by hooks. Lives alongside `policy.py` (kept separately for tests — see below). `policy.py` is NOT deleted.
- `src/observability/trace.py` — per-tool-call trace emitter (invoked by PostToolUse hook)
- `src/observability/audit_report.py` — session-end audit report (invoked by Stop hook)
  - `telemetry.py` is NOT deleted — tests import `Telemetry`, `Span`, `Meter`, `get_telemetry` from it directly. The zip files are additions.
- `src/mcp/server.py` — **replace** current version with zip's 16KB stdio MCP server. The current `server.py` is a plain Python class with no stdio transport. The zip version is a proper JSON-RPC stdio server. Launch command: `python -m src.mcp.server` (matches `.mcp.json` declaration). No tests import from `src.mcp` — replacement is safe.
- `README.md` — **replace**: rewrite to describe the plugin, not the prototype CLI

### Keep (current repo — more complete implementations)

- `src/discovery/` — full WMI/PowerShell discovery with caching
- `src/execution/` — command builder + PowerShell executor with escaping
- `src/models/` — rich environment + execution dataclasses
- `src/workflow/engine.py` — workflow DSL with stages, approval gates, rollback
- `src/graph/capability_graph.py` — tool selection + routing
- `src/schemas/{capability,tool,workflow}.py` — rich schema with intent classes, safety levels
- `src/config/capability_loader.py` — YAML parser with backward compatibility
- `src/safety/policy.py` — kept as-is; tests import `SafetyPolicy` from it
- `src/observability/telemetry.py` — kept as-is; tests import `Telemetry`/`Span`/`Meter`/`get_telemetry` from it
- `capabilities.yaml` — current version is more complete
- `tests/` — all 112 tests kept

### Keep (stubs — deferred to expand phase)

- `src/adapters/__init__.py`
- `src/audit/__init__.py`
- `src/cli/__init__.py`
- `src/reporting/__init__.py`
- `src/importers/__init__.py` — implementation deferred (powers defrag scan phase)

### Add new

- `apm.yml` — APM manifest so the plugin is installable via `apm install windows-dev-agent`

---

## Safety model (unchanged)

The hooks in `hooks/hooks.json` call `python -m src.safety.gate` before every Bash tool call and every `package_install` MCP call. The gate classifies commands and exits 2 (block) for `checkpoint` and `forbidden` classes.

Safety tiers: `read-only` → `reversible` → `approval-required` → `checkpoint` → `forbidden`

No changes to the safety model in this phase.

---

## Verification criteria

After wire-up, all of the following must pass:

1. `python -m pytest tests/ -q` — all 112 tests still pass (run this first, before any Claude Code testing)
2. `python -m src.mcp.server` — server starts and responds to a `tools/list` JSON-RPC probe without error (standalone pre-flight, no Claude Code required)
3. `claude --plugin-dir .` loads the plugin without errors
4. `/windows-dev-agent:env` invokes the `env_inspect` MCP tool and returns environment data
5. `/windows-dev-agent:defrag` runs the scan phase and presents an inventory
6. `/windows-dev-agent:plan <task>` generates a structured plan before touching anything
7. Hooks fire on Bash tool calls and classify safety level
8. `apm.yml` is valid YAML containing at minimum: `name`, `version`, `description`, and `targets` fields. These four fields are the authoritative definition for this project; external schema validation is deferred.

---

## Out of scope (expand phase)

- Deepening skills to superpowers-level instruction depth
- `src/importers/` implementation (ecosystem importer for defrag scan)
- Governance-toolkit / Cedar policy integration
- Additional skills (systematic-debugging, TDD equivalent)
- APM dependency resolution testing
