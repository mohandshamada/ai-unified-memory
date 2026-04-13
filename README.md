# AI Unified Memory

An MCP-based unified memory server that lets **Claude Code**, **Kimi Code**, **Hermes**, and **OpenClaw** share the same long-term and project-specific memory.

## Status

✅ **Live and operational**

| Component | Status |
|-----------|--------|
| Core Server | ✅ Running |
| MCP Gateway | ✅ Exposed at `https://mcp.mshousha.uk` |
| Hermes Integration | ✅ Connected (8 tools available) |
| Memory Store | ✅ Initialized at `~/.agent-memory/` |

## Quick Start

```bash
# Install
git clone https://github.com/mohandshamada/ai-unified-memory.git
cd ai-unified-memory
pip install -e .

# Run locally
python -m ai_unified_memory

# Or connect to public gateway
curl -H "Authorization: Bearer $TOKEN" \
     https://mcp.mshousha.uk/sse
```

## Available Tools

| Tool | Description |
|------|-------------|
| `memory_read` | Read from core, projects, or daily sections |
| `memory_write` | Write to core or project memory |
| `memory_search` | Full-text search across all memory |
| `memory_append_daily` | Append to today's daily notes |
| `memory_get_project_context` | Get unified context for a project |
| `memory_list_projects` | List all projects with memory |
| `memory_create_project` | Create a new project memory |
| `memory_list_core_keys` | List available core memory keys |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT LAYER                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  Claude │  │  Kimi   │  │ Hermes  │  │ OpenClaw│            │
│  │  Code   │  │  Code   │  │   ✅    │  │         │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                         │                                       │
│                    MCP Protocol                                 │
│                         │                                       │
└─────────────────────────┼───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│          MCP MEMORY SERVER (ai-unified-memory)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ memory_read  │  │memory_write  │  │memory_search │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │memory_append_│  │memory_get_   │                             │
│  │    daily     │  │project_ctx   │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              CANONICAL FILE STORE (~/.agent-memory/)            │
│  core/           daily/           projects/         skills/      │
│  ├── user.md     └── YYYY-MM-DD  ├── cashflow/     └── ...      │
│  ├── agents.md                   │   └── memory.md              │
│  ├── soul.md                     ├── hive/                      │
│  └── memory.md                   │   └── memory.md              │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Structure

The canonical store at `~/.agent-memory/` contains:

- **`core/`** — Global memories shared across all projects:
  - `user.md` — User profile (name, preferences, timezone)
  - `agents.md` — Shared behavior rules for all agents
  - `soul.md` — Agent identity/values
  - `memory.md` — Long-term learnings and decisions

- **`daily/`** — Daily notes organized by date (`YYYY-MM-DD.md`)

- **`projects/`** — Project-specific memories:
  - `cashflow/memory.md`
  - `hive/memory.md`
  - etc.

- **`skills/`** — Shared skill documentation

## Agent Configuration

### Hermes (Current Agent)

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  ai_unified_memory:
    command: "/root/.hermes/hermes-agent/venv/bin/python"
    args: ["-m", "ai_unified_memory"]
    env:
      AGENT_NAME: "hermes"
```

Symlink native memory paths:
```bash
ln -sf ~/.agent-memory/core/soul.md ~/.hermes/SOUL.md
ln -sf ~/.agent-memory/core/user.md ~/.hermes/memories/USER.md
```

### Claude Code

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "ai-unified-memory": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ai_unified_memory"],
      "env": {"AGENT_NAME": "claude-code"}
    }
  }
}
```

### Kimi Code

Add to `~/.kimi/config.toml`:

```toml
[mcp.servers.ai-unified-memory]
command = "python"
args = ["-m", "ai_unified_memory"]
env = { AGENT_NAME = "kimi-code" }
```

### OpenClaw

OpenClaw injects context into subagent prompts. Add MCP config for subagents that support it, or preload context.

See `configs/openclaw.md` for full details.

### MCP Gateway (Public Exposure)

To expose via [MCP-GATEWAY](https://github.com/mohandshamada/MCP-GATEWAY):

```bash
# Create wrapper script
cat > /home/MCP-GATEWAY/scripts/ai-unified-memory.sh << 'EOF'
#!/bin/bash
export PYTHONPATH="/mnt/HC_Volume_104832602/ai-unified-memory/src:$PYTHONPATH"
exec /root/.hermes/hermes-agent/venv/bin/python -m ai_unified_memory
EOF
chmod +x /home/MCP-GATEWAY/scripts/ai-unified-memory.sh
```

Add to `config/gateway.json`:

```json
{
  "id": "ai-unified-memory",
  "transport": "stdio",
  "command": "/home/MCP-GATEWAY/scripts/ai-unified-memory.sh",
  "args": [],
  "enabled": true,
  "timeout": 60000
}
```

See `configs/mcp-gateway.md` for full setup.

## Development

```bash
# Run tests
pytest tests/

# Run the server
python -m ai_unified_memory stdio

# Or with SSE transport
python -m ai_unified_memory sse --host 127.0.0.1 --port 8080
```

## Project Structure

```
ai-unified-memory/
├── src/ai_unified_memory/
│   ├── __init__.py
│   ├── server.py       # FastMCP server
│   ├── store.py        # File storage backend
│   ├── models.py       # Pydantic models
│   ├── sync.py         # Symlink & drift management
│   └── cli.py          # CLI entry point
├── configs/
│   ├── claude.md
│   ├── kimi.md
│   ├── hermes.md
│   ├── openclaw.md
│   └── mcp-gateway.md
├── scripts/
│   ├── setup.sh        # One-shot setup
│   └── migrate.py      # Migration from existing memories
├── tests/
└── docs/
```

## Implementation Stages

1. ✅ **Project Scaffold** — README, pyproject.toml, directory structure
2. ✅ **Core Memory Server** — FastMCP server with 8 tools
3. ✅ **Agent Configurations** — Setup guides for all 4 agents
4. ✅ **Sync Layer & Tests** — Symlink helpers, drift detection, pytest suite
5. ✅ **Migration Scripts** — Migration tool + guide

## License

MIT
