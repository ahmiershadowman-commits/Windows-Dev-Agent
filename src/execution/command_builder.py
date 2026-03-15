"""
PowerShell command builder with fluent API.

Provides a safe, ergonomic way to construct PowerShell commands.
"""

import re
from typing import List, Dict, Optional, Any
from pathlib import Path


class CommandBuilder:
    """Fluent API for building PowerShell commands safely."""

    def __init__(self, base_command: str = ""):
        self.base_command = base_command
        self.arguments: List[str] = []
        self.parameters: Dict[str, Any] = {}
        self.modules_to_import: List[str] = []
        self.environment_variables: Dict[str, str] = {}
        self._error_action = "Stop"
        self._output_preference = "Continue"
        self._progress_preference = "SilentlyContinue"

    def command(self, cmd: str) -> "CommandBuilder":
        """Set the base command."""
        self.base_command = cmd
        return self

    def arg(self, arg: str) -> "CommandBuilder":
        """Add a positional argument."""
        self.arguments.append(self._escape_argument(arg))
        return self

    def args(self, *args) -> "CommandBuilder":
        """Add multiple positional arguments."""
        for arg in args:
            self.arg(str(arg))
        return self

    def param(self, name: str, value: Optional[Any] = None) -> "CommandBuilder":
        """Add a named parameter."""
        if value is None:
            # Flag parameter
            self.parameters[f"-{name}"] = True
        else:
            self.parameters[f"-{name}"] = value
        return self

    def params(self, **kwargs) -> "CommandBuilder":
        """Add multiple named parameters."""
        for name, value in kwargs.items():
            self.param(name, value)
        return self

    def import_module(self, module_name: str) -> "CommandBuilder":
        """Import a PowerShell module."""
        if module_name not in self.modules_to_import:
            self.modules_to_import.append(module_name)
        return self

    def env(self, name: str, value: str) -> "CommandBuilder":
        """Set an environment variable."""
        self.environment_variables[name] = value
        return self

    def error_action(self, action: str) -> "CommandBuilder":
        """Set PowerShell error action preference."""
        valid_actions = ["Stop", "Continue", "SilentlyContinue", "Ignore", "Inquire"]
        if action not in valid_actions:
            raise ValueError(f"Invalid error action: {action}. Must be one of {valid_actions}")
        self._error_action = action
        return self

    def output_preference(self, preference: str) -> "CommandBuilder":
        """Set output preference."""
        valid_preferences = ["Continue", "SilentlyContinue", "Stop"]
        if preference not in valid_preferences:
            raise ValueError(f"Invalid output preference: {preference}")
        self._output_preference = preference
        return self

    def progress_preference(self, preference: str) -> "CommandBuilder":
        """Set progress preference."""
        valid_preferences = ["Continue", "SilentlyContinue", "Stop"]
        if preference not in valid_preferences:
            raise ValueError(f"Invalid progress preference: {preference}")
        self._progress_preference = preference
        return self

    def build(self) -> str:
        """Build the complete PowerShell command."""
        parts = []

        # Set preferences
        if self._error_action != "Stop":
            parts.append(f"$ErrorActionPreference = '{self._error_action}'")
        if self._output_preference != "Continue":
            parts.append(f"$OutputPreference = '{self._output_preference}'")
        if self._progress_preference != "SilentlyContinue":
            parts.append(f"$ProgressPreference = '{self._progress_preference}'")

        # Import modules
        for module in self.modules_to_import:
            parts.append(f"Import-Module {self._escape_argument(module)}")

        # Build main command
        cmd_parts = [self.base_command]

        # Add arguments
        for arg in self.arguments:
            cmd_parts.append(arg)

        # Add parameters
        for name, value in self.parameters.items():
            if value is True:
                cmd_parts.append(name)
            else:
                cmd_parts.append(f"{name} {self._escape_value(value)}")

        parts.append(" ".join(cmd_parts))

        return "; ".join(parts)

    @staticmethod
    def _escape_argument(arg: str) -> str:
        """Escape a command-line argument for PowerShell."""
        arg_str = str(arg)

        # If the argument contains spaces or special chars, quote it
        if any(c in arg_str for c in [" ", "\t", '"', "'", "$"]):
            # Escape double quotes and backslashes
            escaped = arg_str.replace("\\", "\\\\").replace('"', '\"')
            return f'"{escaped}"'

        return arg_str

    @staticmethod
    def _escape_value(value: Any) -> str:
        """Escape a parameter value."""
        if isinstance(value, bool):
            return "$true" if value else "$false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, Path):
            return CommandBuilder._escape_argument(str(value))
        elif isinstance(value, (list, tuple)):
            # Array
            escaped_items = [CommandBuilder._escape_value(item) for item in value]
            return "@(" + ", ".join(escaped_items) + ")"
        elif isinstance(value, dict):
            # Hashtable
            pairs = [f"{k} = {CommandBuilder._escape_value(v)}" for k, v in value.items()]
            return "@{" + "; ".join(pairs) + "}"
        else:
            # String
            return CommandBuilder._escape_argument(str(value))

    @staticmethod
    def quote(value: str) -> str:
        """Quote a string for PowerShell."""
        return CommandBuilder._escape_argument(value)

    @staticmethod
    def create() -> "CommandBuilder":
        """Factory method to create a new command builder."""
        return CommandBuilder()


class PowerShellScript:
    """Represents a PowerShell script."""

    def __init__(self, script_path: str):
        self.script_path = Path(script_path)
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

    def invoke(self, *args, **kwargs) -> CommandBuilder:
        """Invoke the script with arguments."""
        builder = CommandBuilder()
        builder.command(f"& {CommandBuilder.quote(str(self.script_path))}")

        # Add positional arguments
        for arg in args:
            builder.arg(str(arg))

        # Add named arguments
        for name, value in kwargs.items():
            builder.param(name, value)

        return builder


class PipelineBuilder:
    """Build PowerShell pipelines."""

    def __init__(self):
        self.stages: List[str] = []

    def add(self, command: str) -> "PipelineBuilder":
        """Add a stage to the pipeline."""
        self.stages.append(command)
        return self

    def build(self) -> str:
        """Build the complete pipeline."""
        return " | ".join(self.stages)

    def add_select(self, *properties) -> "PipelineBuilder":
        """Add a Select-Object stage."""
        if properties:
            props = ", ".join([f'"{p}"' for p in properties])
            return self.add(f"Select-Object {props}")
        return self

    def add_where(self, condition: str) -> "PipelineBuilder":
        """Add a Where-Object stage."""
        return self.add(f"Where-Object {{{condition}}}")

    def add_sort(self, property_name: str, descending: bool = False) -> "PipelineBuilder":
        """Add a Sort-Object stage."""
        cmd = f"Sort-Object {CommandBuilder.quote(property_name)}"
        if descending:
            cmd += " -Descending"
        return self.add(cmd)

    def add_group(self, property_name: str) -> "PipelineBuilder":
        """Add a Group-Object stage."""
        return self.add(f"Group-Object {CommandBuilder.quote(property_name)}")

    def add_measure(self) -> "PipelineBuilder":
        """Add a Measure-Object stage."""
        return self.add("Measure-Object")

    def add_format_list(self, *properties) -> "PipelineBuilder":
        """Add a Format-List stage."""
        if properties:
            props = " ".join([CommandBuilder.quote(p) for p in properties])
            return self.add(f"Format-List {props}")
        return self.add("Format-List")

    def add_convert_to_json(self) -> "PipelineBuilder":
        """Add ConvertTo-Json stage."""
        return self.add("ConvertTo-Json -Depth 10")
