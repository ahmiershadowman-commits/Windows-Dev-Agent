"""
Workflow execution engine for Windows Dev Agent Plugin.

Executes workflow definitions with state tracking and approval gates.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..schemas.workflow import WorkflowDefinition, WorkflowStep, StageType
from ..graph.capability_graph import CapabilityGraph

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    step_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class WorkflowExecution:
    """Execution state of a workflow."""
    workflow_id: str
    started_at: datetime
    status: str  # "running", "paused", "completed", "failed", "cancelled"
    steps_completed: Dict[str, StepResult] = None
    current_step: Optional[str] = None
    paused_for_approval: bool = False

    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = {}

    def mark_step_complete(self, result: StepResult):
        """Mark a step as complete."""
        self.steps_completed[result.step_id] = result

    def is_step_complete(self, step_id: str) -> bool:
        """Check if a step is complete."""
        return step_id in self.steps_completed

    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """Get result of a step."""
        return self.steps_completed.get(step_id)


class WorkflowEngine:
    """Executes workflow definitions."""

    def __init__(self, capability_graph: CapabilityGraph):
        self.capability_graph = capability_graph
        self.execution_history: List[WorkflowExecution] = []

    def execute(
        self,
        workflow: WorkflowDefinition,
        auto_approve: bool = False,
    ) -> WorkflowExecution:
        """
        Execute a workflow.

        Args:
            workflow: The workflow definition to execute
            auto_approve: If True, skip approval gates

        Returns:
            WorkflowExecution with final status
        """
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            started_at=datetime.now(),
            status="running",
        )

        logger.info(f"Starting workflow execution: {workflow.id}")

        try:
            # Execute each stage
            for stage in workflow.stages:
                logger.info(f"Executing stage: {stage.id}")

                # Check entry criteria
                if not self._check_criteria(stage.entry_criteria):
                    logger.warning(f"Stage {stage.id} entry criteria not met")
                    if workflow.stop_on_failure:
                        execution.status = "failed"
                        return execution

                # Execute steps in stage
                for step in stage.steps:
                    # Check dependencies
                    if not self._dependencies_met(step, execution):
                        logger.info(f"Skipping step {step.id} (dependencies not met)")
                        continue

                    # Check approval
                    if step.approval_gate and not auto_approve:
                        execution.paused_for_approval = True
                        execution.current_step = step.id
                        execution.status = "paused"
                        logger.info(f"Paused for approval at step: {step.id}")
                        return execution

                    # Execute step
                    result = self._execute_step(step)
                    execution.mark_step_complete(result)

                    if not result.success:
                        logger.error(f"Step {step.id} failed: {result.error}")
                        if workflow.stop_on_failure:
                            execution.status = "failed"
                            return execution

                # Check exit criteria
                if not self._check_criteria(stage.exit_criteria):
                    logger.warning(f"Stage {stage.id} exit criteria not met")
                    if workflow.stop_on_failure:
                        execution.status = "failed"
                        return execution

            execution.status = "completed"
            logger.info(f"Workflow {workflow.id} completed successfully")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = "failed"

        self.execution_history.append(execution)
        return execution

    def resume(
        self,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition,
        approve: bool = True,
    ) -> WorkflowExecution:
        """Resume a paused workflow execution."""
        if execution.status != "paused":
            raise RuntimeError(f"Cannot resume workflow with status {execution.status}")

        if not approve:
            execution.status = "cancelled"
            return execution

        execution.paused_for_approval = False
        # Continue execution from current step
        return self.execute(workflow, auto_approve=True)

    def _execute_step(self, step: WorkflowStep) -> StepResult:
        """Execute a single step."""
        logger.info(f"Executing step: {step.id}")

        # Check if capability can run
        can_run, reason = self.capability_graph.can_run_capability(step.capability_id)
        if not can_run:
            return StepResult(
                step_id=step.id,
                success=False,
                error=f"Cannot run capability: {reason}",
            )

        # Select tool
        capability = self.capability_graph.get_capability(step.capability_id)
        tool, selection_reason = self.capability_graph.select_tool(capability)

        if not tool:
            return StepResult(
                step_id=step.id,
                success=False,
                error=f"No tool available: {selection_reason}",
            )

        logger.info(f"Selected tool {tool.id} for step {step.id}")

        # In a real execution, we would run the tool here
        # For now, simulate success
        return StepResult(
            step_id=step.id,
            success=True,
            output=f"Executed capability {step.capability_id} with tool {tool.id}",
            duration_seconds=1.0,
        )

    def _dependencies_met(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> bool:
        """Check if all step dependencies are met."""
        for dep_id in step.dependencies:
            if not execution.is_step_complete(dep_id):
                return False

            # Check if dependency was successful
            result = execution.get_step_result(dep_id)
            if result and not result.success:
                return False

        return True

    def _check_criteria(self, criteria: List[str]) -> bool:
        """Check if all criteria are met."""
        # For now, assume all criteria are met
        # In a real implementation, evaluate expressions
        return len(criteria) == 0 or all(c for c in criteria)

    def get_execution_history(self) -> List[WorkflowExecution]:
        """Get execution history."""
        return self.execution_history.copy()
