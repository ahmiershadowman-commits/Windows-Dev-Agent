# Windows Dev Agent Plugin - Comprehensive Build Plan

**Status**: Starting Phase 1
**Last Updated**: 2026-03-15
**Branch**: `claude/windows-agent-plugin-EAUGh`

---

## Executive Summary

This document details the complete build plan from the current Python prototype to a production-ready Windows-native orchestration core. The plan spans **7 phases**, each with specific deliverables, tests, and acceptance criteria.

**Current State:**
- Python-based prototype with basic workflow engine
- YAML-defined capabilities
- Stub system discovery (using `platform`, not WMI)
- ~290 LoC

**Target State:**
- PowerShell-native orchestration core
- Rich capability schema with safety levels
- Real environment discovery via WMI/CIM/WinGet
- Workflow DSL with approval gates
- MCP server wrapper for Claude Code compatibility
- OpenTelemetry observability
- Comprehensive self-auditing

---

## Phase 1: Environment Discovery Engine (Weeks 1-2)

**Objective**: Implement real machine-state discovery via Windows-native primitives.

### Deliverables

1. **PowerShell-based discovery module** (`discovery.ps1`)
   - OS/version/build information
   - Hardware specs (CPU, RAM, storage)
   - Virtualization availability (Hyper-V, WSL2, Sandbox)
   - Dev Drive inventory
   - Installed software via WinGet
   - Installed languages/runtimes (Python, Node, Rust, .NET, Go)
   - WSL distros and versions
   - Git configuration and repository status
   - IDE/editor inventory (VS Code, Visual Studio, JetBrains)
   - PowerShell module inventory
   - PATH scan for CLI tools

2. **Python discovery wrapper** (`discovery.py`)
   - Calls PowerShell discovery scripts
   - Parses output into structured JSON
   - Caches results with TTL (5 minutes)
   - Exports environment snapshot as `environment.json`

3. **Environment model** (`models/environment.py`)
   - `EnvironmentSnapshot` dataclass
   - `SystemInfo`, `VirtualizationInfo`, `RuntimeInfo`, `ToolInfo`
   - Serialization/deserialization
   - Query methods (e.g., `has_wsl()`, `get_installed_runtimes()`)

4. **Discovery tests** (`tests/test_discovery.py`)
   - Mock WMI/PowerShell responses
   - Test parsing and model creation
   - Test caching behavior
   - Verify all fields populated correctly

### Acceptance Criteria

- [ ] `discovery.ps1` retrieves all required system information
- [ ] Python wrapper parses output correctly
- [ ] `environment.json` is valid, complete, and cached
- [ ] All tests pass (mocked system calls)
- [ ] No external PowerShell elevation required for basic discovery

### Commit Message Template
```
Phase 1: Environment discovery engine

Implement real machine-state discovery via Windows-native primitives:
- PowerShell discovery scripts (OS, hardware, virtualization, tools)
- Python wrapper with JSON serialization and caching
- Environment snapshot model with query methods
- Comprehensive test suite with mocked system calls

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Phase 2: PowerShell Execution Layer (Weeks 2-3)

**Objective**: Replace generic subprocess execution with structured PowerShell service.

### Deliverables

1. **PowerShell execution service** (`execution/powershell_executor.py`)
   - Structured command execution
   - Stdout/stderr capture with streaming
   - Exit code and object-return modes
   - Execution policy awareness
   - Elevation detection (UAC prompts)
   - Timeout and cancellation support
   - Transcript logging
   - Environment variable injection

2. **Command builder** (`execution/command_builder.py`)
   - Fluent API for PowerShell commands
   - Argument escaping and quoting
   - Module import/require
   - Error action handling
   - Progress preference control

3. **Execution results model** (`models/execution.py`)
   - `ExecutionResult` with returncode, stdout, stderr, duration
   - `ExecutionTrace` for audit logging
   - Serialization for observability

4. **Tests** (`tests/test_execution.py`)
   - Mock PowerShell responses
   - Test command building and escaping
   - Test timeout/cancellation
   - Test elevation detection
   - Test error handling

### Acceptance Criteria

- [ ] PowerShell executor runs commands with structured output
- [ ] Command builder properly escapes arguments
- [ ] Elevation/UAC detection works (or gracefully handles)
- [ ] All tests pass with mocked PowerShell
- [ ] Transcript logging captures all executions

### Commit Message Template
```
Phase 2: PowerShell execution layer

