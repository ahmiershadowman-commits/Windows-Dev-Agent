"""
Tests for PowerShell execution and command building.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution.command_builder import CommandBuilder, PipelineBuilder, PowerShellScript
from src.execution.powershell_executor import PowerShellExecutor, ExecutionError, ExecutionTimeout
from src.models.execution import ExecutionResult, ExecutionTrace


class TestCommandBuilder:
    """Test CommandBuilder."""

    def test_simple_command(self):
        """Test building a simple command."""
        builder = CommandBuilder("Get-Process")
        cmd = builder.build()
        assert "Get-Process" in cmd

    def test_command_with_arguments(self):
        """Test building command with arguments."""
        builder = CommandBuilder().command("Write-Output").arg("Hello").arg("World")
        cmd = builder.build()
        assert "Write-Output" in cmd
        assert "Hello" in cmd
        assert "World" in cmd

    def test_command_with_parameters(self):
        """Test building command with parameters."""
        builder = (
            CommandBuilder()
            .command("Get-ChildItem")
            .param("Path", "C:\\Users")
            .param("Recurse")
        )
        cmd = builder.build()
        assert "Get-ChildItem" in cmd
        assert "-Path" in cmd
        assert "-Recurse" in cmd

    def test_argument_escaping(self):
        """Test argument escaping."""
        builder = CommandBuilder().command("Write-Output").arg('Hello "World"')
        cmd = builder.build()
        # Should have escaped quotes
        assert '\\"' in cmd or '"' in cmd

    def test_argument_escaping_spaces(self):
        """Test escaping arguments with spaces."""
        builder = CommandBuilder().command("Write-Output").arg("Hello World")
        cmd = builder.build()
        assert '"Hello World"' in cmd

    def test_import_module(self):
        """Test module import."""
        builder = (
            CommandBuilder()
            .import_module("Az.Accounts")
            .command("Get-AzContext")
        )
        cmd = builder.build()
        assert "Import-Module" in cmd
        assert "Az.Accounts" in cmd

    def test_error_action_preference(self):
        """Test setting error action preference."""
        # Test setting to non-default value so it's included in build
        builder = CommandBuilder("Get-Item")
        result = builder.error_action("Continue")
        # Should return builder for fluent API
        assert result is builder
        cmd = builder.build()
        # Continue preference should be in the command
        assert "Continue" in cmd and "ErrorActionPreference" in cmd

    def test_environment_variables(self):
        """Test setting environment variables (in command)."""
        builder = CommandBuilder().command("echo $env:TEST").env("TEST", "value")
        # Environment variables are stored but not in command string
        assert len(builder.environment_variables) == 1

    def test_factory_method(self):
        """Test factory method."""
        builder = CommandBuilder.create().command("Test-Connection")
        cmd = builder.build()
        assert "Test-Connection" in cmd

    def test_quote_string(self):
        """Test quote helper."""
        quoted = CommandBuilder.quote("C:\\Program Files\\Test")
        assert '"' in quoted

    def test_pipeline_builder(self):
        """Test pipeline construction."""
        pipeline = PipelineBuilder().add("Get-Process").add("Select-Object Name")
        cmd = pipeline.build()
        assert "Get-Process | Select-Object Name" == cmd

    def test_pipeline_select(self):
        """Test pipeline with Select."""
        pipeline = PipelineBuilder().add("Get-Process").add_select("Name", "Id")
        cmd = pipeline.build()
        assert "Select-Object" in cmd

    def test_pipeline_where(self):
        """Test pipeline with Where."""
        pipeline = (
            PipelineBuilder()
            .add("Get-Process")
            .add_where("$_.WorkingSet -gt 100MB")
        )
        cmd = pipeline.build()
        assert "Where-Object" in cmd

    def test_pipeline_sort(self):
        """Test pipeline with Sort."""
        pipeline = (
            PipelineBuilder()
            .add("Get-Process")
            .add_sort("WorkingSet", descending=True)
        )
        cmd = pipeline.build()
        assert "Sort-Object" in cmd
        assert "Descending" in cmd

    def test_escape_value_bool(self):
        """Test escaping boolean values."""
        escaped = CommandBuilder._escape_value(True)
        assert escaped == "$true"
        escaped = CommandBuilder._escape_value(False)
        assert escaped == "$false"

    def test_escape_value_number(self):
        """Test escaping numeric values."""
        escaped = CommandBuilder._escape_value(42)
        assert escaped == "42"
        escaped = CommandBuilder._escape_value(3.14)
        assert escaped == "3.14"

    def test_escape_value_list(self):
        """Test escaping list values."""
        escaped = CommandBuilder._escape_value(["a", "b", "c"])
        assert "@(" in escaped
        assert ")" in escaped

    def test_escape_value_dict(self):
        """Test escaping dictionary values."""
        escaped = CommandBuilder._escape_value({"key1": "value1", "key2": 42})
        assert "@{" in escaped
        assert "}" in escaped


class TestPowerShellScript:
    """Test PowerShellScript."""

    def test_script_not_found(self):
        """Test error when script not found."""
        with pytest.raises(FileNotFoundError):
            PowerShellScript("/nonexistent/script.ps1")

    def test_script_invoke(self, tmp_path):
        """Test invoking a script."""
        script = tmp_path / "test.ps1"
        script.write_text("Write-Output 'Hello'")
        ps_script = PowerShellScript(str(script))
        builder = ps_script.invoke("arg1", param1="value1")
        cmd = builder.build()
        assert "test.ps1" in cmd
        assert "arg1" in cmd


class TestExecutionResult:
    """Test ExecutionResult."""

    def test_result_success(self):
        """Test successful result."""
        result = ExecutionResult(
            returncode=0,
            stdout="Output",
            command="test",
        )
        assert result.succeeded is True

    def test_result_failure(self):
        """Test failed result."""
        result = ExecutionResult(
            returncode=1,
            stderr="Error",
            command="test",
        )
        assert result.succeeded is False

    def test_result_to_dict(self):
        """Test result serialization."""
        result = ExecutionResult(
            returncode=0,
            stdout="Output",
            command="test",
        )
        d = result.to_dict()
        assert d["returncode"] == 0
        assert d["stdout"] == "Output"

    def test_result_from_dict(self):
        """Test result deserialization."""
        data = {
            "returncode": 0,
            "stdout": "Output",
            "command": "test",
            "succeeded": True,
        }
        result = ExecutionResult.from_dict(data)
        assert result.returncode == 0
        assert result.stdout == "Output"


class TestExecutionTrace:
    """Test ExecutionTrace."""

    def test_trace_creation(self):
        """Test trace creation."""
        trace = ExecutionTrace(
            timestamp=datetime.now(),
            command="test-command",
            tool_name="test-tool",
            exit_code=0,
            success=True,
        )
        assert trace.tool_name == "test-tool"
        assert trace.success is True

    def test_trace_to_dict(self):
        """Test trace serialization."""
        trace = ExecutionTrace(
            timestamp=datetime.now(),
            command="test",
            tool_name="test",
            exit_code=0,
            success=True,
        )
        d = trace.to_dict()
        assert "timestamp" in d
        assert d["exit_code"] == 0

    def test_trace_to_json(self):
        """Test trace JSON serialization."""
        trace = ExecutionTrace(
            timestamp=datetime.now(),
            command="test",
            exit_code=0,
            success=True,
        )
        json_str = trace.to_json()
        assert isinstance(json_str, str)
        assert "test" in json_str


class TestPowerShellExecutor:
    """Test PowerShellExecutor."""

    @patch("subprocess.run")
    def test_execute_success(self, mock_run):
        """Test successful execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Output",
            stderr="",
        )

        executor = PowerShellExecutor(transcript_enabled=False)
        result = executor.execute("Write-Output 'test'")

        assert result.succeeded is True
        assert result.returncode == 0
        assert result.stdout == "Output"

    @patch("subprocess.run")
    def test_execute_failure(self, mock_run):
        """Test failed execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error",
        )

        executor = PowerShellExecutor(transcript_enabled=False)
        result = executor.execute("Get-Item /nonexistent")

        assert result.succeeded is False
        assert result.returncode == 1
        assert result.stderr == "Error"

    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run):
        """Test timeout handling."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        executor = PowerShellExecutor(timeout_seconds=5, transcript_enabled=False)

        with pytest.raises(ExecutionTimeout):
            executor.execute("Start-Sleep -Seconds 10")

    @patch("subprocess.run")
    def test_execute_with_tool_name(self, mock_run):
        """Test execution with tool name."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        executor = PowerShellExecutor(transcript_enabled=False)
        result = executor.execute("Write-Output 'test'", tool_name="ruff")

        # Check trace was created
        traces = executor.get_traces()
        assert len(traces) == 1
        assert traces[0].tool_name == "ruff"

    @patch("subprocess.run")
    def test_execute_builder(self, mock_run):
        """Test executing with command builder."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        executor = PowerShellExecutor(transcript_enabled=False)
        builder = CommandBuilder().command("Write-Output").arg("test")
        result = executor.execute_builder(builder)

        assert result.succeeded is True

    @patch("subprocess.run")
    def test_execution_traces(self, mock_run):
        """Test execution trace collection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        executor = PowerShellExecutor(transcript_enabled=False)
        executor.execute("Write-Output 'test1'")
        executor.execute("Write-Output 'test2'")

        traces = executor.get_traces()
        assert len(traces) == 2

        executor.clear_traces()
        assert len(executor.get_traces()) == 0

    @patch("subprocess.run")
    def test_duration_tracking(self, mock_run):
        """Test execution duration tracking."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        executor = PowerShellExecutor(transcript_enabled=False)
        result = executor.execute("Write-Output 'test'")

        assert result.duration_seconds >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
