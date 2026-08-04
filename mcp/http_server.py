"""Run the remote MCP endpoint locally, for testing before deploying.

This imports the *same* handler class Vercel imports from api/mcp.py, so what you test
here is what ships. Useful with a tunnel (cloudflared, ngrok) when you want the Claude
web or mobile app, which can only talk to a public URL, to hit your working copy.

    python3 mcp/http_server.py                 # http://127.0.0.1:8901/api/mcp
    python3 mcp/http_server.py 9000            # another port
    python3 mcp/http_server.py --host 0.0.0.0  # reachable on the LAN

Every path is served by the handler, so the tunnel URL works with or without /api/mcp.
For a local client that can spawn a process, prefer mcp/stdio_server.py: no port, no tunnel.
"""
import importlib.util
import os
import sys
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load api/mcp.py the way Vercel does: the deployment root on sys.path, the function's own
# directory NOT on it. An earlier version added api/ here, which silently satisfied that
# file's `from _core import ...` locally while production failed with ModuleNotFoundError.
# A local harness that is more forgiving than production is worse than no harness.
sys.path.insert(0, ROOT)
_spec = importlib.util.spec_from_file_location("vercel_api_mcp",
                                              os.path.join(ROOT, "api", "mcp.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
handler = _mod.handler                              # the Vercel function, unmodified


def main(argv):
    host, port = "127.0.0.1", int(os.environ.get("PORT") or 8901)
    args = list(argv)
    if "--host" in args:
        host = args.pop(args.index("--host") + 1)
        args.remove("--host")
    if args:
        port = int(args[0])

    srv = ThreadingHTTPServer((host, port), handler)
    shown = "127.0.0.1" if host in ("0.0.0.0", "") else host
    print(f"MCP (streamable http) on http://{shown}:{port}/api/mcp", flush=True)
    print("Ctrl-C to stop.", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped", flush=True)
    finally:
        srv.server_close()


if __name__ == "__main__":
    main(sys.argv[1:])
