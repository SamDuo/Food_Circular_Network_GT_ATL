# -*- coding: utf-8 -*-
"""
Compute CDC mRFEI (Modified Retail Food Environment Index) + LILA flags
+ income distribution per census tract for AFCN dashboard.

Outputs: geojson/map1_food_retail_mrfei.geojson
         (replaces map1_food_retail_density.geojson)

Requirements: pip install geopandas requests shapely
"""

import os, sys, json, math, requests
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEOJSON = os.path.join(BASE_DIR, "geojson")
DATA = os.path.join(BASE_DIR, "data")
os.makedirs(DATA, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Step 1: Fetch income distribution from Census ACS
# B19001: Household Income in the Past 12 Months
# ═══════════════════════════════════════════════════════════
def fetch_income_distribution():
    print("=" * 60)
    print("Step 1: Fetching income distribution (B19001)...")

    ACS = "https://api.census.gov/data/2022/acs/acs5"

    # B19001_001E = total households
    # B19001_002E = < $10,000
    # B19001_003E = $10,000 - $14,999
    # B19001_004E = $15,000 - $19,999
    # B19001_005E = $20,000 - $24,999
    # B19001_006E = $25,000 - $29,999
    # B19001_007E = $30,000 - $34,999
    # B19001_008E = $35,000 - $39,999
    # B19001_009E = $40,000 - $44,999
    # B19001_010E = $45,000 - $49,999
    # B19001_011E = $50,000 - $59,999
    # B19001_012E = $60,000 - $74,999
    # B19001_013E = $75,000 - $99,999
    # B19001_014E = $100,000 - $124,999
    # B19001_015E = $125,000 - $149,999
    # B19001_016E = $150,000 - $199,999
    # B19001_017E = $200,000 or more

    vars_list = [f"B19001_{str(i).zfill(3)}E" for i in range(1, 18)]
    var_str = ",".join(vars_list)

    all_rows = []
    headers = None
    for county in ["121", "089"]:
        url = f"{ACS}?get=NAME,{var_str}&for=tract:*&in=state:13&in=county:{county}"
        print(f"  Fetching county {county}...")
        resp = requests.get(url, timeout=60)
        data = resp.json()
        if headers is None:
            headers = data[0]
        all_rows.extend(data[1:])

    print(f"  {len(all_rows)} tracts")

    # Group into income brackets for pie chart
    # Simplified into 6 categories:
    # < $25k (low), $25k-$50k (lower-middle), $50k-$75k (middle),
    # $75k-$100k (upper-middle), $100k-$150k (high), $150k+ (affluent)
    income_data = {}
    for row in all_rows:
        d = dict(zip(headers, row))
        geoid = f"13{d['county']}{d['tract']}"

        def s(k):
            v = d.get(k, "")
            return int(v) if v and v not in ("-666666666", "") else 0

        total = s("B19001_001E")
        if total == 0:
            income_data[geoid] = {
                "income_total_hh": 0,
                "income_under_25k": 0, "income_25k_50k": 0, "income_50k_75k": 0,
                "income_75k_100k": 0, "income_100k_150k": 0, "income_150k_plus": 0,
                "pct_under_25k": 0, "pct_25k_50k": 0, "pct_50k_75k": 0,
                "pct_75k_100k": 0, "pct_100k_150k": 0, "pct_150k_plus": 0,
            }
            continue

        under_25k = s("B19001_002E") + s("B19001_003E") + s("B19001_004E") + s("B19001_005E")
        k25_50 = s("B19001_006E") + s("B19001_007E") + s("B19001_008E") + s("B19001_009E") + s("B19001_010E")
        k50_75 = s("B19001_011E") + s("B19001_012E")
        k75_100 = s("B19001_013E")
        k100_150 = s("B19001_014E") + s("B19001_015E")
        k150_plus = s("B19001_016E") + s("B19001_017E")

        income_data[geoid] = {
            "income_total_hh": total,
            "income_under_25k": under_25k,
            "income_25k_50k": k25_50,
            "income_50k_75k": k50_75,
            "income_75k_100k": k75_100,
            "income_100k_150k": k100_150,
            "income_150k_plus": k150_plus,
            "pct_under_25k": round(under_25k / total * 100, 1),
            "pct_25k_50k": round(k25_50 / total * 100, 1),
            "pct_50k_75k": round(k50_75 / total * 100, 1),
            "pct_75k_100k": round(k75_100 / total * 100, 1),
            "pct_100k_150k": round(k100_150 / total * 100, 1),
            "pct_150k_plus": round(k150_plus / total * 100, 1),
        }

    with open(os.path.join(DATA, "census_income_dist.json"), "w") as f:
        json.dump(income_data, f, indent=2)
    print(f"  Saved income distribution for {len(income_data)} tracts")
    return income_data


# ═══════════════════════════════════════════════════════════
# Step 2: Load spatial data and compute mRFEI
# ═══════════════════════════════════════════════════════════
def load_pts(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1])
            for feat in data["features"]
            if feat.get("geometry") and feat["geometry"]["type"] == "Point"]


