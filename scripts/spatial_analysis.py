"""
Atlanta Food System — Spatial / Variable Analysis Pipeline
═════════════════════════════════════════════════════════
Joins tract-level food retail metrics, transit accessibility, and CDC food
insecurity into a single dataframe, then runs:

  1. Pearson correlations (numeric vars vs food_access_gap and mrfei)
  2. One-way ANOVA across gap_label groups (Adequate → Critical)
  3. Welch's t-tests for LILA vs non-LILA tracts on each predictor
  4. Group means + 95% CIs for the storytelling pullnumbers
  5. Simple OLS regression of food_access_gap on POI density + transit + income

Outputs two artifacts the story website consumes:
  - data/analysis_findings.json  (numbers used as pullnumbers and inline cites)
  - data/analysis_summary.md     (human-readable sanity check for the report)

Run:
  python scripts/spatial_analysis.py
"""

import json, math, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import f_oneway, ttest_ind, pearsonr, spearmanr

# ──────────────────────────────────────────────────────────
# Atlanta neighborhood reference points (lon, lat).
# Used to label tracts by their closest well-known neighborhood
# so the story can write "West End" instead of "Census Tract 78".
# Centroids derived from City of Atlanta NPU centerpoints.
# ──────────────────────────────────────────────────────────
NEIGHBORHOODS = {
    # ── In-town core ──────────────────────────
    "Midtown":            (-84.385, 33.781),
    "Downtown":           (-84.388, 33.755),
    "Old Fourth Ward":    (-84.371, 33.762),
    "Sweet Auburn":       (-84.378, 33.755),
    "Castleberry Hill":   (-84.398, 33.749),
    "Vine City":          (-84.418, 33.762),
    "English Avenue":     (-84.418, 33.770),
    "Atlantic Station":   (-84.396, 33.793),
    "Home Park":          (-84.402, 33.789),
    "Georgia Tech":       (-84.396, 33.776),
    "West End":           (-84.418, 33.736),
    "Westview":           (-84.430, 33.733),
    "Mechanicsville":     (-84.396, 33.732),
    "Summerhill":         (-84.388, 33.728),
    "Peoplestown":        (-84.380, 33.724),
    "Pittsburgh":         (-84.398, 33.722),
    "Adair Park":         (-84.413, 33.722),
    "Capitol View":       (-84.401, 33.715),
    "Grant Park":         (-84.371, 33.741),
    "Cabbagetown":        (-84.362, 33.751),
    "Reynoldstown":       (-84.353, 33.749),
    "Inman Park":         (-84.353, 33.760),
    "Edgewood":           (-84.343, 33.764),
    "Kirkwood":           (-84.327, 33.752),
    "East Atlanta":       (-84.337, 33.736),
    "Ormewood Park":      (-84.340, 33.737),
    # ── North & northeast ────────────────────
    "Buckhead":           (-84.378, 33.834),
    "Lindbergh":          (-84.367, 33.819),
    "Virginia-Highland":  (-84.354, 33.778),
    "Morningside":        (-84.354, 33.795),
    "Ansley Park":        (-84.380, 33.793),
    "Druid Hills":        (-84.328, 33.776),
    "North Druid Hills":  (-84.318, 33.831),
    # ── West / Northwest ─────────────────────
    "Bankhead":           (-84.448, 33.770),
    "Grove Park":         (-84.453, 33.776),
    "West Highlands":     (-84.450, 33.795),
    "Adamsville":         (-84.493, 33.747),
    "Cascade Heights":    (-84.467, 33.733),
    "Adams Park":         (-84.473, 33.720),
    # ── South / Southwest ────────────────────
    "South Atlanta":      (-84.379, 33.711),
    "Lakewood":           (-84.383, 33.694),
    "Lakewood Heights":   (-84.382, 33.690),
    "Browns Mill Park":   (-84.357, 33.681),
    "College Park":       (-84.450, 33.654),
    "East Point":         (-84.439, 33.679),
    # ── DeKalb ───────────────────────────────
    "Decatur":            (-84.298, 33.774),
    "Avondale Estates":   (-84.272, 33.770),
    "Stone Mountain":     (-84.170, 33.808),
    "Tucker":             (-84.218, 33.854),
    "Brookhaven":         (-84.336, 33.860),
    "Chamblee":           (-84.298, 33.892),
    "Doraville":          (-84.284, 33.898),
}

# Georgia Tech campus centroid (the building, not the neighborhood)
GT_CAMPUS_CENTROID = (-84.3963, 33.7756)


