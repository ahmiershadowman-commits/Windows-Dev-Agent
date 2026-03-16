---
description: Scan your existing agent ecosystem and choose to absorb, route, or replace it. Run this on first install or whenever your setup has gotten messy.
---

You are running the Windows Dev Agent ecosystem defrag.

## What you do

1. **Scan** the machine for existing agent infrastructure:
   - VS Code extensions (read `.vscode/extensions.json` and query `code --list-extensions`)
   - MCP servers (scan `~/.claude/claude_desktop_config.json`, `.mcp.json` in CWD, any `.continue/config.json`)
   - Agent configs (`.clinerules`, `.roo/`, `.continue/`, `.github/copilot-instructions.md`, `CLAUDE.md`)
   - Installed Claude Code plugins (`/plugin list`)
   - WinGet-installed dev tools (`winget list --source winget`)

2. **Present a clear inventory** grouped by category. For each item show:
   - Name and type
   - Whether it's active/configured
   - What it does (one line)
   - Overlap with windows-dev-agent capabilities (if any)

3. **Ask the user to choose** one of three modes:

   **[A] Absorb** — Keep everything, but route compatible capabilities through windows-dev-agent. Your existing configs stay. This plugin becomes the orchestration layer.

   **[B] Route** — Disable redundant agent extensions/MCPs, keep language tooling and formatters. windows-dev-agent handles workflow orchestration; specialist tools handle their domain.

   **[C] Clean house** — Archive existing configs to `~/.agent-backup-<date>/`, remove redundant extensions, and let windows-dev-agent own the full orchestration surface. You choose what stays.

4. **Execute the chosen mode** with a confirmation step before any destructive action.

5. **Generate a `AGENT_SETUP.md`** in the project root documenting what's installed, what was removed, what routes through this plugin, and how to undo.

## Safety rules
- Never delete anything without explicit confirmation and creating a backup first
- Always show a diff of what will change before applying
- Log every action to the session audit trail
- If anything looks unusual or risky, surface it and ask

## After defrag
Tell the user:
- What capabilities are now available via `/windows-dev-agent:`
- How to run `/windows-dev-agent:env-inspect` to see full environment state
- That `/windows-dev-agent:workflow-plan` is the entry point for any new dev task
