"""
Fetch City of Atlanta Open Data Hub layers for the Land Use row of the
matrix: zoning, parks, neighborhoods. Public ArcGIS REST endpoints, free.

Each layer is a featureserver/0/query call paged at 2,000 features (Esri's
default max). Stdlib-only; no arcgis-python or arcpy.

OUTPUTS:
  geojson/atl_zoning.geojson           (categorical zoning polygons)
  geojson/atl_parks.geojson            (city parks polygons)
  geojson/atl_neighborhoods.geojson    (neighborhood boundary polygons)

USAGE:
  python -X utf8 scripts/fetch_atlanta_landuse.py
  python -X utf8 scripts/fetch_atlanta_landuse.py --only zoning,parks
"""
from __future__ import annotations
import argparse, json, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Windows + Python 3.14 sometimes lacks the system cert bundle. Use certifi
# if present, otherwise fall back to an unverified context (these are read-
# only public endpoints with no auth).
def _ssl_ctx() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
SSL_CTX = _ssl_ctx()

# City of Atlanta Department of City Planning — LandUsePlanning MapServer
DPCD = "https://gis.atlantaga.gov/dpcd/rest/services/LandUsePlanning/LandUsePlanning/MapServer"

# Layer registry — name → (rest endpoint, output path).
# Layer indices verified from the live MapServer JSON catalog 2026-05.
LAYERS = {
    "zoning": {
        "endpoint":  f"{DPCD}/0",            # Zoning District
        "out":       ROOT / "geojson" / "atl_zoning.geojson",
        "fields":    "*",
    },
    "zoning_overlay": {
        "endpoint":  f"{DPCD}/1",            # Zoning Overlay
        "out":       ROOT / "geojson" / "atl_zoning_overlay.geojson",
        "fields":    "*",
    },
    "future_land_use": {
        "endpoint":  f"{DPCD}/8",            # Development Patterns - Future Land Use
        "out":       ROOT / "geojson" / "atl_future_land_use.geojson",
        "fields":    "*",
    },
    "historic_districts": {
        "endpoint":  f"{DPCD}/6",            # Historic District
        "out":       ROOT / "geojson" / "atl_historic_districts.geojson",
        "fields":    "*",
    },
    "neighborhood_plans": {
        "endpoint":  f"{DPCD}/19",           # Neighborhood, Small Area and Corridor Plans
        "out":       ROOT / "geojson" / "atl_neighborhood_plans.geojson",
        "fields":    "*",
    },
    "beltline_corridor": {
        "endpoint":  f"{DPCD}/4",            # BeltLine TCU Corridor
        "out":       ROOT / "geojson" / "atl_beltline_corridor.geojson",
        "fields":    "*",
    },
}


def fetch_layer(endpoint: str, fields: str = "*") -> dict:
    """Pages through an ArcGIS FeatureServer until all features are returned."""
    all_feats = []
    offset = 0
    page = 2_000
    while True:
        qs = {
            "where": "1=1",
            "outFields": fields,
            "f": "geojson",
            "outSR": 4326,
            "resultOffset": offset,
            "resultRecordCount": page,
        }
        url = f"{endpoint}/query?" + urllib.parse.urlencode(qs)
        req = urllib.request.Request(url, headers={"User-Agent": "AFCN/1.0"})
        with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
            chunk = json.loads(r.read().decode("utf-8"))
        feats = chunk.get("features", [])
        all_feats.extend(feats)
        print(f"  · offset {offset:>6}  +{len(feats):>5}  total {len(all_feats):,}")
        if len(feats) < page:
            break
        offset += page
    return {"type": "FeatureCollection", "features": all_feats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="",
                     help="comma-separated subset: zoning,parks,neighborhoods")
    args = ap.parse_args()

    todo = list(LAYERS.keys())
    if args.only:
        todo = [n.strip() for n in args.only.split(",") if n.strip() in LAYERS]
    print(f"  · fetching: {', '.join(todo)}\n")

    for name in todo:
        cfg = LAYERS[name]
        print(f"=== {name} ===")
        try:
            fc = fetch_layer(cfg["endpoint"], cfg["fields"])
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            continue
        out_path = Path(cfg["out"])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fc["_source"] = f"{cfg['endpoint']} · {time.strftime('%Y-%m-%d')}"
        out_path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
        size_mb = out_path.stat().st_size / 1_048_576
        print(f"  ✓ wrote {out_path.relative_to(ROOT)} "
                f"({len(fc['features']):,} features, {size_mb:.2f} MB)\n")

        meta = {
            "source":        cfg["endpoint"],
            "fetched_at":    time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "feature_count": len(fc["features"]),
            "size_bytes":    out_path.stat().st_size,
            "script":        "scripts/fetch_atlanta_landuse.py",
        }
        out_path.with_suffix(".meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
