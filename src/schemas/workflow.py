"""
Workflow DSL schema for Windows Dev Agent Plugin.

Defines declarative workflow structures for orchestrating capabilities.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class StageType(str, Enum):
    """Workflow stage types."""
    DISCOVERY = "discovery"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    INTEGRATION = "integration"


@dataclass
class ApprovalGate:
    """User approval requirement."""
    title: str
    description: str
    default_approved: bool = False


@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    id: str
    name: str
    description: str
    capability_id: str  # Reference to a capability

    # Conditions
    skip_if: Optional[str] = None  # Condition to skip this step
    dependencies: List[str] = field(default_factory=list)  # IDs of previous steps

    # Control
    approval_gate: Optional[ApprovalGate] = None
    timeout_seconds: Optional[float] = None
    retry_on_failure: bool = False
    max_retries: int = 3


@dataclass
class WorkflowStage:
    """Workflow stage with multiple steps."""
    id: str
    stage_type: StageType
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)

    # Conditions
    entry_criteria: List[str] = field(default_factory=list)  # Must all be true
    exit_criteria: List[str] = field(default_factory=list)   # Must all be true


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    id: str
    name: str
    description: str
    version: str = "1.0"

    stages: List[WorkflowStage] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_date: Optional[str] = None
    estimated_duration_seconds: Optional[float] = None

    # Configuration
    sequential: bool = True  # Run stages sequentially
    stop_on_failure: bool = True
    rollback_on_failure: bool = True

    def get_stage(self, stage_id: str) -> Optional[WorkflowStage]:
        """Get stage by ID."""
        return next((s for s in self.stages if s.id == stage_id), None)

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID across all stages."""
        for stage in self.stages:
            for step in stage.steps:
                if step.id == step_id:
                    return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "stages": [
                {
                    "id": stage.id,
                    "type": stage.stage_type.value,
                    "description": stage.description,
                    "steps": [
                        {
                            "id": step.id,
                            "name": step.name,
                            "description": step.description,
                            "capability_id": step.capability_id,
                            "dependencies": step.dependencies,
                            "approval_gate": {
                                "title": step.approval_gate.title,
                                "description": step.approval_gate.description,
                            } if step.approval_gate else None,
                            "timeout_seconds": step.timeout_seconds,
                            "retry_on_failure": step.retry_on_failure,
                            "max_retries": step.max_retries,
                        }
                        for step in stage.steps
                    ],
                    "entry_criteria": stage.entry_criteria,
                    "exit_criteria": stage.exit_criteria,
                }
                for stage in self.stages
            ],
            "tags": self.tags,
            "author": self.author,
            "sequential": self.sequential,
            "stop_on_failure": self.stop_on_failure,
            "rollback_on_failure": self.rollback_on_failure,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDefinition":
        """Create from dictionary."""
        stages = []
        for stage_data in data.get("stages", []):
            steps = [
                WorkflowStep(
                    id=step.get("id"),
                    name=step.get("name"),
                    description=step.get("description"),
                    capability_id=step.get("capability_id"),
                    skip_if=step.get("skip_if"),
                    dependencies=step.get("dependencies", []),
                    approval_gate=(
                        ApprovalGate(
                            title=gate.get("title"),
                            description=gate.get("description"),
                        )
                        if (gate := step.get("approval_gate"))
                        else None
                    ),
                    timeout_seconds=step.get("timeout_seconds"),
                    retry_on_failure=step.get("retry_on_failure", False),
                    max_retries=step.get("max_retries", 3),
                )
                for step in stage_data.get("steps", [])
            ]

            stages.append(
                WorkflowStage(
                    id=stage_data.get("id"),
                    stage_type=StageType(stage_data.get("type")),
                    description=stage_data.get("description"),
                    steps=steps,
                    entry_criteria=stage_data.get("entry_criteria", []),
                    exit_criteria=stage_data.get("exit_criteria", []),
                )
            )

        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version", "1.0"),
            stages=stages,
            tags=data.get("tags", []),
            author=data.get("author"),
            created_date=data.get("created_date"),
            estimated_duration_seconds=data.get("estimated_duration_seconds"),
            sequential=data.get("sequential", True),
            stop_on_failure=data.get("stop_on_failure", True),
            rollback_on_failure=data.get("rollback_on_failure", True),
        )