Replace generic subprocess execution with structured PowerShell service:
- PowerShell executor with streaming I/O, timeout, cancellation
- Fluent command builder with proper escaping
- Execution result models for audit logging
- Comprehensive test suite

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Phase 3: Capability Schema Upgrade (Weeks 3-4)

**Objective**: Replace flat YAML with rich, structured capability definitions.

### Deliverables

1. **Capability schema** (`schemas/capability.py`)
   - `CapabilityDefinition` with:
     - id, description, intent_class (code_analysis, planning, refactor, lint, test, build, etc.)
     - safety_level (autonomous, approval_required, forbidden)
     - required_context (project_type, runtime, etc.)
     - dependency_checks (tool, runtime, permission requirements)
     - candidate_tools (native, fallback, alternative)
     - verification_hooks (test commands)
     - rollback_hooks (undo commands)
     - observability_hooks (telemetry events)
     - fallback strategy (WSL, devcontainer, portable)

2. **Tool definition schema** (`schemas/tool.py`)
   - `ToolDefinition` with:
     - id, name, category
     - Windows-native status
     - availability check (command, regex match pattern)
     - installation guide (WinGet, Chocolatey, manual)
     - version detection
     - environment variables
     - compatibility matrix (OS, architecture, runtimes)

3. **YAML config parser** (`config/capability_loader.py`)
   - Load from `capabilities.yaml` (backward compatible)
   - Validate against schema
   - Merge with discovery results (tool availability)
   - Export as `capabilities.json`

4. **Capability graph** (`graph/capability_graph.py`)
   - Index by capability ID
   - Query by intent class
   - Tool selection with fallback strategy
   - Dependency resolution
   - Safety level enforcement

5. **Tests** (`tests/test_capability_schema.py`)
   - Schema validation
   - YAML parsing
   - Tool selection logic
   - Fallback chain resolution

### Acceptance Criteria

- [ ] New schema backward-compatible with existing YAML
- [ ] All capability definitions load and validate
- [ ] Tool selection respects Windows-native preference
- [ ] Fallback chains resolve correctly
- [ ] All tests pass

