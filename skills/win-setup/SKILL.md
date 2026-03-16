---
description: Bootstrap or repair a Windows development environment. Use when setting up a new machine, onboarding to a project, or fixing a broken environment. Triggers on phrases like "set up my environment", "bootstrap", "my Python isn't working", or "I need to install X".
---

When bootstrapping or repairing a Windows dev environment:

1. **Inspect first** — run `env_inspect` to get current state before touching anything
2. **Identify gaps** — compare discovered state against what the project or task needs
3. **Propose a plan** — list everything that needs installing or fixing, with WinGet commands
4. **Safety gate** — all installs are `approval-required`. Show the full list, wait for confirmation.
5. **Execute in order**:
   - WinGet sources first (`winget source update`)
   - Runtimes (Python, Node, Rust, Go, .NET)
   - Dev tools (Git, VS Code, Docker if needed)
   - Project dependencies (via language-native tool after runtime is confirmed)
6. **Verify** — re-run `env_inspect` after install, confirm versions match expectations
7. **Report** — summarize what was installed, what was already present, anything that failed

## WinGet patterns

```powershell
# Update sources
winget source update

# Install a runtime
winget install --id Python.Python.3.12 --exact --silent

# Install a tool
winget install --id Git.Git --exact --silent
winget install --id Microsoft.VisualStudioCode --exact --silent

# Check what's installed
winget list --source winget
```

Never use `--silent` for anything that requires a license agreement confirmation.
Always verify the `--id` is exact before running.
