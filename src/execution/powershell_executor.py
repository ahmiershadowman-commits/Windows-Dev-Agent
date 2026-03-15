"""
PowerShell execution service for the Windows Dev Agent Plugin.

Provides structured command execution via PowerShell with logging and error handling.
"""

import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..models.execution import ExecutionResult, ExecutionTrace, ExecutionError, ExecutionTimeout
from .command_builder import CommandBuilder

logger = logging.getLogger(__name__)

# Transcript log file
TRANSCRIPT_FILE = Path(__file__).parent.parent.parent / ".logs" / "powershell_transcript.txt"


class PowerShellExecutor:
    """Executes PowerShell commands with structured output and error handling."""

    def __init__(self, transcript_enabled: bool = True, timeout_seconds: float = 300):
        self.transcript_enabled = transcript_enabled
        self.timeout_seconds = timeout_seconds
        self.execution_traces: List[ExecutionTrace] = []

        if transcript_enabled:
            TRANSCRIPT_FILE.parent.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        command: str,
        tool_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        elevated: bool = False,
    ) -> ExecutionResult:
        """
        Execute a PowerShell command.

        Args:
            command: The PowerShell command to execute.
            tool_name: Optional name of the tool being executed (for logging).
            timeout_seconds: Command timeout (uses instance default if not provided).
            environment_variables: Additional environment variables.
            elevated: If True, attempt to run with elevated privileges.

        Returns:
            ExecutionResult with returncode, stdout, stderr, and duration.

        Raises:
            ExecutionTimeout: If command exceeds timeout.
            ExecutionError: If execution fails for other reasons.
        """
        timeout = timeout_seconds or self.timeout_seconds
        start_time = time.time()

        try:
            # Prepare PowerShell invocation
            ps_args = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ]

            # Setup environment
            env = dict(os.environ) if hasattr(os, 'environ') else {}
            if environment_variables:
                env.update(environment_variables)

            # Log execution start
            logger.info(f"Executing command: {command[:100]}..." if len(command) > 100 else f"Executing: {command}")

            # Run PowerShell
            result = subprocess.run(
                ps_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )

            duration = time.time() - start_time

            # Create result
            exec_result = ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_seconds=duration,
                command=command,
                succeeded=result.returncode == 0,
            )

            # Log execution
            self._log_execution(
                command,
                tool_name,
                result.returncode,
                result.stdout,
                result.stderr,
                duration,
                elevated,
            )

            # Log transcript
            if self.transcript_enabled:
                self._write_transcript(exec_result)

            logger.info(
                f"Command completed with exit code {result.returncode} in {duration:.2f}s"
            )

            return exec_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"Command timed out after {duration:.2f}s")
            raise ExecutionTimeout(f"Command timed out after {timeout}s") from None
        except FileNotFoundError:
            logger.warning("PowerShell executable not found; command not executed")
            raise ExecutionError("PowerShell not available on this system") from None
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise ExecutionError(f"Execution failed: {e}") from e

    def execute_builder(
        self,
        builder: CommandBuilder,
        tool_name: Optional[str] = None,
        **kwargs,
    ) -> ExecutionResult:
        """Execute a command built with CommandBuilder."""
        command = builder.build()
        return self.execute(command, tool_name=tool_name, **kwargs)

    def execute_script(
        self,
        script_path: str,
        *args,
        tool_name: Optional[str] = None,
        **kwargs,
    ) -> ExecutionResult:
        """Execute a PowerShell script."""
        script_path = Path(script_path)
        if not script_path.exists():
            raise ExecutionError(f"Script not found: {script_path}")

        # Build command to invoke script
        ps_args = [f"& {CommandBuilder.quote(str(script_path))}"]
        for arg in args:
            ps_args.append(CommandBuilder.quote(str(arg)))

        command = " ".join(ps_args)
        return self.execute(command, tool_name=tool_name, **kwargs)

    def _log_execution(
        self,
        command: str,
        tool_name: Optional[str],
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
        elevated: bool,
    ):
        """Create and store an execution trace."""
        trace = ExecutionTrace(
            timestamp=datetime.now(),
            command=command,
            tool_name=tool_name,
            exit_code=exit_code,
            stdout_size_bytes=len(stdout),
            stderr_size_bytes=len(stderr),
            duration_seconds=duration,
            elevated=elevated,
            success=exit_code == 0,
            error_message=stderr if exit_code != 0 else None,
        )
        self.execution_traces.append(trace)
        logger.debug(f"Execution trace: {trace}")

    def _write_transcript(self, result: ExecutionResult):
        """Write execution to transcript file."""
        try:
            with open(TRANSCRIPT_FILE, "a") as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Command: {result.command}\n")
                f.write(f"Duration: {result.duration_seconds:.2f}s\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"Succeeded: {result.succeeded}\n")
                f.write(f"\nStdout:\n{result.stdout}\n")
                if result.stderr:
                    f.write(f"\nStderr:\n{result.stderr}\n")
                f.write(f"\n{'='*70}\n")
        except Exception as e:
            logger.warning(f"Failed to write transcript: {e}")

    def get_traces(self) -> List[ExecutionTrace]:
        """Get all execution traces."""
        return self.execution_traces.copy()

    def clear_traces(self):
        """Clear execution trace history."""
        self.execution_traces.clear()


# Global executor instance
_executor: Optional[PowerShellExecutor] = None


def get_executor() -> PowerShellExecutor:
    """Get or create the global PowerShell executor."""
    global _executor
    if _executor is None:
        _executor = PowerShellExecutor()
    return _executor


def execute(command: str, **kwargs) -> ExecutionResult:
    """Execute a command using the global executor."""
    return get_executor().execute(command, **kwargs)


# Import os for environ
import os
