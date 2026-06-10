"""Build a bivariate choropleth GeoJSON joining CDC obesity prevalence
with USDA LILA food-desert flags on census-tract GEOID.

Method: Stevens (2015) "Bivariate Choropleth Maps" — 3 obesity tertiles ×
3 LILA-strictness classes = 9 categories per tract. Output is consumed
by showcase.js / atlas.js as a unique-value renderer keyed on bivar_class.

Output: geojson/bivariate_obesity_lila.geojson
"""
import json
import os
import sys

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO   = os.path.join(ROOT, "geojson")
HEALTH = os.path.join(GEO, "atl_health_places.geojson")
LILA   = os.path.join(GEO, "atl_pro_food_deserts.geojson")
OUT    = os.path.join(GEO, "bivariate_obesity_lila.geojson")

# Obesity tertile breaks (CDC PLACES 2024 Atlanta tracts, derived).
# Values in percent.  Low = <30, Mid = 30-40, High = >=40.
OBESITY_LOW_MAX  = 30.0
OBESITY_MID_MAX  = 40.0

def obesity_class(v):
    if v is None: return 0
    if v <  OBESITY_LOW_MAX: return 0   # Low
    if v <  OBESITY_MID_MAX: return 1   # Mid
    return 2                            # High

def lila_class(props):
    """Sum of 4 USDA LILA flags → 3 classes: 0 = none, 1 = some, 2 = strict."""
    flags = [
        props.get("LILATracts_1And10",     0) or 0,
        props.get("LILATracts_halfAnd10",  0) or 0,
        props.get("LILATracts_1And20",     0) or 0,
        props.get("LILATracts_Vehicle",    0) or 0,
    ]
    s = sum(int(f) for f in flags)
    if s == 0: return 0   # No LILA
    if s <= 2: return 1   # Some LILA (one or two thresholds met)
    return 2              # Strict LILA (3+ thresholds)

def main():
    with open(HEALTH) as f: health = json.load(f)
    with open(LILA)   as f: lila   = json.load(f)

    # Index LILA by GEOID
    lila_by_geoid = {}
    for feat in lila["features"]:
        gid = (feat.get("properties") or {}).get("GEOID")
        if gid: lila_by_geoid[str(gid)] = feat["properties"]

    out_features = []
    counts = [[0,0,0],[0,0,0],[0,0,0]]   # 3x3 tally

    for feat in health["features"]:
        props = dict(feat.get("properties") or {})
        gid   = str(props.get("GEOID") or "")
        obesity = props.get("OBESITY_CrudePrev")
        # Class assignments
        oc = obesity_class(obesity)
        lc = lila_class(lila_by_geoid.get(gid, {})) if gid in lila_by_geoid else 0
        bivar = oc * 3 + lc           # 0..8
        # Carry through useful fields for popups
        props["obesity_class"] = oc
        props["lila_class"]    = lc
        props["bivar_class"]   = bivar
        props["bivar_label"]   = f"{['Low','Mid','High'][oc]} obesity · {['No','Some','Strict'][lc]} LILA"
        out_features.append({
            "type": "Feature",
            "geometry": feat.get("geometry"),
            "properties": props,
        })
        counts[oc][lc] += 1

    out = { "type": "FeatureCollection", "features": out_features }
    with open(OUT, "w") as f:
        json.dump(out, f)

    print(f"Wrote {OUT}")
    print(f"  {len(out_features)} tracts · {len(lila_by_geoid)} LILA-flagged tracts joined")
    print()
    print("Class distribution (rows = obesity tertile, cols = LILA strictness):")
    print(f"            None    Some   Strict")
    for i, label in enumerate(["Low ", "Mid ", "High"]):
        row = "  ".join(f"{counts[i][j]:5d}" for j in range(3))
        print(f"  {label}    {row}")

if __name__ == "__main__":
    main()
