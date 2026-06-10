"""
Compute a transit-accessibility score for every census tract:
  count of MARTA rail/bus stops within walking distance (default 800 m)
  of each tract's centroid.

This is a stand-in for full OpenTripPlanner isochrones and is good enough
for the matrix's Accessibility lens. Runs in seconds, stdlib only.

OUTPUT:
  geojson/atl_transit_access.geojson
    properties:
      stops_within_800m   integer
      stops_within_1600m  integer
      access_score        0–100 scaled
      tier                "high" | "medium" | "low" | "none"

USAGE:
  python -X utf8 scripts/compute_transit_access.py
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACTS_GJ = ROOT / "geojson" / "census_tracts_tiger.geojson"
STOPS_GJ  = ROOT / "geojson" / "marta_stops_atl.geojson"
OUT       = ROOT / "geojson" / "atl_transit_access.geojson"


def haversine(lon1, lat1, lon2, lat2):
    R = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def centroid(coords):
    """Naive centroid of [Multi]Polygon coords. Returns (lon, lat)."""
    if not coords: return (0, 0)
    if isinstance(coords[0][0][0], (int, float)):
        rings = [coords[0]]                    # Polygon
    else:
        rings = [poly[0] for poly in coords]   # MultiPolygon: take outer rings
    pts = [pt for ring in rings for pt in ring]
    n = len(pts) or 1
    return (sum(p[0] for p in pts)/n, sum(p[1] for p in pts)/n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--near",  type=float, default=800,
                     help="primary buffer in meters (default 800m ~ 10-min walk)")
    ap.add_argument("--far",   type=float, default=1600,
                     help="secondary buffer in meters (default 1600m)")
    args = ap.parse_args()

    tracts = json.loads(TRACTS_GJ.read_text(encoding="utf-8"))
    stops  = json.loads(STOPS_GJ.read_text(encoding="utf-8"))
    print(f"  · {len(tracts['features']):,} tracts · {len(stops['features']):,} stops")

    stop_pts = []
    for f in stops["features"]:
        g = f.get("geometry") or {}
        if g.get("type") == "Point":
            stop_pts.append(tuple(g["coordinates"]))
    print(f"  · {len(stop_pts):,} valid point stops")

    out_features = []
    max_score = 0
    for feat in tracts["features"]:
        g = feat.get("geometry") or {}
        if g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        clon, clat = centroid(g["coordinates"])
        n_near, n_far = 0, 0
        for slon, slat in stop_pts:
            d = haversine(clon, clat, slon, slat)
            if d <= args.near: n_near += 1
            if d <= args.far:  n_far  += 1
        score = n_near * 3 + (n_far - n_near)        # weight near stops 3×
        max_score = max(max_score, score)
        props = dict(feat["properties"])             # carry through GEOID etc.
        props["stops_within_800m"]  = n_near
        props["stops_within_1600m"] = n_far
        props["access_raw"]         = score
        out_features.append({
            "type": "Feature", "geometry": g, "properties": props,
        })

    # Scale to 0-100
    for f in out_features:
        raw = f["properties"]["access_raw"]
        f["properties"]["access_score"] = round(raw / max_score * 100, 1) if max_score else 0
        s = f["properties"]["access_score"]
        f["properties"]["tier"] = ("high"   if s >= 60 else
                                    "medium" if s >= 25 else
                                    "low"    if s >= 5  else
                                    "none")

    OUT.write_text(json.dumps({"type": "FeatureCollection",
                                "features": out_features}, separators=(",", ":")),
                    encoding="utf-8")
    size_mb = OUT.stat().st_size / 1_048_576
    print(f"  ✓ wrote {OUT.relative_to(ROOT)} ({len(out_features):,} features, {size_mb:.2f} MB)")

    # Quick distribution print
    from collections import Counter
    c = Counter(f["properties"]["tier"] for f in out_features)
    print(f"  · tier distribution: {dict(c)}")

    meta = {
        "source":        f"derived from {STOPS_GJ.name} + {TRACTS_GJ.name}",
        "method":        f"haversine buffer; near={args.near}m, far={args.far}m",
        "fetched_at":    __import__('time').strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature_count": len(out_features),
        "script":        "scripts/compute_transit_access.py",
    }
    OUT.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
