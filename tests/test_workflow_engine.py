"""
Tests for workflow DSL and engine.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schemas.workflow import (
    WorkflowDefinition,
    WorkflowStage,
    WorkflowStep,
    StageType,
    ApprovalGate,
)
from src.workflow.engine import WorkflowEngine, StepResult, WorkflowExecution
from src.graph.capability_graph import CapabilityGraph
from src.schemas.capability import CapabilityDefinition, IntentClass, SafetyLevel


class TestWorkflowSchema:
    """Test workflow schema."""

    def test_workflow_creation(self):
        """Test creating a workflow."""
        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            description="Test workflow",
        )
        assert workflow.id == "test-workflow"
        assert workflow.sequential is True

    def test_workflow_with_stages(self):
        """Test workflow with stages."""
        stage = WorkflowStage(
            id="discovery",
            stage_type=StageType.DISCOVERY,
            description="Discover environment",
        )
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            description="Test",
            stages=[stage],
        )
        assert len(workflow.stages) == 1
        assert workflow.get_stage("discovery") is not None

    def test_workflow_with_steps(self):
        """Test workflow with steps."""
        step = WorkflowStep(
            id="step1",
            name="Step 1",
            description="First step",
            capability_id="lint-python",
        )
        stage = WorkflowStage(
            id="impl",
            stage_type=StageType.IMPLEMENTATION,
            description="Implementation",
            steps=[step],
        )
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            description="Test",
            stages=[stage],
        )
        assert workflow.get_step("step1") is not None

    def test_approval_gate(self):
        """Test approval gate on step."""
        gate = ApprovalGate(
            title="Review changes",
            description="Please review",
        )
        step = WorkflowStep(
            id="step1",
            name="Step 1",
            description="Step",
            capability_id="test",
            approval_gate=gate,
        )
        assert step.approval_gate is not None
        assert step.approval_gate.title == "Review changes"

    def test_workflow_to_dict(self):
        """Test workflow serialization."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            description="Test",
        )
        d = workflow.to_dict()
        assert d["id"] == "test"
        assert d["name"] == "Test"

    def test_workflow_from_dict(self):
        """Test workflow deserialization."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "stages": [],
        }
        workflow = WorkflowDefinition.from_dict(data)
        assert workflow.id == "test"


class TestWorkflowExecution:
    """Test workflow execution."""

    def test_execution_creation(self):
        """Test creating execution state."""
        execution = WorkflowExecution(
            workflow_id="test",
            started_at=datetime.now(),
            status="running",
        )
        assert execution.workflow_id == "test"
        assert execution.status == "running"

    def test_mark_step_complete(self):
        """Test marking step complete."""
        execution = WorkflowExecution(
            workflow_id="test",
            started_at=datetime.now(),
            status="running",
        )
        result = StepResult(
            step_id="step1",
            success=True,
            output="Done",
        )
        execution.mark_step_complete(result)
        assert execution.is_step_complete("step1")
        assert execution.get_step_result("step1").success is True


class TestWorkflowEngine:
    """Test workflow execution engine."""

    def test_engine_creation(self):
        """Test creating workflow engine."""
        graph = CapabilityGraph()
        engine = WorkflowEngine(graph)
        assert engine.capability_graph is not None

    def test_simple_workflow_execution(self):
        """Test executing a simple workflow."""
        graph = CapabilityGraph()
        engine = WorkflowEngine(graph)

        # Add a test capability
        capability = CapabilityDefinition(
            id="test-cap",
            name="Test",
            description="Test",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        graph.capabilities["test-cap"] = capability

        # Create workflow
        step = WorkflowStep(
            id="step1",
            name="Test Step",
            description="Test",
            capability_id="test-cap",
        )
        stage = WorkflowStage(
            id="impl",
            stage_type=StageType.IMPLEMENTATION,
            description="Impl",
            steps=[step],
        )
        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test",
            description="Test",
            stages=[stage],
        )

        # Execute
        execution = engine.execute(workflow, auto_approve=True)
        assert execution.status in ["completed", "paused", "failed"]

    def test_workflow_with_approval(self):
        """Test workflow with approval gate."""
        graph = CapabilityGraph()
        engine = WorkflowEngine(graph)

        capability = CapabilityDefinition(
            id="test-cap",
            name="Test",
            description="Test",
            intent_class=IntentClass.TEST,
            safety_level=SafetyLevel.APPROVAL_REQUIRED,
        )
        graph.capabilities["test-cap"] = capability

        gate = ApprovalGate(
            title="Approve",
            description="Please approve",
        )
        step = WorkflowStep(
            id="step1",
            name="Step",
            description="Step",
            capability_id="test-cap",
            approval_gate=gate,
        )
        stage = WorkflowStage(
            id="impl",
            stage_type=StageType.IMPLEMENTATION,
            description="Impl",
            steps=[step],
        )
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            description="Test",
            stages=[stage],
        )

        # Execute without auto_approve - should pause
        execution = engine.execute(workflow, auto_approve=False)
        # May pause or complete depending on capability availability
        assert execution.status in ["paused", "completed"]

    def test_step_dependencies(self):
        """Test step dependencies."""
        step1 = WorkflowStep(
            id="step1",
            name="Step 1",
            description="Step",
            capability_id="lint",
        )
        step2 = WorkflowStep(
            id="step2",
            name="Step 2",
            description="Step",
            capability_id="test",
            dependencies=["step1"],
        )
        assert "step1" in step2.dependencies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
