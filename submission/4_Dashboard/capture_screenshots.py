#!/usr/bin/env python3
"""
Capture submission screenshots for the AFCN dashboard system.

Hits each of the 5 (+1 supplementary) views via headless Chromium and saves
1920×1080 PNGs into submission/4_Dashboard/screenshots/.

Prerequisites:
    pip install playwright
    playwright install chromium

The dev server must be running:
    cd "Python Script" && python serve.py

Usage:
    python submission/4_Dashboard/capture_screenshots.py
    python submission/4_Dashboard/capture_screenshots.py --base http://prod.example.com
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from urllib.parse import urljoin

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Install with: pip install playwright && playwright install chromium")

OUT = Path(__file__).resolve().parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

VIEWS = [
    # (filename,                 path,                                              wait_ms, dark_mode)
    ("01_atlas_matrix.png",       "atlas/index.html",                                2500, False),
    ("02_atlas_matrix_dark.png",  "atlas/index.html?dark=1",                         2500, True),
    ("03_showcase_scene_01.png",  "showcase/index.html",                             3500, False),
    ("04_showcase_scene_05.png",  "showcase/index.html#scene=5",                     3500, False),
    ("05_network_radial.png",     "network/index.html",                              3000, False),
    ("06_network_force.png",      "network/force.html",                              4500, True),
    ("07_surplus_map.png",        "resources/Layers%20%26%20Packages/surplus-map.html", 4000, True),
    ("08_surplus_route_active.png","resources/Layers%20%26%20Packages/surplus-map.html?route=1", 5500, True),
    ("09_campus_hub.png",         "resources/Layers%20%26%20Packages/gt-campus-hub.html", 3500, True),
    ("10_fleet_analytics.png",    "resources/Layers%20%26%20Packages/fleet-analytics.html", 3500, True),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="http://localhost:8090/",
                    help="Base URL of running dashboard (trailing slash).")
    args = ap.parse_args()
    base = args.base if args.base.endswith("/") else args.base + "/"

    print(f"Capturing {len(VIEWS)} screenshots from {base}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for filename, path, wait_ms, _dark in VIEWS:
            url = urljoin(base, path)
            ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                                       device_scale_factor=2)
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                # Fall back: many ArcGIS pages never reach 'networkidle' because of
                # repeating tile requests. Hard-wait then continue.
                pass
            page.wait_for_timeout(wait_ms)
            out = OUT / filename
            page.screenshot(path=str(out), full_page=False)
            print(f"  + {filename}")
            ctx.close()
        browser.close()
    print(f"\nDone. Files in {OUT}")


if __name__ == "__main__":
    main()
