"""
Capability schema for Windows Dev Agent Plugin.

Defines rich capability definitions with safety levels, intent classes,
dependency requirements, and tool selection strategies.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class IntentClass(str, Enum):
    """Capability intent classification."""
    CODE_ANALYSIS = "code_analysis"
    PLANNING = "planning"
    REFACTOR = "refactor"
    LINT = "lint"
    TEST = "test"
    BUILD = "build"
    DEPENDENCY_UPDATE = "dependency_update"
    DOCUMENT = "document"
    DEBUG = "debug"
    RESEARCH = "research"
    ENVIRONMENT_REPAIR = "environment_repair"
    PACKAGE_INSTALL = "package_install"
    SANDBOX_EXECUTE = "sandbox_execute"


class SafetyLevel(str, Enum):
    """Safety classification for capabilities."""
    AUTONOMOUS = "autonomous"          # Safe read-only or reversible
    APPROVAL_REQUIRED = "approval_required"  # Requires user approval
    FORBIDDEN = "forbidden"           # Always requires explicit permission


class FallbackStrategy(str, Enum):
    """Tool fallback strategy when preferred tool unavailable."""
    WSL = "wsl"                       # Run in WSL
    DEVCONTAINER = "devcontainer"     # Run in dev container
    PORTABLE = "portable"             # Use portable toolkit
    REFUSE = "refuse"                 # Refuse if preferred unavailable


@dataclass
class DependencyCheck:
    """A single dependency requirement."""
    check_type: str  # "tool", "runtime", "permission", "virtualization"
    name: str
    version_constraint: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ToolReference:
    """Reference to a tool implementation."""
    tool_id: str
    priority: int = 0  # Higher priority = preferred


@dataclass
class CapabilityDefinition:
    """Rich definition of a capability."""
    id: str
    name: str
    description: str
    intent_class: IntentClass
    safety_level: SafetyLevel

    # Requirements
    required_context: List[str] = field(default_factory=list)  # "project_type", "runtime", etc.
    dependency_checks: List[DependencyCheck] = field(default_factory=list)

    # Tool selection
    preferred_tools: List[ToolReference] = field(default_factory=list)
    fallback_tools: List[ToolReference] = field(default_factory=list)
    fallback_strategy: FallbackStrategy = FallbackStrategy.REFUSE

    # Verification and rollback
    verification_commands: List[str] = field(default_factory=list)
    rollback_commands: List[str] = field(default_factory=list)

    # Observability
    observability_hooks: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    estimated_duration_seconds: Optional[float] = None
    compatible_platforms: List[str] = field(default_factory=list)  # "windows", "wsl", etc.

    def is_autonomous(self) -> bool:
        """Check if capability can run autonomously."""
        return self.safety_level == SafetyLevel.AUTONOMOUS

    def requires_approval(self) -> bool:
        """Check if capability requires approval."""
        return self.safety_level == SafetyLevel.APPROVAL_REQUIRED

    def is_forbidden(self) -> bool:
        """Check if capability is forbidden."""
        return self.safety_level == SafetyLevel.FORBIDDEN

    def get_all_tools(self) -> List[ToolReference]:
        """Get all tools (preferred + fallback) in priority order."""
        all_tools = self.preferred_tools + self.fallback_tools
        return sorted(all_tools, key=lambda t: -t.priority)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "intent_class": self.intent_class.value,
            "safety_level": self.safety_level.value,
            "required_context": self.required_context,
            "dependency_checks": [
                {
                    "type": dep.check_type,
                    "name": dep.name,
                    "version_constraint": dep.version_constraint,
                }
                for dep in self.dependency_checks
            ],
            "preferred_tools": [{"tool_id": t.tool_id, "priority": t.priority} for t in self.preferred_tools],
            "fallback_tools": [{"tool_id": t.tool_id, "priority": t.priority} for t in self.fallback_tools],
            "fallback_strategy": self.fallback_strategy.value,
            "verification_commands": self.verification_commands,
            "rollback_commands": self.rollback_commands,
            "tags": self.tags,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "compatible_platforms": self.compatible_platforms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityDefinition":
        """Create from dictionary."""
        dependency_checks = [
            DependencyCheck(
                check_type=dep.get("type"),
                name=dep.get("name"),
                version_constraint=dep.get("version_constraint"),
            )
            for dep in data.get("dependency_checks", [])
        ]

        preferred_tools = [
            ToolReference(tool_id=t.get("tool_id"), priority=t.get("priority", 0))
            for t in data.get("preferred_tools", [])
        ]

        fallback_tools = [
            ToolReference(tool_id=t.get("tool_id"), priority=t.get("priority", 0))
            for t in data.get("fallback_tools", [])
        ]

        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            intent_class=IntentClass(data.get("intent_class")),
            safety_level=SafetyLevel(data.get("safety_level")),
            required_context=data.get("required_context", []),
            dependency_checks=dependency_checks,
            preferred_tools=preferred_tools,
            fallback_tools=fallback_tools,
            fallback_strategy=FallbackStrategy(data.get("fallback_strategy", "refuse")),
            verification_commands=data.get("verification_commands", []),
            rollback_commands=data.get("rollback_commands", []),
            observability_hooks=data.get("observability_hooks", []),
            tags=data.get("tags", []),
            estimated_duration_seconds=data.get("estimated_duration_seconds"),
            compatible_platforms=data.get("compatible_platforms", ["windows"]),
        )
