"""
Environment model for Windows Dev Agent Plugin.

Defines dataclasses representing system and environment state discovered during
the discovery phase.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class SystemInfo:
    """System and hardware information."""
    os_name: str
    os_version: str
    os_build: str
    architecture: str
    install_date: Optional[str] = None
    system_root: str = ""
    computer_name: str = ""
    username: str = ""
    domain: str = ""
    processor_count: int = 0
    processor_name: str = ""
    total_physical_memory_gb: float = 0.0
    locale: str = ""
    timezone: str = ""

    def is_windows_11(self) -> bool:
        """Check if running Windows 11."""
        return "11" in self.os_name or int(self.os_build) >= 22000

    def is_windows_10(self) -> bool:
        """Check if running Windows 10."""
        return "10" in self.os_name


@dataclass
class DevDrive:
    """Dev Drive information."""
    drive_letter: str
    label: str
    size_gb: float
    free_space_gb: float

    @property
    def usage_percent(self) -> float:
        """Get Dev Drive usage percentage."""
        if self.size_gb == 0:
            return 0.0
        return ((self.size_gb - self.free_space_gb) / self.size_gb) * 100


@dataclass
class VirtualizationInfo:
    """Virtualization capabilities and status."""
    hyper_v_available: bool = False
    wsl_installed: bool = False
    wsl_version: str = ""
    wsl_distros: List[str] = field(default_factory=list)
    windows_sandbox_available: bool = False
    dev_drives: List[DevDrive] = field(default_factory=list)

    def has_wsl(self) -> bool:
        """Check if WSL2 is available."""
        return self.wsl_installed and "2" in self.wsl_version

    def has_hyper_v(self) -> bool:
        """Check if Hyper-V is available."""
        return self.hyper_v_available

    def has_sandbox(self) -> bool:
        """Check if Windows Sandbox is available."""
        return self.windows_sandbox_available

    def get_available_isolation_options(self) -> List[str]:
        """Get list of available isolation environments."""
        options = []
        if self.has_hyper_v():
            options.append("hyper-v")
        if self.has_wsl():
            options.append("wsl")
        if self.has_sandbox():
            options.append("windows-sandbox")
        if self.dev_drives:
            options.append("dev-drive")
        return options


@dataclass
class DevelopmentTools:
    """Available package managers and development tools."""
    winget_available: bool = False
    chocolatey_available: bool = False
    scoop_available: bool = False
    git_available: bool = False
    docker_available: bool = False
    vscode_available: bool = False
    visual_studio_available: bool = False

    def get_available_package_managers(self) -> List[str]:
        """Get list of available package managers."""
        managers = []
        if self.winget_available:
            managers.append("winget")
        if self.chocolatey_available:
            managers.append("chocolatey")
        if self.scoop_available:
            managers.append("scoop")
        return managers


@dataclass
class RuntimeInfo:
    """Single runtime/SDK information."""
    available: bool = False
    version: Optional[str] = None
    versions: List[str] = field(default_factory=list)  # For multiple versions like .NET


@dataclass
class Runtimes:
    """Available language runtimes and SDKs."""
    python: RuntimeInfo = field(default_factory=RuntimeInfo)
    node: RuntimeInfo = field(default_factory=RuntimeInfo)
    rust: RuntimeInfo = field(default_factory=RuntimeInfo)
    golang: RuntimeInfo = field(default_factory=RuntimeInfo)
    dotnet: RuntimeInfo = field(default_factory=RuntimeInfo)

    def get_available_runtimes(self) -> List[str]:
        """Get list of available runtimes."""
        runtimes = []
        if self.python.available:
            runtimes.append("python")
        if self.node.available:
            runtimes.append("node")
        if self.rust.available:
            runtimes.append("rust")
        if self.golang.available:
            runtimes.append("golang")
        if self.dotnet.available:
            runtimes.append("dotnet")
        return runtimes


@dataclass
class GitConfig:
    """Git configuration and availability."""
    available: bool = False
    version: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if git is available and configured."""
        return self.available and self.user_name and self.user_email


@dataclass
class EditorAvailability:
    """Available IDEs and editors."""
    visual_studio_code: bool = False
    visual_studio: bool = False
    jetbrains_rider: bool = False
    jetbrains_pycharm: bool = False
    jetbrains_clion: bool = False

    def get_available_editors(self) -> List[str]:
        """Get list of available editors."""
        editors = []
        if self.visual_studio_code:
            editors.append("vscode")
        if self.visual_studio:
            editors.append("visual-studio")
        if self.jetbrains_rider:
            editors.append("rider")
        if self.jetbrains_pycharm:
            editors.append("pycharm")
        if self.jetbrains_clion:
            editors.append("clion")
        return editors


@dataclass
class PowerShellModules:
    """Available PowerShell modules."""
    count: int = 0
    modules: List[str] = field(default_factory=list)

    def has_module(self, module_name: str) -> bool:
        """Check if a specific module is available."""
        return module_name in self.modules


