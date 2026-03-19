"""
Simple local HTTP server for the AFCN dashboard.
Serves the GT campus dataset root so both /geojson and /resources are available.

Usage:
    python serve.py          # starts on http://localhost:8080
    python serve.py 3000     # starts on http://localhost:3000
"""

import sys
import os
import json
import http.server
import webbrowser
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(BASE_DIR, ".env")


def load_env():
    """Read key=value pairs from .env file."""
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers and /api/config endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        try:
            if self.path == "/api/config":
                env = load_env()
                payload = json.dumps({"arcgisApiKey": env.get("ARCGIS_API_KEY", "")})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload.encode())
                return
            super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, TimeoutError):
            # Browser/client closed the socket while we were writing.
            # This is common during reloads and should not crash/log tracebacks.
            return

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        if args and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)


class AFCNHTTPServer(http.server.ThreadingHTTPServer):
    """HTTP server that suppresses noisy client-disconnect tracebacks."""

    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        ex = sys.exc_info()[1]
        if isinstance(ex, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, TimeoutError)):
            return
        if isinstance(ex, OSError) and getattr(ex, "winerror", None) in (10053, 10054):
            return
        super().handle_error(request, client_address)


def main():
    entry_path = "/resources/Layers & Packages/index.html"
    url = f"http://localhost:{PORT}{urllib.parse.quote(entry_path, safe='/')}"

    dash_dir = os.path.join(BASE_DIR, "resources", "Layers & Packages")
    dashboards = sorted(f for f in os.listdir(dash_dir) if f.endswith(".html") and ".tmp." not in f)

    print("AFCN Map Server")
    print(f"  Serving: {BASE_DIR}")
    print(f"\n  Dashboards:")
    for d in dashboards:
        durl = f"http://localhost:{PORT}/resources/Layers%20%26%20Packages/{urllib.parse.quote(d, safe='')}"
        tag = " (opens)" if d == "index.html" else ""
        print(f"    {d:30s} {durl}{tag}")
    print(f"\n  Stop: Ctrl+C\n")

    with AFCNHTTPServer(("", PORT), CORSHandler) as httpd:
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
