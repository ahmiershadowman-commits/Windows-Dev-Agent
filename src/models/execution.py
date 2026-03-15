"""
Execution result models for the Windows Dev Agent Plugin.

Defines dataclasses for command execution results and traces.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class ExecutionResult:
    """Result of a command execution."""

    returncode: int
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    command: str = ""
    succeeded: bool = False

    def __post_init__(self):
        """Set succeeded status based on returncode."""
        if not hasattr(self, '_succeeded_set'):
            self.succeeded = self.returncode == 0
            self._succeeded_set = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "command": self.command,
            "succeeded": self.succeeded,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ExecutionTrace:
    """Audit trace for a single execution."""

    timestamp: datetime
    command: str
    tool_name: Optional[str] = None
    exit_code: int = 0
    stdout_size_bytes: int = 0
    stderr_size_bytes: int = 0
    duration_seconds: float = 0.0
    environment_variables: Dict[str, str] = field(default_factory=dict)
    elevated: bool = False
    sandbox_type: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
            "tool_name": self.tool_name,
            "exit_code": self.exit_code,
            "stdout_size_bytes": self.stdout_size_bytes,
            "stderr_size_bytes": self.stderr_size_bytes,
            "duration_seconds": self.duration_seconds,
            "elevated": self.elevated,
            "sandbox_type": self.sandbox_type,
            "success": self.success,
            "error_message": self.error_message,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionTrace":
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        return cls(
            timestamp=timestamp,
            command=data.get("command", ""),
            tool_name=data.get("tool_name"),
            exit_code=data.get("exit_code", 0),
            stdout_size_bytes=data.get("stdout_size_bytes", 0),
            stderr_size_bytes=data.get("stderr_size_bytes", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            environment_variables=data.get("environment_variables", {}),
            elevated=data.get("elevated", False),
            sandbox_type=data.get("sandbox_type"),
            success=data.get("success", False),
            error_message=data.get("error_message"),
        )


@dataclass
class ExecutionPlan:
    """Plan for executing a sequence of commands."""

    name: str
    description: str = ""
    commands: list = field(default_factory=list)
    sequential: bool = True  # If False, commands can run in parallel
    stop_on_failure: bool = True
    timeout_seconds: Optional[float] = None
    sandbox_type: Optional[str] = None
    elevation_required: bool = False
    approval_required: bool = False


class ExecutionError(Exception):
    """Raised when execution fails."""
    pass


class ExecutionTimeout(ExecutionError):
    """Raised when execution times out."""
    pass


class ExecutionCancelled(ExecutionError):
    """Raised when execution is cancelled."""
    pass
