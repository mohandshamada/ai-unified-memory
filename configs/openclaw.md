# OpenClaw Configuration

## Overview

OpenClaw is an orchestrator that spawns subagents (`kimi`, `claude-code`, `opencode`). Unified memory works best when OpenClaw **injects shared context into every subagent prompt** and registers the MCP server so subagents can read/write at runtime.

## Subagent Context Injection

When OpenClaw spawns a subagent, prepend the following context to its prompt:

```text
## Shared Memory Context

You have access to a unified memory system via MCP tools. At the start of this task:
1. Call `memory_get_project_context(project_path="{project_path}")` to load relevant context.
2. Call `memory_read(section="core", key="user")` to load the user profile.
3. Call `memory_read(section="core", key="agents")` to load shared behavior rules.

Available memory tools:
- memory_read(section, key)
- memory_write(section, key, content, tags)
- memory_search(query, scope)
- memory_append_daily(content, tags)
- memory_get_project_context(project_path)
- memory_list_projects()
- memory_create_project(name, path)
- memory_list_core_keys()
```

## MCP Server Registration

OpenClaw should pass MCP server config to subagents that support it (Claude Code, Kimi Code). Example config block to inject:

```json
{
  "mcpServers": {
    "ai-unified-memory": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ai_unified_memory"],
      "env": {
        "AGENT_NAME": "{agent_name}"
      }
    }
  }
}
```

## File Memory for Native Agents

Some subagents (like Hermes) read files natively instead of using MCP. For these, ensure the workspace has symlinks:

```bash
ln -sf ~/.agent-memory/core/agents.md ./AGENTS.md
ln -sf ~/.agent-memory/core/memory.md ./MEMORY.md
```

## Recommended: Preload Key Memories

In `~/.openclaw/openclaw.json` (or equivalent config), add a `memory_preload` section:

```json
{
  "memory_preload": {
    "enabled": true,
    "core_keys": ["user", "agents", "memory"],
    "project_lookup": true
  }
}
```

This tells OpenClaw to fetch core memories before dispatching any task.
