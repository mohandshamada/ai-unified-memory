# AI Unified Memory - Implementation Plan

## Stage 1: Project Scaffold ✅
Status: Complete

**Deliverables:**
- [x] README.md with architecture overview
- [x] pyproject.toml with dependencies
- [x] .gitignore
- [x] Directory structure (src/, tests/, configs/, scripts/, docs/)
- [x] PLAN.md (this file)
- [x] Initial commit to GitHub

---

## Stage 2: Core Memory Server ✅
Status: Complete

**Deliverables:**
- [x] `src/ai_unified_memory/__init__.py` - package init
- [x] `src/ai_unified_memory/server.py` - FastMCP server with tools:
  - `memory_read(section: str, key: str) -> str`
  - `memory_write(section: str, key: str, content: str) -> bool`
  - `memory_search(query: str, scope: str = "all") -> list`
  - `memory_append_daily(content: str, tags: list = []) -> bool`
  - `memory_get_project_context(project_path: str) -> dict`
  - `memory_list_projects() -> list`
  - `memory_create_project(name: str) -> bool`
- [x] `src/ai_unified_memory/store.py` - File system operations
  - Read/write markdown files
  - Handle YAML frontmatter for metadata
  - Search with FTS (sqlite-fts or simple grep fallback)
- [x] `src/ai_unified_memory/models.py` - Pydantic models for memory entries
- [x] `src/ai_unified_memory/cli.py` - CLI entry point

**File Store Layout:**
```
~/.agent-memory/
├── core/
│   ├── user.md          # User profile (name, prefs, timezone)
│   ├── agents.md        # Shared agent behavior rules
│   ├── soul.md          # Agent identity/values
│   └── memory.md        # Global long-term memory
├── daily/
│   └── 2026-04-13.md    # Daily notes (YYYY-MM-DD.md)
├── projects/
│   └── {project_name}/
│       └── memory.md    # Project-specific memory
└── skills/
    └── {skill_name}/
        └── SKILL.md     # Shared skills
```

**Commit Point:** Stage 2 complete

---

## Stage 3: Agent Configurations ✅
Status: Complete

**Deliverables:**
- [x] `configs/claude.md` - Claude Code setup:
  - How to add MCP server to `~/.claude.json`
  - Symlink strategy for `CLAUDE.md`
  - Example `.mcp.json` for project-level config
  
- [x] `configs/kimi.md` - Kimi Code setup:
  - Add to `~/.kimi/config.toml` [mcp.servers] section
  - Since Kimi has no native file memory, rely entirely on MCP
  
- [x] `configs/hermes.md` - Hermes setup:
  - Symlink `~/.hermes/SOUL.md` → `~/.agent-memory/core/soul.md`
  - Symlink `~/.hermes/memories/USER.md` → `~/.agent-memory/core/user.md`
  - Add MCP server to `~/.hermes/config.yaml`
  
- [x] `configs/openclaw.md` - OpenClaw setup:
  - Configure to inject `~/.agent-memory/core/` context into subagent prompts
  - MCP server registration in `~/.openclaw/`

**Commit Point:** Stage 3 complete

---

## Stage 4: Sync Layer & Tests ✅
Status: Complete

**Deliverables:**
- [x] `src/ai_unified_memory/sync.py` - Sync helpers:
  - `ensure_symlinks()` - Create/update symlinks for Hermes/Claude
  - `check_drift()` - Detect if agents wrote to native paths instead of canonical
  - `repair_drift()` - Merge divergent files
  
- [x] `scripts/setup.sh` - One-shot setup script:
  - Create `~/.agent-memory/` structure
  - Migrate existing memories
  - Set up symlinks
  - Register MCP server with each agent
  
- [x] `tests/test_server.py` - pytest suite:
  - Test each MCP tool
  - Test concurrent writes
  - Test search functionality
  
- [x] `tests/test_store.py` - File system tests:
  - YAML frontmatter parsing
  - Markdown read/write
  - FTS search
  
- [x] `tests/test_sync.py` - Sync tests:
  - Symlink creation
  - Drift detection

**Commit Point:** Stage 4 complete

---

## Stage 5: Migration Scripts ✅
Status: Complete

**Deliverables:**
- [x] `scripts/migrate.py` - Migration tool:
  - Detect existing Hermes memories (`~/.hermes/memories/`, workspace `MEMORY.md`)
  - Detect existing Claude memories (`~/.claude/projects/*/memory/MEMORY.md`)
  - Merge into canonical store with conflict resolution
  - Backup original files
  
- [x] Migration guide in `docs/migration.md`

**Commit Point:** Stage 5 complete

---

## Post-MVP Ideas (Future)

- **Vector search** - Embed memory chunks for semantic search
- **Web dashboard** - Browse and edit memory via web UI
- **Conflict resolution UI** - When drift is detected, interactive merge
- **Encryption** - Encrypt sensitive memory at rest
- **Cloud sync** - Sync to S3/GCS for multi-machine use
- **Obsidian integration** - Use Obsidian vault as the canonical store

---

## Current Stage

Working on **Stage 1: Project Scaffold**
