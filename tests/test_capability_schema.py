"""
Tests for capability and tool schemas.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schemas.capability import (
    CapabilityDefinition,
    IntentClass,
    SafetyLevel,
    ToolReference,
    DependencyCheck,
    FallbackStrategy,
)
from src.schemas.tool import (
    ToolDefinition,
    AvailabilityCheck,
    InstallationGuide,
    VersionInfo,
    EnvironmentRequirement,
    CompatibilityInfo,
)
from src.config.capability_loader import CapabilityLoader
from src.graph.capability_graph import CapabilityGraph


class TestCapabilitySchema:
    """Test capability schema definitions."""

    def test_capability_creation(self):
        """Test creating a capability."""
        cap = CapabilityDefinition(
            id="lint-python",
            name="Lint Python",
            description="Lint Python code",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        assert cap.id == "lint-python"
        assert cap.intent_class == IntentClass.LINT

    def test_capability_safety_checks(self):
        """Test capability safety level checks."""
        autonomous_cap = CapabilityDefinition(
            id="test1",
            name="Test",
            description="Test",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        assert autonomous_cap.is_autonomous()
        assert not autonomous_cap.requires_approval()

        approval_cap = CapabilityDefinition(
            id="test2",
            name="Test",
            description="Test",
            intent_class=IntentClass.DEPENDENCY_UPDATE,
            safety_level=SafetyLevel.APPROVAL_REQUIRED,
        )
        assert approval_cap.requires_approval()
        assert not approval_cap.is_autonomous()

    def test_capability_with_tools(self):
        """Test capability with tool references."""
        cap = CapabilityDefinition(
            id="lint",
            name="Lint",
            description="Lint",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
            preferred_tools=[
                ToolReference(tool_id="ruff", priority=10),
                ToolReference(tool_id="pylint", priority=5),
            ],
        )
        tools = cap.get_all_tools()
        assert len(tools) == 2
        assert tools[0].tool_id == "ruff"  # Highest priority first

    def test_capability_to_dict(self):
        """Test capability serialization."""
        cap = CapabilityDefinition(
            id="test",
            name="Test",
            description="Test capability",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        d = cap.to_dict()
        assert d["id"] == "test"
        assert d["intent_class"] == "test"
        assert d["safety_level"] == "autonomous"

    def test_capability_from_dict(self):
        """Test capability deserialization."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test capability",
            "intent_class": "test",
            "safety_level": "autonomous",
        }
        cap = CapabilityDefinition.from_dict(data)
        assert cap.id == "test"
        assert cap.intent_class == IntentClass.TEST


class TestToolSchema:
    """Test tool schema definitions."""

    def test_tool_creation(self):
        """Test creating a tool."""
        tool = ToolDefinition(
            id="ruff",
            name="Ruff",
            category="linter",
            description="Python linter",
            is_windows_native=False,
        )
        assert tool.id == "ruff"
        assert not tool.is_windows_native

    def test_tool_windows_native(self):
        """Test Windows native tool flag."""
        windows_tool = ToolDefinition(
            id="msbuild",
            name="MSBuild",
            category="builder",
            description="MSBuild",
            is_windows_native=True,
        )
        assert windows_tool.is_native_windows()

    def test_tool_with_availability(self):
        """Test tool with availability check."""
        tool = ToolDefinition(
            id="ruff",
            name="Ruff",
            category="linter",
            description="Ruff",
            availability_check=AvailabilityCheck(
                command="ruff --version",
                expected_output_pattern=r"ruff \d+\.\d+",
            ),
        )
        assert tool.availability_check is not None
        assert tool.availability_check.command == "ruff --version"

    def test_tool_with_installation(self):
        """Test tool with installation guide."""
        tool = ToolDefinition(
            id="ruff",
            name="Ruff",
            category="linter",
            description="Ruff",
            installation_guide=InstallationGuide(
                winget_package="ruff",
                manual_url="https://github.com/astral-sh/ruff",
            ),
        )
        assert tool.installation_guide.winget_package == "ruff"

    def test_tool_compatibility(self):
        """Test tool compatibility info."""
        tool = ToolDefinition(
            id="dotnet",
            name=".NET",
            category="runtime",
            description=".NET runtime",
            compatibility=CompatibilityInfo(
                min_windows_build=19041,
                requires_admin=False,
                architectures=["x64"],
            ),
        )
        assert tool.compatibility.min_windows_build == 19041
        assert "x64" in tool.compatibility.architectures

    def test_tool_to_dict(self):
        """Test tool serialization."""
        tool = ToolDefinition(
            id="test",
            name="Test Tool",
            category="utility",
            description="Test",
        )
        d = tool.to_dict()
        assert d["id"] == "test"
        assert d["category"] == "utility"

    def test_tool_from_dict(self):
        """Test tool deserialization."""
        data = {
            "id": "test",
            "name": "Test",
            "category": "utility",
            "description": "Test tool",
        }
        tool = ToolDefinition.from_dict(data)
        assert tool.id == "test"


