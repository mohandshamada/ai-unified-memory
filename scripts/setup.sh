#!/bin/bash
# AI Unified Memory - One-shot setup script

set -e

echo "=========================================="
echo "AI Unified Memory - Setup Script"
echo "=========================================="
echo ""

# Check if running from repo
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Please run this script from the ai-unified-memory repository root."
    exit 1
fi

# Install package
echo "[1/5] Installing ai-unified-memory package..."
pip install -e . -q
echo "      Done."
echo ""

# Create memory structure
echo "[2/5] Creating ~/.agent-memory directory structure..."
python -c "from ai_unified_memory.store import MemoryStore; MemoryStore()"
echo "      Created at ~/.agent-memory/"
echo ""

# Setup symlinks
echo "[3/5] Setting up symlinks for existing agents..."
python -c "
from ai_unified_memory.sync import run_full_sync
result = run_full_sync(dry_run=False)
print(f'      Created {len(result[\"created_symlinks\"])} symlinks')
print(f'      Detected and repaired {result[\"drift_repaired\"]} drift issues')
"
echo ""

# Register MCP with agents
echo "[4/5] MCP Server Registration Guide:"
echo ""
echo "  For Claude Code:"
echo "      Add to ~/.claude.json (see configs/claude.md)"
echo ""
echo "  For Kimi Code:"
echo "      Add to ~/.kimi/config.toml (see configs/kimi.md)"
echo ""
echo "  For Hermes:"
echo "      Add to ~/.hermes/config.yaml (see configs/hermes.md)"
echo ""
echo "  For OpenClaw:"
echo "      See configs/openclaw.md for subagent context injection"
echo ""

# Test
echo "[5/5] Testing memory server..."
python -c "
from ai_unified_memory.store import MemoryStore
store = MemoryStore()
keys = store.list_core_keys()
print(f'      Core memories: {keys}')
"
echo ""

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Configure your agents (see configs/*.md)"
echo "  2. Run 'aimemory stdio' to start the MCP server"
echo "  3. Test with: /mcp memory_list_core_keys"
echo ""
