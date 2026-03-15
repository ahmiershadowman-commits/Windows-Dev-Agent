# Windows Dev Agent Plugin - System Discovery Script
# This PowerShell script gathers comprehensive machine state information for the plugin.
# It uses WMI, CIM, registry queries, and built-in commands to discover:
# - OS and hardware information
# - Virtualization capabilities and status
# - Development tools and runtimes
# - WSL distros and services
# - Git configuration
# - IDE and editor availability
# - PowerShell modules

# Error handling
$ErrorActionPreference = "Continue"

# Create result object
$discoveryResult = @{
    timestamp = Get-Date -Format "o"
    success = $true
    errors = @()
    system = @{}
    virtualization = @{}
    development_tools = @{}
    runtimes = @{}
    wsl = @{}
    git = @{}
    editors = @{}
    powershell_modules = @{}
}

function Get-SafeWMIObject {
    param(
        [string]$Class,
        [string]$Property
    )
    try {
        $result = Get-WmiObject -Class $Class -ErrorAction SilentlyContinue | Select-Object -ExpandProperty $Property
        return $result
    }
    catch {
        return $null
    }
}

# ============================================================================
# 1. System Information
# ============================================================================
try {
    $osInfo = Get-WmiObject -Class Win32_OperatingSystem -ErrorAction SilentlyContinue
    $computerInfo = Get-ComputerInfo -ErrorAction SilentlyContinue

    $discoveryResult.system = @{
        os_name = $osInfo.Caption
        os_version = $osInfo.Version
        os_build = $osInfo.BuildNumber
        architecture = $osInfo.OSArchitecture
        install_date = $osInfo.InstallDate
        system_root = $osInfo.SystemRoot
        computer_name = $env:COMPUTERNAME
        username = $env:USERNAME
        domain = $env:USERDOMAIN
        processor_count = (Get-WmiObject -Class Win32_Processor -ErrorAction SilentlyContinue).Count
        processor_name = (Get-WmiObject -Class Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1).Name
        total_physical_memory_gb = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem -ErrorAction SilentlyContinue).TotalPhysicalMemory / 1GB, 2)
        locale = $computerInfo.OSLocale
        timezone = (Get-TimeZone).Id
    }
}
catch {
    $discoveryResult.errors += "System information discovery failed: $_"
}

# ============================================================================
# 2. Virtualization Capabilities
# ============================================================================
try {
    # Hyper-V
    $hyperv = Get-WmiObject -Namespace "root\cimv2" -Class Win32_ComputerSystemProduct -ErrorAction SilentlyContinue
    $hyperv_enabled = (Get-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V -ErrorAction SilentlyContinue).State -eq "Enabled"

    # WSL
    $wsl_installed = Test-Path "C:\Windows\System32\wsl.exe"
    $wsl_version = ""
    $wsl_distros = @()

    if ($wsl_installed) {
        try {
            $wsl_version = wsl.exe --version 2>$null
            $wsl_list_output = wsl.exe --list --verbose 2>$null
            # Parse distro names (this is a simplification)
            $wsl_distros = @($wsl_list_output -match "^\s*[*\s]" | ForEach-Object { $_.Trim() })
        }
        catch {
            # WSL might not be fully configured
        }
    }

    # Windows Sandbox
    $sandbox_available = (Get-WindowsOptionalFeature -FeatureName "Containers-DisposableVM" -ErrorAction SilentlyContinue).State -eq "Enabled"

    # Dev Drive
    $dev_drives = @()
    try {
        $volumes = Get-Volume -ErrorAction SilentlyContinue | Where-Object { $_.FileSystemLabel -match "DevDrive" }
        $dev_drives = $volumes | ForEach-Object {
            @{
                drive_letter = $_.DriveLetter
                label = $_.FileSystemLabel
                size_gb = [math]::Round($_.Size / 1GB, 2)
                free_space_gb = [math]::Round($_.SizeRemaining / 1GB, 2)
            }
        }
    }
    catch {
        # Dev Drive not available
    }

    $discoveryResult.virtualization = @{
        hyper_v_available = $hyperv_enabled
        wsl_installed = $wsl_installed
        wsl_version = $wsl_version
        wsl_distros = $wsl_distros
        windows_sandbox_available = $sandbox_available
        dev_drives = $dev_drives
    }
}
catch {
    $discoveryResult.errors += "Virtualization discovery failed: $_"
}