@dataclass
class EnvironmentSnapshot:
    """Complete environment snapshot from discovery phase."""
    timestamp: datetime
    success: bool
    errors: List[str] = field(default_factory=list)
    system: SystemInfo = field(default_factory=SystemInfo)
    virtualization: VirtualizationInfo = field(default_factory=VirtualizationInfo)
    development_tools: DevelopmentTools = field(default_factory=DevelopmentTools)
    runtimes: Runtimes = field(default_factory=Runtimes)
    git: GitConfig = field(default_factory=GitConfig)
    editors: EditorAvailability = field(default_factory=EditorAvailability)
    powershell_modules: PowerShellModules = field(default_factory=PowerShellModules)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "errors": self.errors,
            "system": {
                "os_name": self.system.os_name,
                "os_version": self.system.os_version,
                "os_build": self.system.os_build,
                "architecture": self.system.architecture,
                "computer_name": self.system.computer_name,
                "processor_count": self.system.processor_count,
                "processor_name": self.system.processor_name,
                "total_physical_memory_gb": self.system.total_physical_memory_gb,
            },
            "virtualization": {
                "hyper_v_available": self.virtualization.hyper_v_available,
                "wsl_installed": self.virtualization.wsl_installed,
                "wsl_version": self.virtualization.wsl_version,
                "wsl_distros": self.virtualization.wsl_distros,
                "windows_sandbox_available": self.virtualization.windows_sandbox_available,
                "dev_drives": [
                    {
                        "drive_letter": d.drive_letter,
                        "label": d.label,
                        "size_gb": d.size_gb,
                        "free_space_gb": d.free_space_gb,
                    }
                    for d in self.virtualization.dev_drives
                ],
            },
            "development_tools": {
                "winget_available": self.development_tools.winget_available,
                "chocolatey_available": self.development_tools.chocolatey_available,
                "scoop_available": self.development_tools.scoop_available,
                "git_available": self.development_tools.git_available,
                "docker_available": self.development_tools.docker_available,
                "vscode_available": self.development_tools.vscode_available,
                "visual_studio_available": self.development_tools.visual_studio_available,
            },
            "runtimes": {
                "python": {
                    "available": self.runtimes.python.available,
                    "version": self.runtimes.python.version,
                },
                "node": {
                    "available": self.runtimes.node.available,
                    "version": self.runtimes.node.version,
                },
                "rust": {
                    "available": self.runtimes.rust.available,
                    "version": self.runtimes.rust.version,
                },
                "golang": {
                    "available": self.runtimes.golang.available,
                    "version": self.runtimes.golang.version,
                },
                "dotnet": {
                    "available": self.runtimes.dotnet.available,
                    "versions": self.runtimes.dotnet.versions,
                },
            },
            "git": {
                "available": self.git.available,
                "version": self.git.version,
                "configured": self.git.is_configured(),
            },
            "editors": self.editors.get_available_editors(),
            "available_package_managers": self.development_tools.get_available_package_managers(),
            "available_runtimes": self.runtimes.get_available_runtimes(),
            "available_isolation_options": self.virtualization.get_available_isolation_options(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentSnapshot":
        """Create from dictionary (e.g., from JSON)."""
        timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))

        # Reconstruct nested objects
        sys_data = data.get("system", {})
        # Provide defaults for required fields
        if "os_name" not in sys_data:
            sys_data["os_name"] = "Unknown"
        if "os_version" not in sys_data:
            sys_data["os_version"] = ""
        if "os_build" not in sys_data:
            sys_data["os_build"] = ""
        if "architecture" not in sys_data:
            sys_data["architecture"] = ""
        system = SystemInfo(**sys_data)

        dev_drives = [
            DevDrive(**drive) for drive in data.get("virtualization", {}).get("dev_drives", [])
        ]
        virtualization = VirtualizationInfo(
            **{k: v for k, v in data.get("virtualization", {}).items() if k != "dev_drives"},
            dev_drives=dev_drives,
        )

        development_tools = DevelopmentTools(**data.get("development_tools", {}))

        runtimes_data = data.get("runtimes", {})
        runtimes = Runtimes(
            python=RuntimeInfo(**runtimes_data.get("python", {})),
            node=RuntimeInfo(**runtimes_data.get("node", {})),
            rust=RuntimeInfo(**runtimes_data.get("rust", {})),
            golang=RuntimeInfo(**runtimes_data.get("golang", {})),
            dotnet=RuntimeInfo(**runtimes_data.get("dotnet", {})),
        )

        # Remove 'configured' field if present (it's computed)
        git_data = data.get("git", {})
        git_data.pop("configured", None)
        git = GitConfig(**git_data)

        editors = EditorAvailability(**data.get("editors_detail", {}))
        powershell_modules = PowerShellModules(**data.get("powershell_modules", {}))

        return cls(
            timestamp=timestamp,
            success=data.get("success", True),
            errors=data.get("errors", []),
            system=system,
            virtualization=virtualization,
            development_tools=development_tools,
            runtimes=runtimes,
            git=git,
            editors=editors,
            powershell_modules=powershell_modules,
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "EnvironmentSnapshot":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
