"""
Simple local HTTP server for the GT-FCH ArcGIS web map.
Serves files from this directory with proper CORS headers.

Usage:
    python serve.py          # starts on http://localhost:8080
    python serve.py 3000     # starts on http://localhost:3000
"""

import sys
import os
import http.server
import webbrowser

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that adds CORS headers so ArcGIS JS SDK can load local GeoJSON."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

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
        # Suppress noisy request logs; only print errors
        if args and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)


def main():
    url = f"http://localhost:{PORT}/resources/Layers%20%26%20Packages/index.html"
    print(f"GT-FCH Map Server")
    print(f"  Serving: {BASE_DIR}")
    print(f"  URL:     {url}")
    print(f"  Surplus: http://localhost:{PORT}/resources/Layers%20%26%20Packages/surplus-map.html")
    print(f"  Stop:    Ctrl+C\n")

    with http.server.HTTPServer(("", PORT), CORSHandler) as httpd:
        # Open the map automatically in the default browser
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
