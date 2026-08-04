"""Remote MCP endpoint (Streamable HTTP) for the UNIZG course catalog.

Deployed as a Vercel Python function, so it ships with the website: POST JSON-RPC to
/api/mcp. Remote HTTP is what the Claude web and mobile apps need; the local stdio
variant lives in mcp/stdio_server.py.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Vercel puts the deployment root (/var/task) on sys.path, not the function's own directory,
# so a bare `import _core` fails there while working anywhere that runs this from api/. Add
# our own directory rather than relying on the caller's sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _core import handle_rpc  # noqa: E402  (needs the path above)

INFO = {
    "name": "unizg-courses",
    "transport": "streamable-http",
    "endpoint": "/api/mcp",
    "usage": "POST JSON-RPC 2.0. Add this URL as a custom connector in the Claude app.",
    "scope": "UNIZG course catalog: courses, curricula, literature, prerequisites. Not a people directory.",
}


class handler(BaseHTTPRequestHandler):
    def _wants_sse(self):
        return "text/event-stream" in (self.headers.get("Accept") or "")

    def _send(self, code, payload, ctype="application/json"):
        body = (payload if isinstance(payload, (bytes, bytearray))
                else json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Mcp-Session-Id, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _send_rpc(self, payload):
        """Answer in whichever framing the client asked for.

        Streamable HTTP allows a JSON-RPC response to come back as one JSON object or as an
        SSE stream, and the client states its preference in Accept. Clients that ask for
        text/event-stream and get application/json can sit there waiting for a stream that
        never arrives, which looks exactly like the server not responding.
        """
        if not self._wants_sse():
            return self._send(200, payload)
        data = json.dumps(payload, ensure_ascii=False)
        self._send(200, f"event: message\ndata: {data}\n\n".encode("utf-8"),
                   ctype="text/event-stream")

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        # GET is for opening a server-initiated stream, which this server does not do: it is
        # stateless and only ever answers a POST. Say so properly instead of handing back an
        # unrelated 200, which a client would try to parse as a stream.
        if self._wants_sse():
            self.send_response(405)
            self.send_header("Allow", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send(200, INFO)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            msg = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, TypeError) as e:
            return self._send(400, {"jsonrpc": "2.0", "id": None,
                                    "error": {"code": -32700, "message": f"Parse error: {e}"}})
        # A client may batch several calls in one array.
        if isinstance(msg, list):
            out = [r for r in (handle_rpc(m) for m in msg) if r is not None]
            return self._send_rpc(out) if out else self._send(202, b"")
        res = handle_rpc(msg)
        if res is None:                      # notification, nothing to return
            return self._send(202, b"")
        return self._send_rpc(res)

    def log_message(self, *a):               # keep Vercel logs quiet
        pass
