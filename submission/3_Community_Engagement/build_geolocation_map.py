"""Inline the workshop_orgs.geojson into geolocation_map.html so the map works
as a single-file standalone (file:// URL, no server, no fetch)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
gj = json.loads((HERE / "workshop_orgs.geojson").read_text(encoding="utf-8"))
html = (HERE / "geolocation_map.html").read_text(encoding="utf-8")
html = html.replace("__GEOJSON__", json.dumps(gj, ensure_ascii=False))
out = HERE / "geolocation_map_standalone.html"
out.write_text(html, encoding="utf-8")
print(f"+ {out.name} ({out.stat().st_size:,} bytes, 14 orgs + GT host)")
