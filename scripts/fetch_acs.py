"""
Fetch ACS 5-year (2022) demographics for Atlanta MSA census tracts and join
onto data/census_tracts_tiger.geojson → output geojson/atl_demographics_acs.geojson.

Stdlib only. Census API is public (no key required for these read endpoints
at low volume) but if rate-limited, register a free key at
https://api.census.gov/data/key_signup.html and put it in .env as
CENSUS_API_KEY.

VARIABLES PULLED  (all ACS 5-year 2022 table codes):
  B19013_001E    median household income
  B01003_001E    total population
  B25010_001E    average household size
  B02001_002E    white alone
  B02001_003E    black or african american alone
  B02001_005E    asian alone
  B03003_003E    hispanic or latino (any race)
  B01002_001E    median age
  B15003_022E    bachelor's degree
  B15003_023E    master's degree
  B15003_024E    professional degree
  B15003_025E    doctorate degree
  B23025_005E    civilian unemployed
  B23025_002E    civilian labor force (denominator for unemployment)
  B08301_010E    public transit commuters
  B08301_001E    total commuters (denominator for transit %)

DERIVED FIELDS (computed locally):
  pct_white                 = B02001_002E / B01003_001E
  pct_black                 = B02001_003E / B01003_001E
  pct_asian                 = B02001_005E / B01003_001E
  pct_hispanic              = B03003_003E / B01003_001E
  pct_bachelor_or_higher    = (B15003_022E + 023E + 024E + 025E) / total adults 25+
  pct_unemployed            = B23025_005E / B23025_002E
  pct_public_transit        = B08301_010E / B08301_001E
  pop_density               = B01003_001E / area_sqkm   (computed from polygon area)

USAGE:
    python -X utf8 scripts/fetch_acs.py
    python -X utf8 scripts/fetch_acs.py --counties 121,089          # just Fulton+DeKalb
    python -X utf8 scripts/fetch_acs.py --year 2023                  # if 5-year 2023 published
"""
from __future__ import annotations
import argparse, csv, json, os, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 7-county metro Atlanta (Fulton, DeKalb, Cobb, Gwinnett, Clayton, Cherokee, Henry)
DEFAULT_COUNTIES = ["121", "089", "067", "135", "063", "057", "151"]
DEFAULT_STATE    = "13"          # Georgia
DEFAULT_YEAR     = 2022          # latest 5-year vintage at time of writing

# Variables to fetch — keys are the API codes, values are friendly names.
VARS = {
    "B19013_001E": "median_income",
    "B01003_001E": "total_pop",
    "B25010_001E": "avg_household_size",
    "B02001_002E": "white_alone",
    "B02001_003E": "black_alone",
    "B02001_005E": "asian_alone",
    "B03003_003E": "hispanic",
    "B01002_001E": "median_age",
    "B15003_022E": "bachelor",
    "B15003_023E": "masters",
    "B15003_024E": "professional",
    "B15003_025E": "doctorate",
    "B15003_001E": "edu_total_25plus",       # denominator
    "B23025_005E": "unemployed",
    "B23025_002E": "labor_force",
    "B08301_010E": "transit_commuters",
    "B08301_001E": "all_commuters",
}


