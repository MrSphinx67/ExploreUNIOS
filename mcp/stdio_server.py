#!/usr/bin/env python3
"""Local stdio MCP server for the SUJJS (Osijek) course catalog.

For Claude Desktop and Claude Code, which speak MCP over stdio. The Claude web and
mobile apps cannot use this: they need the remote HTTP endpoint in api/mcp.py.

    python3 mcp/stdio_server.py

Claude Desktop config:
    {"mcpServers": {"unios-courses": {"command": "python3",
                                      "args": ["/abs/path/to/mcp/stdio_server.py"]}}}
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
os.environ.setdefault("ISVU_CACHE", os.path.expanduser("~/.cache/isvu"))

from _core import handle_rpc  # noqa: E402


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        res = handle_rpc(msg)
        if res is not None:
            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
