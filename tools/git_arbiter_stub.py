#!/usr/bin/env python3
"""
Git-Arbiter Stub v0.1 — INTENT-2026-08-23-INFRASTRUCTURE-BOOTSTRAP-ARBITER
Voie Bellard : stub minimal de l'endpoint /git/locks/status attendu par GT-017.
Repond 200 avec locks vides tant que l'implementation Zig reelle n'existe pas.
Remplacement futur: trixd mode arbitre (voir INTENT infra, Phase 2 voie A).
IntentHash: 0xARBITER_STUB_20260823
Usage: python git_arbiter_stub.py [port]
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8742


class Handler(BaseHTTPRequestHandler):
    def _respond(self):
        body = json.dumps({
            "service": "git-arbiter-stub",
            "version": "0.1",
            "locks": [],
            "note": "stub per INTENT-2026-08-23-INFRASTRUCTURE-BOOTSTRAP-ARBITER; "
                    "real worktree-lock tracking pending trixd Phase 2"
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._respond()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        self._respond()

    def log_message(self, fmt, *args):
        sys.stdout.write("[ARBITER-STUB] %s\n" % (fmt % args))


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[ARBITER-STUB] listening on 127.0.0.1:{PORT} (GT-017 contract)")
    server.serve_forever()
