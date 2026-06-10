"""
Sprint 6 — Capstone: classify every Atlanta MSA tract into one of the
5 supervisor-named urban typologies, using k-means on five derived axes:

  1. income_score        z(ACS median household income)
  2. density_score       z(ACS population per km²)
  3. vulnerability_score z(avg of CDC PLACES OBESITY + DIABETES + MHLTH)
  4. transit_score       z(stops within 800 m, from compute_transit_access)
  5. food_access_score   z(grocery within 1 mi, from atl_pro_food_deserts;
                            inverted so higher = better access)

Inputs (all already on disk after Sprints 1, 2, 4 + existing data):
  geojson/atl_demographics_acs.geojson   (Sprint 1 + 5c broadband join)
  geojson/atl_health_places.geojson      (Sprint 2)
  geojson/atl_transit_access.geojson     (Sprint 4b)
  geojson/atl_pro_food_deserts.geojson   (existing)
  geojson/census_tracts_tiger.geojson    (geometry source if missing in joins)

Output:
  geojson/atl_typology_classified.geojson
    properties:
      GEOID                              tract identifier
      typology_id                        0..4
      typology_label                     one of:
        "High-growth Core"      — Midtown / BeltLine
        "Affluent Suburban"     — North Atlanta
        "Disinvested Urban"     — South / West
        "Industrial Logistics"  — near Hartsfield-Jackson
        "Emerging Mixed-use"    — BeltLine edges
      <all five input scores>
      <distance to nearest cluster centroid>

K-means is implemented in stdlib (numpy not required), seeded
deterministically so results are reproducible.

USAGE:
  python -X utf8 scripts/build_typology.py
  python -X utf8 scripts/build_typology.py --k 6     # try a 6-class refinement
"""
from __future__ import annotations
import argparse, json, math, random, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 4242  # reproducible

DEMO_GJ      = ROOT / "geojson" / "atl_demographics_acs.geojson"
HEALTH_GJ    = ROOT / "geojson" / "atl_health_places.geojson"
TRANSIT_GJ   = ROOT / "geojson" / "atl_transit_access.geojson"
FOODDES_GJ   = ROOT / "geojson" / "atl_pro_food_deserts.geojson"
TRACTS_GJ    = ROOT / "geojson" / "census_tracts_tiger.geojson"
OUT          = ROOT / "geojson" / "atl_typology_classified.geojson"

FEATURE_NAMES = ["income", "density", "vulnerability", "transit", "food_access"]


# ── Data loading + join ─────────────────────────────────────
def index_by_geoid(path: Path, geom_too: bool = False):
    if not path.exists():
        print(f"  ! {path.name} missing")
        return {}
    gj = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for f in gj["features"]:
        p = f.get("properties") or {}
        geoid = (p.get("GEOID") or p.get("GEOID20") or
                  p.get("GEO_ID") or p.get("GEOID11") or "")
        if geoid.startswith("1400000US"):
            geoid = geoid[9:]
        if not geoid:
            continue
        out[geoid] = (p, f.get("geometry")) if geom_too else p
    return out


def load_geometries():
    """Use the largest geometry source available. Demographics has 530 tracts;
    transit has the same 530 with valid geom; tracts_tiger is the original."""
    for path in (DEMO_GJ, TRANSIT_GJ, TRACTS_GJ):
        if path.exists():
            return {gid: g for gid, (_, g) in index_by_geoid(path, geom_too=True).items()
                    if g}
    return {}


# ── Stdlib k-means ──────────────────────────────────────────
def zscore(col):
    n = len(col)
    if not n:
        return col
    valid = [v for v in col if v is not None]
    if not valid:
        return [0.0]*n
    mu = sum(valid) / len(valid)
    var = sum((v - mu)**2 for v in valid) / len(valid)
    sd = math.sqrt(var) if var > 0 else 1.0
    return [(v - mu)/sd if v is not None else 0.0 for v in col]