def polygon_centroid(coords) -> tuple[float, float]:
    """Return (lon, lat) centroid for a GeoJSON polygon (first ring only)."""
    if not coords:
        return (0.0, 0.0)
    ring = coords[0] if isinstance(coords[0][0], list) else coords
    sx = sy = 0.0
    n = 0
    for pt in ring:
        if isinstance(pt, list) and len(pt) >= 2:
            sx += pt[0]; sy += pt[1]; n += 1
    return (sx / n, sy / n) if n else (0.0, 0.0)


def haversine_miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance between (lon, lat) points, in miles."""
    R = 3958.8
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def closest_neighborhood(lon: float, lat: float) -> str:
    best, best_d = "—", 1e9
    for name, (nlon, nlat) in NEIGHBORHOODS.items():
        d = haversine_miles((lon, lat), (nlon, nlat))
        if d < best_d:
            best, best_d = name, d
    return best


def point_in_ring(pt, ring):
    """Ray-cast point-in-polygon (single ring)."""
    x, y = pt
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside

ROOT = Path(__file__).resolve().parent.parent
GJ   = ROOT / "geojson"
OUT  = ROOT / "data"
OUT.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────
# 1. Load tract-level base table (already joined upstream)
# ──────────────────────────────────────────────────────────
def load_tract_table() -> tuple[pd.DataFrame, dict]:
    """map1_food_retail_mrfei.geojson is the canonical tract table — already
    has POI counts, mRFEI, LILA flags, demographics, gap score, and gap label.
    We also compute polygon centroid and the closest known Atlanta neighborhood
    so the story can label tracts by name."""
    src = GJ / "map1_food_retail_mrfei.geojson"
    with open(src, encoding="utf-8") as f:
        gj = json.load(f)
    rows, geoms = [], {}
    for feat in gj["features"]:
        p = feat["properties"]
        # Centroid for naming + spatial-weights
        coords = (feat.get("geometry") or {}).get("coordinates") or []
        # MultiPolygon: take largest ring; Polygon: take first ring
        if (feat.get("geometry") or {}).get("type") == "MultiPolygon":
            biggest = max(coords, key=lambda poly: len(poly[0]) if poly else 0, default=[[[0, 0]]])
            ring = biggest[0]
        elif (feat.get("geometry") or {}).get("type") == "Polygon":
            ring = coords[0] if coords else [[0, 0]]
        else:
            ring = [[0, 0]]
        cx = sum(pt[0] for pt in ring) / max(1, len(ring))
        cy = sum(pt[1] for pt in ring) / max(1, len(ring))
        p["_centroid_lon"] = cx
        p["_centroid_lat"] = cy
        p["neighborhood"]  = closest_neighborhood(cx, cy)
        rows.append(p)
        geoms[p.get("census_tract_id")] = ring
    df = pd.DataFrame(rows)
    numeric_cols = [
        "mrfei", "healthy_count", "unhealthy_count", "grocery_count",
        "supermarket_count", "fastfood_count", "convenience_count",
        "farmers_market_count", "nearest_healthy_miles", "food_access_gap",
        "population", "median_income", "poverty_rate", "snap_rate",
        "pct_no_vehicle", "unemployment_rate",
        "_centroid_lon", "_centroid_lat",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["is_low_income", "is_low_access", "is_lila"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().isin(["True", "true", "1"])
    return df, geoms


def find_gt_tract(df: pd.DataFrame, geoms: dict) -> dict:
    """Locate the census tract that contains the Georgia Tech campus.
    Tries point-in-polygon first; falls back to nearest centroid."""
    target = list(GT_CAMPUS_CENTROID)
    # Point-in-polygon scan
    for tid, ring in geoms.items():
        if point_in_ring(target, ring):
            row = df.loc[df["census_tract_id"] == tid]
            if not row.empty:
                r = row.iloc[0].to_dict()
                r["_match"] = "containment"
                return r
    # Fallback: nearest centroid
    df2 = df.assign(_d=df.apply(
        lambda r: haversine_miles(target, (r["_centroid_lon"], r["_centroid_lat"])), axis=1))
    near = df2.nsmallest(1, "_d").iloc[0].to_dict()
    near["_match"] = f"nearest ({near['_d']:.2f} mi from campus center)"
    return near


def named_extremes(df: pd.DataFrame, col: str, n: int = 5) -> dict:
    """Top and bottom n tracts on a column, returned with neighborhood names."""
    keep_cols = ["census_tract_id", "tract_name", "neighborhood", col,
                 "gap_label", "is_lila", "median_income", "poverty_rate",
                 "fastfood_count", "convenience_count", "supermarket_count",
                 "pct_no_vehicle"]
    keep_cols = [c for c in keep_cols if c in df.columns]
    sub = df[keep_cols].dropna(subset=[col])
    return {
        "top":    sub.nlargest(n, col).to_dict(orient="records"),
        "bottom": sub.nsmallest(n, col).to_dict(orient="records"),
    }


def morans_i_knn(df: pd.DataFrame, col: str, k: int = 5) -> dict:
    """Approximate Moran's I using a k-nearest-neighbor row-standardized
    weights matrix. Tests whether values cluster spatially — i.e., whether
    *where you live* predicts an outcome beyond the tract's own attributes.

    Returns I, expected I (= -1/(n-1)), and a permutation p-value."""
    sub = df[["_centroid_lon", "_centroid_lat", col]].dropna()
    if len(sub) < 30:
        return {}
    pts = sub[["_centroid_lon", "_centroid_lat"]].to_numpy()
    x   = sub[col].to_numpy()
    n   = len(x)

    # Pairwise great-circle distances (small n=530, fine to vectorize)
    R   = 3958.8
    lon, lat = np.radians(pts[:, 0]), np.radians(pts[:, 1])
    dlon = lon[:, None] - lon[None, :]
    dlat = lat[:, None] - lat[None, :]
    h    = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    D    = 2 * R * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
    np.fill_diagonal(D, np.inf)

    # k-nearest neighbors → row-standardized weights
    W = np.zeros_like(D)
    nn_idx = np.argpartition(D, kth=k, axis=1)[:, :k]
    for i in range(n):
        W[i, nn_idx[i]] = 1
    rowsums = W.sum(axis=1, keepdims=True)
    W = np.divide(W, rowsums, where=rowsums > 0)

    z   = x - x.mean()
    num = (W * np.outer(z, z)).sum()
    den = (z * z).sum()
    if den == 0:
        return {}
    s0  = W.sum()
    I   = (n / s0) * (num / den)
    EI  = -1 / (n - 1)

    # Permutation test (199 reps is enough for storytelling)
    rng     = np.random.default_rng(7)
    n_perm  = 199
    sims    = np.empty(n_perm)
    for i in range(n_perm):
        zp = z[rng.permutation(n)]
        sims[i] = (n / s0) * ((W * np.outer(zp, zp)).sum()) / den
    p   = float((np.abs(sims - EI) >= abs(I - EI)).mean())

    return {"variable": col, "n": int(n), "I": round(float(I), 3),
            "expected_I": round(EI, 3), "p_value": round(p, 4),
            "interpretation": ("strong clustering" if I > 0.4 else
                                "moderate clustering" if I > 0.15 else
                                "weak clustering" if I > 0.05 else
                                "essentially random")}


def neighborhood_effect_analysis(df: pd.DataFrame) -> dict:
    """Variance decomposition: how much of food-insecurity variance is
    explained by the tract's *neighborhood* (a place-based factor) compared
    to its income/demographics? If the neighborhood term remains significant
    after controlling for income, then 'where you live' is more than 'how
    much you earn'."""
    if "food_insecurity_rate" not in df.columns:
        return {}
    sub = df[["food_insecurity_rate", "median_income", "poverty_rate",
              "neighborhood"]].dropna()
    if len(sub) < 50:
        return {}

    # Group neighborhoods with <3 tracts into "Other" so cells aren't sparse
    counts = sub["neighborhood"].value_counts()
    keep   = counts[counts >= 3].index
    sub["nbhd_grp"] = sub["neighborhood"].where(sub["neighborhood"].isin(keep), "Other")

    # Model A: food_insecurity ~ income + poverty (no place)
    Xa = np.column_stack([np.ones(len(sub)),
                          sub["median_income"].to_numpy(),
                          sub["poverty_rate"].to_numpy()])
    y  = sub["food_insecurity_rate"].to_numpy()
    ba, *_  = np.linalg.lstsq(Xa, y, rcond=None)
    yhat_a  = Xa @ ba
    rss_a   = float(((y - yhat_a) ** 2).sum())

    # Model B: + neighborhood fixed effects
    nbhd_dum = pd.get_dummies(sub["nbhd_grp"], drop_first=True).to_numpy().astype(float)
    Xb = np.column_stack([Xa, nbhd_dum])
    bb, *_  = np.linalg.lstsq(Xb, y, rcond=None)
    yhat_b  = Xb @ bb
    rss_b   = float(((y - yhat_b) ** 2).sum())

    tss = float(((y - y.mean()) ** 2).sum())
    r2_a = 1 - rss_a / tss if tss else 0
    r2_b = 1 - rss_b / tss if tss else 0
    delta_r2 = r2_b - r2_a

    # Partial F-test: does adding neighborhood improve fit?
    n  = len(sub)
    qA = Xa.shape[1]; qB = Xb.shape[1]
    if (qB - qA) > 0 and (n - qB) > 0 and rss_b > 0:
        F      = ((rss_a - rss_b) / (qB - qA)) / (rss_b / (n - qB))
        pF     = 1 - stats.f.cdf(F, qB - qA, n - qB)
    else:
        F, pF = float("nan"), float("nan")

    return {
        "model_A_no_place":     {"R2": round(r2_a, 3),
                                  "predictors": ["median_income", "poverty_rate"]},
        "model_B_with_place":   {"R2": round(r2_b, 3),
                                  "predictors": ["median_income", "poverty_rate", "neighborhood_FE"],
                                  "n_neighborhood_groups": int(nbhd_dum.shape[1] + 1)},
        "delta_R2":             round(delta_r2, 3),
        "partial_F":            round(float(F), 2) if not math.isnan(F) else None,
        "partial_F_p_value":    round(float(pF), 4) if not math.isnan(pF) else None,
        "interpretation":       (
            "Where you live still explains "
            f"{int(round(delta_r2 * 100))}% of variance in food insecurity "
            "even after controlling for household income and poverty rate."
            if delta_r2 > 0.05 else
            "Once income and poverty are controlled for, neighborhood adds little."
        ),
    }


