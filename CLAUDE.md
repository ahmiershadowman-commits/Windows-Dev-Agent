# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Windows Dev Agent Plugin** — a prototype implementation of a Windows-native agent plugin for automated development tasks. The plugin implements a **capability → workflow → tool** model where high-level capabilities (e.g., `lint-python`, `update-dependencies`) are resolved to appropriate tools through a workflow engine with five phases: discovery, planning, implementation, verification, and integration.

The repository contains two implementations:
- **Simple prototype** in `plugin.py`: Illustrates the core architecture with minimal dependencies
- **Extended architecture** in `src/`: A comprehensive implementation with discovery engines, workflow DSL, safety policies, and observability

## Installation & Dependencies

Install the base dependency (PyYAML):

```bash
pip install pyyaml
```

For development and testing, also install:

```bash
pip install pytest
```

## Common Commands

### Running the Plugin

The plugin takes a capability name as an argument:

```bash
python plugin.py lint-python
python plugin.py update-dependencies
python plugin.py test-driven-development
```

Available capabilities are defined in `capabilities.yaml`. Use `--config` to specify a different configuration file:

```bash
python plugin.py <capability> --config /path/to/custom/capabilities.yaml
```

### Running Tests

Run all tests:

```bash
python -m pytest tests/
```

Run tests in a specific file:

```bash
python -m pytest tests/test_workflow_engine.py
```

Run a specific test:

```bash
python -m pytest tests/test_workflow_engine.py::TestWorkflowSchema::test_workflow_creation
```

Run with verbose output and test summary:

```bash
python -m pytest tests/ -v
```

Run integration tests:

```bash
python -m pytest tests/integration/
```

### Code Structure

The main entry point is `plugin.py`, which provides a reference implementation. The more comprehensive source code lives in `src/` and includes:

- **Schemas** (`src/schemas/`): Data models for capabilities, tools, and workflows
- **Discovery** (`src/discovery/`): System introspection and environment analysis
- **Execution** (`src/execution/`): Command execution engines (PowerShell, subprocess-based)
- **Workflow** (`src/workflow/`): Workflow DSL and execution engine
- **Graph** (`src/graph/`): Capability graph for intelligent tool selection
- **Config** (`src/config/`): Configuration loading and parsing
- **Safety** (`src/safety/`): Safety policy enforcement and permission checks
- **Observability** (`src/observability/`): Telemetry and logging
- **MCP** (`src/mcp/`): Model Context Protocol server adapters
- **CLI** (`src/cli/`): Command-line interface
- **Other modules**: `adapters/`, `audit/`, `importers/`, `reporting/`, `web/`, `models/`

## Architecture

### Prototype (plugin.py)

The prototype demonstrates the core pattern:

1. **ToolDefinition**: A tool candidate with `name`, `command` to execute, and `check` command to verify availability
2. **Capability**: A high-level capability with a description and list of candidate tools
3. **CapabilityGraph**: Loads capability definitions from `capabilities.yaml`
4. **WorkflowEngine**: Executes the five-phase workflow:
   - **Discovery**: Gather system information (OS, Python version, CPU count)
   - **Planning**: Select first available tool for the capability
   - **Implementation**: Execute the tool's command
   - **Verification**: Verify execution success (currently a no-op)
   - **Integration**: Log completion (currently a no-op)

### Extended Architecture (src/)

The extended architecture in `src/` builds on this foundation:

- **Capability Graph** (`src/graph/capability_graph.py`): Intelligent tool selection based on environment discovery
- **Workflow Engine** (`src/workflow/engine.py`): Full workflow DSL with approval gates, conditional steps, and execution tracking
- **Environment Discovery** (`src/discovery/discovery.py`): Detailed system introspection (WMI queries, installed software, WSL distros, virtualization support)
- **PowerShell Executor** (`src/execution/powershell_executor.py`): Native Windows command execution via PowerShell
- **Safety Policy Engine** (`src/safety/policy.py`): Permission checks and safety policies for sensitive operations
- **Observability** (`src/observability/telemetry.py`): Telemetry collection and structured logging

## Configuration

Capabilities are defined in `capabilities.yaml` in the following format:

```yaml
capability-name:
  description: Human-readable description
  tools:
    - name: tool-name
      command: "command to execute"
      check: "command to verify tool availability"
    - name: fallback-tool
      command: "fallback command"
      check: "fallback check command"
```

The plugin attempts each tool in order and uses the first one that passes its `check` command. Add new capabilities by extending this file.

## Logging

All execution is logged to `agent.log` in the repository root. The log includes:
- System discovery information
- Tool selection and availability checks
- Workflow phase progression
- Command output and errors
- Workflow completion status

Check `agent.log` to understand what the plugin executed and why.

## Key Design Patterns

- **Tool Resolution**: Tools are selected dynamically based on availability checks. The plugin gracefully degrades if preferred tools are unavailable.
- **Workflow Phases**: The five-phase workflow (discovery → planning → implementation → verification → integration) provides a consistent execution model.
- **Extensibility**: New capabilities and tools can be added by editing `capabilities.yaml` without code changes.
- **Logging**: All actions are logged for auditability and debugging.

## Prototype Limitations

The prototype (`plugin.py`) is intentionally minimal. The extended architecture in `src/` provides more functionality, but many features from the design report remain unimplemented:

- Full WMI/WinGet integration for Windows-specific introspection and package management
- Real PowerShell module integration (the prototype uses basic `subprocess` execution)
- Hyper-V and Windows Sandbox integration for sandboxed tool execution
- Comprehensive OpenTelemetry observability
- Complex planning heuristics and automatic fallback to WSL/containers

These can be added incrementally as needed for your environment.
