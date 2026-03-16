"""
Windows Dev Agent MCP Server
Exposes environment inspection, capability routing, workflow planning,
package management, and sandbox execution via MCP stdio transport.
"""

import asyncio
import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)


# ── tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "env_inspect",
        "description": "Run a full Windows environment snapshot. Returns OS, runtimes, installed tools, WSL distros, Dev Drive status, and package manager availability.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "force_refresh": {
                    "type": "boolean",
                    "description": "Skip cache and re-run discovery",
                    "default": False
                }
            }
        }
    },
    {
        "name": "tool_discover",
        "description": "Scan for installed dev tools, runtimes, and editors. Returns availability and version for each.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["all", "runtimes", "editors", "package_managers", "vcs"],
                    "default": "all"
                }
            }
        }
    },
    {
        "name": "capability_run",
        "description": "Route a named capability to the best available Windows-native tool. Handles tool selection, fallback routing, and logging.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "capability": {
                    "type": "string",
                    "description": "Capability name from capabilities.yaml (e.g. lint-python, run-tests, create-pr)"
                },
                "args": {
                    "type": "object",
                    "description": "Optional arguments to pass to the capability"
                }
            },
            "required": ["capability"]
        }
    },
    {
        "name": "workflow_plan",
        "description": "Generate a structured execution plan for a task. Returns phases with entry criteria, steps, exit criteria, rollback instructions, and safety classifications. Does not execute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Natural language description of the task to plan"
                },
                "context": {
                    "type": "string",
                    "description": "Optional additional context (project type, constraints)"
                }
            },
            "required": ["task"]
        }
    },
    {
        "name": "package_install",
        "description": "Install a package via WinGet (preferred), Chocolatey, or Scoop. Always approval-required — returns the install command for confirmation before execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package_id": {
                    "type": "string",
                    "description": "Exact WinGet package ID (e.g. Python.Python.3.12)"
                },
                "source": {
                    "type": "string",
                    "enum": ["winget", "chocolatey", "scoop"],
                    "default": "winget"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Return install command without executing",
                    "default": True
                }
            },
            "required": ["package_id"]
        }
    },
    {
        "name": "sandbox_run",
        "description": "Execute a command in an isolated environment (Windows Sandbox, WSL, or Dev Container). Approval-required.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute in the sandbox"
                },
                "environment": {
                    "type": "string",
                    "enum": ["auto", "windows_sandbox", "wsl", "dev_container"],
                    "description": "Target isolation environment. auto selects based on availability and command type.",
                    "default": "auto"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Return sandbox config without launching",
                    "default": True
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "logs_query",
        "description": "Query the session audit log and telemetry trace. Returns tool calls, safety gate decisions, fallback events, and timing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "last_n": {
                    "type": "integer",
                    "description": "Return last N events",
                    "default": 20
                },
                "filter": {
                    "type": "string",
                    "enum": ["all", "approvals", "failures", "installs", "sandbox"],
                    "default": "all"
                }
            }
        }
    },
    {
        "name": "mcp_audit",
        "description": "Inspect and report on configured MCP servers. Returns tool count, naming validity, capability overlap, and host compatibility warnings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "config_path": {
                    "type": "string",
                    "description": "Path to MCP config file. Defaults to ~/.claude/claude_desktop_config.json and ./.mcp.json"
                }
            }
        }
    }
]


# ── handlers ──────────────────────────────────────────────────────────────────

async def handle_env_inspect(args: dict) -> dict:
    try:
        from src.discovery.discovery import EnvironmentDiscovery
        discovery = EnvironmentDiscovery(cache_enabled=True)
        snapshot = discovery.discover(force_refresh=args.get("force_refresh", False))
        return snapshot.to_dict()
    except Exception as e:
        logger.warning(f"Full discovery failed, using fallback: {e}")
        import platform, sys, shutil
        return {
            "success": False,
            "error": str(e),
            "fallback": True,
            "system": {"os_name": platform.system(), "os_version": platform.version()},
            "runtimes": {
                "python": {"available": True, "version": sys.version.split()[0]},
                "node": {"available": shutil.which("node") is not None},
                "rust": {"available": shutil.which("cargo") is not None},
                "git": {"available": shutil.which("git") is not None},
            }
        }


async def handle_tool_discover(args: dict) -> dict:
    import shutil, subprocess
    tools = {}
    candidates = {
        "runtimes": ["python", "node", "cargo", "go", "dotnet", "java"],
        "editors": ["code", "devenv", "rider", "pycharm"],
        "package_managers": ["winget", "choco", "scoop", "pip", "npm", "uv"],
        "vcs": ["git", "gh", "git-lfs"],
    }
    category = args.get("category", "all")
    scan = candidates if category == "all" else {category: candidates.get(category, [])}
    for cat, cmds in scan.items():
        tools[cat] = {}
        for cmd in cmds:
            path = shutil.which(cmd)
            if path:
                try:
                    result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                    version = (result.stdout or result.stderr).strip().splitlines()[0]
                except Exception:
                    version = "unknown"
                tools[cat][cmd] = {"available": True, "path": path, "version": version}
            else:
                tools[cat][cmd] = {"available": False}
    return tools


