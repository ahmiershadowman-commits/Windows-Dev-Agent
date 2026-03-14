# Windows Dev Agent Plugin (Prototype)

This repository contains a **prototype implementation** of the Windows‑native agent plugin described in the accompanying design report.  The goal of this plugin is to provide a single control surface for agent‑driven development tasks on Windows by building on native primitives such as PowerShell, WinGet, WMI, MSBuild, WSL, and Dev Drive.

## What it does

* **Capability → Workflow → Tool resolution** – You ask the plugin to perform a high‑level capability (e.g. `lint-python` or `update-dependencies`).  The plugin determines the appropriate workflow (discovery → planning → implementation → verification → integration) and selects tools to satisfy each step.
* **System introspection** – The plugin gathers information about the machine using WMI and PowerShell to discover installed software, available runtimes, virtualization support, WSL distros, etc.  In this prototype, the discovery phase uses Python’s `platform` and `subprocess` modules as a placeholder for more detailed WMI queries.
* **Dependency checks** – Before executing a task, the plugin verifies that the necessary tools are installed.  If not, it suggests installing them via WinGet or using an alternative runtime (e.g. WSL).  In the prototype, the check is stubbed out with basic `shutil.which` lookups.
* **Workflow engine skeleton** – The plugin defines the five workflow phases (`discovery`, `planning`, `implementation`, `verification`, and `integration`) and runs them in sequence.  Each phase logs its actions to a log file (`agent.log`) and prints a summary to the console.  The implementation phase demonstrates how a specific capability such as `lint-python` can run a tool (`ruff`) via `subprocess`.
* **Extensible capability graph** – Capabilities and their candidate tools are defined in a YAML configuration file (`capabilities.yaml`).  You can extend the graph by adding new entries.  The plugin picks the first available tool for each capability.

## Prototype limitations

This code is **not a full implementation** of the design report.  It is intended to illustrate the architecture and provide a starting point for further development.  Key features not implemented include:

* Full WMI/WMI queries and virtualization management via Hyper‑V or Windows Sandbox.
* Real integration with WinGet, PowerShell modules, VS Code MCP servers, or external agent frameworks.
* Comprehensive logging with OpenTelemetry.
* Complex planning heuristics or automatic fallback to WSL/dev containers.

Please treat this as a proof of concept and adapt/extend it according to your environment and needs.

## Installation

This plugin is a plain Python project that requires Python 3.9+ and PyYAML.  To install dependencies:

```bash
pip install pyyaml
```

Clone this repository or copy the files into your project.  The main entry point is `plugin.py`.

## Usage

Run the plugin with a capability name:

```bash
python plugin.py lint-python
python plugin.py update-dependencies
```

The plugin will run through the discovery and planning phases, check that the required tool is installed, and then execute the implementation and verification phases.  Results are logged to `agent.log`.

## Adding capabilities and tools

Capabilities and their associated tools are defined in `capabilities.yaml` in the following format:

```yaml
lint-python:
  description: Lint Python code using available linters
  tools:
    - name: ruff
      command: ruff .
      check: ruff --version
    - name: pylint
      command: pylint src/
      check: pylint --version

update-dependencies:
  description: Update Python dependencies using uv
  tools:
    - name: uv
      command: uv pip sync
      check: uv --version
```

The plugin reads this file at startup, picks the first tool whose `check` command succeeds, and uses its `command` for the implementation phase.

## License

This prototype is provided as‑is under the MIT license.  It contains no proprietary code and may be freely modified.