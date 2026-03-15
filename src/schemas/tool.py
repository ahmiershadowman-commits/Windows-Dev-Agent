"""
Tool definition schema for Windows Dev Agent Plugin.

Defines available tools, their capabilities, availability, and compatibility.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AvailabilityCheck:
    """How to check if a tool is available."""
    command: str  # Command to run to check availability
    expected_output_pattern: Optional[str] = None  # Regex to match in output


@dataclass
class InstallationGuide:
    """How to install the tool."""
    winget_package: Optional[str] = None
    chocolatey_package: Optional[str] = None
    scoop_bucket: Optional[str] = None
    portable_url: Optional[str] = None
    manual_url: Optional[str] = None


@dataclass
class VersionInfo:
    """Version detection for a tool."""
    command: str  # Command to get version
    output_pattern: str  # Regex to extract version


@dataclass
class EnvironmentRequirement:
    """Environment variable requirement."""
    name: str
    purpose: str
    example_value: Optional[str] = None


@dataclass
class CompatibilityInfo:
    """Compatibility matrix for a tool."""
    min_windows_build: Optional[int] = None
    requires_admin: bool = False
    requires_wsl: bool = False
    requires_virtualization: bool = False
    architectures: List[str] = field(default_factory=lambda: ["x64", "x86"])


@dataclass
class ToolDefinition:
    """Complete definition of an available tool."""
    id: str
    name: str
    category: str  # "linter", "formatter", "test_runner", "builder", etc.
    description: str

    # Availability
    is_windows_native: bool = True
    availability_check: Optional[AvailabilityCheck] = None
    installation_guide: Optional[InstallationGuide] = None

    # Version detection
    version_info: Optional[VersionInfo] = None

    # Environment
    environment_variables: List[EnvironmentRequirement] = field(default_factory=list)

    # Compatibility
    compatibility: CompatibilityInfo = field(default_factory=CompatibilityInfo)

    # Metadata
    homepage_url: Optional[str] = None
    documentation_url: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Fallback options
    alternative_tools: List[str] = field(default_factory=list)  # IDs of similar tools

    def is_native_windows(self) -> bool:
        """Check if this is a Windows-native tool."""
        return self.is_windows_native

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "is_windows_native": self.is_windows_native,
            "availability_check": {
                "command": self.availability_check.command,
                "expected_output_pattern": self.availability_check.expected_output_pattern,
            } if self.availability_check else None,
            "installation_guide": {
                "winget_package": self.installation_guide.winget_package,
                "chocolatey_package": self.installation_guide.chocolatey_package,
                "scoop_bucket": self.installation_guide.scoop_bucket,
                "portable_url": self.installation_guide.portable_url,
                "manual_url": self.installation_guide.manual_url,
            } if self.installation_guide else None,
            "version_info": {
                "command": self.version_info.command,
                "output_pattern": self.version_info.output_pattern,
            } if self.version_info else None,
            "environment_variables": [
                {
                    "name": e.name,
                    "purpose": e.purpose,
                    "example_value": e.example_value,
                }
                for e in self.environment_variables
            ],
            "compatibility": {
                "min_windows_build": self.compatibility.min_windows_build,
                "requires_admin": self.compatibility.requires_admin,
                "requires_wsl": self.compatibility.requires_wsl,
                "requires_virtualization": self.compatibility.requires_virtualization,
                "architectures": self.compatibility.architectures,
            },
            "homepage_url": self.homepage_url,
            "documentation_url": self.documentation_url,
            "license": self.license,
            "tags": self.tags,
            "alternative_tools": self.alternative_tools,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        """Create from dictionary."""
        avail_data = data.get("availability_check")
        availability_check = (
            AvailabilityCheck(
                command=avail_data.get("command"),
                expected_output_pattern=avail_data.get("expected_output_pattern"),
            )
            if avail_data
            else None
        )

        install_data = data.get("installation_guide")
        installation_guide = (
            InstallationGuide(
                winget_package=install_data.get("winget_package"),
                chocolatey_package=install_data.get("chocolatey_package"),
                scoop_bucket=install_data.get("scoop_bucket"),
                portable_url=install_data.get("portable_url"),
                manual_url=install_data.get("manual_url"),
            )
            if install_data
            else None
        )

        version_data = data.get("version_info")
        version_info = (
            VersionInfo(
                command=version_data.get("command"),
                output_pattern=version_data.get("output_pattern"),
            )
            if version_data
            else None
        )

        env_vars = [
            EnvironmentRequirement(
                name=e.get("name"),
                purpose=e.get("purpose"),
                example_value=e.get("example_value"),
            )
            for e in data.get("environment_variables", [])
        ]

        compat_data = data.get("compatibility", {})
        compatibility = CompatibilityInfo(
            min_windows_build=compat_data.get("min_windows_build"),
            requires_admin=compat_data.get("requires_admin", False),
            requires_wsl=compat_data.get("requires_wsl", False),
            requires_virtualization=compat_data.get("requires_virtualization", False),
            architectures=compat_data.get("architectures", ["x64", "x86"]),
        )

        return cls(
            id=data.get("id"),
            name=data.get("name"),
            category=data.get("category"),
            description=data.get("description"),
            is_windows_native=data.get("is_windows_native", True),
            availability_check=availability_check,
            installation_guide=installation_guide,
            version_info=version_info,
            environment_variables=env_vars,
            compatibility=compatibility,
            homepage_url=data.get("homepage_url"),
            documentation_url=data.get("documentation_url"),
            license=data.get("license"),
            tags=data.get("tags", []),
            alternative_tools=data.get("alternative_tools", []),
        )
