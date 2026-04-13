# Claude Code Configuration

## Overview

Claude Code supports MCP servers natively via `~/.claude.json` (global) or `.mcp.json` (per-project).

## Option A: Global MCP Server (Recommended)

Add the following to `~/.claude.json` under the `"/root"` (or your default work dir) project:

```json
{
  "projects": {
    "/root": {
      "mcpServers": {
        "ai-unified-memory": {
          "type": "stdio",
          "command": "python",
          "args": [
            "-m",
            "ai_unified_memory"
          ],
          "env": {
            "AGENT_NAME": "claude-code"
          }
        }
      }
    }
  }
}
```

## Option B: Project-Level MCP Server

Create `.mcp.json` in any project root:

```json
{
  "mcpServers": {
    "ai-unified-memory": {
      "type": "stdio",
      "command": "python",
      "args": [
        "-m",
        "ai_unified_memory"
      ],
      "env": {
        "AGENT_NAME": "claude-code"
      }
    }
  }
}
```

## File Memory Symlink Strategy

Claude Code reads `CLAUDE.md` and `memory/MEMORY.md` natively. To unify these with the canonical store, create symlinks in your project roots:

```bash
# In each project directory where you want unified memory:
ln -s ~/.agent-memory/core/agents.md ./CLAUDE.md
mkdir -p memory
ln -s ~/.agent-memory/projects/my-project/memory.md ./memory/MEMORY.md
```

> **Note:** `CLAUDE.md` can reference external files, so you can also use `@~/.agent-memory/core/memory.md` within a `CLAUDE.md` file.

## Verification

After restarting Claude Code, run:

```bash
/mcp memory_list_core_keys
```

You should see: `["agents", "memory", "soul", "user"]`