class TestCapabilityLoader:
    """Test capability configuration loader."""

    def test_loader_creation(self, tmp_path):
        """Test creating a loader."""
        loader = CapabilityLoader(config_dir=tmp_path)
        assert loader.config_dir == tmp_path

    def test_backward_compatibility(self):
        """Test loading old flat YAML format."""
        loader = CapabilityLoader()
        # Create old-style capability definition
        old_format = {
            "description": "Lint Python code",
            "tools": [
                {"name": "ruff", "command": "ruff .", "check": "ruff --version"},
                {"name": "pylint", "command": "pylint .", "check": "pylint --version"},
            ],
        }

        cap = loader._convert_old_format("lint-python", old_format)
        assert cap.id == "lint-python"
        assert cap.intent_class == IntentClass.LINT
        assert len(cap.preferred_tools) > 0

    def test_get_capability(self):
        """Test retrieving a capability."""
        loader = CapabilityLoader()
        loader.capabilities["test"] = CapabilityDefinition(
            id="test",
            name="Test",
            description="Test",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        cap = loader.get_capability("test")
        assert cap is not None
        assert cap.id == "test"

    def test_get_capabilities_by_intent(self):
        """Test filtering capabilities by intent."""
        loader = CapabilityLoader()
        loader.capabilities["lint1"] = CapabilityDefinition(
            id="lint1",
            name="Lint 1",
            description="Lint",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        loader.capabilities["test1"] = CapabilityDefinition(
            id="test1",
            name="Test 1",
            description="Test",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.AUTONOMOUS,
        )

        linters = loader.get_capabilities_by_intent(IntentClass.LINT)
        assert len(linters) == 1
        assert linters[0].id == "lint1"

    def test_get_autonomous_capabilities(self):
        """Test filtering autonomous capabilities."""
        loader = CapabilityLoader()
        loader.capabilities["auto"] = CapabilityDefinition(
            id="auto",
            name="Auto",
            description="Auto",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        loader.capabilities["approval"] = CapabilityDefinition(
            id="approval",
            name="Approval",
            description="Approval",
            intent_class=IntentClass.DEPENDENCY_UPDATE,
            safety_level=SafetyLevel.APPROVAL_REQUIRED,
        )

        autonomous = loader.get_autonomous_capabilities()
        assert len(autonomous) == 1
        assert autonomous[0].id == "auto"


class TestCapabilityGraph:
    """Test capability graph and tool selection."""

    def test_graph_creation(self):
        """Test creating a capability graph."""
        graph = CapabilityGraph()
        assert graph.capabilities is not None
        assert graph.tools is not None

    def test_get_capability(self):
        """Test retrieving capability from graph."""
        graph = CapabilityGraph()
        graph.capabilities["test"] = CapabilityDefinition(
            id="test",
            name="Test",
            description="Test",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        cap = graph.get_capability("test")
        assert cap is not None

    def test_estimate_safety(self):
        """Test safety estimation."""
        graph = CapabilityGraph()
        graph.capabilities["auto"] = CapabilityDefinition(
            id="auto",
            name="Auto",
            description="Auto",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )

        safety = graph.estimate_safety("auto")
        assert safety == SafetyLevel.AUTONOMOUS

    def test_capability_not_found(self):
        """Test handling missing capability."""
        graph = CapabilityGraph()
        cap = graph.get_capability("nonexistent")
        assert cap is None

    def test_get_executable_capabilities(self):
        """Test getting executable capabilities."""
        graph = CapabilityGraph()
        # Refresh to populate environment
        graph.refresh_environment()

        # Should return list (even if empty on non-Windows)
        executable = graph.get_executable_capabilities()
        assert isinstance(executable, list)

    def test_get_unavailable_capabilities(self):
        """Test getting unavailable capabilities."""
        graph = CapabilityGraph()
        graph.refresh_environment()

        # Should return list of tuples
        unavailable = graph.get_unavailable_capabilities()
        assert isinstance(unavailable, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
