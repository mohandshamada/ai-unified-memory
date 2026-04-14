"""Health checks for various agents and services."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str  # "ok", "warning", "error"
    message: str
    details: dict[str, Any] | None = None


def check_hermes() -> CheckResult:
    """Check Hermes configuration health."""
    config_path = Path.home() / ".hermes" / "config.yaml"
    
    if not config_path.exists():
        return CheckResult("Hermes", "error", "Config file not found")
    
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        mcp_servers = config.get("mcp_servers", {})
        has_unified_memory = "ai_unified_memory" in mcp_servers
        
        model = config.get("model", {})
        default_model = model.get("default", "unknown")
        
        details = {
            "config_version": config.get("_config_version", "unknown"),
            "default_model": default_model,
            "unified_memory_connected": has_unified_memory,
            "mcp_servers_count": len(mcp_servers),
        }
        
        if has_unified_memory:
            return CheckResult("Hermes", "ok", f"Running ({default_model})", details)
        else:
            return CheckResult("Hermes", "warning", f"Running but no unified memory ({default_model})", details)
    except Exception as e:
        return CheckResult("Hermes", "error", str(e))


def check_openclaw() -> CheckResult:
    """Check OpenClaw service status."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "openclaw-gateway.service"],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_active = result.stdout.strip() == "active"
        
        gateway_info = {}
        try:
            result = subprocess.run(
                ["openclaw", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            gateway_info["status_output"] = result.stdout[:200] if result.stdout else "No output"
        except Exception:
            gateway_info["status_output"] = "Could not get status"
        
        details = {
            "service_active": is_active,
            "gateway_info": gateway_info,
        }
        
        if is_active:
            return CheckResult("OpenClaw", "ok", "Gateway running", details)
        else:
            return CheckResult("OpenClaw", "error", "Gateway not running", details)
    except Exception as e:
        return CheckResult("OpenClaw", "error", str(e))


def check_mcp_gateway() -> CheckResult:
    """Check local MCP gateway health."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "mcp-gateway"],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_active = result.stdout.strip() == "active"
        
        # Try to count tools from config if a gateway config path is set
        tool_count = 0
        gateway_config_env = os.environ.get("MCP_GATEWAY_CONFIG")
        if gateway_config_env:
            try:
                gateway_config = Path(gateway_config_env)
                if gateway_config.exists():
                    with open(gateway_config) as f:
                        data = json.load(f)
                        servers = data.get("servers", [])
                        for server in servers:
                            if server.get("enabled"):
                                tool_count += server.get("tools", 0)
            except Exception:
                pass
        
        details = {
            "service_active": is_active,
            "tool_count": tool_count,
        }
        
        if is_active:
            msg = f"Running with {tool_count} tools" if tool_count else "Running"
            return CheckResult("MCP Gateway", "ok", msg, details)
        else:
            return CheckResult("MCP Gateway", "error", "Not running", details)
    except Exception as e:
        return CheckResult("MCP Gateway", "error", str(e))


def check_unified_memory() -> CheckResult:
    """Check AI Unified Memory store."""
    try:
        try:
            from ai_unified_memory.store import MemoryStore
            from ai_unified_memory.sync import check_drift, get_hermes_mappings, get_claude_mappings
        except ImportError:
            ai_unified_path = os.environ.get("AI_UNIFIED_MEMORY_PATH")
            if ai_unified_path:
                sys.path.insert(0, str(Path(ai_unified_path) / "src"))
                from ai_unified_memory.store import MemoryStore
                from ai_unified_memory.sync import check_drift, get_hermes_mappings, get_claude_mappings
            else:
                raise ImportError(
                    "ai-unified-memory not found. Install it or set AI_UNIFIED_MEMORY_PATH."
                )
        
        store = MemoryStore()
        
        projects = len(store.list_projects())
        core = len(store.list_core_keys())
        
        drift = check_drift(get_hermes_mappings() + get_claude_mappings())
        drift_count = len(drift)
        
        total_size = sum(f.stat().st_size for f in store.base_path.rglob("*") if f.is_file())
        size_mb = round(total_size / (1024 * 1024), 2)
        
        details = {
            "projects": projects,
            "core_memories": core,
            "drift_count": drift_count,
            "size_mb": size_mb,
        }
        
        if drift_count == 0:
            return CheckResult("Unified Memory", "ok", f"{projects} projects, {core} core, {size_mb} MB", details)
        else:
            return CheckResult("Unified Memory", "warning", f"{drift_count} drift issues detected", details)
    except Exception as e:
        return CheckResult("Unified Memory", "error", str(e))


def check_disk() -> CheckResult:
    """Check disk usage."""
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            usage = parts[4]  # e.g., "83%"
            used_gb = parts[2]
            total_gb = parts[1]
            
            usage_pct = int(usage.rstrip("%"))
            details = {
                "usage_percent": usage_pct,
                "used": used_gb,
                "total": total_gb,
            }
            
            if usage_pct > 90:
                return CheckResult("Disk", "error", f"Critical: {usage}", details)
            elif usage_pct > 80:
                return CheckResult("Disk", "warning", f"High: {usage}", details)
            else:
                return CheckResult("Disk", "ok", f"{usage} used", details)
    except Exception as e:
        return CheckResult("Disk", "error", str(e))


def run_all_checks() -> list[CheckResult]:
    """Run all health checks."""
    return [
        check_hermes(),
        check_openclaw(),
        check_mcp_gateway(),
        check_unified_memory(),
        check_disk(),
    ]
