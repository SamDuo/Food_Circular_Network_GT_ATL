"""
Fetch HIFLD (Homeland Infrastructure Foundation-Level Data) utility
infrastructure for Sprint 5: Infrastructure row of the matrix.

HIFLD Open is a federal open-data ArcGIS portal — free, no key. We pull
electric transmission lines and natural gas pipelines for Georgia and clip
to the Atlanta MSA bbox.

OUTPUTS:
  geojson/atl_electric_transmission.geojson
  geojson/atl_natural_gas_pipelines.geojson

USAGE:
  python -X utf8 scripts/fetch_hifld_utilities.py
"""
from __future__ import annotations
import argparse, json, ssl, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
SSL_CTX = _ssl_ctx()

# Atlanta MSA bbox — same as fetch_overpass.py
BBOX = {"xmin": -84.75, "ymin": 33.45, "xmax": -84.00, "ymax": 34.10,
         "spatialReference": {"wkid": 4326}}

LAYERS = {
    "electric_transmission": {
        "endpoint": "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/ArcGIS/rest/services/Electric_Power_Transmission_Lines/FeatureServer/0",
        "out":      ROOT / "geojson" / "atl_electric_transmission.geojson",
    },
    "gas_pipelines": {
        "endpoint": "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/ArcGIS/rest/services/Natural_Gas_Pipelines/FeatureServer/0",
        "out":      ROOT / "geojson" / "atl_natural_gas_pipelines.geojson",
    },
}


def fetch_layer(endpoint: str) -> dict:
    all_feats = []
    offset = 0
    page = 2_000
    while True:
        qs = {
            "where": "1=1",
            "outFields": "*",
            "geometry": json.dumps(BBOX),
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "f": "geojson",
            "outSR": 4326,
            "resultOffset": offset,
            "resultRecordCount": page,
        }
        url = f"{endpoint}/query?" + urllib.parse.urlencode(qs)
        req = urllib.request.Request(url, headers={"User-Agent": "AFCN/1.0"})
        with urllib.request.urlopen(req, timeout=90, context=SSL_CTX) as r:
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
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    todo = list(LAYERS.keys())
    if args.only:
        todo = [n.strip() for n in args.only.split(",") if n.strip() in LAYERS]
    print(f"  · fetching HIFLD: {', '.join(todo)}\n")
    for name in todo:
        cfg = LAYERS[name]
        print(f"=== {name} ===")
        try:
            fc = fetch_layer(cfg["endpoint"])
        except Exception as e:
            print(f"  ✗ {name}: {e}\n")
            continue
        out_path = Path(cfg["out"])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fc["_source"] = f"HIFLD Open · {cfg['endpoint']} · {time.strftime('%Y-%m-%d')}"
        out_path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
        size_mb = out_path.stat().st_size / 1_048_576
        print(f"  ✓ wrote {out_path.relative_to(ROOT)} "
                f"({len(fc['features']):,} features, {size_mb:.2f} MB)\n")
        meta = {
            "source":        cfg["endpoint"],
            "bbox":          BBOX,
            "fetched_at":    time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "feature_count": len(fc["features"]),
            "script":        "scripts/fetch_hifld_utilities.py",
        }
        out_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
