"""
Fetch OpenStreetMap features from Overpass API for Atlanta MSA.
One script that handles bike infra (Sprint 4), airport (Sprint 4),
universities/colleges (Sprint 5).

Each layer is a single Overpass query that returns OSM elements; we convert
to GeoJSON ourselves (osm2geojson is not stdlib, so we hand-build features).

OUTPUTS:
  geojson/atl_bike_infrastructure.geojson   ← cycleway=*, BeltLine, paths
  geojson/atl_airports.geojson               ← Hartsfield + DeKalb-Peachtree + Charlie Brown
  geojson/atl_universities.geojson           ← amenity=university, college, with student housing context

USAGE:
  python -X utf8 scripts/fetch_overpass.py
  python -X utf8 scripts/fetch_overpass.py --only bike,airport
"""
from __future__ import annotations
import argparse, json, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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

# Atlanta MSA bbox: roughly 7-county metro
BBOX = "33.45,-84.75,34.10,-84.00"   # south, west, north, east
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",   # fallback mirror
]

LAYERS = {
    "bike": {
        # Tighter query: city-of-atlanta bbox + only the highest-signal tags.
        # The wider 7-county bbox + all cycleway:* tags timed Overpass out.
        "out": ROOT / "geojson" / "atl_bike_infrastructure.geojson",
        "query": """
            [out:json][timeout:90][bbox:33.65,-84.55,33.92,-84.25];
            (
              way["highway"="cycleway"];
              way["cycleway"="track"];
              way["cycleway"="lane"];
              way["highway"="path"]["bicycle"="designated"];
            );
            out tags geom;
        """,
    },
    "airport": {
        "out": ROOT / "geojson" / "atl_airports.geojson",
        "query": f"""
            [out:json][timeout:90][bbox:{BBOX}];
            (
              way["aeroway"="aerodrome"];
              relation["aeroway"="aerodrome"];
              way["aeroway"="runway"];
              way["aeroway"="terminal"];
            );
            out tags geom;
        """,
    },
    "universities": {
        "out": ROOT / "geojson" / "atl_universities.geojson",
        "query": f"""
            [out:json][timeout:90][bbox:{BBOX}];
            (
              way["amenity"~"university|college"];
              relation["amenity"~"university|college"];
              node["amenity"~"university|college"];
            );
            out tags center geom;
        """,
    },
}


def overpass(query: str) -> dict:
    body = "data=" + urllib.parse.quote(query)
    last_err = None
    for url in OVERPASS_URLS:
        try:
            req = urllib.request.Request(url, data=body.encode("utf-8"),
                                          headers={"User-Agent": "AFCN/1.0"})
            with urllib.request.urlopen(req, timeout=180, context=SSL_CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  ! {url}: {e}")
            last_err = e
    raise RuntimeError(f"all overpass mirrors failed: {last_err}")


def osm_to_geojson(elements: list) -> list:
    """Convert Overpass JSON elements into GeoJSON features."""
    feats = []
    for e in elements:
        tags = e.get("tags", {})
        geom = None
        etype = e.get("type")
        if etype == "node" and "lat" in e and "lon" in e:
            geom = {"type": "Point", "coordinates": [e["lon"], e["lat"]]}
        elif etype == "way" and "geometry" in e:
            coords = [[g["lon"], g["lat"]] for g in e["geometry"]]
            if len(coords) >= 2:
                # Closed way → polygon
                if coords[0] == coords[-1] and len(coords) >= 4:
                    geom = {"type": "Polygon", "coordinates": [coords]}
                else:
                    geom = {"type": "LineString", "coordinates": coords}
        elif etype == "way" and "center" in e:
            geom = {"type": "Point", "coordinates": [e["center"]["lon"], e["center"]["lat"]]}
        elif etype == "relation" and "center" in e:
            geom = {"type": "Point", "coordinates": [e["center"]["lon"], e["center"]["lat"]]}
        if geom:
            feats.append({"type": "Feature", "geometry": geom,
                            "properties": {**tags, "osm_id": e.get("id"),
                                            "osm_type": etype}})
    return feats


def fetch_one(name: str, cfg: dict):
    print(f"=== {name} ===")
    print(f"  · querying Overpass…")
    res = overpass(cfg["query"])
    elements = res.get("elements", [])
    print(f"  · {len(elements):,} OSM elements returned")
    feats = osm_to_geojson(elements)
    print(f"  · {len(feats):,} GeoJSON features after conversion")

    out_path = Path(cfg["out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": feats,
            "_source": f"OpenStreetMap via Overpass API · "
                        f"{time.strftime('%Y-%m-%d')}"}
    out_path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    size_mb = out_path.stat().st_size / 1_048_576
    print(f"  ✓ wrote {out_path.relative_to(ROOT)} ({len(feats):,} features, {size_mb:.2f} MB)")

    meta = {
        "source":        "OpenStreetMap (Overpass API)",
        "bbox":          BBOX,
        "fetched_at":    time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature_count": len(feats),
        "size_bytes":    out_path.stat().st_size,
        "script":        "scripts/fetch_overpass.py",
    }
    out_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="",
                     help="comma-separated subset: bike,airport,universities")
    args = ap.parse_args()
    todo = list(LAYERS.keys())
    if args.only:
        todo = [n.strip() for n in args.only.split(",") if n.strip() in LAYERS]
    print(f"  · fetching: {', '.join(todo)}\n")
    for name in todo:
        try:
            fetch_one(name, LAYERS[name])
        except Exception as e:
            print(f"  ✗ {name} failed: {e}\n")


if __name__ == "__main__":
    main()