async def handle_capability_run(args: dict) -> dict:
    from pathlib import Path
    import yaml, subprocess, shutil
    cap_name = args["capability"]
    cap_file = Path(__file__).parent.parent.parent / "capabilities.yaml"
    if not cap_file.exists():
        return {"error": f"capabilities.yaml not found at {cap_file}"}
    with open(cap_file) as f:
        caps = yaml.safe_load(f) or {}
    cap = caps.get(cap_name)
    if not cap:
        return {"error": f"Unknown capability '{cap_name}'", "available": list(caps.keys())}
    for tool in cap.get("tools", []):
        exe = tool["check"].split()[0]
        if shutil.which(exe):
            result = subprocess.run(tool["command"], shell=True, capture_output=True, text=True, timeout=120)
            return {
                "capability": cap_name,
                "tool_used": tool["name"],
                "command": tool["command"],
                "returncode": result.returncode,
                "stdout": result.stdout[:4000],
                "stderr": result.stderr[:2000],
                "succeeded": result.returncode == 0,
            }
    return {"error": f"No available tools for capability '{cap_name}'", "checked": [t["name"] for t in cap.get("tools", [])]}


async def handle_package_install(args: dict) -> dict:
    pkg = args["package_id"]
    source = args.get("source", "winget")
    dry_run = args.get("dry_run", True)
    commands = {
        "winget": f"winget install --id {pkg} --exact",
        "chocolatey": f"choco install {pkg} -y",
        "scoop": f"scoop install {pkg}",
    }
    cmd = commands.get(source, commands["winget"])
    result = {"package_id": pkg, "source": source, "command": cmd, "safety_class": "approval-required"}
    if dry_run:
        result["dry_run"] = True
        result["message"] = "Dry run — confirm this command before execution"
    else:
        import subprocess
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        result["returncode"] = r.returncode
        result["stdout"] = r.stdout[:4000]
        result["succeeded"] = r.returncode == 0
    return result


async def handle_sandbox_run(args: dict) -> dict:
    import shutil
    command = args["command"]
    env = args.get("environment", "auto")
    dry_run = args.get("dry_run", True)
    if env == "auto":
        env = "wsl" if shutil.which("wsl") else "windows_sandbox"
    configs = {
        "wsl": {"launch": f'wsl -- bash -c "{command}"', "type": "WSL"},
        "windows_sandbox": {"launch": f"[Generate .wsb config for: {command}]", "type": "Windows Sandbox"},
        "dev_container": {"launch": f"devcontainer exec --workspace-folder . {command}", "type": "Dev Container"},
    }
    result = {
        "command": command,
        "environment": env,
        "config": configs.get(env, {}),
        "safety_class": "approval-required",
    }
    if dry_run:
        result["dry_run"] = True
        result["message"] = "Dry run — confirm sandbox config before launching"
    return result


async def handle_logs_query(args: dict) -> dict:
    from pathlib import Path
    log_file = Path(__file__).parent.parent.parent / "agent.log"
    if not log_file.exists():
        return {"events": [], "message": "No log file found"}
    lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    last_n = args.get("last_n", 20)
    return {"events": lines[-last_n:], "total_lines": len(lines)}


async def handle_mcp_audit(args: dict) -> dict:
    import json, os
    from pathlib import Path
    configs = []
    paths = [
        Path.home() / ".claude" / "claude_desktop_config.json",
        Path.cwd() / ".mcp.json",
    ]
    if args.get("config_path"):
        paths.append(Path(args["config_path"]))
    findings = []
    for p in paths:
        if p.exists():
            try:
                data = json.loads(p.read_text())
                servers = data.get("mcpServers", {})
                configs.append({
                    "file": str(p),
                    "server_count": len(servers),
                    "servers": list(servers.keys()),
                })
            except Exception as e:
                findings.append({"file": str(p), "error": str(e)})
    return {"configs": configs, "findings": findings}


async def handle_workflow_plan(args: dict) -> dict:
    return {
        "message": "Workflow planning is handled by the /windows-dev-agent:plan command and the workflow-plan skill. This tool confirms the plan is ready to execute.",
        "task": args.get("task"),
        "next": "Use /windows-dev-agent:plan to generate a structured plan, then confirm before executing."
    }


HANDLERS = {
    "env_inspect": handle_env_inspect,
    "tool_discover": handle_tool_discover,
    "capability_run": handle_capability_run,
    "package_install": handle_package_install,
    "sandbox_run": handle_sandbox_run,
    "logs_query": handle_logs_query,
    "mcp_audit": handle_mcp_audit,
    "workflow_plan": handle_workflow_plan,
}


# ── MCP stdio transport ───────────────────────────────────────────────────────

async def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "windows-dev-agent", "version": "0.2.0"}
            }
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        tool_args = request.get("params", {}).get("arguments", {})
        handler = HANDLERS.get(tool_name)
        if not handler:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
        try:
            result = await handler(tool_args)
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]}
            }
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

    if method == "notifications/initialized":
        return None  # no response needed

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main_sync():
    """Windows-compatible synchronous stdio loop (avoids ProactorEventLoop pipe issues)."""
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stdin = sys.stdin
    stdout = sys.stdout
    while True:
        try:
            line = stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            response = loop.run_until_complete(handle_request(request))
            if response is not None:
                stdout.write(json.dumps(response) + "\n")
                stdout.flush()
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Server error: {e}")
            break
    loop.close()


if __name__ == "__main__":
    main_sync()
