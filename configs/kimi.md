# Kimi Code Configuration

## Overview

Kimi Code has minimal native file-based memory. The best approach is to connect it entirely through the MCP server so all memory is dynamically fetched at runtime.

## Configuration

Add the MCP server to `~/.kimi/config.toml` under the `[mcp.servers]` section:

```toml
[mcp.client]
tool_call_timeout_ms = 60000

[mcp.servers.ai-unified-memory]
command = "python"
args = ["-m", "ai_unified_memory"]
env = { AGENT_NAME = "kimi-code" }
```

## Important Notes

- Kimi Code does **not** natively read `MEMORY.md` or `AGENTS.md` files.
- All shared context must come through MCP tools.
- At the start of each session, Kimi will call `memory_get_project_context` if you prime it.

## Prompt Priming (Recommended)

Add this to your Kimi system prompt or first message:

```text
Before we start, please use the memory_get_project_context tool with the current project path to load shared memory. Also read core memories with memory_read(section="core", key="user") and memory_read(section="core", key="agents").
```

## Verification

Start Kimi Code in a project directory and run:

```text
/mcp memory_list_core_keys
```

Expected output: `["agents", "memory", "soul", "user"]`