def kmeans(X, k, max_iter=80, seed=SEED):
    """X = list[list[float]]. Returns (labels, centroids).
    Deterministic with k-means++ seeding."""
    n = len(X)
    d = len(X[0])
    rng = random.Random(seed)

    # k-means++ init
    centroids = [list(X[rng.randrange(n)])]
    for _ in range(k-1):
        dists = []
        for x in X:
            min_d = min(sum((x[i]-c[i])**2 for i in range(d)) for c in centroids)
            dists.append(min_d)
        s = sum(dists)
        if s == 0:
            centroids.append(list(X[rng.randrange(n)]))
            continue
        r = rng.random() * s
        acc = 0.0
        for i, dd in enumerate(dists):
            acc += dd
            if acc >= r:
                centroids.append(list(X[i])); break

    labels = [0]*n
    for _ in range(max_iter):
        # Assign
        new_labels = []
        for x in X:
            best, best_d = 0, float("inf")
            for ci, c in enumerate(centroids):
                dd = sum((x[i]-c[i])**2 for i in range(d))
                if dd < best_d:
                    best_d, best = dd, ci
            new_labels.append(best)
        if new_labels == labels:
            break
        labels = new_labels
        # Update
        for ci in range(k):
            members = [X[i] for i in range(n) if labels[i] == ci]
            if not members: continue
            for j in range(d):
                centroids[ci][j] = sum(m[j] for m in members) / len(members)
    return labels, centroids


