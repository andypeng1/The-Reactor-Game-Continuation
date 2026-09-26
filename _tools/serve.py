#!/usr/bin/env python3
"""Serve files off disk to the Studio plugin, byte for byte.

This is the mirror of receive.py. receive.py moves a script's Source OUT of
Studio without the text ever entering the model's context; this moves one IN the
same way. Both exist because the tool-call path is lossy in a way that is hard to
see: it hands the bytes to the model and back, so a module can arrive one
character different from the file it came from, and Studio escape-decodes text
that comes through an editing tool (CLAUDE.md 0.10) so a backslash can arrive as
a different, broken program.

Fetching instead of transmitting skips all of that: the bytes go from this
process into ModuleScript.Source with nothing in between, so a cmp afterwards is
a real check rather than a check of my typing.

    python _tools/serve.py --dir src/ReactorBackend --port 8767

Then, from Studio's plugin context:

    local body = game:GetService('HttpService'):GetAsync(
        'http://127.0.0.1:8767/RoomShell.luau')
    script.Parent.RoomShell.Source = body

One request per file, the whole body, no paths outside --dir.
"""
import argparse
import http.server
import os
import socketserver
import sys


class Handler(http.server.BaseHTTPRequestHandler):
    root = None

    def _resolve(self):
        # Everything after the leading slash, with any query string dropped.
        wanted = self.path.split('?', 1)[0].lstrip('/')
        if not wanted:
            return None
        # Reject traversal outright rather than sanitising it: there is no
        # legitimate request for a path containing a separator.
        if '/' in wanted or '\\' in wanted or wanted.startswith('.'):
            return None
        full = os.path.join(self.root, wanted)
        return full if os.path.isfile(full) else None

    def do_GET(self):
        # Byte mode throughout. This machine's console codec is GBK, so a
        # text-mode read or print raises on the first non-ASCII byte.
        target = self._resolve()
        if target is None:
            self.send_error(404, 'no such file')
            return
        with open(target, 'rb') as handle:
            payload = handle.read()
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        sys.stdout.buffer.write(
            b'SENT %s %d bytes\n' % (os.path.basename(target).encode(), len(payload)))
        sys.stdout.flush()

    def log_message(self, fmt, *args):
        pass


class Server(socketserver.ThreadingTCPServer):
    # Deliberately NOT allow_reuse_address. receive.py sets it true, and on
    # Windows that lets a second process bind a port that is already being
    # served while reporting success, so requests go to whichever process bound
    # first and the --dir on the new command line is silently ignored. That cost
    # a whole debugging round on the receive side. Here the second bind fails
    # loudly instead.
    allow_reuse_address = False
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='src/ReactorBackend')
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    root = os.path.abspath(args.dir)
    if not os.path.isdir(root):
        raise SystemExit('not a directory: %s' % root)
    Handler.root = root
    with Server(('127.0.0.1', args.port), Handler) as httpd:
        print('serving %s on http://127.0.0.1:%d' % (root, args.port))
        sys.stdout.flush()
        httpd.serve_forever()


if __name__ == '__main__':
    main()
