# AI Unified Memory

An MCP-based unified memory server that lets **Claude Code**, **Kimi Code**, **Hermes**, and **OpenClaw** share the same long-term and project-specific memory.

## Problem

Each AI agent stores memory in its own silo:
- Claude Code → `~/.claude/projects/.../memory/MEMORY.md`
- Hermes → `~/.hermes/memories/`, workspace `MEMORY.md`
- Kimi Code → minimal native memory
- OpenClaw → orchestrates subagents but can't inject shared context

This means learnings, user preferences, and project context get fragmented or lost when switching agents.

## Solution

A **single canonical file store** (`~/.agent-memory/`) plus an **MCP Memory Server** that all agents can read from and write to at runtime.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT LAYER                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  Claude │  │  Kimi   │  │ Hermes  │  │ OpenClaw│            │
│  │  Code   │  │  Code   │  │         │  │         │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                         │                                       │
│                    MCP Protocol                                 │
│                         │                                       │
└─────────────────────────┼───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MCP MEMORY SERVER                              │
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
│  ├── user.md     └── 2026-04-13  ├── cashflow/     └── ...      │
│  ├── agents.md                   │   └── memory.md              │
│  ├── soul.md                     ├── hive/                      │
│  ├── memory.md                   │   └── memory.md              │
│  └── ...                         └── ...                        │
└─────────────────────────────────────────────────────────────────┘
```

## Stages

1. **Project Scaffold** ✅ — README, architecture, plan
2. **Core Memory Server** — FastMCP server with read/write/search/append tools
3. **Agent Configurations** — Config templates for Claude, Kimi, Hermes, OpenClaw
4. **Sync Layer & Tests** — Symlink helpers, drift detection, pytest suite
5. **Migration Scripts** — One-shot migration from existing Hermes/Claude memories

## Quick Start

```bash
# Install
pip install -e .

# Start the MCP server
python -m ai_unified_memory

# Or via stdio (for MCP clients)
python -m ai_unified_memory --stdio
```

## Agent Integration

See `configs/` for per-agent setup instructions:
- `configs/claude.md`
- `configs/kimi.md`
- `configs/hermes.md`
- `configs/openclaw.md`

## License

MIT
