# -*- coding: utf-8 -*-
"""
Compute 4 analytical map layers for AFCN Food System Study.

Map 1: Food Retail Density (fast food vs grocery density per tract)
Map 2: Food Access Distance (nearest grocery + 5-mile threshold)
Map 3: Transportation Accessibility (vehicle availability enriched)
Map 4: Food Assistance Demand (SNAP + poverty + pantry count)

Requirements: pip install geopandas requests shapely
Usage: python scripts/compute_analytical_maps.py
"""

import os
import sys
import json
import math
import requests
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GEOJSON_DIR = os.path.join(BASE_DIR, "geojson")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Step 1: Fetch Census ACS Data
# ═══════════════════════════════════════════════════════════
def fetch_census_acs():
    """Fetch ACS 5-year 2022 data for Fulton + DeKalb tracts."""
    print("=" * 60)
    print("Step 1: Fetching Census ACS data...")
    ACS_BASE = "https://api.census.gov/data/2022/acs/acs5"

    variables = [
        "B01003_001E",  # total population
        "B19013_001E",  # median household income
        "B17001_002E",  # pop below poverty
        "B17001_001E",  # pop for poverty calc
        "B22010_002E",  # HH receiving SNAP
        "B22010_001E",  # total HH
        "B08141_002E",  # no vehicle workers
        "B08141_001E",  # total workers
        "B15003_017E",  # HS diploma
        "B15003_022E",  # bachelors
        "B15003_001E",  # education universe
        "B03002_003E",  # white non-hispanic
        "B03002_004E",  # black
        "B03002_012E",  # hispanic
        "B23025_005E",  # unemployed
        "B23025_002E",  # labor force
    ]
    var_str = ",".join(variables)

    all_rows = []
    headers = None
    for county in ["121", "089"]:  # Fulton, DeKalb
        url = f"{ACS_BASE}?get=NAME,{var_str}&for=tract:*&in=state:13&in=county:{county}"
        print(f"  Fetching county {county}...")
        resp = requests.get(url, timeout=60)
        data = resp.json()
        if headers is None:
            headers = data[0]
        all_rows.extend(data[1:])

    print(f"  Total tracts: {len(all_rows)}")

    # Parse into dict keyed by GEOID
    acs = {}
    for row in all_rows:
        d = dict(zip(headers, row))
        geoid = f"13{d['county']}{d['tract']}"

        def safe(k):
            v = d.get(k, "")
            return int(v) if v and v not in ("-666666666", "") else 0

        pop = safe("B01003_001E")
        income_raw = d.get("B19013_001E", "")
        income = int(income_raw) if income_raw and income_raw not in ("-666666666", "") else None
        pov_n, pov_d = safe("B17001_002E"), safe("B17001_001E")
        snap_n, snap_d = safe("B22010_002E"), safe("B22010_001E")
        noveh_n, noveh_d = safe("B08141_002E"), safe("B08141_001E")
        hs, ba, edu_d = safe("B15003_017E"), safe("B15003_022E"), safe("B15003_001E")
        white, black, hisp = safe("B03002_003E"), safe("B03002_004E"), safe("B03002_012E")
        unemp, labor = safe("B23025_005E"), safe("B23025_002E")

        acs[geoid] = {
            "population": pop,
            "median_income": income,
            "poverty_rate": round(pov_n / pov_d * 100, 1) if pov_d > 0 else None,
            "snap_rate": round(snap_n / snap_d * 100, 1) if snap_d > 0 else None,
            "snap_households": snap_n,
            "pct_no_vehicle": round(noveh_n / noveh_d * 100, 1) if noveh_d > 0 else None,
            "pct_hs_diploma": round(hs / edu_d * 100, 1) if edu_d > 0 else None,
            "pct_bachelors": round(ba / edu_d * 100, 1) if edu_d > 0 else None,
            "pct_white": round(white / pop * 100, 1) if pop > 0 else None,
            "pct_black": round(black / pop * 100, 1) if pop > 0 else None,
            "pct_hispanic": round(hisp / pop * 100, 1) if pop > 0 else None,
            "unemployment_rate": round(unemp / labor * 100, 1) if labor > 0 else None,
        }

    # Save
    with open(os.path.join(DATA_DIR, "census_acs_parsed.json"), "w") as f:
        json.dump(acs, f, indent=2)
    print(f"  Saved ACS data for {len(acs)} tracts")
    return acs