# ============================================================================
# 3. Package Managers and Development Tools
# ============================================================================
try {
    $winget_available = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
    $choco_available = $null -ne (Get-Command choco -ErrorAction SilentlyContinue)
    $scoop_available = $null -ne (Get-Command scoop -ErrorAction SilentlyContinue)

    $discoveryResult.development_tools = @{
        winget_available = $winget_available
        chocolatey_available = $choco_available
        scoop_available = $scoop_available
        git_available = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
        docker_available = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
        vscode_available = Test-Path "C:\Program Files\Microsoft VS Code\Code.exe" -ErrorAction SilentlyContinue
        visual_studio_available = Test-Path "C:\Program Files\Microsoft Visual Studio" -ErrorAction SilentlyContinue
    }
}
catch {
    $discoveryResult.errors += "Development tools discovery failed: $_"
}

# ============================================================================
# 4. Language Runtimes and SDKs
# ============================================================================
try {
    $runtimes = @{
        python = @{ available = $false; version = $null }
        node = @{ available = $false; version = $null }
        rust = @{ available = $false; version = $null }
        golang = @{ available = $false; version = $null }
        dotnet = @{ available = $false; versions = @() }
    }

    # Python
    if ($null -ne (Get-Command python -ErrorAction SilentlyContinue)) {
        $runtimes.python.available = $true
        try {
            $runtimes.python.version = (python --version 2>&1) -replace "Python\s+" , ""
        }
        catch {}
    }

    # Node.js
    if ($null -ne (Get-Command node -ErrorAction SilentlyContinue)) {
        $runtimes.node.available = $true
        try {
            $runtimes.node.version = (node --version 2>&1).TrimStart("v")
        }
        catch {}
    }

    # Rust
    if ($null -ne (Get-Command rustc -ErrorAction SilentlyContinue)) {
        $runtimes.rust.available = $true
        try {
            $runtimes.rust.version = (rustc --version 2>&1) -replace "rustc\s+", ""
        }
        catch {}
    }

    # Go
    if ($null -ne (Get-Command go -ErrorAction SilentlyContinue)) {
        $runtimes.golang.available = $true
        try {
            $runtimes.golang.version = (go version 2>&1) -replace "go version go", ""
        }
        catch {}
    }

    # .NET
    if ($null -ne (Get-Command dotnet -ErrorAction SilentlyContinue)) {
        $runtimes.dotnet.available = $true
        try {
            $dotnet_output = dotnet --list-sdks 2>&1
            $runtimes.dotnet.versions = @($dotnet_output -match '^\d+\.\d+' | ForEach-Object { $_.Split()[0] })
        }
        catch {}
    }

    $discoveryResult.runtimes = $runtimes
}
catch {
    $discoveryResult.errors += "Runtime discovery failed: $_"
}

# ============================================================================
# 5. Git Configuration
# ============================================================================
try {
    $git_available = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
    $git_config = @{
        available = $git_available
        version = $null
        user_name = $null
        user_email = $null
    }

    if ($git_available) {
        try {
            $git_config.version = (git --version 2>&1) -replace "git version\s+", ""
            $git_config.user_name = (git config --global user.name 2>$null)
            $git_config.user_email = (git config --global user.email 2>$null)
        }
        catch {}
    }

    $discoveryResult.git = $git_config
}
catch {
    $discoveryResult.errors += "Git discovery failed: $_"
}

# ============================================================================
# 6. IDE and Editor Availability
# ============================================================================
try {
    $editors = @{
        visual_studio_code = Test-Path "C:\Program Files\Microsoft VS Code\Code.exe" -ErrorAction SilentlyContinue
        visual_studio = $null -ne (Get-Command devenv -ErrorAction SilentlyContinue)
        jetbrains_rider = Test-Path "C:\Program Files\JetBrains\Rider*" -ErrorAction SilentlyContinue
        jetbrains_pycharm = Test-Path "C:\Program Files\JetBrains\PyCharm*" -ErrorAction SilentlyContinue
        jetbrains_clion = Test-Path "C:\Program Files\JetBrains\CLion*" -ErrorAction SilentlyContinue
    }

    $discoveryResult.editors = $editors
}
catch {
    $discoveryResult.errors += "Editor discovery failed: $_"
}

# ============================================================================
# 7. PowerShell Modules
# ============================================================================
try {
    $modules = @()
    $installed_modules = Get-Module -ListAvailable -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name -Unique

    if ($null -ne $installed_modules) {
        $modules = @($installed_modules)
    }

    $discoveryResult.powershell_modules = @{
        count = $modules.Count
        modules = $modules
    }
}
catch {
    $discoveryResult.errors += "PowerShell modules discovery failed: $_"
}

# ============================================================================
# Output result as JSON
# ============================================================================
$discoveryResult | ConvertTo-Json -Depth 10
