# Agent Framework 接入指南

Mnemosyne V8 MCP Server 支持所有 MCP 兼容的 AI Agent 框架。

## 通用前提

```bash
cd /path/to/Mnemosyne
pip install -e .
```

环境变量：
- `MCP_V8_DB`：V8 数据库路径（默认 `v8/data/v8.db`）

---

## Hermes Agent

在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp_servers:
  mnemosyne:
    command: "python"
    args: ["-m", "mcp_server"]
    env:
      PYTHONPATH: "/path/to/Mnemosyne/v8/src:/path/to/Mnemosyne/scripts"
      MCP_V8_DB: "/path/to/Mnemosyne/v8/data/v8.db"
```

或者用一键命令：

```bash
hermes mcp add mnemosyne --command python --args "-m mcp_server"
```

重启 Hermes：`hermes chat`

---

## OpenClaw

在 `~/.openclaw/openclaw.json` 的 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "mnemosyne": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "transport": "stdio",
      "env": {
        "PYTHONPATH": "/path/to/Mnemosyne/v8/src:/path/to/Mnemosyne/scripts",
        "MCP_V8_DB": "/path/to/Mnemosyne/v8/data/v8.db"
      }
    }
  }
}
```

或者用命令：

```bash
openclaw mcp set mnemosyne '{"command":"python","args":["-m","mcp_server"],"transport":"stdio"}'
openclaw gateway restart
```

验证：`openclaw mcp list`

---

## Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "mnemosyne": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/Mnemosyne/v8/src:/path/to/Mnemosyne/scripts",
        "MCP_V8_DB": "/path/to/Mnemosyne/v8/data/v8.db"
      }
    }
  }
}
```

---

## Cursor

在 `.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "mnemosyne": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/Mnemosyne/v8/src:/path/to/Mnemosyne/scripts",
        "MCP_V8_DB": "/path/to/Mnemosyne/v8/data/v8.db"
      }
    }
  }
}
```

---

## Claude Code

```bash
claude mcp add mnemosyne -- python -m mcp_server
```

---

## Cherry Studio

Settings → MCP → Add Server:
- Name: `mnemosyne`
- Command: `python`
- Args: `-m mcp_server`
- Env: `PYTHONPATH=/path/to/Mnemosyne/v8/src:/path/to/Mnemosyne/scripts`, `MCP_V8_DB=/path/to/Mnemosyne/v8/data/v8.db`

---

## 验证

启动后问 Agent：

```
What tools do you have from the mnemosyne server?
```

应该看到 19 个 `v8_` 前缀的工具。
