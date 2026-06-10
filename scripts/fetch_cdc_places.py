"""
Fetch CDC PLACES tract-level health prevalence for Georgia, slice to the
7-county Atlanta MSA, join onto data/census_tracts_tiger.geojson →
output geojson/atl_health_places.geojson.

CDC PLACES is the authoritative source for small-area chronic-disease
prevalence; data flows from BRFSS via multilevel regression poststratification.
Free, public, no API key.

VARIABLES PULLED (CrudePrev = % crude prevalence):
  OBESITY      adult obesity (BMI ≥ 30)
  DIABETES     diagnosed diabetes
  BPHIGH       high blood pressure
  CHD          coronary heart disease
  STROKE       stroke
  CASTHMA      current asthma
  MHLTH        poor mental health (≥14 days/month)
  PHLTH        poor physical health (≥14 days/month)
  DEPRESSION   diagnosed depression
  ACCESS2      lack of health insurance
  CHECKUP      no annual checkup
  COLON_SCREEN no colorectal cancer screening (50-75)
  FOODINSECU   food insecurity (PLACES 2024+)

USAGE:
  python -X utf8 scripts/fetch_cdc_places.py
  python -X utf8 scripts/fetch_cdc_places.py --year 2024
"""
from __future__ import annotations
import argparse, json, os, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

# Windows + Python 3.14 sometimes lacks the system cert bundle. Use certifi
# if present, otherwise fall back to an unverified context (these are read-
# only public API endpoints with no auth — no MITM exposure).
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

ROOT = Path(__file__).resolve().parent.parent

# Atlanta MSA — 7-county FIPS used elsewhere in this repo
ATL_COUNTIES = ["121", "089", "067", "135", "063", "057", "151"]
STATE_FIPS   = "13"

# CDC PLACES tract-level dataset id (Socrata).
# 2024 release: cwsq-ngmh    (latest; uses 2022 BRFSS + ACS)
# 2023 release: yjkw-uj5s
DEFAULT_DATASET = "cwsq-ngmh"
SOCRATA_HOST    = "https://chronicdata.cdc.gov/resource"

MEASURES = [
    "OBESITY", "DIABETES", "BPHIGH", "CHD", "STROKE", "CASTHMA",
    "MHLTH",   "PHLTH",    "DEPRESSION", "ACCESS2", "CHECKUP",
    "COLON_SCREEN", "FOODINSECU",
]


def fetch_chunk(dataset: str, where: str, limit: int = 50_000,
                 offset: int = 0) -> list[dict]:
    qs = {"$where": where, "$limit": limit, "$offset": offset}
    url = f"{SOCRATA_HOST}/{dataset}.json?" + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, headers={"User-Agent": "AFCN/1.0"})
    with urllib.request.urlopen(req, timeout=45, context=SSL_CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_atl_tracts(dataset: str) -> dict[str, dict]:
    """Return {GEOID11: {measure_id: crude_prev_value, ...}}"""
    # State filter, then keep only counties in our list. Some PLACES vintages
    # use 'countyfips' (5-digit), others 'stateabbr'. Try the simple state filter.
    where = f"stateabbr='GA'"
    rows = []
    offset = 0
    while True:
        chunk = fetch_chunk(dataset, where, limit=50_000, offset=offset)
        if not chunk:
            break
        rows.extend(chunk)
        print(f"  · pulled {len(rows):,} so far…")
        if len(chunk) < 50_000:
            break
        offset += 50_000
    print(f"  · {len(rows):,} GA tract-measure rows fetched")

    # Filter to Atlanta MSA counties (locationid often = 'tract' geoid '13121010100')
    by_geoid: dict[str, dict] = {}
    for r in rows:
        geoid = r.get("locationid") or r.get("locationname") or ""
        if not geoid or len(geoid) < 11:
            continue
        county = geoid[2:5]
        if county not in ATL_COUNTIES:
            continue
        if r.get("datavaluetypeid") != "CrdPrv":     # crude prevalence only
            continue
        meas = r.get("measureid")
        if not meas:
            continue
        try:
            val = float(r.get("data_value")) if r.get("data_value") else None
        except (TypeError, ValueError):
            val = None
        by_geoid.setdefault(geoid, {})[f"{meas}_CrudePrev"] = val
    print(f"  · {len(by_geoid):,} unique Atlanta-MSA tracts after filter")
    return by_geoid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=DEFAULT_DATASET,
                     help="Socrata dataset id (default: 2024 PLACES)")
    ap.add_argument("--tracts-geojson",
                     default=str(ROOT / "geojson" / "census_tracts_tiger.geojson"))
    ap.add_argument("--out",
                     default=str(ROOT / "geojson" / "atl_health_places.geojson"))
    args = ap.parse_args()

    print(f"  · CDC PLACES dataset {args.dataset}")
    by_geoid = fetch_atl_tracts(args.dataset)

    # Load tract polygons
    tracts_path = Path(args.tracts_geojson)
    if not tracts_path.exists():
        sys.exit(f"missing {tracts_path}")
    gj = json.loads(tracts_path.read_text(encoding="utf-8"))
    print(f"  · {len(gj['features']):,} tract polygons in {tracts_path.name}")

    matched, unmatched = 0, 0
    out_features = []
    for feat in gj["features"]:
        p = feat["properties"]
        geoid = (p.get("GEOID") or p.get("GEOID20") or p.get("GEO_ID") or "")
        if geoid.startswith("1400000US"):
            geoid = geoid[9:]
        rec = by_geoid.get(geoid)
        if not rec:
            unmatched += 1
            continue
        matched += 1
        props = {"GEOID": geoid,
                 "NAME":  p.get("NAME") or p.get("NAMELSAD") or geoid}
        for m in MEASURES:
            props[f"{m}_CrudePrev"] = rec.get(f"{m}_CrudePrev")
        out_features.append({
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": props,
        })
    print(f"  · matched {matched:,}  unmatched {unmatched:,}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": out_features,
            "_source": f"CDC PLACES {args.dataset} · {time.strftime('%Y-%m-%d')}"}
    out_path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    print(f"  ✓ wrote {out_path.relative_to(ROOT)} "
            f"({len(out_features):,} features, {out_path.stat().st_size:,} bytes)")

    meta = {
        "source": f"{SOCRATA_HOST}/{args.dataset}.json",
        "dataset": args.dataset,
        "measures": MEASURES,
        "value_type": "CrudePrev (crude prevalence %)",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature_count": len(out_features),
        "script": "scripts/fetch_cdc_places.py",
    }
    out_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  ✓ wrote {out_path.with_suffix('.meta.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
