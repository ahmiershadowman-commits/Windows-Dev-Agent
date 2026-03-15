"""
Capability and tool configuration loader.

Loads YAML configurations and validates against schemas.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ..schemas.capability import CapabilityDefinition, IntentClass, SafetyLevel
from ..schemas.tool import ToolDefinition
from ..discovery.discovery import EnvironmentDiscovery

logger = logging.getLogger(__name__)


class CapabilityLoadError(Exception):
    """Raised when capability loading fails."""
    pass


class CapabilityLoader:
    """Loads and validates capability and tool configurations."""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent.parent.parent / "config"
        self.capabilities: Dict[str, CapabilityDefinition] = {}
        self.tools: Dict[str, ToolDefinition] = {}
        self.discovery = EnvironmentDiscovery()

    def load_all(self) -> tuple[Dict[str, CapabilityDefinition], Dict[str, ToolDefinition]]:
        """Load all configurations."""
        self.load_capabilities()
        self.load_tools()
        return self.capabilities, self.tools

    def load_capabilities(self, from_file: Optional[Path] = None):
        """Load capability definitions from YAML."""
        filepath = from_file or self.config_dir / "capabilities.yaml"

        if not filepath.exists():
            logger.warning(f"Capability file not found: {filepath}")
            return

        try:
            with open(filepath) as f:
                data = yaml.safe_load(f) or {}

            # Handle both old flat format and new structured format
            for cap_id, cap_def in data.items():
                if isinstance(cap_def, dict):
                    if "intent_class" in cap_def:
                        # New structured format
                        cap = CapabilityDefinition.from_dict({"id": cap_id, **cap_def})
                    else:
                        # Old flat format - convert
                        cap = self._convert_old_format(cap_id, cap_def)

                    self.capabilities[cap_id] = cap

            logger.info(f"Loaded {len(self.capabilities)} capabilities")

        except Exception as e:
            raise CapabilityLoadError(f"Failed to load capabilities: {e}") from e

    def load_tools(self, from_file: Optional[Path] = None):
        """Load tool definitions from YAML."""
        filepath = from_file or self.config_dir / "tools.yaml"

        if not filepath.exists():
            logger.debug(f"Tool file not found: {filepath}")
            return

        try:
            with open(filepath) as f:
                data = yaml.safe_load(f) or {}

            for tool_id, tool_def in data.items():
                if isinstance(tool_def, dict):
                    tool = ToolDefinition.from_dict({"id": tool_id, **tool_def})
                    self.tools[tool_id] = tool

            logger.info(f"Loaded {len(self.tools)} tools")

        except Exception as e:
            raise CapabilityLoadError(f"Failed to load tools: {e}") from e

    def _convert_old_format(self, cap_id: str, cap_def: dict) -> CapabilityDefinition:
        """Convert old flat YAML format to new structured format."""
        # Old format: name, description, tools list
        # New format: capability with intent class, safety level, tool references

        # Map old capability names to intent classes
        intent_mapping = {
            "lint": IntentClass.LINT,
            "test": IntentClass.TEST,
            "format": IntentClass.LINT,
            "dependency": IntentClass.DEPENDENCY_UPDATE,
            "build": IntentClass.BUILD,
            "debug": IntentClass.DEBUG,
            "document": IntentClass.DOCUMENT,
        }

        intent_class = IntentClass.CODE_ANALYSIS  # default
        for keyword, intent in intent_mapping.items():
            if keyword in cap_id.lower() or keyword in cap_def.get("description", "").lower():
                intent_class = intent
                break

        # Convert tools list to tool references
        preferred_tools = []
        fallback_tools = []
        for i, tool_def in enumerate(cap_def.get("tools", [])):
            tool_id = tool_def.get("name", "").lower().replace(" ", "_")
            if i == 0:
                preferred_tools.append(
                    __import__("src.schemas.capability", fromlist=["ToolReference"]).ToolReference(
                        tool_id=tool_id, priority=10 - i
                    )
                )
            else:
                fallback_tools.append(
                    __import__("src.schemas.capability", fromlist=["ToolReference"]).ToolReference(
                        tool_id=tool_id, priority=10 - i
                    )
                )

        return CapabilityDefinition(
            id=cap_id,
            name=cap_id.replace("-", " ").title(),
            description=cap_def.get("description", ""),
            intent_class=intent_class,
            safety_level=SafetyLevel.AUTONOMOUS,  # Default for old format
            preferred_tools=preferred_tools,
            fallback_tools=fallback_tools,
        )

    def save_capabilities(self, to_file: Optional[Path] = None):
        """Save capability definitions to YAML."""
        filepath = to_file or self.config_dir / "capabilities-new.yaml"

        try:
            data = {cap_id: cap.to_dict() for cap_id, cap in self.capabilities.items()}

            with open(filepath, "w") as f:
                yaml.dump(data, f, default_flow_style=False)

            logger.info(f"Saved {len(self.capabilities)} capabilities to {filepath}")

        except Exception as e:
            raise CapabilityLoadError(f"Failed to save capabilities: {e}") from e

    def save_capabilities_json(self, to_file: Optional[Path] = None):
        """Export capabilities as JSON for analysis."""
        filepath = to_file or self.config_dir / "capabilities.json"

        try:
            data = {cap_id: cap.to_dict() for cap_id, cap in self.capabilities.items()}

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported {len(self.capabilities)} capabilities to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")

    def get_capability(self, cap_id: str) -> Optional[CapabilityDefinition]:
        """Get a capability by ID."""
        return self.capabilities.get(cap_id)

    def get_capabilities_by_intent(self, intent_class: IntentClass) -> List[CapabilityDefinition]:
        """Get all capabilities with a specific intent class."""
        return [cap for cap in self.capabilities.values() if cap.intent_class == intent_class]

    def get_autonomous_capabilities(self) -> List[CapabilityDefinition]:
        """Get all autonomous (safe) capabilities."""
        return [cap for cap in self.capabilities.values() if cap.is_autonomous()]

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get a tool by ID."""
        return self.tools.get(tool_id)

    def get_native_windows_tools(self) -> List[ToolDefinition]:
        """Get all Windows-native tools."""
        return [tool for tool in self.tools.values() if tool.is_windows_native]