# ── Main pipeline ───────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    # Load all four source layers
    print("  · loading source layers")
    demo    = index_by_geoid(DEMO_GJ)
    health  = index_by_geoid(HEALTH_GJ)
    transit = index_by_geoid(TRANSIT_GJ)
    fooddes = index_by_geoid(FOODDES_GJ)
    geoms   = load_geometries()

    print(f"      demo:{len(demo)}  health:{len(health)}  "
            f"transit:{len(transit)}  fooddes:{len(fooddes)}  geoms:{len(geoms)}")

    # Build feature rows (only tracts present in all REQUIRED sources)
    rows = []
    for geoid, dp in demo.items():
        hp = health.get(geoid, {})
        tp = transit.get(geoid, {})
        fp = fooddes.get(geoid, {})

        income       = dp.get("median_income")
        density      = dp.get("pop_density")
        obesity      = hp.get("OBESITY_CrudePrev")
        diabetes     = hp.get("DIABETES_CrudePrev")
        mhealth      = hp.get("MHLTH_CrudePrev")
        access_score = tp.get("access_score")

        # food_access_score: invert LILA flag where present.
        # LILA fields vary by source; we look for a "lila" or similar flag;
        # otherwise fall back to whether tract is in the food-desert layer.
        lila = None
        for k in ("lila", "LILA", "LILATracts_Vehicle", "lilatracts_vehicle"):
            if k in fp and fp[k] is not None:
                lila = fp[k]; break
        food_access = 0 if lila in (1, "1", True, "True") else 1   # 1 = ok, 0 = LILA

        # Combine vulnerability components (any of the 3 may be missing)
        vuln_parts = [v for v in (obesity, diabetes, mhealth) if v is not None]
        vulnerability = sum(vuln_parts)/len(vuln_parts) if vuln_parts else None

        # Skip if too sparse
        non_null = sum(1 for v in (income, density, vulnerability,
                                    access_score, food_access) if v is not None)
        if non_null < 3:
            continue

        rows.append({
            "geoid":         geoid,
            "income":        income,
            "density":       density,
            "vulnerability": vulnerability,
            "transit":       access_score,
            "food_access":   food_access,
        })

    print(f"  · {len(rows):,} tracts joined with usable data")

    # Standardize each feature
    cols = {n: zscore([r[n] for r in rows]) for n in FEATURE_NAMES}
    X = []
    for i in range(len(rows)):
        X.append([cols[n][i] for n in FEATURE_NAMES])

    print(f"  · running k-means (k={args.k})…")
    labels, centroids = kmeans(X, args.k, max_iter=80, seed=SEED)

    # Cluster centroid table for naming
    print("\n  cluster centroids (z-scored):")
    print(f"    {'k':>2} {'income':>8} {'density':>8} {'vuln':>8} {'transit':>8} {'food':>8}  count")
    counts = [labels.count(i) for i in range(args.k)]
    for i, c in enumerate(centroids):
        print(f"    {i:>2} {c[0]:>8.2f} {c[1]:>8.2f} {c[2]:>8.2f} {c[3]:>8.2f} {c[4]:>8.2f}  {counts[i]:>4}")

    # ── Name clusters using rules over centroid signs ──────────
    # Rules (consistent with the supervisor's 5 typologies):
    #   High-growth Core      : high density + high income + high transit
    #   Affluent Suburban     : low density  + high income + low transit + low vuln
    #   Disinvested Urban     : low income   + high vuln   + low food access
    #   Industrial Logistics  : low density  + low income  + low vuln (transient pop)
    #   Emerging Mixed-use    : middling everything (balance)
    def name_cluster(c):
        income, density, vuln, transit, food = c
        scores = {
            "High-growth Core":     density + income + transit,
            "Affluent Suburban":    income - density - transit - vuln,
            "Disinvested Urban":    -income + vuln - food,
            "Industrial Logistics": -density - income - vuln,
            "Emerging Mixed-use":   1.0 - (abs(income) + abs(density) + abs(vuln)
                                            + abs(transit) + abs(food)),
        }
        return max(scores, key=scores.get)

    # Score every (cluster, label) combination, then greedily assign by
    # highest fitness so the best-fitting cluster gets each label first.
    label_pool = ["High-growth Core", "Affluent Suburban", "Disinvested Urban",
                   "Industrial Logistics", "Emerging Mixed-use"]
    def fitness(c, label):
        income, density, vuln, transit, food = c
        if label == "High-growth Core":
            # dense + transit-rich + middle/high income
            return 2*density + income + 1.5*transit
        if label == "Affluent Suburban":
            # high income + low density + low vulnerability (sprawl)
            return 2*income - density - vuln - transit
        if label == "Disinvested Urban":
            # low income + high vulnerability (S/W Atlanta core)
            return -income + 1.5*vuln
        if label == "Industrial Logistics":
            # the airport / freight tracts: extreme negative food access
            # is the unique signature, plus low income
            return -2*food - income - density
        if label == "Emerging Mixed-use":
            # Prefer balanced clusters (low absolute z-scores) — typical
            # outer-suburb / transition zones. Reward closeness to origin.
            return 4.0 - (abs(income) + abs(density) + abs(vuln)
                          + abs(transit) + abs(food))
        return -math.inf

    triples = [(fitness(c, lbl), i, lbl)
               for i, c in enumerate(centroids)
               for lbl in label_pool]
    triples.sort(reverse=True)            # highest fitness first
    final = [None] * args.k
    used_labels = set()
    for score, i, lbl in triples:
        if final[i] is None and lbl not in used_labels:
            final[i] = lbl; used_labels.add(lbl)
        if all(f is not None for f in final[:len(label_pool)]):
            break
    # If k > 5, leftover clusters get numeric labels
    for i in range(args.k):
        if final[i] is None:
            final[i] = f"Cluster {i}"
    # If k > 5, leftover clusters keep their suggested names with a number
    print("\n  cluster name assignments:")
    for i, name in enumerate(final):
        print(f"    {i} → {name}  ({counts[i]} tracts)")

    # ── Write output ─────────────────────────────────────────
    out_features = []
    written = 0
    for i, r in enumerate(rows):
        geom = geoms.get(r["geoid"])
        if not geom:
            continue
        cluster_id = labels[i]
        props = {
            "GEOID":             r["geoid"],
            "typology_id":       cluster_id,
            "typology_label":    final[cluster_id],
            "income":            r["income"],
            "density":           r["density"],
            "vulnerability":     r["vulnerability"],
            "transit":           r["transit"],
            "food_access":       r["food_access"],
        }
        out_features.append({"type": "Feature", "geometry": geom, "properties": props})
        written += 1
    print(f"\n  · {written:,} features written ({len(rows) - written:,} dropped for missing geometry)")

    fc = {"type": "FeatureCollection", "features": out_features,
            "_source": f"k-means classifier · k={args.k} · {time.strftime('%Y-%m-%d')}"}
    OUT.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    size_mb = OUT.stat().st_size / 1_048_576
    print(f"  ✓ wrote {OUT.relative_to(ROOT)} ({len(out_features):,} features, {size_mb:.2f} MB)")

    # Distribution
    from collections import Counter
    dist = Counter(f["properties"]["typology_label"] for f in out_features)
    print(f"\n  typology distribution:")
    for label, n in dist.most_common():
        print(f"    {label:<22} {n:>4}")

    meta = {
        "source":        "derived from atl_demographics_acs + atl_health_places + atl_transit_access + atl_pro_food_deserts",
        "method":        f"k-means k={args.k} on z-scored features {FEATURE_NAMES}",
        "seed":          SEED,
        "fetched_at":    time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature_count": len(out_features),
        "typology_distribution": dict(dist),
        "script":        "scripts/build_typology.py",
    }
    OUT.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  ✓ wrote {OUT.with_suffix('.meta.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
