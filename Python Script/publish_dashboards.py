"""
Build a publish-ready static bundle for AFCN dashboards.

Usage:
    python publish_dashboards.py
    python publish_dashboards.py --out ../publish
    python publish_dashboards.py --api-key YOUR_ARCGIS_KEY
    python publish_dashboards.py --clean
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from urllib.parse import quote


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
ENV_PATH = BASE_DIR / ".env"

SOURCE_DIRS = ("geojson", "resources")
ENTRY_PATH = "/resources/Layers%20%26%20Packages/index.html"
DASHBOARD_DIR = Path("resources") / "Layers & Packages"
PRIORITY_DASHBOARDS = (
    "index.html",
    "surplus-map.html",
    "fleet-analytics.html",
    "gt-campus-hub.html",
    "gt_fch_preview.html",
    "gt_fch_map.html",
)
DISPLAY_NAMES = {
    "index.html": "AFCN Main Map",
    "surplus-map.html": "Real-Time Surplus Map",
    "fleet-analytics.html": "Fleet Analytics",
    "gt-campus-hub.html": "GT Campus Hub",
    "gt_fch_preview.html": "GT-FCH Preview Map",
    "gt_fch_map.html": "GT-FCH ArcGIS Feature Map",
}


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def prepare_out_dir(path: Path, clean: bool) -> None:
    resolved = path.resolve()
    if resolved == BASE_DIR.resolve():
        raise ValueError("Refusing to overwrite project root.")
    if clean and resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def discover_dashboards(base_dir: Path) -> list[str]:
    dashboard_root = base_dir / DASHBOARD_DIR
    if not dashboard_root.exists():
        return []

    discovered = []
    for item in dashboard_root.glob("*.html"):
        name = item.name
        if ".tmp." in name.lower():
            continue
        discovered.append(name)

    ranked: list[str] = []
    for name in PRIORITY_DASHBOARDS:
        if name in discovered:
            ranked.append(name)

    for name in sorted(discovered):
        if name not in ranked:
            ranked.append(name)
    return ranked


def dashboard_title(filename: str) -> str:
    if filename in DISPLAY_NAMES:
        return DISPLAY_NAMES[filename]
    stem = filename.rsplit(".", 1)[0]
    return stem.replace("-", " ").replace("_", " ").title()


def dashboard_href(filename: str) -> str:
    path = f"/resources/Layers & Packages/{filename}"
    return quote(path, safe="/._-")


def build_landing_page(dashboards: list[str]) -> str:
    if dashboards:
        links = "\n".join(
            f'    <li><a href="{dashboard_href(name)}">{dashboard_title(name)}</a></li>'
            for name in dashboards
        )
        summary = f"<p>{len(dashboards)} dashboards/maps are included in this publish bundle.</p>"
        list_block = f"<ul>\n{links}\n  </ul>"
    else:
        summary = "<p>No dashboard HTML files were discovered.</p>"
        list_block = ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AFCN Dashboards</title>
</head>
<body>
  <h1>AFCN Dashboard Index</h1>
  {summary}
{list_block}
</body>
</html>
"""


def build_bundle(out_dir: Path, arcgis_api_key: str, clean: bool) -> list[str]:
    prepare_out_dir(out_dir, clean=clean)

    for name in SOURCE_DIRS:
        src = BASE_DIR / name
        if not src.exists():
            raise FileNotFoundError(f"Required source directory is missing: {src}")
        shutil.copytree(src, out_dir / name, dirs_exist_ok=True)

    payload = {
        "arcgisApiKey": arcgis_api_key,
        "ARCGIS_API_KEY": arcgis_api_key,
    }
    payload_json = json.dumps(payload, indent=2) + "\n"
    write_text(out_dir / "api" / "config", payload_json)
    write_text(out_dir / "api" / "config.json", payload_json)

    dashboards = discover_dashboards(out_dir)
    write_text(out_dir / "index.html", build_landing_page(dashboards))
    return dashboards


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static files for dashboard publishing.")
    parser.add_argument(
        "--out",
        default=str(BASE_DIR / "publish"),
        help="Output directory for the publish-ready bundle.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="ArcGIS API key override. If omitted, reads ARCGIS_API_KEY from .env.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete output folder before copying (may fail on locked files).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out).resolve()
    env = load_env(ENV_PATH)
    api_key = args.api_key if args.api_key is not None else env.get("ARCGIS_API_KEY", "")

    dashboards = build_bundle(out_dir, api_key, clean=args.clean)

    print("Publish bundle created.")
    print(f"  Output: {out_dir}")
    if dashboards:
        print("  Dashboards:")
        for name in dashboards:
            print(f"    - {dashboard_title(name)}: {dashboard_href(name)}")
    else:
        print(f"  Entry:  {ENTRY_PATH}")
    if api_key:
        print("  ArcGIS API key: included from .env/--api-key")
    else:
        print("  ArcGIS API key: not set (dashboards still run with mock/fallback where supported)")


if __name__ == "__main__":
    main()
