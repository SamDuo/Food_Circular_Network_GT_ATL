"""Re-capture screenshots 07-10 that depend on the ArcGIS map tile pipeline.

The plain http.server doesn't expose /api/config so the dashboards fall back
to geodesic-only routing and the basemap fails to load. This script targets
the proper dev server (serve.py on :8091) and uses a generous wait.
"""
import sys
from pathlib import Path
from urllib.parse import urljoin
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "http://localhost:8091/"
TARGETS = [
    # filename, path, wait_seconds, viewport
    ("07_surplus_map.png",         "resources/Layers%20%26%20Packages/surplus-map.html",     16, (1920, 1080)),
    ("08_surplus_route_active.png","resources/Layers%20%26%20Packages/surplus-map.html?route=1", 20, (1920, 1080)),
    ("09_campus_hub.png",          "resources/Layers%20%26%20Packages/gt-campus-hub.html",   14, (1920, 1080)),
    ("10_fleet_analytics.png",     "resources/Layers%20%26%20Packages/fleet-analytics.html", 14, (1920, 1080)),
]


def capture(p, base, filename, path, wait_seconds, viewport):
    url = urljoin(base, path)
    print(f"  -> {url}")
    ctx = p.chromium.launch().new_context(
        viewport={"width": viewport[0], "height": viewport[1]},
        device_scale_factor=2,
    )
    page = ctx.new_page()
    page.set_default_timeout(45000)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"     (goto warn: {e})")
    # Wait for ArcGIS map to settle: poll for the .esri-view element
    try:
        page.wait_for_selector(".esri-view, #map, .map, .view", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(wait_seconds * 1000)
    out = OUT / filename
    page.screenshot(path=str(out), full_page=False)
    print(f"     + {filename} ({out.stat().st_size:,} bytes)")
    ctx.close()


def main():
    print(f"Re-capturing 4 dashboards from {BASE} (proper serve.py with /api/config)")
    with sync_playwright() as p:
        for filename, path, wait_s, viewport in TARGETS:
            capture(p, BASE, filename, path, wait_s, viewport)


if __name__ == "__main__":
    main()
