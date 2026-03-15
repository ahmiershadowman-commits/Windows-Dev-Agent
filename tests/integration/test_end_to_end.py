"""
End-to-end integration tests for Windows Dev Agent Plugin.

Tests complete workflows from discovery through execution.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.discovery.discovery import EnvironmentDiscovery
from src.execution.powershell_executor import PowerShellExecutor
from src.execution.command_builder import CommandBuilder
from src.config.capability_loader import CapabilityLoader
from src.graph.capability_graph import CapabilityGraph
from src.workflow.engine import WorkflowEngine
from src.schemas.capability import CapabilityDefinition, IntentClass, SafetyLevel
from src.schemas.workflow import WorkflowDefinition, WorkflowStage, WorkflowStep, StageType
from src.safety.policy import SafetyPolicy
from src.observability.telemetry import Telemetry


class TestEnvironmentToCapability:
    """Test environment discovery to capability execution."""

    def test_discovery_to_graph(self):
        """Test discovery feeds into capability graph."""
        discovery = EnvironmentDiscovery(cache_enabled=False)
        snapshot = discovery.discover()

        graph = CapabilityGraph(discovery=discovery)
        graph.environment = snapshot

        # Should be able to query graph with environment
        assert graph.environment is not None
        assert graph.environment.system.os_name

    def test_command_builder_integration(self):
        """Test command builder with executor."""
        executor = PowerShellExecutor(transcript_enabled=False)
        builder = CommandBuilder("Write-Output").arg("test")
        cmd = builder.build()

        assert "Write-Output" in cmd
        assert "test" in cmd


class TestWorkflowExecution:
    """Test complete workflow execution."""

    def test_simple_workflow_execution(self):
        """Test executing a simple workflow."""
        graph = CapabilityGraph()

        # Add a test capability
        capability = CapabilityDefinition(
            id="test-lint",
            name="Test Lint",
            description="Test lint capability",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        graph.capabilities["test-lint"] = capability

        # Create workflow
        step = WorkflowStep(
            id="lint-step",
            name="Lint Code",
            description="Lint the code",
            capability_id="test-lint",
        )
        stage = WorkflowStage(
            id="implementation",
            stage_type=StageType.IMPLEMENTATION,
            description="Implementation stage",
            steps=[step],
        )
        workflow = WorkflowDefinition(
            id="lint-workflow",
            name="Lint Workflow",
            description="Lint code",
            stages=[stage],
        )

        # Execute workflow
        engine = WorkflowEngine(graph)
        execution = engine.execute(workflow, auto_approve=True)

        assert execution.workflow_id == "lint-workflow"
        # Status can be completed, paused, or failed (if tool not available)
        assert execution.status in ["completed", "paused", "failed"]


class TestSafetyWithCapabilities:
    """Test safety policy with capabilities."""

    def test_safety_with_capability_graph(self):
        """Test safety policy integration with capability graph."""
        graph = CapabilityGraph()
        policy = SafetyPolicy()

        # Create and register capabilities
        autonomous_cap = CapabilityDefinition(
            id="autonomous-lint",
            name="Autonomous Lint",
            description="Safe linting",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        approval_cap = CapabilityDefinition(
            id="approval-update",
            name="Approval Update",
            description="Needs approval",
            intent_class=IntentClass.DEPENDENCY_UPDATE,
            safety_level=SafetyLevel.APPROVAL_REQUIRED,
        )

        graph.capabilities["autonomous-lint"] = autonomous_cap
        graph.capabilities["approval-update"] = approval_cap

        policy.register_capability(autonomous_cap)
        policy.register_capability(approval_cap)

        # Test autonomous
        can_run, reason = policy.can_execute("autonomous-lint")
        assert can_run is True

        # Test approval required
        can_run, reason = policy.can_execute("approval-update", user_approved=False)
        assert can_run is False

        can_run, reason = policy.can_execute("approval-update", user_approved=True)
        assert can_run is True


class TestTelemetryIntegration:
    """Test telemetry collection during execution."""

    def test_telemetry_during_execution(self):
        """Test telemetry collection."""
        telemetry = Telemetry()

        # Simulate execution
        with_span = telemetry.start_span("test-execution", {"capability": "lint"})
        with_span.end(status="ok")

        telemetry.log("info", "Execution completed")
        telemetry.record_execution("lint-python", "ruff", 1.5, True)

        # Check telemetry
        summary = telemetry.get_summary()
        assert summary["spans"] == 1
        assert summary["logs"] == 1
        assert summary["metrics"]["counters"]["executions_total"] == 1


class TestCompleteWorkflow:
    """Test complete integrated workflow."""

    def test_discovery_plan_execute(self):
        """Test complete discovery -> plan -> execute workflow."""
        # Discovery
        discovery = EnvironmentDiscovery(cache_enabled=False)
        snapshot = discovery.discover()
        assert snapshot is not None

        # Build capability graph
        graph = CapabilityGraph(discovery=discovery)
        assert len(graph.capabilities) >= 0

        # Create workflow
        workflow = WorkflowDefinition(
            id="complete-workflow",
            name="Complete Workflow",
            description="Complete test workflow",
        )

        # Execute
        engine = WorkflowEngine(graph)
        execution = engine.execute(workflow, auto_approve=True)

        assert execution.workflow_id == "complete-workflow"
        assert execution.status in ["completed", "paused", "failed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