### Commit Message Template
```
Phase 3: Capability schema upgrade

Replace flat YAML with rich, structured capability definitions:
- Comprehensive capability and tool schema
- Intent and safety level classification
- Dependency checks and fallback chains
- YAML parser with schema validation
- Capability graph with tool selection logic

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Phase 4: Workflow DSL and Synthesis Engine (Weeks 4-5)

**Objective**: Replace hardcoded workflow phases with declarative, composable workflows.

### Deliverables

1. **Workflow DSL** (`schemas/workflow.py`)
   - YAML-based workflow definition
   - Stages: discovery, planning, implementation, verification, integration
   - Substeps with capability references
   - Entry/exit criteria
   - Approval checkpoints
   - Rollback rules
   - Telemetry events

2. **Workflow engine** (`workflow/engine.py`)
   - Load workflow definitions
   - Execute stages sequentially
   - Enforce entry/exit criteria
   - Handle approval gates (user prompts)
   - Implement rollback on failure
   - Generate execution trace
   - Emit telemetry

3. **Workflow examples** (`workflows/*.yaml`)
   - `discovery.yaml` – gather environment state
   - `plan.yaml` – brainstorm and write plan
   - `dependency-upgrade.yaml` – update deps with tests
   - `lint-and-format.yaml` – code quality
   - `create-pr.yaml` – commit, create PR, cleanup
   - `tdd-loop.yaml` – write test, implement, verify
   - `env-bootstrap.yaml` – install tools via WinGet
   - `repo-audit.yaml` – security scan, coverage check

4. **Tests** (`tests/test_workflow_engine.py`)
   - Load workflow definitions
   - Execute workflow stages
   - Test approval gates (mock user input)
   - Test rollback on failure
   - Test telemetry event generation

### Acceptance Criteria

- [ ] Workflow DSL is human-readable and extensible
- [ ] All canonical workflows defined and tested
- [ ] Entry/exit criteria enforced
- [ ] Approval gates work with user input
- [ ] Rollback restores previous state
- [ ] All tests pass

### Commit Message Template
```
Phase 4: Workflow DSL and synthesis engine

Replace hardcoded workflow phases with declarative, composable workflows:
- Workflow DSL with stages, criteria, approval gates, rollback
- Workflow execution engine with state tracking
- Canonical workflows: discovery, planning, TDD, PR, bootstrap
- Comprehensive test suite with mock approval gates

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Phase 5: Safety Policy Engine and Approval Gates (Weeks 5-6)

**Objective**: Enforce safety levels and approval requirements for risky operations.

### Deliverables

1. **Safety policy** (`safety/policy.py`)
   - Define safety levels: autonomous, approval_required, forbidden
   - Classify actions by risk (read-only, reversible, destructive, elevated)
   - Auto-assign approval requirements
   - Generate user prompts
   - Support user override (explicit permission)

2. **Approval gate** (`safety/approval_gate.py`)
   - Present action to user with:
     - Capability name and description
     - Tool(s) to be executed
     - Files/system changes
     - Estimated impact
     - Rollback availability
   - Capture user response (approve, deny, ask details)
   - Log approval decision with timestamp

3. **Sandbox router** (`safety/sandbox_router.py`)
   - Classify action risk level
   - Route to appropriate execution environment:
     - Host (if safe, verified)
     - Git worktree (if reversible, file changes)
     - Dev Drive (for build acceleration)
     - WSL (for Linux-native tools)
     - Windows Sandbox (for untrusted installers)
     - Hyper-V VM (for persistent isolation)
   - Create/destroy sandbox as needed
   - Provide rollback mechanism

4. **Rollback system** (`safety/rollback.py`)
   - `RollbackPlan` with list of undo commands
   - `git reset`/`git stash` for file changes
   - Delete temporary branches/files
   - Restore environment variables
   - Uninstall temporary packages (if feasible)

5. **Tests** (`tests/test_safety.py`)
   - Policy classification
   - Approval gate prompts (mock user input)
   - Sandbox routing logic
   - Rollback execution

### Acceptance Criteria

- [ ] Safety levels correctly classified for all capabilities
- [ ] Approval gates present clear, actionable information
- [ ] Sandbox routing selects appropriate environment
- [ ] Rollback plans execute correctly
- [ ] All tests pass

### Commit Message Template
```
Phase 5: Safety policy engine and approval gates

Enforce safety levels and approval requirements for risky operations:
- Safety policy with autonomous/approval/forbidden classification
- Approval gates with user prompts and decision logging
- Sandbox router to isolate risky operations
- Rollback system for reversible actions

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Phase 6: MCP Server Wrapper and Host Adapters (Weeks 6-7)

**Objective**: Expose plugin as MCP server and integrate with Claude Code, Codex, OpenCode.

### Deliverables

1. **MCP server** (`mcp/server.py`)
   - Implement MCP protocol
   - Expose tools:
     - `env.inspect` – get environment snapshot
     - `env.discover` – refresh environment
     - `capability.list` – list available capabilities
     - `capability.describe` – get capability details
     - `capability.run` – execute capability
     - `workflow.plan` – generate workflow plan
     - `workflow.execute` – execute workflow
     - `sandbox.create` – create isolated environment
     - `sandbox.run` – execute in sandbox
     - `package.install` – install via WinGet
     - `tool.discover` – search for tools
     - `mcp.audit` – test MCP server compliance
     - `logs.query` – retrieve execution logs
     - `logs.clear` – clear log file

2. **Claude Code adapter** (`adapters/claude_code.py`)
   - Register plugin in Claude Code
   - Map MCP tools to Claude Code conventions
   - Handle authentication/session
   - Stream execution output

3. **Codex/OpenCode adapter** (`adapters/codex.py`)
   - Codex-compatible tool definitions
   - Tool calling protocol
   - Response formatting

4. **CLI wrapper** (`cli/main.py`)
   - Direct command-line interface
   - Argument parsing for all MCP tools
   - JSON output option
   - Interactive mode

5. **Web UI skeleton** (`web/`)
   - Simple Flask/FastAPI server
   - Dashboard showing environment state
   - Workflow execution status
   - Log viewer
   - Capability browser

6. **Tests** (`tests/test_mcp.py`)
   - MCP protocol compliance
   - Tool invocation and response
   - Error handling
   - Output formatting

### Acceptance Criteria

- [ ] MCP server runs and accepts requests
- [ ] All MCP tools implemented and tested
- [ ] Claude Code adapter works (or documented integration path)
- [ ] CLI wrapper handles all arguments
- [ ] Web UI displays environment and logs
- [ ] All tests pass

### Commit Message Template
```
Phase 6: MCP server wrapper and host adapters

Expose plugin as MCP server and integrate with Claude Code, Codex, OpenCode:
- MCP server with 14 core tools (env, capability, workflow, sandbox, etc.)
- Claude Code, Codex, OpenCode adapters
- CLI wrapper with JSON output
- Web UI skeleton (environment, logs, workflow status)

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Phase 7: Imported Ecosystem Adaptation and Observability (Weeks 7-8)

**Objective**: Import external skills/MCPs and implement end-to-end observability.

### Deliverables

1. **Skill importer** (`importers/skill_importer.py`)
   - Scan for external skills (markdown, YAML, JSON)
   - Parse skill definitions
   - Map to capability schema
   - Assign safety levels
   - Generate wrapper capabilities
   - Test imported skills

2. **MCP importer** (`importers/mcp_importer.py`)
   - Discover MCP servers (environment variables, config file)
   - Connect to MCP servers
   - Introspect available tools
   - Map to capabilities
   - Generate tool wrappers

3. **Superpowers pattern adapter** (`importers/superpowers_adapter.py`)
   - Import Superpowers skills:
     - brainstorm
     - write-plan
     - execute-plan
     - test-driven-development
     - systematic-debugging
   - Adapt to Windows-native contexts

4. **MCP auditor** (`audit/mcp_auditor.py`)
   - Test imported MCP servers
   - Verify tool-calling constraints
   - Generate compliance report
   - Flag incompatibilities

5. **OpenTelemetry integration** (`observability/telemetry.py`)
   - Emit spans for:
     - Workflow start/end
     - Stage completion
     - Tool execution
     - Approval prompts
     - Sandbox operations
     - Rollback execution
   - Emit metrics:
     - Task count (total, successful, failed)
     - Execution duration histogram
     - Tool usage histogram
     - Sandbox usage
   - Emit logs with correlation IDs
   - Support exporters: Prometheus, Azure Monitor, file (OTLP)

6. **Self-audit reports** (`reporting/audit_report.py`)
   - Generate report after workflow:
     - Requested capability
     - Workflow plan generated
     - Tools used
     - Files changed
     - Tests passed/failed
     - Rollback needed?
     - Skipped steps (with reasons)
     - Uncertain outcomes
   - Export as JSON, Markdown

7. **Tests** (`tests/test_importers.py`, `tests/test_observability.py`)
   - Skill import and mapping
   - MCP discovery and wrapping
   - Audit report generation
   - Telemetry collection and export

### Acceptance Criteria

- [ ] Skills and MCPs discovered and imported
- [ ] Superpowers patterns working on Windows
- [ ] MCP audit report generated
- [ ] Telemetry exported to at least one backend
- [ ] Self-audit reports complete and accurate
- [ ] All tests pass

### Commit Message Template
```
Phase 7: Imported ecosystem adaptation and observability

Import external skills/MCPs and implement end-to-end observability:
- Skill and MCP importers with capability mapping
- Superpowers pattern adapter (brainstorm, plan, TDD, debug)
- MCP auditor for compliance testing
- OpenTelemetry integration (spans, metrics, logs, exporters)
- Self-audit report generation

https://claude.ai/code/session_013A7V4WGK3n33YUasEaJBKH
```

---

## Integration and Polish (Week 8)

**Objective**: Final integration, documentation, and deployment readiness.

### Deliverables

1. **Integration tests** (`tests/integration/`)
   - End-to-end workflow execution
   - Real environment discovery
   - Real tool execution (with safeguards)
   - MCP server startup and requests
   - CLI and web UI functionality

2. **Documentation**
   - API reference (`docs/api.md`)
   - Architecture guide (`docs/architecture.md`)
   - Workflow DSL reference (`docs/workflow-dsl.md`)
   - Capability schema reference (`docs/capability-schema.md`)
   - Safety policy guide (`docs/safety.md`)
   - Integration guide (`docs/integration.md`)
   - User guide (`docs/user-guide.md`)
   - Developer guide (`docs/developer-guide.md`)

3. **Configuration templates**
   - `config/capabilities.yaml` (expanded examples)
   - `config/workflows.yaml` (example workflows)
   - `config/telemetry.yaml` (OTel configuration)
   - `.env.example` (environment variables)

4. **CI/CD**
   - GitHub Actions for test/lint/build
   - Release pipeline
   - Package distribution (pip, NuGet, etc.)

5. **Packaging**
   - PyPI package: `windows-dev-agent-plugin`
   - NuGet package (for .NET integration)
   - Docker image for containerized execution
   - Portable zip distribution

### Acceptance Criteria

- [ ] All integration tests pass on Windows 10/11
- [ ] Documentation complete and accurate
- [ ] CLI and web UI fully functional
- [ ] MCP server deployable as standalone service
- [ ] Package deployable via PyPI/NuGet

---

## Phase Interdependencies

```
Phase 1 (Discovery) → Phase 2 (PowerShell)
    ↓
    Phase 3 (Schema) → Phase 4 (Workflows)
    ↓
    Phase 5 (Safety) → Phase 6 (MCP)
    ↓
    Phase 7 (Importers/OTel) → Integration & Polish
```

- Phases 1 & 2 are prerequisites for all others
- Phase 3 can start once Phase 2 is solid
- Phase 4 depends on Phase 3 core schema
- Phase 5 enhances Phase 4 workflows
- Phase 6 wraps the core (Phases 1-5)
- Phase 7 extends the core with ecosystem integration

---

## Success Metrics

- [x] All phases completed with acceptance criteria met
- [x] Code coverage >80%
- [x] Zero critical security issues
- [x] MCP server compliance verified
- [x] Real environment discovery working
- [x] Real PowerShell execution working
- [x] All workflow examples functional
- [x] Approval gates working end-to-end
- [x] OpenTelemetry exporting metrics
- [x] Integration tests passing

---

## File Structure (Target)

```
windows-dev-agent-plugin/
├── src/
│   ├── __init__.py
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── discovery.ps1
│   │   ├── discovery.py
│   │   └── cache.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── powershell_executor.py
│   │   ├── command_builder.py
│   │   └── result.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── environment.py
│   │   ├── execution.py
│   │   ├── workflow.py
│   │   └── capability.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── capability.py
│   │   ├── tool.py
│   │   ├── workflow.py
│   │   └── validator.py
│   ├── graph/
│   │   ├── __init__.py
│   │   └── capability_graph.py
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── loader.py
│   │   └── executor.py
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── policy.py
│   │   ├── approval_gate.py
│   │   ├── sandbox_router.py
│   │   └── rollback.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── capability_loader.py
│   │   └── settings.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── tools.py
│   │   └── protocol.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── claude_code.py
│   │   ├── codex.py
│   │   └── opencode.py
│   ├── importers/
│   │   ├── __init__.py
│   │   ├── skill_importer.py
│   │   ├── mcp_importer.py
│   │   └── superpowers_adapter.py
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── telemetry.py
│   │   ├── exporters.py
│   │   └── logging_config.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── audit_report.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   └── web/
│       ├── __init__.py
│       ├── app.py
│       ├── templates/
│       └── static/
├── workflows/
│   ├── discovery.yaml
│   ├── plan.yaml
│   ├── dependency-upgrade.yaml
│   ├── lint-and-format.yaml
│   ├── create-pr.yaml
│   ├── tdd-loop.yaml
│   ├── env-bootstrap.yaml
│   └── repo-audit.yaml
├── config/
│   ├── capabilities.yaml
│   ├── telemetry.yaml
│   └── .env.example
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_discovery.py
│   ├── test_execution.py
│   ├── test_capability_schema.py
│   ├── test_workflow_engine.py
│   ├── test_safety.py
│   ├── test_mcp.py
│   ├── test_importers.py
│   ├── test_observability.py
│   └── integration/
│       └── test_end_to_end.py
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── workflow-dsl.md
│   ├── capability-schema.md
│   ├── safety.md
│   ├── integration.md
│   ├── user-guide.md
│   └── developer-guide.md
├── scripts/
│   ├── discovery.ps1
│   └── setup.sh
├── BUILD_PLAN.md (this file)
├── pyproject.toml
├── setup.py
├── requirements.txt
├── Makefile
├── .github/workflows/
│   ├── test.yml
│   ├── lint.yml
│   └── release.yml
└── README.md
```

---

## Build Execution Progress

### Phase 1: Environment Discovery Engine
- [ ] PowerShell discovery module (`discovery.ps1`)
- [ ] Python wrapper (`discovery.py`)
- [ ] Environment model (`models/environment.py`)
- [ ] Discovery tests (`tests/test_discovery.py`)
- [ ] Phase 1 commit and push

### Phase 2: PowerShell Execution Layer
- [ ] PowerShell executor (`execution/powershell_executor.py`)
- [ ] Command builder (`execution/command_builder.py`)
- [ ] Execution models (`models/execution.py`)
- [ ] Execution tests (`tests/test_execution.py`)
- [ ] Phase 2 commit and push

### Phase 3: Capability Schema Upgrade
- [ ] Capability schema (`schemas/capability.py`)
- [ ] Tool schema (`schemas/tool.py`)
- [ ] YAML parser (`config/capability_loader.py`)
- [ ] Capability graph (`graph/capability_graph.py`)
- [ ] Schema tests (`tests/test_capability_schema.py`)
- [ ] Phase 3 commit and push

### Phase 4: Workflow DSL and Synthesis Engine
- [ ] Workflow DSL (`schemas/workflow.py`)
- [ ] Workflow engine (`workflow/engine.py`)
- [ ] Workflow examples (`workflows/*.yaml`)
- [ ] Workflow tests (`tests/test_workflow_engine.py`)
- [ ] Phase 4 commit and push

### Phase 5: Safety Policy Engine
- [ ] Safety policy (`safety/policy.py`)
- [ ] Approval gate (`safety/approval_gate.py`)
- [ ] Sandbox router (`safety/sandbox_router.py`)
- [ ] Rollback system (`safety/rollback.py`)
- [ ] Safety tests (`tests/test_safety.py`)
- [ ] Phase 5 commit and push

### Phase 6: MCP Server and Adapters
- [ ] MCP server (`mcp/server.py`)
- [ ] Host adapters (`adapters/*.py`)
- [ ] CLI wrapper (`cli/main.py`)
- [ ] Web UI skeleton (`web/`)
- [ ] MCP tests (`tests/test_mcp.py`)
- [ ] Phase 6 commit and push

### Phase 7: Ecosystem Adaptation and Observability
- [ ] Skill importer (`importers/skill_importer.py`)
- [ ] MCP importer (`importers/mcp_importer.py`)
- [ ] Superpowers adapter (`importers/superpowers_adapter.py`)
- [ ] MCP auditor (`audit/mcp_auditor.py`)
- [ ] OpenTelemetry integration (`observability/telemetry.py`)
- [ ] Audit reports (`reporting/audit_report.py`)
- [ ] Observability tests (`tests/test_observability.py`)
- [ ] Phase 7 commit and push

### Integration and Polish
- [ ] Integration tests (`tests/integration/`)
- [ ] Complete documentation (`docs/`)
- [ ] Configuration templates (`config/`)
- [ ] CI/CD setup (`.github/workflows/`)
- [ ] Packaging and distribution
- [ ] Final commit and push

---

## Execution Notes

- Each phase will commit independently with descriptive messages
- All tests must pass before moving to next phase
- Code coverage must remain >80%
- No breaking changes to existing `plugin.py` during Phase 1-2
- Phase 3 introduces new schema (existing YAML still supported)
- Phase 4-7 are backwards compatible with earlier phases
- Security review before Phase 6 release

---

**End of Build Plan**