# ═══════════════════════════════════════════════════════════
# Step 2: Load spatial data and count points per tract
# ═══════════════════════════════════════════════════════════
def load_points(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    pts = []
    for feat in data["features"]:
        g = feat.get("geometry")
        if g and g["type"] == "Point":
            pts.append(Point(g["coordinates"][0], g["coordinates"][1]))
    return pts


def count_in_polygons(gdf, points):
    counts = []
    for _, row in gdf.iterrows():
        prepared = prep(row.geometry)
        counts.append(sum(1 for p in points if prepared.contains(p)))
    return counts


def haversine_miles(lon1, lat1, lon2, lat2):
    R = 3958.8
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def compute_all_maps(acs):
    print("\n" + "=" * 60)
    print("Step 2: Loading spatial data...")

    tracts = gpd.read_file(os.path.join(GEOJSON_DIR, "food_deserts_atlanta.geojson"))
    print(f"  {len(tracts)} tract polygons")

    layers = {
        "grocery": "pkg_atlanta_grocery_stores.geojson",
        "supermarket": "pkg_supermarkets_metroatl.geojson",
        "fastfood": "pkg_all_fast_food_locations_in_metro_atlanta.geojson",
        "convenience": "convenience_stores_atl.geojson",
        "farmers_market": "pkg_atlanta_metro_area_farmers_markets.geojson",
        "religious": "pkg_religious_institutions_metro_atlanta.geojson",
        "pantry": "redistribution_nodes.geojson",
    }

    points = {}
    for name, filename in layers.items():
        pts = load_points(os.path.join(GEOJSON_DIR, filename))
        points[name] = pts
        print(f"  {name}: {len(pts)} points")

    # ── Count points per tract ──
    print("\nStep 3: Counting points per tract (spatial join)...")
    for name, pts in points.items():
        col = f"{name}_count"
        tracts[col] = count_in_polygons(tracts, pts)
        print(f"  {col}: total {tracts[col].sum()}")

    # ── Join ACS data ──
    print("\nStep 4: Joining ACS data to tracts...")
    joined = 0
    for idx, row in tracts.iterrows():
        tid = row.get("census_tract_id", "")
        if tid in acs:
            for k, v in acs[tid].items():
                tracts.at[idx, k] = v
            joined += 1
    print(f"  Joined {joined}/{len(tracts)} tracts")

    # ── Compute density per 1000 pop ──
    for col in ["grocery", "supermarket", "fastfood", "convenience"]:
        tracts[f"{col}_per_1000"] = tracts.apply(
            lambda r: round(r[f"{col}_count"] / r["population"] * 1000, 2)
            if r.get("population", 0) and r["population"] > 0
            else 0,
            axis=1,
        )

    # ── Nearest grocery distance ──
    print("\nStep 5: Computing nearest grocery distances...")
    with open(os.path.join(GEOJSON_DIR, "pkg_atlanta_grocery_stores.geojson"), encoding="utf-8") as f:
        gdata = json.load(f)
    grocery_locs = [
        (f["geometry"]["coordinates"], f["properties"].get("Store_Name", ""))
        for f in gdata["features"]
        if f["geometry"]["type"] == "Point"
    ]

    dists, names = [], []
    for _, row in tracts.iterrows():
        c = row.geometry.centroid
        best_d, best_n = float("inf"), ""
        for coords, nm in grocery_locs:
            d = haversine_miles(c.x, c.y, coords[0], coords[1])
            if d < best_d:
                best_d, best_n = d, nm
        dists.append(round(best_d, 2))
        names.append(best_n)

    tracts["nearest_grocery_miles"] = dists
    tracts["nearest_grocery_name"] = names
    tracts["low_access_1mi"] = tracts["nearest_grocery_miles"] > 1.0
    tracts["low_access_5mi"] = tracts["nearest_grocery_miles"] > 5.0

    # ═══════════════════════════════════════════════════════════
    # Map 1: Food Retail Environment Score
    # High fast food density + low grocery density = bad
    # ═══════════════════════════════════════════════════════════
    print("\nStep 6: Computing Map 1 — Food Retail Environment Score...")
    ff = tracts["fastfood_per_1000"]
    gr = tracts["grocery_per_1000"]
    ff_norm = (ff - ff.min()) / (ff.max() - ff.min() + 0.001)
    gr_norm = (gr - gr.min()) / (gr.max() - gr.min() + 0.001)
    tracts["food_retail_score"] = round((ff_norm * 0.5 + (1 - gr_norm) * 0.5) * 100, 1)

    # ═══════════════════════════════════════════════════════════
    # Map 4: Food Assistance Demand Score
    # SNAP rate + poverty rate = demand
    # ═══════════════════════════════════════════════════════════
    print("Step 7: Computing Map 4 — Food Assistance Demand Score...")
    snap = tracts["snap_rate"].fillna(0)
    pov = tracts["poverty_rate"].fillna(0)
    snap_norm = (snap - snap.min()) / (snap.max() - snap.min() + 0.001)
    pov_norm = (pov - pov.min()) / (pov.max() - pov.min() + 0.001)
    tracts["food_assistance_demand"] = round((snap_norm * 0.5 + pov_norm * 0.5) * 100, 1)

    # ═══════════════════════════════════════════════════════════
    # Save output GeoJSONs
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("Step 8: Saving analytical GeoJSON files...")

    # Map 1
    c1 = ["census_tract_id", "tract_name", "population", "grocery_count", "supermarket_count",
           "fastfood_count", "convenience_count", "farmers_market_count",
           "grocery_per_1000", "fastfood_per_1000", "convenience_per_1000",
           "food_retail_score", "geometry"]
    gdf1 = tracts[[c for c in c1 if c in tracts.columns]].copy()
    gdf1.to_file(os.path.join(GEOJSON_DIR, "map1_food_retail_density.geojson"), driver="GeoJSON")
    print(f"  Map 1: map1_food_retail_density.geojson ({len(gdf1)} tracts)")

    # Map 2
    c2 = ["census_tract_id", "tract_name", "population", "median_income", "poverty_rate",
           "nearest_grocery_miles", "nearest_grocery_name", "low_access_1mi", "low_access_5mi",
           "grocery_count", "pct_no_vehicle", "geometry"]
    gdf2 = tracts[[c for c in c2 if c in tracts.columns]].copy()
    gdf2.to_file(os.path.join(GEOJSON_DIR, "map2_food_access_distance.geojson"), driver="GeoJSON")
    print(f"  Map 2: map2_food_access_distance.geojson ({len(gdf2)} tracts)")

    # Map 3
    c3 = ["census_tract_id", "tract_name", "population", "pct_no_vehicle", "median_income",
           "unemployment_rate", "nearest_grocery_miles", "grocery_count", "geometry"]
    gdf3 = tracts[[c for c in c3 if c in tracts.columns]].copy()
    gdf3.to_file(os.path.join(GEOJSON_DIR, "map3_transport_accessibility.geojson"), driver="GeoJSON")
    print(f"  Map 3: map3_transport_accessibility.geojson ({len(gdf3)} tracts)")

    # Map 4
    c4 = ["census_tract_id", "tract_name", "population", "snap_rate", "snap_households",
           "poverty_rate", "median_income", "unemployment_rate", "pantry_count", "religious_count",
           "food_assistance_demand", "pct_black", "pct_hispanic", "geometry"]
    gdf4 = tracts[[c for c in c4 if c in tracts.columns]].copy()
    gdf4.to_file(os.path.join(GEOJSON_DIR, "map4_food_assistance_demand.geojson"), driver="GeoJSON")
    print(f"  Map 4: map4_food_assistance_demand.geojson ({len(gdf4)} tracts)")

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("ANALYTICAL SUMMARY")
    print(f"{'=' * 60}")
    print(f"Map 1 — Food Retail Environment:")
    print(f"  Avg fast food per tract: {tracts['fastfood_count'].mean():.1f}")
    print(f"  Avg grocery per tract: {tracts['grocery_count'].mean():.1f}")
    print(f"  Tracts with 0 grocery stores: {(tracts['grocery_count'] == 0).sum()}")
    print(f"  Worst food retail score: {tracts['food_retail_score'].max()}")
    print(f"Map 2 — Food Access Distance:")
    print(f"  Tracts >1mi to grocery: {tracts['low_access_1mi'].sum()}")
    print(f"  Tracts >5mi to grocery: {tracts['low_access_5mi'].sum()}")
    print(f"  Max distance: {tracts['nearest_grocery_miles'].max():.1f} mi")
    print(f"Map 3 — Transportation:")
    print(f"  Avg % no vehicle: {tracts['pct_no_vehicle'].mean():.1f}%")
    print(f"Map 4 — Food Assistance Demand:")
    print(f"  Avg SNAP rate: {tracts['snap_rate'].mean():.1f}%")
    print(f"  Avg poverty rate: {tracts['poverty_rate'].mean():.1f}%")
    print(f"  Tracts with 0 pantries: {(tracts['pantry_count'] == 0).sum()}")
    print(f"  Highest demand score: {tracts['food_assistance_demand'].max()}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    acs = fetch_census_acs()
    compute_all_maps(acs)