def count_in_polys(gdf, points):
    counts = []
    for _, row in gdf.iterrows():
        p = prep(row.geometry)
        counts.append(sum(1 for pt in points if p.contains(pt)))
    return counts


def haversine(lon1, lat1, lon2, lat2):
    R = 3958.8
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def compute_mrfei(income_data):
    print("\n" + "=" * 60)
    print("Step 2: Loading tracts and point data...")

    tracts = gpd.read_file(os.path.join(GEOJSON, "census_tracts_tiger.geojson"))
    tracts = tracts.rename(columns={"GEOID": "census_tract_id", "NAMELSAD": "tract_name"})
    print(f"  {len(tracts)} tracts")

    # Load ACS base data
    acs_path = os.path.join(DATA, "census_acs_parsed.json")
    with open(acs_path) as f:
        acs = json.load(f)

    # ── Healthy retailers ──
    # Supermarkets + grocery stores + farmers markets
    healthy_pts = (
        load_pts(os.path.join(GEOJSON, "pkg_atlanta_grocery_stores.geojson"))
        + load_pts(os.path.join(GEOJSON, "pkg_supermarkets_metroatl.geojson"))
        + load_pts(os.path.join(GEOJSON, "pkg_atlanta_metro_area_farmers_markets.geojson"))
    )

    # ── Unhealthy retailers ──
    # Fast food + convenience stores (includes dollar stores from OSM)
    unhealthy_pts = (
        load_pts(os.path.join(GEOJSON, "pkg_all_fast_food_locations_in_metro_atlanta.geojson"))
        + load_pts(os.path.join(GEOJSON, "convenience_stores_atl.geojson"))
    )

    print(f"  Healthy retailers: {len(healthy_pts)}")
    print(f"  Unhealthy retailers: {len(unhealthy_pts)}")

    # Count per tract
    print("\nStep 3: Spatial join — counting retailers per tract...")
    tracts["healthy_count"] = count_in_polys(tracts, healthy_pts)
    tracts["unhealthy_count"] = count_in_polys(tracts, unhealthy_pts)

    # Also count by specific type for popup detail
    tracts["grocery_count"] = count_in_polys(tracts, load_pts(os.path.join(GEOJSON, "pkg_atlanta_grocery_stores.geojson")))
    tracts["supermarket_count"] = count_in_polys(tracts, load_pts(os.path.join(GEOJSON, "pkg_supermarkets_metroatl.geojson")))
    tracts["fastfood_count"] = count_in_polys(tracts, load_pts(os.path.join(GEOJSON, "pkg_all_fast_food_locations_in_metro_atlanta.geojson")))
    tracts["convenience_count"] = count_in_polys(tracts, load_pts(os.path.join(GEOJSON, "convenience_stores_atl.geojson")))
    tracts["farmers_market_count"] = count_in_polys(tracts, load_pts(os.path.join(GEOJSON, "pkg_atlanta_metro_area_farmers_markets.geojson")))

    # ── mRFEI = healthy / (healthy + unhealthy) × 100 ──
    print("\nStep 4: Computing mRFEI scores...")
    def calc_mrfei(row):
        h = row["healthy_count"]
        u = row["unhealthy_count"]
        total = h + u
        if total == 0:
            return None  # no food retailers at all = food desert
        return round(h / total * 100, 1)

    tracts["mrfei"] = tracts.apply(calc_mrfei, axis=1)

    # ── Nearest healthy retailer distance ──
    print("Step 5: Computing distance to nearest healthy retailer...")
    healthy_locs = []
    for path in ["pkg_atlanta_grocery_stores.geojson", "pkg_supermarkets_metroatl.geojson"]:
        with open(os.path.join(GEOJSON, path), encoding="utf-8") as f:
            data = json.load(f)
        for feat in data["features"]:
            if feat["geometry"]["type"] == "Point":
                healthy_locs.append((
                    feat["geometry"]["coordinates"],
                    feat["properties"].get("Store_Name") or feat["properties"].get("Company", "")
                ))

    dists, gnames = [], []
    for _, row in tracts.iterrows():
        c = row.geometry.centroid
        bd, bn = float("inf"), ""
        for coords, nm in healthy_locs:
            d = haversine(c.x, c.y, coords[0], coords[1])
            if d < bd:
                bd, bn = d, nm
        dists.append(round(bd, 2))
        gnames.append(bn)

    tracts["nearest_healthy_miles"] = dists
    tracts["nearest_healthy_name"] = gnames

    # ── Join ACS data ──
    print("Step 6: Joining ACS + income data...")
    for idx, row in tracts.iterrows():
        tid = row["census_tract_id"]
        if tid in acs:
            for k, v in acs[tid].items():
                tracts.at[idx, k] = v
        if tid in income_data:
            for k, v in income_data[tid].items():
                tracts.at[idx, k] = v

    # ── LILA flag (USDA definition) ──
    # Low-income: poverty rate >= 20% OR median income <= 80% of metro median
    # Low-access: >= 500 people OR 33% of pop > 1 mile from supermarket (urban)
    print("Step 7: Computing LILA food desert flags...")

    metro_median_income = tracts["median_income"].median()
    print(f"  Metro median income: ${metro_median_income:,.0f}")

    tracts["is_low_income"] = (
        (tracts["poverty_rate"].fillna(0) >= 20) |
        (tracts["median_income"].fillna(999999) <= metro_median_income * 0.8)
    )

    tracts["is_low_access"] = tracts["nearest_healthy_miles"] >= 1.0  # >= not > (USDA uses >=)

    tracts["is_lila"] = tracts["is_low_income"] & tracts["is_low_access"]

    # ── Combined food access gap ──
    # Multi-factor scoring: distance + food environment quality + poverty
    # Each factor contributes 0-33 points, total 0-100
    print("Step 8: Computing combined food access gap...")

    def access_gap(row):
        score = 0

        # Factor 1: Distance to healthy retailer (0-35 pts)
        d = row["nearest_healthy_miles"]
        if d >= 5:
            score += 35
        elif d >= 2:
            score += 25
        elif d >= 1:
            score += 15
        elif d >= 0.5:
            score += 5

        # Factor 2: Food environment quality — mRFEI (0-35 pts)
        m = row["mrfei"]
        if m is None:
            score += 35  # no retailers at all = worst
        elif m == 0:
            score += 30  # food swamp (only unhealthy)
        elif m < 20:
            score += 20
        elif m < 40:
            score += 10
        elif m < 60:
            score += 5

        # Factor 3: Economic vulnerability (0-30 pts)
        pov = row.get("poverty_rate") or 0
        if pov >= 30:
            score += 20
        elif pov >= 20:
            score += 12
        elif pov >= 10:
            score += 5

        noveh = row.get("pct_no_vehicle") or 0
        if noveh >= 20:
            score += 10
        elif noveh >= 10:
            score += 5

        return min(score, 100)

    tracts["food_access_gap"] = tracts.apply(access_gap, axis=1)

    # Classify
    def gap_label(score):
        if score >= 70:
            return "Critical"
        elif score >= 50:
            return "Severe"
        elif score >= 30:
            return "Moderate"
        elif score >= 15:
            return "Low"
        return "Adequate"

    tracts["gap_label"] = tracts["food_access_gap"].apply(gap_label)

    # ── Save ──
    print("\n" + "=" * 60)
    print("Step 9: Saving...")

    cols = [
        "census_tract_id", "tract_name", "geometry",
        # mRFEI
        "mrfei", "healthy_count", "unhealthy_count",
        "grocery_count", "supermarket_count", "fastfood_count",
        "convenience_count", "farmers_market_count",
        # Distance
        "nearest_healthy_miles", "nearest_healthy_name",
        # LILA
        "is_low_income", "is_low_access", "is_lila",
        # Combined
        "food_access_gap", "gap_label",
        # ACS
        "population", "median_income", "poverty_rate", "snap_rate",
        "pct_no_vehicle", "unemployment_rate",
        # Income distribution
        "income_total_hh",
        "pct_under_25k", "pct_25k_50k", "pct_50k_75k",
        "pct_75k_100k", "pct_100k_150k", "pct_150k_plus",
    ]

    out = tracts[[c for c in cols if c in tracts.columns]].copy()
    out_path = os.path.join(GEOJSON, "map1_food_retail_mrfei.geojson")
    out.to_file(out_path, driver="GeoJSON")
    sz = os.path.getsize(out_path) / 1024
    print(f"  map1_food_retail_mrfei.geojson ({len(out)} tracts, {sz:.0f} KB)")

    # Stats
    print(f"\n{'=' * 60}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 60}")
    mrfei_valid = tracts["mrfei"].dropna()
    print(f"mRFEI scores:")
    print(f"  Mean: {mrfei_valid.mean():.1f}")
    print(f"  Median: {mrfei_valid.median():.1f}")
    print(f"  Tracts with mRFEI=0 (food swamp): {(mrfei_valid == 0).sum()}")
    print(f"  Tracts with no retailers: {tracts['mrfei'].isna().sum()}")
    print(f"  Tracts mRFEI < 10: {(mrfei_valid < 10).sum()}")
    print(f"LILA (food desert):")
    print(f"  Low-income tracts: {tracts['is_low_income'].sum()}")
    print(f"  Low-access tracts: {tracts['is_low_access'].sum()}")
    print(f"  LILA (both): {tracts['is_lila'].sum()}")
    print(f"Combined food access gap:")
    for label in ["Critical", "Severe", "Moderate", "Low", "Adequate"]:
        n = (tracts["gap_label"] == label).sum()
        print(f"  {label}: {n} tracts")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    income = fetch_income_distribution()
    compute_mrfei(income)
