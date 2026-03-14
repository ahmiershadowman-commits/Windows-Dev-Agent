"""
Windows Dev Agent Plugin (Prototype)
====================================

This module provides a skeleton implementation of the Windows‑native agent
plugin described in the accompanying design report.  It defines a simple
capability→workflow→tool model, performs basic system discovery, chooses
appropriate tools for a requested capability based on a YAML configuration,
and executes a minimal workflow with logging.

The intent of this code is illustrative – it shows how the architecture can
be implemented in Python, but it does not attempt to realise every feature
from the design.  Notably, WMI/PowerShell integration, WinGet installation
or WSL fallback are stubbed out.  You are encouraged to extend this
prototype to suit your environment.

Usage:

    python plugin.py lint-python
    python plugin.py update-dependencies

Before running, install dependencies with:

    pip install pyyaml

Capability definitions live in `capabilities.yaml` in this package.

"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


###############################################################################
# Logging setup
###############################################################################

LOG_FILE = Path(__file__).resolve().parent / "agent.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


###############################################################################
# Data structures
###############################################################################

@dataclass
class ToolDefinition:
    """Represents a tool candidate for a capability."""

    name: str
    command: str
    check: str

    def is_available(self) -> bool:
        """
        Determine whether this tool is available on the system.  This
        implementation checks whether the executable can be found via
        `shutil.which()` and, if present, attempts to run the `check`
        command to verify it responds.
        """
        # Check if the executable name appears in PATH
        exe_name = self.check.split()[0]
        if shutil.which(exe_name) is None:
            return False

        # Try to run the check command to confirm tool health
        try:
            subprocess.run(
                self.check,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except Exception:
            return False
        return True

    def run(self) -> int:
        """
        Execute the tool's command.  Returns the exit code of the process.
        Logs the command and captures output for auditing.  Raises
        subprocess.CalledProcessError on failure.
        """
        logger.info("Running tool '%s': %s", self.name, self.command)
        result = subprocess.run(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info("Stdout:\n%s", result.stdout.strip())
        if result.stderr:
            logger.info("Stderr:\n%s", result.stderr.strip())
        if result.returncode != 0:
            logger.error("Command failed with return code %s", result.returncode)
        return result.returncode


@dataclass
class Capability:
    """Represents a high‑level capability requested by the user."""

    name: str
    description: str
    tools: List[ToolDefinition] = field(default_factory=list)

    def select_tool(self) -> Optional[ToolDefinition]:
        """
        Select the first available tool for this capability.  Returns
        `None` if no candidate tools are available.  Logs the selection
        process.
        """
        logger.info("Selecting tool for capability '%s'", self.name)
        for t in self.tools:
            logger.info("Checking availability of tool '%s'", t.name)
            if t.is_available():
                logger.info("Selected tool '%s' for capability '%s'", t.name, self.name)
                return t
            logger.info("Tool '%s' not available", t.name)
        logger.warning("No available tools for capability '%s'", self.name)
        return None


class CapabilityGraph:
    """Loads capability definitions from a YAML configuration file."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.capabilities: Dict[str, Capability] = {}
        self.load_config()

    def load_config(self) -> None:
        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for cap_name, cap_def in data.items():
            tools: List[ToolDefinition] = []
            for tool_def in cap_def.get("tools", []):
                tools.append(
                    ToolDefinition(
                        name=tool_def.get("name"),
                        command=tool_def.get("command"),
                        check=tool_def.get("check"),
                    )
                )
            capability = Capability(
                name=cap_name,
                description=cap_def.get("description", ""),
                tools=tools,
            )
            self.capabilities[cap_name] = capability
        logger.info("Loaded %d capabilities from %s", len(self.capabilities), self.config_path)

    def get(self, capability_name: str) -> Optional[Capability]:
        return self.capabilities.get(capability_name)


###############################################################################
# Workflow Engine
###############################################################################

class WorkflowEngine:
    """
    Implements the high‑level workflows for capabilities.  Each workflow
    consists of five phases: discovery, planning, implementation, verification
    and integration.  The engine is intentionally simplistic – it logs each
    stage and calls a tool during the implementation phase.
    """

    def __init__(self, capability_graph: CapabilityGraph):
        self.capability_graph = capability_graph

    def run(self, capability_name: str) -> None:
        capability = self.capability_graph.get(capability_name)
        if capability is None:
            logger.error("Capability '%s' not found in configuration", capability_name)
            return
        logger.info("Starting workflow for capability '%s'", capability.name)
        # 1. Discovery
        self.discovery_phase()
        # 2. Planning
        tool = capability.select_tool()
        if tool is None:
            logger.error("Cannot proceed without a tool for capability '%s'", capability.name)
            return
        plan = self.planning_phase(capability, tool)
        # 3. Implementation
        success = self.implementation_phase(tool, plan)
        if not success:
            logger.error("Implementation failed; aborting workflow")
            return
        # 4. Verification
        verification_success = self.verification_phase(capability, tool)
        if not verification_success:
            logger.error("Verification failed; aborting workflow")
            return
        # 5. Integration
        self.integration_phase(capability, tool)
        logger.info("Workflow for capability '%s' completed successfully", capability.name)

    def discovery_phase(self) -> None:
        logger.info("---- Discovery phase ----")
        # Basic system discovery: OS, Python version, CPU count
        os_info = platform.platform()
        python_version = sys.version.split()[0]
        cpu_count = os.cpu_count()
        logger.info("System information: OS=%s, Python=%s, CPUs=%s", os_info, python_version, cpu_count)
        # Additional discovery (e.g. WMI queries, WinGet list, WSL distros) could be added here

    def planning_phase(self, capability: Capability, tool: ToolDefinition) -> Dict[str, str]:
        logger.info("---- Planning phase ----")
        # For the prototype, the plan is trivial: we just record the chosen command
        plan = {"command": tool.command}
        logger.info("Plan for capability '%s': Using tool '%s' with command '%s'", capability.name, tool.name, tool.command)
        return plan

    def implementation_phase(self, tool: ToolDefinition, plan: Dict[str, str]) -> bool:
        logger.info("---- Implementation phase ----")
        try:
            exit_code = tool.run()
            return exit_code == 0
        except subprocess.CalledProcessError as e:
            logger.error("Tool execution raised an exception: %s", e)
            return False

    def verification_phase(self, capability: Capability, tool: ToolDefinition) -> bool:
        logger.info("---- Verification phase ----")
        # In a full implementation this would run unit tests, linters, etc.
        # Here we simply assume success if the tool executed successfully.
        logger.info("Verification for capability '%s' succeeded", capability.name)
        return True

    def integration_phase(self, capability: Capability, tool: ToolDefinition) -> None:
        logger.info("---- Integration phase ----")
        # Integration could commit changes, create a PR, or generate docs.
        # Here we simply log that integration would occur.
        logger.info("Integration for capability '%s' completed (no-op)", capability.name)


###############################################################################
# Main entry point
###############################################################################

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Windows Dev Agent Plugin (Prototype)")
    parser.add_argument(
        "capability",
        type=str,
        help="Name of the capability to execute (see capabilities.yaml)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).resolve().parent / "capabilities.yaml"),
        help="Path to capabilities YAML file",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    cap_graph = CapabilityGraph(Path(args.config))
    engine = WorkflowEngine(cap_graph)
    engine.run(args.capability)


if __name__ == "__main__":
    main()