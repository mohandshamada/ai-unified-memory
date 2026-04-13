# Migration Guide

This guide walks you through migrating your existing agent memories into the AI Unified Memory canonical store.

## Before You Start

1. Make sure `ai-unified-memory` is installed:
   ```bash
   pip install -e .
   ```

2. Review what will be migrated:
   - Hermes: `~/.hermes/memories/USER.md`, workspace `AGENTS.md`, `MEMORY.md`
   - Claude Code: `~/.claude/projects/*/memory/MEMORY.md`, workspace `CLAUDE.md`
   - OpenClaw: `~/.openclaw/memory/main.sqlite` (metadata only)

## Dry Run

Always preview first:

```bash
python scripts/migrate.py --dry-run
```

This shows you exactly what will be migrated without making any changes.

## Apply Migration

```bash
python scripts/migrate.py --apply
```

Original files are automatically backed up to:
```
~/.agent-memory-backups/YYYYMMDD_HHMMSS/
```

## Post-Migration Steps

1. **Verify canonical store:**
   ```bash
   ls ~/.agent-memory/
   ls ~/.agent-memory/core/
   ls ~/.agent-memory/projects/
   ```

2. **Run sync to set up symlinks:**
   ```bash
   bash scripts/setup.sh
   ```

3. **Register MCP server with each agent** (see `configs/*.md`)

4. **Test:** Start an agent and run:
   ```
   /mcp memory_list_core_keys
   ```

## Troubleshooting

### Duplicate or conflicting memories
If multiple agents have conflicting info for the same project, the migration script preserves both by backing up originals. You can manually merge them in `~/.agent-memory/projects/<name>/memory.md`.

### Missing workspace files
The migration scanner looks in `~`, `~/hive`, and `~/workspace`. If your workspace is elsewhere, create symlinks manually or move the files into the canonical store.

### Restore from backup
If anything goes wrong, simply copy files from `~/.agent-memory-backups/YYYYMMDD_HHMMSS/` back to their original locations.
