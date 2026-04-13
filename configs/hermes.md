# Hermes Configuration

## Overview

Hermes already has a file-based memory system (`SOUL.md`, `USER.md`, workspace `MEMORY.md`). The best approach is to **symlink** those paths to the canonical store and add the MCP server for runtime access.

## Step 1: Symlink Native Memory to Canonical Store

```bash
# Core memories
ln -sf ~/.agent-memory/core/soul.md ~/.hermes/SOUL.md
ln -sf ~/.agent-memory/core/user.md ~/.hermes/memories/USER.md

# For each workspace where Hermes runs:
ln -sf ~/.agent-memory/core/agents.md ./AGENTS.md
ln -sf ~/.agent-memory/core/memory.md ./MEMORY.md

# For project-specific workspaces:
mkdir -p ~/.agent-memory/projects/my-project
ln -sf ~/.agent-memory/projects/my-project/memory.md ./memory/MEMORY.md
```

## Step 2: Add MCP Server to Hermes

Add to `~/.hermes/config.yaml` under `mcp_servers`:

```yaml
mcp_servers:
  ai-unified-memory:
    command: python
    args:
      - -m
      - ai_unified_memory
    env:
      AGENT_NAME: hermes
```

> **Note:** Hermes' MCP config format may vary by version. If `mcp_servers` is not supported, use the `native_mcp` skill or `mcporter` bridge.

## Step 3: Hermes Startup Behavior

Hermes already reads `SOUL.md`, `USER.md`, and workspace `AGENTS.md` on startup. With symlinks in place, it will automatically load the unified memory.

The MCP server provides runtime access for:
- Searching across all memory
- Appending daily notes
- Looking up project-specific context

## Verification

Start Hermes and check:

```text
/mcp memory_list_core_keys
```

Expected output: `["agents", "memory", "soul", "user"]`
