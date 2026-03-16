---
description: Inspect the full Windows development environment. Use when diagnosing tool availability, runtime versions, WSL state, Dev Drive, or package manager status. Triggers automatically when environment state is needed before planning or executing any task.
---

When environment inspection is needed:

1. Call the `env_inspect` MCP tool to get a full `EnvironmentSnapshot`
2. Parse and present:

**System**
- OS name, build, architecture
- RAM, CPU count

**Virtualization surface**
- Hyper-V: available or not
- WSL: version, installed distros
- Windows Sandbox: available or not
- Dev Drive: drive letter, free space

**Package managers**
- WinGet, Chocolatey, Scoop — available/version

**Runtimes**
- Python, Node, Rust, Go, .NET — version or missing

**Developer tools**
- Git — available, user.name/email configured
- Docker — available
- VS Code, Visual Studio, JetBrains — detected editors
- PowerShell modules count

3. Flag anything broken or missing that would block common dev tasks
4. For missing tools, suggest the WinGet install command

If the MCP server is unavailable, fall back to asking the user to run:
```powershell
python -m src.discovery.discovery
```
and share the output.
