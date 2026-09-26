"""Receive bulk data pushed out of Roblox Studio.

Why this exists: the Studio MCP can read instance properties back to me, but a
602 KB telemetry blob costs ~200 K tokens to pull through the tool boundary.
The Studio plugin, however, can make an HTTP request. So instead of the data
coming *to me*, I stand up this listener and the plugin pushes the bytes
straight to disk. Nothing large ever enters the conversation.

Usage:
    python _tools/receive.py [--port 8765] [--dir D:/rblxTRGproject/Data]
Then from Studio (plugin VM):
    game:GetService("HttpService"):PostAsync("http://127.0.0.1:8765/<name>", payload)

The server appends a newline-delimited receipt to stdout after every write:
    RECV <name> <bytes> <crc32>
so the plugin side and the disk side can be compared by hash, never by length.
"""

import argparse
import http.server
import socketserver
import sys
import zlib
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8765)
parser.add_argument("--dir", default="D:/rblxTRGproject/Data")
args = parser.parse_args()

DEST = Path(args.dir)
DEST.mkdir(parents=True, exist_ok=True)


class Handler(http.server.BaseHTTPRequestHandler):
    def _receive(self, name: str, append: bool) -> None:
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        # A name may carry a subdirectory, e.g. "logs/DataCollection.Log".
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        # HttpService:PostAsync refuses anything over 1024 KB, so a producer whose
        # output can grow without bound has to stream it. `?mode=a` makes the sink
        # append, which lets the producer send the file in segments and lets the
        # file system do the concatenation. The default stays overwrite, so an
        # unmodified caller is unaffected.
        with open(target, "ab" if append else "wb") as fh:
            fh.write(body)
        crc = zlib.crc32(body) & 0xFFFFFFFF
        print(f"RECV {name} {'append' if append else 'write'} {len(body)} {crc:08x}",
              flush=True)

    def do_POST(self) -> None:
        raw = self.path.lstrip("/") or "unnamed"
        name, _, query = raw.partition("?")
        append = query == "mode=a"
        try:
            self._receive(name, append)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        except Exception as exc:  # noqa: BLE001 - report to the caller, never crash
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(exc).encode())

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"receiver up")

    def log_message(self, *_args) -> None:
        pass  # keep stdout clean for the RECV lines


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


with Server(("127.0.0.1", args.port), Handler) as httpd:
    print(f"listening on 127.0.0.1:{args.port} -> {DEST}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
