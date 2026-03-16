---
description: Install packages or tools using WinGet (preferred), Chocolatey, or Scoop. Always approval-required. Use when the user asks to install something or when a dependency check finds a missing tool.
---

Package installation is always `approval-required`. Never install silently without showing the user exactly what will run.

## Process

1. **Identify the package** — use `winget search <name>` to find the exact package ID
2. **Show the install command** before running it:
   ```powershell
   winget install --id <exact.Package.Id> --exact
   ```
3. **Wait for confirmation**
4. **Run with logging** — capture stdout/stderr
5. **Verify** — run the tool's version command to confirm install succeeded
6. **Update PATH if needed** — some tools require a new shell session

## Tool routing for installs

| What to install | Preferred command |
|----------------|------------------|
| Runtimes (Python, Node, Rust, Go, .NET) | `winget install` |
| Dev tools (Git, VS Code, Docker) | `winget install` |
| CLI utilities | `winget install` → `scoop install` fallback |
| Windows features (WSL, Hyper-V) | PowerShell `Enable-WindowsOptionalFeature` |
| npm packages | `npm install` (after Node confirmed) |
| pip packages | `pip install` / `uv pip install` (after Python confirmed) |
| Rust crates | `cargo install` (after Rust confirmed) |

## Never
- Install with `--silent` if it bypasses license prompts
- Run elevated installs without flagging it as `checkpoint`
- Install from unknown sources without surfacing the source to the user
