#!/usr/bin/env python3
"""MCP Server entry point for external agent frameworks (Hermes, OpenClaw, etc.)

Usage in Hermes config.yaml:
  mcp_servers:
    mnemosyne:
      command: "python"
      args: ["path/to/Mnemosyne/scripts/mcp_server/serve_mcp.py"]
      env:
        MCP_V8_DB: "path/to/Mnemosyne/v8/data/v8.db"

Usage in OpenClaw openclaw.json:
  "mcpServers": {
    "mnemosyne": {
      "command": "python",
      "args": ["path/to/Mnemosyne/scripts/mcp_server/serve_mcp.py"],
      "transport": "stdio",
      "env": {
        "MCP_V8_DB": "path/to/Mnemosyne/v8/data/v8.db"
      }
    }
  }
"""

import sys
import os
from pathlib import Path

scripts_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(scripts_dir))

root_dir = scripts_dir.parent
v8_src = root_dir / "v8" / "src"
if v8_src.exists():
    sys.path.insert(0, str(v8_src))

from mcp_server import main

if __name__ == "__main__":
    main()