def twin_tracts(df: pd.DataFrame, n: int = 4) -> list[dict]:
    """Find pairs of tracts with similar income but very different
    Food Access Gap Scores. Demonstrates that geography (not income alone)
    drives the gap."""
    sub = df[["census_tract_id", "tract_name", "neighborhood",
              "median_income", "food_access_gap", "is_lila",
              "supermarket_count", "convenience_count",
              "fastfood_count", "pct_no_vehicle"]].dropna()
    if len(sub) < 10:
        return []
    # Income bands of $10k width
    sub = sub.copy()
    sub["income_band"] = (sub["median_income"] // 10000).astype(int) * 10000
    pairs = []
    for band, grp in sub.groupby("income_band"):
        if len(grp) < 2:
            continue
        gh = grp.nlargest(1, "food_access_gap").iloc[0]
        gl = grp.nsmallest(1, "food_access_gap").iloc[0]
        if gh["food_access_gap"] - gl["food_access_gap"] >= 30:
            pairs.append({
                "income_band":      f"${int(band):,} – ${int(band + 9999):,}",
                "high_gap": {
                    "neighborhood":      gh["neighborhood"],
                    "tract_name":        gh["tract_name"],
                    "food_access_gap":   int(gh["food_access_gap"]),
                    "median_income":     int(gh["median_income"]),
                    "supermarket_count": int(gh["supermarket_count"]),
                    "convenience_count": int(gh["convenience_count"]),
                    "is_lila":           bool(gh["is_lila"]),
                },
                "low_gap": {
                    "neighborhood":      gl["neighborhood"],
                    "tract_name":        gl["tract_name"],
                    "food_access_gap":   int(gl["food_access_gap"]),
                    "median_income":     int(gl["median_income"]),
                    "supermarket_count": int(gl["supermarket_count"]),
                    "convenience_count": int(gl["convenience_count"]),
                    "is_lila":           bool(gl["is_lila"]),
                },
                "gap_difference": int(gh["food_access_gap"] - gl["food_access_gap"]),
            })
    pairs.sort(key=lambda p: -p["gap_difference"])
    return pairs[:n]


def merge_transit(df: pd.DataFrame) -> pd.DataFrame:
    """Add tract-level transit accessibility (pct_no_vehicle is duplicated, but
    map3 has nearest_grocery_miles which the mrfei file may lack)."""
    src = GJ / "map3_transport_accessibility.geojson"
    if not src.exists():
        return df
    with open(src, encoding="utf-8") as f:
        gj = json.load(f)
    t = pd.DataFrame([feat["properties"] for feat in gj["features"]])
    keep = ["census_tract_id"] + [c for c in (
        "nearest_grocery_miles", "pct_no_vehicle", "median_income"
    ) if c in t.columns]
    t = t[keep].copy()
    for c in keep[1:]:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    # Suffix columns we already have so they don't clobber the base
    rename = {c: f"{c}_t3" for c in keep[1:] if c in df.columns}
    t = t.rename(columns=rename)
    return df.merge(t, on="census_tract_id", how="left")


def merge_cdc_insecurity(df: pd.DataFrame) -> pd.DataFrame:
    """CDC PLACES food insecurity is only fetched live in the dashboard — but
    if a cached snapshot exists, join on TractFIPS."""
    src = GJ / "places_food_insecurity.geojson"
    if not src.exists():
        return df
    with open(src, encoding="utf-8") as f:
        gj = json.load(f)
    rows = []
    for feat in gj["features"]:
        p = feat["properties"]
        rows.append({
            "TractFIPS": str(p.get("TractFIPS") or "").strip(),
            "food_insecurity_rate": pd.to_numeric(
                p.get("FOODINSECU_CrudePrev"), errors="coerce"
            ),
            "obesity_rate":       pd.to_numeric(p.get("OBESITY_CrudePrev"),  errors="coerce"),
            "diabetes_rate":      pd.to_numeric(p.get("DIABETES_CrudePrev"), errors="coerce"),
        })
    cdc = pd.DataFrame(rows)
    df = df.copy()
    df["TractFIPS"] = df["census_tract_id"].astype(str).str.strip()
    return df.merge(cdc, on="TractFIPS", how="left")


# ──────────────────────────────────────────────────────────
# 2. Statistical analyses
# ──────────────────────────────────────────────────────────
def pearson_table(df: pd.DataFrame, target: str, predictors: list[str]) -> pd.DataFrame:
    rows = []
    for p in predictors:
        if p == target or p not in df.columns:
            continue
        sub = df[[target, p]].dropna()
        if len(sub) < 30:
            continue
        # both vectors must have non-zero variance
        if sub[target].std() == 0 or sub[p].std() == 0:
            continue
        try:
            r, pval = pearsonr(sub[target].to_numpy(), sub[p].to_numpy())
            rs, _   = spearmanr(sub[target].to_numpy(), sub[p].to_numpy())
            r, rs, pval = float(r), float(rs), float(pval)
        except Exception as e:
            print(f"  ! pearsonr failed for {target} vs {p}: {e}")
            continue
        rows.append({"predictor": p, "n": int(len(sub)),
                     "pearson_r": round(r, 3),
                     "spearman_rho": round(rs, 3),
                     "p_value": pval,
                     "r_squared": round(r * r, 3)})
    out = pd.DataFrame(rows).sort_values("pearson_r", key=lambda s: s.abs(),
                                          ascending=False)
    return out


def anova_by_gap_label(df: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    """One-way ANOVA: do POI counts and demographics differ by gap_label?"""
    label_order = ["Adequate", "Low", "Moderate", "Severe", "Critical"]
    df2 = df[df["gap_label"].isin(label_order)].copy()
    rows = []
    for p in predictors:
        if p not in df2.columns:
            continue
        groups = [df2.loc[df2["gap_label"] == lab, p].dropna().values
                  for lab in label_order]
        # need at least 2 non-empty groups with ≥3 observations
        groups = [g for g in groups if len(g) >= 3]
        if len(groups) < 2:
            continue
        try:
            f_stat, p_val = f_oneway(*groups)
            f_stat, p_val = float(f_stat), float(p_val)
        except Exception:
            continue
        means = {lab: float(df2.loc[df2["gap_label"] == lab, p].mean())
                 for lab in label_order
                 if not df2.loc[df2["gap_label"] == lab, p].dropna().empty}
        rows.append({"predictor": p, "F": round(f_stat, 2), "p_value": p_val,
                     "means_by_group": means})
    return pd.DataFrame(rows).sort_values("F", ascending=False)


def lila_vs_nonlila(df: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    """Welch's t-test: LILA vs non-LILA tracts."""
    rows = []
    for p in predictors:
        if p not in df.columns:
            continue
        a = df.loc[df["is_lila"] == True,  p].dropna().values
        b = df.loc[df["is_lila"] == False, p].dropna().values
        if len(a) < 5 or len(b) < 5:
            continue
        t_stat, p_val = ttest_ind(a, b, equal_var=False)
        t_stat, p_val = float(t_stat), float(p_val)
        # Cohen's d
        sd_pool = math.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2) if a.var() and b.var() else 0
        d = float((a.mean() - b.mean()) / sd_pool) if sd_pool > 0 else float("nan")
        rows.append({"predictor": p,
                     "lila_mean":     round(float(a.mean()), 2),
                     "non_lila_mean": round(float(b.mean()), 2),
                     "diff":          round(float(a.mean() - b.mean()), 2),
                     "cohen_d":       round(float(d), 3) if not math.isnan(d) else None,
                     "t":             round(float(t_stat), 2),
                     "p_value":       float(p_val),
                     "n_lila":        int(len(a)),
                     "n_non_lila":    int(len(b))})
    return pd.DataFrame(rows).sort_values("cohen_d",
                                          key=lambda s: s.abs(),
                                          ascending=False)


def ols_regression(df: pd.DataFrame, target: str, predictors: list[str]) -> dict:
    """Plain OLS via numpy.linalg — no statsmodels dependency."""
    cols = [target] + [p for p in predictors if p in df.columns]
    sub = df[cols].dropna()
    if len(sub) < 50 or len(cols) < 3:
        return {}
    y = sub[target].values
    X = sub[predictors].values
    X = np.column_stack([np.ones(len(X)), X])  # intercept
    try:
        beta, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return {}
    y_hat = X @ beta
    ss_res = float(((y - y_hat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    n, k = X.shape
    adj_r2 = 1 - (1 - r2) * (n - 1) / max(1, n - k)
    coefs = {"(intercept)": round(float(beta[0]), 3)}
    for name, c in zip(predictors, beta[1:]):
        coefs[name] = round(float(c), 3)
    return {"n": int(n), "r_squared": round(float(r2), 3),
            "adj_r_squared": round(float(adj_r2), 3),
            "coefficients": coefs}


# ──────────────────────────────────────────────────────────
# 3. Group descriptives for narrative pullnumbers
# ──────────────────────────────────────────────────────────
def descriptive_pullnumbers(df: pd.DataFrame) -> dict:
    out = {}
    out["n_tracts"]      = int(len(df))
    out["n_lila"]        = int((df["is_lila"] == True).sum())
    out["lila_pct"]      = round(out["n_lila"] / out["n_tracts"] * 100, 1)
    out["n_severe_crit"] = int(df["gap_label"].isin(["Severe", "Critical"]).sum())
    out["pop_total"]     = int(df["population"].fillna(0).sum())
    if "pct_no_vehicle" in df.columns and "population" in df.columns:
        no_veh_pop = (df["population"].fillna(0) * df["pct_no_vehicle"].fillna(0) / 100).sum()
        out["no_vehicle_pop"] = int(round(no_veh_pop))
    out["avg_mrfei"]     = round(float(df["mrfei"].mean(skipna=True)), 1)
    # LILA vs non-LILA comparisons
    if "fastfood_count" in df.columns:
        ff_lila = df.loc[df["is_lila"] == True,  "fastfood_count"].mean()
        ff_non  = df.loc[df["is_lila"] == False, "fastfood_count"].mean()
        out["fastfood_lila_vs_nonlila"] = {
            "lila_mean": round(float(ff_lila), 2),
            "non_lila_mean": round(float(ff_non), 2),
            "ratio": round(float(ff_lila / ff_non), 2) if ff_non else None,
        }
    if "convenience_count" in df.columns:
        cs_lila = df.loc[df["is_lila"] == True,  "convenience_count"].mean()
        cs_non  = df.loc[df["is_lila"] == False, "convenience_count"].mean()
        out["convenience_lila_vs_nonlila"] = {
            "lila_mean": round(float(cs_lila), 2),
            "non_lila_mean": round(float(cs_non), 2),
            "ratio": round(float(cs_lila / cs_non), 2) if cs_non else None,
        }
    if "supermarket_count" in df.columns:
        sm_lila = df.loc[df["is_lila"] == True,  "supermarket_count"].mean()
        sm_non  = df.loc[df["is_lila"] == False, "supermarket_count"].mean()
        out["supermarket_lila_vs_nonlila"] = {
            "lila_mean": round(float(sm_lila), 2),
            "non_lila_mean": round(float(sm_non), 2),
        }
    if "pct_no_vehicle" in df.columns:
        nv_lila = df.loc[df["is_lila"] == True,  "pct_no_vehicle"].mean()
        nv_non  = df.loc[df["is_lila"] == False, "pct_no_vehicle"].mean()
        out["no_vehicle_lila_vs_nonlila"] = {
            "lila_mean_pct": round(float(nv_lila), 2),
            "non_lila_mean_pct": round(float(nv_non), 2),
            "diff_pct_pts": round(float(nv_lila - nv_non), 2),
        }
    return out


# ──────────────────────────────────────────────────────────
# 4. Main
# ──────────────────────────────────────────────────────────
def main():
    print("→ Loading tract-level master table…")
    df, geoms = load_tract_table()
    print(f"  base rows: {len(df)}")

    df = merge_transit(df)
    df = merge_cdc_insecurity(df)
    print(f"  merged with transit + CDC PLACES; cols: {len(df.columns)}")

    # Quick sanity: how many neighborhoods got assigned, and top counts?
    if "neighborhood" in df.columns:
        nbhd_counts = df["neighborhood"].value_counts().head(8)
        print(f"  Top labeled neighborhoods (closest-centroid): {nbhd_counts.to_dict()}")

    # Predictors used across analyses
    poi_cols = [
        "supermarket_count", "grocery_count", "farmers_market_count",
        "fastfood_count",    "convenience_count",
    ]
    socio_cols = [
        "median_income", "poverty_rate", "snap_rate",
        "pct_no_vehicle", "unemployment_rate",
    ]
    health_cols = [c for c in ("food_insecurity_rate", "obesity_rate", "diabetes_rate")
                   if c in df.columns]
    all_predictors = poi_cols + socio_cols + ["nearest_healthy_miles"] + health_cols

    print("→ Pearson correlations vs food_access_gap")
    corr_gap = pearson_table(df, "food_access_gap", all_predictors)
    print(corr_gap.to_string(index=False))

    print("\n→ Pearson correlations vs mRFEI")
    corr_mrfei = pearson_table(df, "mrfei", all_predictors)
    print(corr_mrfei.to_string(index=False))

    print("\n→ Pearson correlations vs food_insecurity_rate (CDC PLACES)")
    corr_fi = (pearson_table(df, "food_insecurity_rate", all_predictors)
               if "food_insecurity_rate" in df.columns else pd.DataFrame())
    if not corr_fi.empty:
        print(corr_fi.to_string(index=False))

    print("\n→ One-way ANOVA across gap_label groups")
    anova_tbl = anova_by_gap_label(df, all_predictors)
    print(anova_tbl.drop(columns=["means_by_group"]).to_string(index=False))

    print("\n→ Welch's t-test: LILA vs non-LILA tracts")
    lila_tbl = lila_vs_nonlila(df, all_predictors)
    print(lila_tbl.to_string(index=False))

    print("\n→ OLS: food_access_gap ~ POI density + transit + income")
    ols_pois  = ols_regression(df, "food_access_gap",
                                ["fastfood_count", "convenience_count",
                                 "supermarket_count", "pct_no_vehicle",
                                 "median_income"])
    ols_pois_simple = ols_regression(df, "food_access_gap",
                                      ["fastfood_count", "supermarket_count",
                                       "pct_no_vehicle"])
    if ols_pois:
        print(json.dumps(ols_pois, indent=2))

    if "food_insecurity_rate" in df.columns:
        print("\n→ OLS: food_insecurity_rate ~ access gap + POIs + income")
        ols_fi = ols_regression(df, "food_insecurity_rate",
                                 ["food_access_gap", "fastfood_count",
                                  "convenience_count", "supermarket_count",
                                  "median_income", "pct_no_vehicle"])
        print(json.dumps(ols_fi, indent=2) if ols_fi else "(insufficient overlap)")
    else:
        ols_fi = {}

    pulls = descriptive_pullnumbers(df)
    print("\n→ Descriptive pullnumbers")
    print(json.dumps(pulls, indent=2))

    # ─── New analyses for the story ──────────────────────────
    print("\n→ Locating Georgia Tech campus tract")
    gt_tract = find_gt_tract(df, geoms)
    gt_summary = {
        "match":              gt_tract.get("_match"),
        "tract_name":         gt_tract.get("tract_name"),
        "census_tract_id":    gt_tract.get("census_tract_id"),
        "neighborhood":       gt_tract.get("neighborhood"),
        "food_access_gap":    int(gt_tract.get("food_access_gap") or 0),
        "gap_label":          gt_tract.get("gap_label"),
        "mrfei":              gt_tract.get("mrfei"),
        "is_lila":            bool(gt_tract.get("is_lila")),
        "median_income":      int(gt_tract.get("median_income") or 0),
        "poverty_rate":       gt_tract.get("poverty_rate"),
        "pct_no_vehicle":     gt_tract.get("pct_no_vehicle"),
        "supermarket_count":  int(gt_tract.get("supermarket_count") or 0),
        "fastfood_count":     int(gt_tract.get("fastfood_count") or 0),
        "convenience_count":  int(gt_tract.get("convenience_count") or 0),
        "nearest_healthy_miles": gt_tract.get("nearest_healthy_miles"),
        "food_insecurity_rate": gt_tract.get("food_insecurity_rate"),
    }
    print(json.dumps(gt_summary, indent=2, default=str))

    print("\n→ Named extreme tracts on Food Access Gap Score")
    extremes_gap = named_extremes(df, "food_access_gap", n=5)
    for e in extremes_gap["top"]:
        print(f"  WORST: {e['neighborhood']:22s} ({e['tract_name']:18s})  gap={e['food_access_gap']}")
    for e in extremes_gap["bottom"]:
        print(f"  BEST:  {e['neighborhood']:22s} ({e['tract_name']:18s})  gap={e['food_access_gap']}")

    extremes_fi = (named_extremes(df, "food_insecurity_rate", n=5)
                   if "food_insecurity_rate" in df.columns else {"top": [], "bottom": []})

    print("\n→ Spatial clustering — Moran's I (kNN, k=5)")
    morans = {}
    for col in ["food_access_gap", "mrfei", "food_insecurity_rate", "convenience_count",
                "pct_no_vehicle"]:
        if col in df.columns:
            mi = morans_i_knn(df, col, k=5)
            if mi:
                morans[col] = mi
                print(f"  {col:22s}  I={mi['I']:+.3f}  p={mi['p_value']:.4f}  → {mi['interpretation']}")

    print("\n→ Neighborhood-fixed-effects variance decomposition")
    nbhd_effect = neighborhood_effect_analysis(df)
    if nbhd_effect:
        print(json.dumps(nbhd_effect, indent=2))

    print("\n→ Twin tracts (same income band, divergent gap scores)")
    twins = twin_tracts(df, n=5)
    for t in twins:
        print(f"  income {t['income_band']}:  "
              f"{t['high_gap']['neighborhood']} (gap {t['high_gap']['food_access_gap']})  "
              f"vs  {t['low_gap']['neighborhood']} (gap {t['low_gap']['food_access_gap']})  "
              f"Δ={t['gap_difference']}")

    # ─── Persist findings as JSON for the story website ───
    findings = {
        "generated_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        "n_tracts_analyzed": int(len(df)),
        "pullnumbers": pulls,
        "georgia_tech_tract": gt_summary,
        "named_extremes": {
            "food_access_gap":      extremes_gap,
            "food_insecurity_rate": extremes_fi,
        },
        "morans_i": morans,
        "neighborhood_effect": nbhd_effect,
        "twin_tracts": twins,
        "correlations": {
            "vs_food_access_gap": corr_gap.to_dict(orient="records"),
            "vs_mrfei":           corr_mrfei.to_dict(orient="records"),
            "vs_food_insecurity": (corr_fi.to_dict(orient="records")
                                   if not corr_fi.empty else []),
        },
        "anova_by_gap_label": [
            {**r, "p_value": float(r["p_value"])}
            for r in anova_tbl.to_dict(orient="records")
        ],
        "lila_vs_nonlila_ttests": [
            {**r, "p_value": float(r["p_value"])}
            for r in lila_tbl.to_dict(orient="records")
        ],
        "ols_food_access_gap": ols_pois,
        "ols_food_access_gap_simple": ols_pois_simple,
        "ols_food_insecurity": ols_fi,
    }

    # Sanitize: pandas leaves NaN floats and numpy scalars in records, which
    # `json.dump` happily writes as the literal `NaN` — but that is NOT valid
    # JSON and will fail `JSON.parse` in the browser.  Walk the tree once,
    # converting NaN/Inf → null and numpy scalars → Python primitives.
    def clean(v):
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        if isinstance(v, (np.floating,)):
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else f
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, np.bool_):
            return bool(v)
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        return v

    findings = clean(findings)

    with open(OUT / "analysis_findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, default=str, allow_nan=False)
    print(f"\n✓ wrote data/analysis_findings.json ({len(json.dumps(findings))} bytes)")

    # Markdown summary
    md = []
    md.append("# Atlanta Food System — Spatial / Variable Analysis\n")
    md.append(f"_Generated {findings['generated_at']} · n = {findings['n_tracts_analyzed']} tracts_\n")
    md.append("## Pullnumbers\n```json\n" + json.dumps(pulls, indent=2) + "\n```\n")
    md.append("## Top correlations with **Food Access Gap Score**\n")
    md.append(corr_gap.head(10).to_markdown(index=False))
    md.append("\n\n## Top correlations with **mRFEI**\n")
    md.append(corr_mrfei.head(10).to_markdown(index=False))
    if not corr_fi.empty:
        md.append("\n\n## Top correlations with **CDC food-insecurity rate**\n")
        md.append(corr_fi.head(10).to_markdown(index=False))
    md.append("\n\n## ANOVA across gap_label groups\n")
    md.append(anova_tbl.drop(columns=["means_by_group"]).head(15).to_markdown(index=False))
    md.append("\n\n## LILA vs non-LILA tract means\n")
    md.append(lila_tbl.head(15).to_markdown(index=False))
    if ols_pois:
        md.append("\n\n## OLS — Food Access Gap regression\n```json\n" +
                  json.dumps(ols_pois, indent=2) + "\n```\n")
    if ols_fi:
        md.append("\n## OLS — Food Insecurity regression\n```json\n" +
                  json.dumps(ols_fi, indent=2) + "\n```\n")

    with open(OUT / "analysis_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"✓ wrote data/analysis_summary.md")


if __name__ == "__main__":
    main()
