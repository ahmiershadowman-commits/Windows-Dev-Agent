---
description: Run a full Windows environment snapshot. Shows OS, runtimes, installed tools, WSL distros, Dev Drive, package managers, and editor availability.
---

Run a full environment discovery using the windows-dev-agent MCP tool `env_inspect`.

Present results in clean sections:
- System (OS build, architecture, memory, CPU)
- Virtualization (Hyper-V, WSL distros, Windows Sandbox, Dev Drive)
- Package managers (WinGet, Chocolatey, Scoop — what's available)
- Runtimes (Python, Node, Rust, Go, .NET — versions)
- Dev tools (Git config, Docker, editors)
- Agent surface (MCP servers, VS Code extensions, shell modules)

Flag anything that looks broken, missing, or misconfigured. Suggest fixes using WinGet where possible.
