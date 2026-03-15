"""
Capability graph for intelligent tool selection.

Manages capability definitions, tool availability, and routing decisions.
"""

import logging
from typing import List, Optional, Tuple

from ..config.capability_loader import CapabilityLoader
from ..schemas.capability import CapabilityDefinition, SafetyLevel
from ..schemas.tool import ToolDefinition
from ..discovery.discovery import EnvironmentDiscovery, EnvironmentSnapshot
from ..execution.powershell_executor import PowerShellExecutor

logger = logging.getLogger(__name__)


class ToolSelectionError(Exception):
    """Raised when tool selection fails."""
    pass


class CapabilityGraph:
    """Manages capabilities, tools, and selection logic."""

    def __init__(
        self,
        loader: Optional[CapabilityLoader] = None,
        discovery: Optional[EnvironmentDiscovery] = None,
    ):
        self.loader = loader or CapabilityLoader()
        self.discovery = discovery or EnvironmentDiscovery()
        self.environment: Optional[EnvironmentSnapshot] = None

        # Load all definitions
        self.capabilities, self.tools = self.loader.load_all()

    def refresh_environment(self) -> EnvironmentSnapshot:
        """Refresh environment discovery."""
        self.environment = self.discovery.discover()
        return self.environment

    def get_capability(self, cap_id: str) -> Optional[CapabilityDefinition]:
        """Get capability by ID."""
        return self.capabilities.get(cap_id)

    def select_tool(
        self,
        capability: CapabilityDefinition,
        allow_fallback: bool = True,
    ) -> Optional[Tuple[ToolDefinition, str]]:
        """
        Select the best available tool for a capability.

        Returns:
            Tuple of (ToolDefinition, reason) or None if no tool available.
        """
        if not self.environment:
            self.refresh_environment()

        # Try preferred tools first
        for tool_ref in capability.preferred_tools:
            tool = self.tools.get(tool_ref.tool_id)
            if tool and self._tool_available(tool):
                logger.info(
                    f"Selected tool {tool.id} for capability {capability.id} (preferred)"
                )
                return tool, "preferred_tool_available"

        # Try fallback tools if allowed
        if allow_fallback:
            for tool_ref in capability.fallback_tools:
                tool = self.tools.get(tool_ref.tool_id)
                if tool and self._tool_available(tool):
                    logger.info(
                        f"Selected tool {tool.id} for capability {capability.id} (fallback)"
                    )
                    return tool, "fallback_tool_available"

        logger.warning(f"No available tools for capability {capability.id}")
        return None

    def _tool_available(self, tool: ToolDefinition) -> bool:
        """Check if a tool is available in the current environment."""
        if not self.environment:
            return False

        # Check native Windows preference
        if tool.is_windows_native and not self.environment.system.os_name:
            return False

        # Check virtualization requirements
        if tool.compatibility.requires_virtualization:
            isolation_options = self.environment.virtualization.get_available_isolation_options()
            if not isolation_options:
                return False

        # Check architecture support
        if self.environment.system.architecture and tool.compatibility.architectures:
            if not any(
                arch.lower() in self.environment.system.architecture.lower()
                for arch in tool.compatibility.architectures
            ):
                return False

        # Check Windows build requirement
        if tool.compatibility.min_windows_build:
            try:
                current_build = int(self.environment.system.os_build)
                if current_build < tool.compatibility.min_windows_build:
                    return False
            except (ValueError, TypeError):
                pass

        return True

    def can_run_capability(self, capability_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a capability can be executed.

        Returns:
            Tuple of (can_run, reason_if_not).
        """
        capability = self.get_capability(capability_id)
        if not capability:
            return False, f"Capability {capability_id} not found"

        # Check if tool is available
        tool, reason = self.select_tool(capability)
        if not tool:
            return False, f"No available tool for {capability_id}"

        # Check if all dependencies are met
        for dep in capability.dependency_checks:
            if not self._check_dependency(dep):
                return False, f"Dependency not met: {dep.name}"

        return True, None

    def _check_dependency(self, dep) -> bool:
        """Check if a dependency is satisfied."""
        if dep.check_type == "runtime":
            available = self.environment.runtimes.get_available_runtimes()
            return dep.name in available
        elif dep.check_type == "tool":
            tool = self.tools.get(dep.name)
            return tool and self._tool_available(tool)
        elif dep.check_type == "virtualization":
            options = self.environment.virtualization.get_available_isolation_options()
            return dep.name in options
        return True

    def get_executable_capabilities(self) -> List[str]:
        """Get list of capability IDs that can currently run."""
        executable = []
        for cap_id, capability in self.capabilities.items():
            can_run, _ = self.can_run_capability(cap_id)
            if can_run:
                executable.append(cap_id)
        return executable

    def get_unavailable_capabilities(self) -> List[Tuple[str, str]]:
        """Get list of capabilities and reasons why they can't run."""
        unavailable = []
        for cap_id in self.capabilities:
            can_run, reason = self.can_run_capability(cap_id)
            if not can_run:
                unavailable.append((cap_id, reason or "Unknown"))
        return unavailable

    def estimate_safety(self, capability_id: str) -> SafetyLevel:
        """Estimate the safety level of running a capability."""
        capability = self.get_capability(capability_id)
        if not capability:
            return SafetyLevel.FORBIDDEN

        return capability.safety_level

    def to_json(self) -> dict:
        """Export graph as JSON for analysis."""
        return {
            "capabilities": {
                cap_id: cap.to_dict() for cap_id, cap in self.capabilities.items()
            },
            "tools": {tool_id: tool.to_dict() for tool_id, tool in self.tools.items()},
            "environment": (
                self.environment.to_dict() if self.environment else None
            ),
        }
