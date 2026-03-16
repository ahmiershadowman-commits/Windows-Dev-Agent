---
description: Route code execution or tool testing into an isolated environment. Use when running untrusted code, testing installers, or needing reproducible execution. Chooses between Windows Sandbox, WSL, Dev Container, or Hyper-V based on what's available and what's needed.
---

When isolated execution is needed, choose the right environment:

## Isolation routing

| Scenario | Environment | Why |
|----------|------------|-----|
| Run untrusted installer/script | Windows Sandbox | Disposable, no host impact |
| Linux-native tool | WSL | Native Linux layer |
| Reproducible project build | Dev Container | Locked deps, portable |
| Persistent high-isolation work | Hyper-V VM | Full OS isolation |
| Fast scripting test | WSL | Lightweight |

## Before routing

1. Check available isolation via `env_inspect` (virtualization section)
2. If requested environment isn't available, tell the user what's missing and how to enable it:
   - Windows Sandbox: `Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM"`
   - WSL: `wsl --install`
   - Hyper-V: `Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All`

## Executing in WSL

```powershell
wsl -d Ubuntu -- bash -c "<command>"
```

## Executing in Windows Sandbox

Create a `.wsb` config file and launch:
```powershell
$config = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$env:USERPROFILE\sandbox-work</HostFolder>
      <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\work</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell -Command "cd C:\Users\WDAGUtilityAccount\Desktop\work; <your-command>"</Command>
  </LogonCommand>
</Configuration>
"@
$config | Out-File "$env:TEMP\sandbox.wsb"
Start-Process "$env:TEMP\sandbox.wsb"
```

All sandbox runs are `approval-required`. Show the config before launching.
