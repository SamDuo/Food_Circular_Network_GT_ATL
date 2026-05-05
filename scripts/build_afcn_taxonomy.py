"""
Build the taxonomy + adjacency table that drives the AFCN Transformation-Map
network visualization (network/index.html).

INPUTS
──────
  data/afcn_directory/full_export.csv   ← preferred (clean Kumu CSV)
  geojson/afcn_directory.geojson        ← fallback (the 53-org subset
                                          parsed from the chat paste)

OUTPUTS
───────
  data/afcn_network.json                ← consumed by network/script.js

The output schema is a flat in-memory shape that maps cleanly to the WEF
Strategic-Intelligence Transformation-Map model:

  {
    "anchor": { "label": "Atlanta Food Circular Network",
                 "subtitle": "Georgia Tech I2CE Lab · curation snapshot",
                 "image": "…hero image url…" },
    "types":  [ { "id": "recovery_redistribution",
                  "label": "Recovery & Redistribution",
                  "subtitle": "Pantries, food rescue, faith-based",
                  "image": "…",
                  "count": 26 }, … ],          ← 8 inner-ring nodes
    "activities": [ { "id": "food_pantry",
                      "label": "Food Pantry",
                      "count": 14,
                      "connects_to": ["recovery_redistribution",
                                       "public_education_sector"] }, … ],
                                                ← outer-ring nodes
    "orgs":   [ { "id": 1, "label": "Open Hand Atlanta",
                  "type_id": "recovery_redistribution",
                  "activities": ["food_pantry", "nutrition_health_wellness"],
                  "address": "…", "url": "…", "image": "…",
                  "description": "…", "phone": "…", "email": "…",
                  "lon": -84.43, "lat": 33.79,
                  "degree": 3 }, … ]
  }

Run:
    python scripts/build_afcn_taxonomy.py
"""

import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent
SRC_CSV_CANDIDATES = [
    ROOT / "data" / "afcn_directory" / "clean_export.csv",   # produced by parse_kumu_paste.py
    ROOT / "data" / "afcn_directory" / "full_export.csv",    # legacy hand-saved file
]
SRC_CSV = next((p for p in SRC_CSV_CANDIDATES if p.exists()), SRC_CSV_CANDIDATES[0])
SRC_GJ   = ROOT / "geojson" / "afcn_directory.geojson"
OUT_JSON = ROOT / "data" / "afcn_network.json"
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

ANCHOR = {
    "label":    "Atlanta Food Circular Network",
    "subtitle": "Georgia Tech I2CE Lab · Curation snapshot",
    "image":    "../resources/Layers & Packages/img/hero_food.jpg",
}

# Color + short subtitle for each top-level type (the inner ring).
# Colors echo the dashboard palette so the two views feel like one system.
TYPE_META = {
    "Recovery & Redistribution":           {"color": "#ef5350", "subtitle": "Pantries, food rescue, faith-based distribution"},
    "Farm / Producer":                      {"color": "#66bb6a", "subtitle": "Urban farms, gardens, growers"},
    "Consumption & Retail":                 {"color": "#ffa502", "subtitle": "Restaurants, markets, retail"},
    "Supporting Resources & Services":      {"color": "#42a5f5", "subtitle": "Funding, training, advocacy, technical assistance"},
    "Public & Education Sector":            {"color": "#fdd835", "subtitle": "Schools, universities, government"},
    "Food Aggregation & Distribution":      {"color": "#ab47bc", "subtitle": "Wholesale, logistics, healthcare food service"},
    "Network":                              {"color": "#26a69a", "subtitle": "Coalitions, member networks"},
    "Organics Recycling & Composting":      {"color": "#8d6e63", "subtitle": "Compost, soil amendments"},
}


def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.lower()).strip("_")
    return s or "unknown"


def load_orgs():
    """Return a list of dicts with keys: id, label, type, activities (list),
    description, address, url, image, email, phone, lon, lat, degree.
    Prefers the clean CSV if present; otherwise reads the 53-org GeoJSON."""
    if SRC_CSV.exists():
        return load_from_csv()
    return load_from_geojson()