def load_census_key() -> str | None:
    k = os.environ.get("CENSUS_API_KEY", "").strip()
    if k: return k
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("CENSUS_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def fetch_acs(year: int, state: str, county: str, key: str | None) -> list[list]:
    """Returns a 2D matrix; first row is header, rest are tract rows."""
    var_codes = ",".join(VARS.keys())
    qs = {
        "get":  var_codes,
        "for":  "tract:*",
        "in":   f"state:{state} county:{county}",
    }
    if key: qs["key"] = key
    url = f"https://api.census.gov/data/{year}/acs/acs5?" + urllib.parse.urlencode(qs)
    print(f"  · fetching county {county}…  ({len(VARS)} vars)")
    req = urllib.request.Request(url, headers={"User-Agent": "AFCN/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def to_float(s):
    try:
        v = float(s)
        return None if v < 0 else v        # ACS uses negatives for suppressed cells
    except (TypeError, ValueError):
        return None


def polygon_area_sqkm(coords: list) -> float:
    """Approximate area for a [Multi]Polygon GeoJSON using the spherical excess
    formula on lon/lat in degrees. Good enough for relative density at tract scale."""
    import math
    R = 6_371_008.8  # Earth radius m
    def _ring_area(ring):
        if len(ring) < 4: return 0.0
        a = 0.0
        for i in range(len(ring) - 1):
            lon1, lat1 = ring[i]
            lon2, lat2 = ring[i + 1]
            a += math.radians(lon2 - lon1) * (
                2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2)))
        return abs(a * R * R / 2.0)
    total = 0.0
    if not coords: return 0.0
    if isinstance(coords[0][0][0], (int, float)):
        # Polygon: [outer_ring, hole, hole, ...]
        rings = coords
    else:
        # MultiPolygon: [[outer, hole...], ...]
        rings = [r for poly in coords for r in poly]
    for i, ring in enumerate(rings):
        sign = 1 if i == 0 else -1
        total += sign * _ring_area(ring)
    return total / 1_000_000.0  # m² → km²


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counties", default=",".join(DEFAULT_COUNTIES),
                     help="Comma-separated 3-digit county FIPS (default: 7-county metro)")
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--year",  type=int, default=DEFAULT_YEAR)
    ap.add_argument("--tracts-geojson",
                     default=str(ROOT / "geojson" / "census_tracts_tiger.geojson"),
                     help="Path to base census tract polygons (TIGER/Line)")
    ap.add_argument("--out",
                     default=str(ROOT / "geojson" / "atl_demographics_acs.geojson"))
    args = ap.parse_args()

    key = load_census_key()
    print(f"  · ACS {args.year} · state {args.state} · counties {args.counties}")
    print(f"  · API key: {'present' if key else 'absent (using public quota)'}")

    # 1) Fetch ACS rows for each county
    counties = [c.strip() for c in args.counties.split(",") if c.strip()]
    rows_by_geoid = {}
    for c in counties:
        matrix = fetch_acs(args.year, args.state, c, key)
        header = matrix[0]
        for row in matrix[1:]:
            rec = dict(zip(header, row))
            geoid = rec["state"] + rec["county"] + rec["tract"]
            rows_by_geoid[geoid] = rec
    print(f"  · {len(rows_by_geoid):,} tracts pulled from ACS")

    # 2) Load existing tract polygons
    tracts_path = Path(args.tracts_geojson)
    if not tracts_path.exists():
        print(f"  ✗ missing {tracts_path}")
        sys.exit(1)
    gj = json.loads(tracts_path.read_text(encoding="utf-8"))
    print(f"  · {len(gj['features']):,} polygons in {tracts_path.name}")

    # 3) Join + derive
    out_features = []
    matched, unmatched = 0, 0
    for feat in gj["features"]:
        p = feat["properties"]
        # Try common geoid keys (TIGER uses GEOID, GEOID20, etc.)
        geoid = (p.get("GEOID") or p.get("GEOID20") or p.get("GEO_ID") or "")
        # GEO_ID format is "1400000US13121010100" — strip prefix
        if geoid.startswith("1400000US"):
            geoid = geoid[9:]
        rec = rows_by_geoid.get(geoid)
        if not rec:
            unmatched += 1
            continue
        matched += 1

        # Friendly-named numeric fields
        out = {VARS[k]: to_float(rec[k]) for k in VARS}

        # Derived percentages
        pop = out["total_pop"] or 0
        if pop:
            out["pct_white"]    = round((out["white_alone"]    or 0) / pop * 100, 2)
            out["pct_black"]    = round((out["black_alone"]    or 0) / pop * 100, 2)
            out["pct_asian"]    = round((out["asian_alone"]    or 0) / pop * 100, 2)
            out["pct_hispanic"] = round((out["hispanic"]       or 0) / pop * 100, 2)

        edu_tot = out["edu_total_25plus"] or 0
        if edu_tot:
            edu_4yr = sum((out[k] or 0) for k in ("bachelor", "masters", "professional", "doctorate"))
            out["pct_bachelor_or_higher"] = round(edu_4yr / edu_tot * 100, 2)

        if (out["labor_force"] or 0):
            out["pct_unemployed"] = round((out["unemployed"] or 0) / out["labor_force"] * 100, 2)
        if (out["all_commuters"] or 0):
            out["pct_public_transit"] = round((out["transit_commuters"] or 0) / out["all_commuters"] * 100, 2)

        # Population density (people per km²)
        try:
            area = polygon_area_sqkm(feat["geometry"]["coordinates"])
            if area > 0:
                out["area_sqkm"] = round(area, 3)
                out["pop_density"] = round(pop / area, 1)
        except Exception:
            pass

        # Pass through useful identifiers
        out["GEOID"]   = geoid
        out["state"]   = rec["state"]
        out["county"]  = rec["county"]
        out["tract"]   = rec["tract"]
        out["NAME"]    = p.get("NAME") or p.get("NAMELSAD") or geoid

        out_features.append({
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": out,
        })

    print(f"  · matched {matched:,}  ·  unmatched {unmatched:,}")

    # 4) Write output GeoJSON + sibling .meta.json (provenance for the rubric)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": out_features,
            "_source": f"ACS 5-year {args.year} · counties {','.join(counties)} ·"
                        f" generated {__import__('time').strftime('%Y-%m-%d')}"}
    out_path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    print(f"\n  ✓ wrote {out_path.relative_to(ROOT)} "
            f"({len(out_features):,} features, {out_path.stat().st_size:,} bytes)")

    meta = {
        "source": f"https://api.census.gov/data/{args.year}/acs/acs5",
        "year": args.year, "state": args.state, "counties": counties,
        "variables": list(VARS.keys()),
        "derived": ["pct_white", "pct_black", "pct_asian", "pct_hispanic",
                    "pct_bachelor_or_higher", "pct_unemployed",
                    "pct_public_transit", "pop_density", "area_sqkm"],
        "fetched_at": __import__('time').strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature_count": len(out_features),
        "script": "scripts/fetch_acs.py",
    }
    out_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  ✓ wrote {out_path.with_suffix('.meta.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
