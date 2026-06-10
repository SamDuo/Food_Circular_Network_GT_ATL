"""
Sprint 5 — Social Systems / Digital divide. Pulls broadband-at-home from
ACS table B28002 for Atlanta-MSA tracts and merges into the existing
atl_demographics_acs.geojson layer (or writes a sibling if the demographics
layer isn't found).

Variables added:
  computer_total          B28002_001E      total households (denominator)
  broadband_any           B28002_004E      with broadband subscription
  no_internet             B28002_013E      no internet access
  pct_broadband           derived = broadband_any / computer_total * 100
  pct_no_internet         derived = no_internet  / computer_total * 100

USAGE:
  python -X utf8 scripts/fetch_acs_broadband.py
"""
from __future__ import annotations
import argparse, json, os, ssl, sys, time, urllib.parse, urllib.request
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

ATL_COUNTIES = ["121", "089", "067", "135", "063", "057", "151"]
STATE        = "13"
YEAR         = 2022
VARS = ["B28002_001E", "B28002_004E", "B28002_013E"]
DEMO_GJ = ROOT / "geojson" / "atl_demographics_acs.geojson"
OUT     = DEMO_GJ                                            # rewrite in place


def load_key():
    k = os.environ.get("CENSUS_API_KEY", "").strip()
    if k: return k
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("CENSUS_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def fetch(year, state, county, key):
    qs = {"get": ",".join(VARS), "for": "tract:*",
          "in": f"state:{state} county:{county}"}
    if key: qs["key"] = key
    url = f"https://api.census.gov/data/{year}/acs/acs5?" + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, headers={"User-Agent": "AFCN/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def to_float(s):
    try:
        v = float(s)
        return None if v < 0 else v
    except (TypeError, ValueError):
        return None


def main():
    if not DEMO_GJ.exists():
        sys.exit(f"missing {DEMO_GJ} — run fetch_acs.py first")
    key = load_key()
    print(f"  · ACS B28002 · {len(ATL_COUNTIES)} counties · key {'present' if key else 'absent'}")
    rows_by_geoid = {}
    for c in ATL_COUNTIES:
        m = fetch(YEAR, STATE, c, key)
        header = m[0]
        for row in m[1:]:
            r = dict(zip(header, row))
            geoid = r["state"] + r["county"] + r["tract"]
            rows_by_geoid[geoid] = r
    print(f"  · {len(rows_by_geoid):,} broadband rows pulled")

    gj = json.loads(DEMO_GJ.read_text(encoding="utf-8"))
    matched = 0
    for feat in gj["features"]:
        geoid = feat["properties"].get("GEOID") or ""
        rec = rows_by_geoid.get(geoid)
        if not rec: continue
        matched += 1
        total      = to_float(rec["B28002_001E"])
        broadband  = to_float(rec["B28002_004E"])
        no_inet    = to_float(rec["B28002_013E"])
        feat["properties"]["computer_total"] = total
        feat["properties"]["broadband_any"]  = broadband
        feat["properties"]["no_internet"]    = no_inet
        if total:
            feat["properties"]["pct_broadband"]   = round((broadband or 0)/total*100, 2)
            feat["properties"]["pct_no_internet"] = round((no_inet  or 0)/total*100, 2)
    print(f"  · merged into {matched:,} tracts")

    OUT.write_text(json.dumps(gj, separators=(",", ":")), encoding="utf-8")
    print(f"  ✓ updated {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