def load_from_csv():
    print(f"→ reading {SRC_CSV}")
    rows = []
    with open(SRC_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader, 1):
            label = (r.get("Label") or "").strip()
            if not label:
                continue
            t = (r.get("Type") or "").strip()
            acts_raw = (r.get("Topics") or "").strip() or (r.get("Activities") or "").strip()
            activities = [a.strip() for a in re.split(r"\s*[\|;]\s*", acts_raw) if a.strip()]
            rows.append({
                "id":          i,
                "label":       label,
                "type":        t,
                "activities":  activities,
                "address":     (r.get("Address") or "").strip(),
                "description": (r.get("Description") or "").strip(),
                "url":         (r.get("URL") or "").strip(),
                "image":       (r.get("Image") or "").strip(),
                "email":       extract(r, ["Contact", "email", "Email"], r"[\w.+-]+@[\w-]+\.[\w.-]+"),
                "phone":       extract(r, ["Contact", "phone", "Phone"], r"\(?\d{3}\)?[\s\.-]?\d{3}[\s\.-]?\d{4}"),
                "demographics": (r.get("Demographics") or "").strip(),
                "region":      (r.get("Geographic Region") or "").strip(),
                "business":    (r.get("Business Type") or "").strip(),
                "degree":      _to_int(r.get("degree")),
                "lon": None, "lat": None,    # CSV may not carry coords
            })
    print(f"  · {len(rows)} rows read from CSV")
    return rows


def _to_int(v):
    try: return int(float(v))
    except: return 0


def extract(row, keys, pattern):
    for k in keys:
        v = row.get(k) or ""
        m = re.search(pattern, v)
        if m: return m.group(0)
    return ""


def load_from_geojson():
    print(f"→ reading {SRC_GJ}  (53-org subset; CSV absent)")
    with open(SRC_GJ, encoding="utf-8") as f:
        gj = json.load(f)
    rows = []
    for feat in gj["features"]:
        p   = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        # GeoJSON parsed-from-paste doesn't have an explicit Activities column,
        # so we fall back on inferring an activity from the description.
        activities = infer_activities(p.get("description", ""), p.get("type", ""))
        rows.append({
            "id":           p.get("id"),
            "label":        p.get("label", ""),
            "type":         p.get("type", ""),
            "activities":   activities,
            "address":      p.get("address", ""),
            "description":  p.get("description", ""),
            "url":          p.get("url", ""),
            "image":        p.get("image", ""),
            "email":        p.get("email", ""),
            "phone":        p.get("phone", ""),
            "demographics": "",
            "region":       "",
            "business":     "",
            "degree":       1,
            "lon":          lon,
            "lat":          lat,
        })
    print(f"  · {len(rows)} rows from GeoJSON")
    return rows


# Activity-tag dictionary used when CSV's "Activities" column is unavailable
ACTIVITY_KEYWORDS = {
    "Food Pantry":                 [r"\bfood pantry\b", r"\bfood closet\b", r"\bpantry\b"],
    "Community Garden":            [r"\bcommunity garden\b"],
    "Urban Agriculture":           [r"\burban (?:farm|agriculture)\b"],
    "Education Outreach":          [r"\beducat", r"\bclassroom"],
    "Youth Programs":              [r"\byouth\b", r"\bschool\b", r"\bk-?12\b"],
    "Nutrition, Health & Wellness": [r"\bnutrition", r"\bhealth", r"\bwellness"],
    "Funding":                     [r"\bfund", r"\bgrant\b"],
    "Advocacy":                    [r"\badvocacy\b", r"\bpolicy\b"],
    "Training":                    [r"\btraining\b", r"\bworkshop"],
    "Technical Assistance":        [r"\btechnical assistance\b", r"\bconsult"],
    "Composting":                  [r"\bcompost"],
    "Faith-Based":                 [r"\bchurch\b", r"\bministry\b", r"\bfaith"],
    "Farmers Market":              [r"\bfarmers? market\b"],
    "Restaurant / Cafe":           [r"\brestaurant\b", r"\bcafé\b", r"\bcafe\b", r"\bdining\b"],
    "Herbalism":                   [r"\bherb"],
    "Seed Saving":                 [r"\bseed sav"],
    "Agritourism":                 [r"\bagrotour"],
}


