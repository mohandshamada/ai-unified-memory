# MCP Gateway Configuration

This guide shows how to expose the AI Unified Memory server through an MCP gateway (like [MCP-GATEWAY](https://github.com/mohandshamada/MCP-GATEWAY)).

## Installation on Gateway Host

```bash
git clone https://github.com/mohandshamada/ai-unified-memory.git /mnt/HC_Volume_104832602/ai-unified-memory
cd /mnt/HC_Volume_104832602/ai-unified-memory
pip install -e . --break-system-packages
```

## Wrapper Script

Create `/home/MCP-GATEWAY/scripts/ai-unified-memory.sh`:

```bash
#!/bin/bash
export PYTHONPATH="/mnt/HC_Volume_104832602/ai-unified-memory/src:$PYTHONPATH"
exec /root/.hermes/hermes-agent/venv/bin/python -m ai_unified_memory
```

Make it executable:
```bash
chmod +x /home/MCP-GATEWAY/scripts/ai-unified-memory.sh
```

## Gateway Config

Add to your gateway's `config/gateway.json` under the `servers` array:

```json
{
  "id": "ai-unified-memory",
  "transport": "stdio",
  "command": "/home/MCP-GATEWAY/scripts/ai-unified-memory.sh",
  "args": [],
  "enabled": true,
  "lazyLoad": false,
  "timeout": 60000,
  "maxRetries": 3,
  "env": {
    "AGENT_NAME": "mcp-gateway"
  }
}
```

## Restart Gateway

```bash
systemctl restart mcp-gateway
```

## Verify

Check the gateway admin API:

```bash
curl -H "Authorization: Bearer <token>" \
     https://mcp.yourdomain.com/admin/status
```

You should see `ai-unified-memory` listed with 8 healthy tools.
