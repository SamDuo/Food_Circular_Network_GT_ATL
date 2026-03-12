"""
Simple local HTTP server for the AFCN web platform.
Serves files from this directory with proper CORS headers.
Exposes GET /api/config  →  { arcgisApiKey, mapboxPublicKey } (read from ../.env)

Usage:
    python serve.py          # starts on http://localhost:8080
    python serve.py 3000     # starts on http://localhost:3000
"""

import sys
import os
import json
import http.server

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env():
    """Parse .env file in BASE_DIR and return a dict of key→value."""
    config = {}
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return config
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers + /api/config route."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    # ── route override ──────────────────────────────────────────
    def do_GET(self):
        if self.path.split("?")[0] == "/api/config":
            self._serve_config()
        else:
            super().do_GET()

    def _serve_config(self):
        env = _load_env()
        body = json.dumps(
            {
                "arcgisApiKey": env.get("ARCGIS_API_KEY", ""),
                "mapboxPublicKey": env.get("MAPBOX_PUBLIC_KEY", ""),
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── CORS headers on every response ─────────────────────────
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        # Suppress 200/304 noise; only print errors
        if args and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)


def main():
    base = f"http://localhost:{PORT}"
    print("AFCN Dev Server")
    print(f"  Serving : {BASE_DIR}")
    print(f"  AFCN    : {base}/resources/Layers%20%26%20Packages/index.html")
    print(f"  Campus  : {base}/resources/Layers%20%26%20Packages/gt-campus-hub.html")
    print(f"  Surplus : {base}/resources/Layers%20%26%20Packages/surplus-map.html")
    print(f"  Config  : {base}/api/config")
    print(f"  Stop    : Ctrl+C\n")

    with http.server.HTTPServer(("", PORT), CORSHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