def infer_activities(text: str, type_: str) -> list[str]:
    out = []
    t = text.lower()
    for tag, patterns in ACTIVITY_KEYWORDS.items():
        for p in patterns:
            if re.search(p, t):
                out.append(tag); break
    # Default activity by type so every org has at least one tag
    if not out:
        defaults = {
            "Recovery & Redistribution": "Food Pantry",
            "Farm / Producer":            "Urban Agriculture",
            "Consumption & Retail":       "Restaurant / Cafe",
            "Supporting Resources & Services": "Technical Assistance",
            "Public & Education Sector":  "Education Outreach",
            "Food Aggregation & Distribution": "Distribution",
            "Network":                    "Advocacy",
            "Organics Recycling & Composting": "Composting",
        }
        d = defaults.get(type_)
        if d: out.append(d)
    return out


def build_taxonomy(orgs):
    # Type counts → inner ring
    type_counts = Counter(o["type"] for o in orgs if o["type"])
    types = []
    for label, count in type_counts.most_common():
        meta = TYPE_META.get(label, {"color": "#9e9e9e", "subtitle": ""})
        types.append({
            "id":       slug(label),
            "label":    label,
            "subtitle": meta["subtitle"],
            "color":    meta["color"],
            "count":    count,
        })

    # Activity counts + cross-type adjacency → outer ring
    activity_counts = Counter()
    activity_to_types = defaultdict(set)
    for o in orgs:
        for a in o["activities"]:
            activity_counts[a] += 1
            if o["type"]:
                activity_to_types[a].add(slug(o["type"]))
    activities = []
    for label, count in activity_counts.most_common():
        if count < 2:                  # drop singleton activities so the outer ring is readable
            continue
        activities.append({
            "id":           slug(label),
            "label":        label,
            "count":        count,
            "connects_to":  sorted(activity_to_types[label]),
        })

    # Optional HTTP-enrichment sidecar (og:image, og:description, favicon,
    # social handles). Produced by scripts/enrich_orgs.py — present only
    # if the user has run that script.
    enrich_path = ROOT / "data" / "afcn_directory" / "enrichment.json"
    enrich = {}
    if enrich_path.exists():
        try:
            enrich = json.loads(enrich_path.read_text(encoding="utf-8"))
            print(f"  · loaded enrichment for {sum(1 for v in enrich.values() if v.get('status') == 'ok'):,} orgs")
        except Exception as e:
            print(f"  ! enrichment.json present but unreadable: {e}")

    # Per-org records
    orgs_out = []
    for o in orgs:
        e = enrich.get(str(o["id"]), {})
        # Use og_image as a fallback hero only if we don't already have one
        hero = o["image"] or e.get("og_image") or ""
        orgs_out.append({
            "id":           o["id"],
            "label":        o["label"],
            "type_id":      slug(o["type"]) if o["type"] else "",
            "type":         o["type"],
            "activities":   [slug(a) for a in o["activities"]],
            "activity_labels": o["activities"],
            "address":      o["address"],
            "description":  o["description"],
            "url":          o["url"],
            "image":        hero,
            "email":        o["email"],
            "phone":        o["phone"],
            "demographics": o["demographics"],
            "region":       o["region"],
            "business":     o["business"],
            "degree":       o["degree"],
            "lon":          o["lon"],
            "lat":          o["lat"],
            # Web-enrichment payload (empty when not yet fetched)
            "tagline":      e.get("og_description") or "",
            "favicon":      e.get("favicon") or "",
            "socials":      e.get("socials") or {},
        })

    return {
        "anchor":     ANCHOR,
        "generated":  __import__("time").strftime("%Y-%m-%d %H:%M"),
        "n_orgs":     len(orgs_out),
        "types":      types,
        "activities": activities,
        "orgs":       orgs_out,
    }


def main():
    orgs = load_orgs()
    if not orgs:
        raise SystemExit("no orgs loaded — supply data/afcn_directory/full_export.csv or geojson/afcn_directory.geojson")
    payload = build_taxonomy(orgs)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\n✓ wrote {OUT_JSON.relative_to(ROOT)}  "
            f"({len(payload['types'])} types, "
            f"{len(payload['activities'])} activity tags, "
            f"{len(payload['orgs'])} orgs, "
            f"{OUT_JSON.stat().st_size:,} bytes)")
    # Quick console summary
    print("\nInner ring (types):")
    for t in payload["types"]:
        print(f"  · {t['label']:38s} count={t['count']:>3}  color={t['color']}")
    print("\nOuter ring (activity tags, count ≥ 2):")
    for a in payload["activities"][:20]:
        print(f"  · {a['label']:30s} count={a['count']:>3}  links→{len(a['connects_to'])}")


if __name__ == "__main__":
    main()
