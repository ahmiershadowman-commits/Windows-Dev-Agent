#!/usr/bin/env python3
"""
Windows Dev Agent Plugin - Phase Executor

Manages the execution of the comprehensive build plan across all 7 phases.
Tracks progress, provides guidance, and ensures acceptance criteria are met.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from typing import Optional, List

REPO_ROOT = Path(__file__).parent.resolve()
STATE_FILE = REPO_ROOT / ".build_state.json"
LOG_FILE = REPO_ROOT / "build.log"


@dataclass
class PhaseStatus:
    """Status of a single phase."""
    phase_number: int
    phase_name: str
    status: str  # pending, in_progress, completed, blocked
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deliverables_completed: List[str] = None
    acceptance_criteria_met: List[bool] = None
    notes: str = ""

    def __post_init__(self):
        if self.deliverables_completed is None:
            self.deliverables_completed = []
        if self.acceptance_criteria_met is None:
            self.acceptance_criteria_met = []


@dataclass
class BuildState:
    """Overall build state."""
    current_phase: int = 1
    phases: List[PhaseStatus] = None
    last_updated: str = ""
    branch_name: str = "claude/windows-agent-plugin-EAUGh"

    def __post_init__(self):
        if self.phases is None:
            self.phases = [
                PhaseStatus(1, "Environment Discovery Engine", "pending"),
                PhaseStatus(2, "PowerShell Execution Layer", "pending"),
                PhaseStatus(3, "Capability Schema Upgrade", "pending"),
                PhaseStatus(4, "Workflow DSL and Synthesis", "pending"),
                PhaseStatus(5, "Safety Policy Engine", "pending"),
                PhaseStatus(6, "MCP Server and Adapters", "pending"),
                PhaseStatus(7, "Ecosystem Adaptation and Observability", "pending"),
                PhaseStatus(8, "Integration and Polish", "pending"),
            ]


class PhaseExecutor:
    """Manages phase execution and progress tracking."""

    def __init__(self):
        self.state = self._load_state()
        self.log_file = LOG_FILE

    def _load_state(self) -> BuildState:
        """Load state from file or create new."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                data = json.load(f)
                # Reconstruct state
                phases = [
                    PhaseStatus(
                        p["phase_number"],
                        p["phase_name"],
                        p["status"],
                        p.get("started_at"),
                        p.get("completed_at"),
                        p.get("deliverables_completed", []),
                        p.get("acceptance_criteria_met", []),
                        p.get("notes", ""),
                    )
                    for p in data.get("phases", [])
                ]
                state = BuildState(
                    current_phase=data.get("current_phase", 1),
                    phases=phases,
                    last_updated=data.get("last_updated", ""),
                    branch_name=data.get("branch_name", "claude/windows-agent-plugin-EAUGh"),
                )
                return state
        return BuildState()

    def _save_state(self):
        """Save state to file."""
        data = {
            "current_phase": self.state.current_phase,
            "last_updated": datetime.now().isoformat(),
            "branch_name": self.state.branch_name,
            "phases": [asdict(p) for p in self.state.phases],
        }
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] {level}: {message}"
        print(log_msg)
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")

    def check_git_status(self) -> bool:
        """Check if we're on the correct branch and working tree is clean."""
        try:
            # Check current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            current_branch = result.stdout.strip()
            if current_branch != self.state.branch_name:
                self.log(f"⚠️  On branch '{current_branch}', not '{self.state.branch_name}'", "WARN")
                return False

            # Check working tree
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.stdout.strip():
                self.log("⚠️  Working tree has uncommitted changes", "WARN")
                return False

            return True
        except Exception as e:
            self.log(f"❌ Git status check failed: {e}", "ERROR")
            return False

    def display_status(self):
        """Display current build status."""
        print("\n" + "=" * 70)
        print("Windows Dev Agent Plugin - Build Status")
        print("=" * 70)
        print(f"Branch: {self.state.branch_name}")
        print(f"Current Phase: {self.state.current_phase}")
        print(f"Last Updated: {self.state.last_updated}")
        print()

        for phase in self.state.phases:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "blocked": "❌",
            }.get(phase.status, "❓")

            print(f"{status_icon} Phase {phase.phase_number}: {phase.phase_name}")
            print(f"   Status: {phase.status}")
            if phase.deliverables_completed:
                print(f"   Deliverables: {len(phase.deliverables_completed)} completed")
            if phase.notes:
                print(f"   Notes: {phase.notes}")
            print()

        print("=" * 70 + "\n")

    def get_next_phase(self) -> Optional[PhaseStatus]:
        """Get the next phase to work on."""
        for phase in self.state.phases:
            if phase.status in ("pending", "in_progress"):
                return phase
        return None

    def start_phase(self, phase_number: int):
        """Mark a phase as in progress."""
        if 1 <= phase_number <= len(self.state.phases):
            phase = self.state.phases[phase_number - 1]
            phase.status = "in_progress"
            phase.started_at = datetime.now().isoformat()
            self.state.current_phase = phase_number
            self._save_state()
            self.log(f"Started Phase {phase_number}: {phase.phase_name}")

    def complete_phase(self, phase_number: int, deliverables: List[str], notes: str = ""):
        """Mark a phase as completed."""
        if 1 <= phase_number <= len(self.state.phases):
            phase = self.state.phases[phase_number - 1]
            phase.status = "completed"
            phase.completed_at = datetime.now().isoformat()
            phase.deliverables_completed = deliverables
            phase.notes = notes
            self._save_state()
            self.log(f"Completed Phase {phase_number}: {phase.phase_name}")
            self.log(f"  Deliverables: {', '.join(deliverables)}")
            if notes:
                self.log(f"  Notes: {notes}")

    def display_phase_guidance(self, phase_number: int):
        """Display detailed guidance for a phase."""
        guidance = {
            1: """
PHASE 1: Environment Discovery Engine (Weeks 1-2)

Objective: Implement real machine-state discovery via Windows-native primitives.

Key Files to Create:
  - src/discovery/discovery.ps1 (PowerShell discovery scripts)
  - src/discovery/discovery.py (Python wrapper)
  - src/models/environment.py (Environment snapshot model)
  - tests/test_discovery.py (Test suite)

Next Steps:
  1. Create directory structure: mkdir -p src/discovery src/models tests
  2. Implement PowerShell discovery for OS, hardware, virtualization, tools
  3. Create Python wrapper to call PowerShell and parse JSON output
  4. Define EnvironmentSnapshot dataclass with all required fields
  5. Write comprehensive tests (use mock WMI/PowerShell responses)
  6. Test acceptance criteria:
     - discovery.ps1 retrieves all system information
     - Python wrapper parses output correctly
     - environment.json is valid and complete
     - All tests pass (mocked calls)

Tests to Run:
  python -m pytest tests/test_discovery.py -v

Commit When Done:
  git add -A
  git commit -m "Phase 1: Environment discovery engine

  Implement real machine-state discovery via Windows-native primitives:
  - PowerShell discovery scripts (OS, hardware, virtualization, tools)
  - Python wrapper with JSON serialization and caching
  - Environment snapshot model with query methods
  - Comprehensive test suite with mocked system calls

  https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH"
  git push -u origin claude/windows-agent-plugin-EAUGh
""",
            2: """
PHASE 2: PowerShell Execution Layer (Weeks 2-3)

Objective: Replace generic subprocess execution with structured PowerShell service.

Key Files to Create:
  - src/execution/powershell_executor.py (PowerShell service)
  - src/execution/command_builder.py (Command builder)
  - src/models/execution.py (Execution result models)
  - tests/test_execution.py (Test suite)

Next Steps:
  1. Create execution module structure
  2. Implement PowerShell executor with:
     - Structured command execution
     - Stdout/stderr capture
     - Exit code and object-return modes
     - Timeout/cancellation support
     - Transcript logging
  3. Build fluent API for command construction
  4. Create execution result models for audit logging
  5. Write comprehensive tests (mock PowerShell)
  6. Test acceptance criteria:
     - PowerShell executor runs commands with structured output
     - Command builder properly escapes arguments
     - All tests pass with mocked PowerShell

Tests to Run:
  python -m pytest tests/test_execution.py -v
""",
            3: """
PHASE 3: Capability Schema Upgrade (Weeks 3-4)

Objective: Replace flat YAML with rich, structured capability definitions.

Key Files to Create:
  - src/schemas/capability.py (Rich capability schema)
  - src/schemas/tool.py (Tool definition schema)
  - src/config/capability_loader.py (YAML parser)
  - src/graph/capability_graph.py (Capability graph)
  - tests/test_capability_schema.py (Test suite)

Next Steps:
  1. Design rich schema with safety levels, intent classes, dependencies
  2. Implement CapabilityDefinition and ToolDefinition dataclasses
  3. Create YAML parser that validates against schema
  4. Build capability graph with tool selection logic
  5. Ensure backward compatibility with existing YAML
  6. Write comprehensive tests
  7. Test acceptance criteria:
     - New schema backward-compatible with existing YAML
     - All capability definitions load and validate
     - Tool selection respects Windows-native preference

Tests to Run:
  python -m pytest tests/test_capability_schema.py -v
""",
            4: """
PHASE 4: Workflow DSL and Synthesis Engine (Weeks 4-5)

Objective: Replace hardcoded workflow phases with declarative, composable workflows.

Key Files to Create:
  - src/schemas/workflow.py (Workflow DSL)
  - src/workflow/engine.py (Workflow execution engine)
  - workflows/*.yaml (Workflow definitions)
  - tests/test_workflow_engine.py (Test suite)

Next Steps:
  1. Design workflow DSL with stages, criteria, approval gates
  2. Implement workflow loader and executor
  3. Create canonical workflow examples:
     - discovery.yaml, plan.yaml, tdd-loop.yaml, create-pr.yaml
  4. Implement approval gate handling
  5. Implement rollback on failure
  6. Write comprehensive tests
  7. Test acceptance criteria:
     - Workflow DSL is human-readable
     - All canonical workflows functional
     - Approval gates and rollback working

Tests to Run:
  python -m pytest tests/test_workflow_engine.py -v
""",
            5: """
PHASE 5: Safety Policy Engine (Weeks 5-6)

Objective: Enforce safety levels and approval requirements for risky operations.

Key Files to Create:
  - src/safety/policy.py (Safety policy)
  - src/safety/approval_gate.py (Approval gate)
  - src/safety/sandbox_router.py (Sandbox routing)
  - src/safety/rollback.py (Rollback system)
  - tests/test_safety.py (Test suite)

Next Steps:
  1. Design safety policy with levels and action classification
  2. Implement approval gate with user prompts
  3. Implement sandbox router for risk-based isolation
  4. Implement rollback system
  5. Write comprehensive tests
  6. Test acceptance criteria:
     - Safety levels correctly classified
     - Approval gates present clear information
     - Sandbox routing selects appropriate environment
     - Rollback plans execute correctly

Tests to Run:
  python -m pytest tests/test_safety.py -v
""",
            6: """
PHASE 6: MCP Server and Adapters (Weeks 6-7)

Objective: Expose plugin as MCP server and integrate with host agents.

Key Files to Create:
  - src/mcp/server.py (MCP server)
  - src/mcp/tools.py (MCP tools)
  - src/adapters/*.py (Host adapters)
  - src/cli/main.py (CLI wrapper)
  - tests/test_mcp.py (Test suite)

Next Steps:
  1. Implement MCP protocol server
  2. Expose MCP tools: env, capability, workflow, sandbox, package, etc.
  3. Create adapters for Claude Code, Codex, OpenCode
  4. Build CLI wrapper with argument parsing
  5. Create web UI skeleton (optional)
  6. Write comprehensive tests
  7. Test acceptance criteria:
     - MCP server runs and accepts requests
     - All MCP tools implemented and tested
     - CLI wrapper handles all arguments

Tests to Run:
  python -m pytest tests/test_mcp.py -v
  python -m src.cli --help
""",
            7: """
PHASE 7: Ecosystem Adaptation and Observability (Weeks 7-8)

Objective: Import external skills/MCPs and implement end-to-end observability.

Key Files to Create:
  - src/importers/*.py (Skill and MCP importers)
  - src/audit/mcp_auditor.py (MCP auditor)
  - src/observability/telemetry.py (OpenTelemetry integration)
  - src/reporting/audit_report.py (Audit report generator)
  - tests/test_observability.py (Test suite)

Next Steps:
  1. Implement skill and MCP discovery and importing
  2. Build Superpowers pattern adapter
  3. Implement MCP auditor for compliance testing
  4. Integrate OpenTelemetry for spans, metrics, logs
  5. Build self-audit report generation
  6. Write comprehensive tests
  7. Test acceptance criteria:
     - Skills and MCPs discovered and imported
     - Superpowers patterns working
     - Telemetry exported to backend
     - Self-audit reports complete

Tests to Run:
  python -m pytest tests/test_observability.py -v
""",
            8: """
PHASE 8: Integration and Polish (Week 8)

Objective: Final integration, documentation, and deployment readiness.

Key Files to Create:
  - tests/integration/test_end_to_end.py (Integration tests)
  - docs/*.md (Documentation)
  - config/*.yaml (Configuration templates)
  - .github/workflows/*.yml (CI/CD)

Next Steps:
  1. Write end-to-end integration tests
  2. Complete comprehensive documentation
  3. Create configuration templates and examples
  4. Set up CI/CD pipelines
  5. Package for distribution (PyPI, NuGet, etc.)
  6. Test acceptance criteria:
     - All integration tests pass
     - Documentation complete and accurate
     - Packaging works correctly

Tests to Run:
  python -m pytest tests/integration/ -v
  python -m pytest tests/ --cov=src --cov-report=term-missing
""",
        }

        phase_text = guidance.get(phase_number, "No guidance available")
        print(phase_text)

    def run_interactive(self):
        """Run interactive phase management."""
        while True:
            self.display_status()

            next_phase = self.get_next_phase()
            if not next_phase:
                print("✅ All phases completed!")
                return

            print(f"\nReady to work on: Phase {next_phase.phase_number} - {next_phase.phase_name}")
            print("\nOptions:")
            print("  1. Show guidance for this phase")
            print("  2. Mark phase as in progress")
            print("  3. Mark phase as completed")
            print("  4. Skip to next phase")
            print("  5. View build log")
            print("  6. Check git status")
            print("  7. Exit")
            print()

            choice = input("Enter option (1-7): ").strip()

            if choice == "1":
                self.display_phase_guidance(next_phase.phase_number)
            elif choice == "2":
                self.start_phase(next_phase.phase_number)
                print(f"✅ Phase {next_phase.phase_number} marked as in progress")
            elif choice == "3":
                deliverables = input("Enter completed deliverables (comma-separated): ").strip().split(",")
                deliverables = [d.strip() for d in deliverables if d.strip()]
                self.complete_phase(next_phase.phase_number, deliverables)
                print(f"✅ Phase {next_phase.phase_number} marked as completed")
            elif choice == "4":
                self.state.current_phase = min(next_phase.phase_number + 1, len(self.state.phases))
                self._save_state()
                print(f"⏭️  Skipped to phase {self.state.current_phase}")
            elif choice == "5":
                if self.log_file.exists():
                    with open(self.log_file) as f:
                        print(f.read()[-2000:])  # Last 2000 chars
                else:
                    print("No log file yet")
            elif choice == "6":
                if self.check_git_status():
                    print("✅ Git status OK")
                else:
                    print("⚠️  Git status issues detected")
            elif choice == "7":
                print("Exiting...")
                return
            else:
                print("Invalid option")

            input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    executor = PhaseExecutor()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "status":
            executor.display_status()
        elif command == "start":
            phase = int(sys.argv[2]) if len(sys.argv) > 2 else executor.state.current_phase
            executor.start_phase(phase)
        elif command == "complete":
            phase = int(sys.argv[2]) if len(sys.argv) > 2 else executor.state.current_phase
            executor.complete_phase(phase, [], "Completed via CLI")
        elif command == "guidance":
            phase = int(sys.argv[2]) if len(sys.argv) > 2 else executor.state.current_phase
            executor.display_phase_guidance(phase)
        elif command == "log":
            if executor.log_file.exists():
                with open(executor.log_file) as f:
                    print(f.read())
            else:
                print("No log file")
        else:
            print(f"Unknown command: {command}")
    else:
        executor.run_interactive()


if __name__ == "__main__":
    main()
