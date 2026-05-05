"""
Parse the Kumu data-editor scrape (the 802-row full export) into a clean,
usable CSV — then feed it into the existing taxonomy + GeoJSON pipeline.

INPUT FILE (any of these names is auto-detected):
    data/afcn_directory/full_export.csv
    data/afcn_directory/full_export.tsv
    data/afcn_directory/Book 2.csv
    data/afcn_directory/Book 2(Sheet1).csv

INPUT FORMAT (the awkward one Kumu's DOM scrape produces):
    Each line is one record. The whole record is wrapped in CSV double-quotes
    `"…"` if any cell contained a newline; otherwise the row is bare. Inside
    the row, the 23 fields are separated by TAB characters (\t). Empty cells
    show up as consecutive tabs. The first field is the Kumu row number.

OUTPUTS:
    data/afcn_directory/clean_export.csv      ← properly headered, comma-CSV
    data/afcn_directory/clean_export.json     ← same data as a JSON list
    geojson/afcn_directory.geojson            ← rebuilt with all 802 records,
                                                 geocoded
    data/afcn_directory/ungeocoded.csv        ← rows we couldn't place

Then it auto-runs `build_afcn_taxonomy.py` so the network page picks up the
new data immediately.

USAGE:
    python scripts/parse_kumu_paste.py
"""

import csv, io, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent
DIR   = ROOT / "data" / "afcn_directory"
DIR.mkdir(parents=True, exist_ok=True)

CANDIDATE_INPUTS = [
    DIR / "full_export.csv",
    DIR / "full_export.tsv",
    DIR / "Book 2.csv",
    DIR / "Book 2(Sheet1).csv",
    DIR / "kumu_export.csv",
]

# Column order matches the actual Kumu data-editor TSV layout (24 fields).
# Profiled from the 802-row export: idx 6 carries the rich pipe-separated
# topical tags ("Nutrition, Health, & Wellness | Education | …"), which we
# treat as the primary outer-ring activity source. Idx 5 ("Activities") is
# Kumu's own activities column but is sparsely populated in this export.
COLUMNS = [
    "id", "Label", "Type", "Tags", "Description",
    "Activities", "Topics", "Address",
    "Business Type", "Contact", "Date", "Date Founded", "degree",
    "Demographics", "Extra Info", "Food Products and Growing Methods",
    "Geographic Region", "Image", "Learn More", "metrics::last", "Quote",
    "Relationship", "Relationship Tags", "URL",
]

# Mojibake from a Latin-1 ↔ UTF-8 round-trip. Replace with reasonable ASCII.
MOJIBAKE_FIX = [
    ("ï¿½", "'"),         # most common — was a curly apostrophe / em dash
    ("ï»¿", ""),          # UTF-8 BOM
    ("ï¿½s", "'s"),       # possessive
    ("ï¿½", "'"),
    ("�", "'"),      # actual replacement character
]


def find_input() -> Path:
    for p in CANDIDATE_INPUTS:
        if p.exists() and p.stat().st_size > 0:
            print(f"→ found input: {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")
            return p
    print("✗ No input file found. Save your Kumu export at one of:")
    for p in CANDIDATE_INPUTS:
        print(f"     {p}")
    sys.exit(1)


def clean_text(s: str) -> str:
    if not s:
        return ""
    for bad, good in MOJIBAKE_FIX:
        s = s.replace(bad, good)
    # Collapse interior whitespace; preserve newlines as a single space
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_kumu_export(path: Path) -> list[dict]:
    """The format is: each line is one record. If the record originally had
    embedded newlines, the line is wrapped in a single pair of double quotes
    and any literal `"` inside is doubled (`""`). Inside the record the 23
    fields are separated by TAB."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows: list[list[str]] = []

    # Use csv module to chunk lines properly (handles the "..." wrapper +
    # doubled quotes). The dialect uses comma, so each line should yield a
    # single-element list — and that one element is the tab-separated payload.
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    for raw in reader:
        if not raw:
            continue
        # Some lines will come back as a single string (the whole tab record);
        # others may be multiple due to commas inside descriptions. Re-join
        # on commas to undo any spurious splits.
        joined = ",".join(raw)
        if not joined.strip():
            continue
        fields = joined.split("\t")
        rows.append(fields)

    # Map each row onto the 23-column schema. Pad/truncate as needed.
    records = []
    for r in rows:
        # Skip the header line (if present) — detected by "Label" appearing
        # anywhere in the first 5 fields and no leading number.
        if len(r) >= 2 and not r[0].strip().isdigit() and "Label" in (r[1] if len(r) > 1 else r[0]):
            continue
        # If first cell isn't a digit, this is probably noise (header / blank)
        if not r or not r[0].strip().isdigit():
            continue
        r = r + [""] * (len(COLUMNS) - len(r))
        r = r[: len(COLUMNS)]
        rec = {col: clean_text(val) for col, val in zip(COLUMNS, r)}
        records.append(rec)

    return records


def write_clean_csv(records: list[dict]) -> Path:
    out = DIR / "clean_export.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(records)
    print(f"  ✓ wrote {out.relative_to(ROOT)}  ({len(records):,} rows)")
    return out


def write_clean_json(records: list[dict]) -> Path:
    out = DIR / "clean_export.json"
    out.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"  ✓ wrote {out.relative_to(ROOT)}")
    return out


# ── Geocoding (Mapbox v6 forward, Nominatim fallback) ────────────────────
def load_token() -> str:
    tok = os.environ.get("MAPBOX_PUBLIC_KEY", "").strip()
    if tok:
        return tok
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("MAPBOX_PUBLIC_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def geocode_one(address: str, token: str) -> tuple[float, float] | None:
    if not address:
        return None
    if token:
        try:
            url = ("https://api.mapbox.com/search/geocode/v6/forward?"
                    + urllib.parse.urlencode({
                        "q": address, "limit": 1, "country": "us",
                        "proximity": "-84.388,33.749",
                        "access_token": token,
                    }))
            with urllib.request.urlopen(url, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
            f = (data.get("features") or [None])[0]
            if f:
                lon, lat = f["geometry"]["coordinates"]
                return (float(lon), float(lat))
        except Exception:
            pass
    # Nominatim fallback (slow, 1 req/s)
    try:
        url = ("https://nominatim.openstreetmap.org/search?"
                + urllib.parse.urlencode({"q": address, "format": "json", "limit": 1}))
        req = urllib.request.Request(url, headers={"User-Agent": "AFCN/parse_kumu 1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
        if data:
            return (float(data[0]["lon"]), float(data[0]["lat"]))
    except Exception:
        pass
    finally:
        time.sleep(1.05)
    return None


def build_geojson(records: list[dict]) -> Path:
    print("\n→ Geocoding addresses (Mapbox first, Nominatim fallback)…")
    token = load_token()
    if not token:
        print("  ! no MAPBOX_PUBLIC_KEY — using Nominatim only (slow)")

    out_path     = ROOT / "geojson" / "afcn_directory.geojson"
    ungeo_path   = DIR / "ungeocoded.csv"
    cache: dict[str, tuple[float, float] | None] = {}
    features, ungeocoded = [], []

    # Reuse already-geocoded coordinates from the prior 53-org run if present
    if out_path.exists():
        try:
            old = json.loads(out_path.read_text(encoding="utf-8"))
            for f in old.get("features", []):
                a = f["properties"].get("address", "")
                if a:
                    cache[a] = tuple(f["geometry"]["coordinates"])
            print(f"  · pre-loaded {len(cache)} cached addresses from prior run")
        except Exception:
            pass

    for rec in records:
        addr = rec.get("Address", "").strip()
        if not addr or addr.upper() in {"NA", "N/A", "—"}:
            ungeocoded.append({"id": rec["id"], "label": rec["Label"],
                                "reason": "no address"})
            continue
        ll = cache.get(addr)
        if ll is None and addr in cache:
            pass
        elif ll is None:
            ll = geocode_one(addr, token)
            cache[addr] = ll
        if not ll:
            ungeocoded.append({"id": rec["id"], "label": rec["Label"],
                                "reason": "geocoder returned no result",
                                "address": addr})
            continue

        lon, lat = ll
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "id":           int(rec["id"]) if rec["id"].isdigit() else rec["id"],
                "label":        rec["Label"],
                "type":         rec["Type"],
                "tags":         rec["Tags"],
                "description":  rec["Description"],
                "activities":   rec.get("Topics") or rec.get("Activities") or "",
                "address":      addr,
                "business":     rec["Business Type"],
                "contact":      rec["Contact"],
                "founded":      rec["Date Founded"],
                "degree":       int(rec["degree"]) if rec["degree"].isdigit() else 0,
                "demographics": rec["Demographics"],
                "products":     rec["Food Products and Growing Methods"],
                "region":       rec["Geographic Region"],
                "image":        rec["Image"],
                "quote":        rec["Quote"],
                "url":          rec["URL"],
            },
        })
        if len(features) % 25 == 0:
            print(f"  · {len(features):>4} placed / {len(ungeocoded):>4} skipped")

    fc = {
        "type": "FeatureCollection",
        "features": features,
        "_source": f"AFCN directory · Kumu export · "
                    + time.strftime("%Y-%m-%d") + f" · {len(records)} input rows",
    }
    out_path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    print(f"\n  ✓ wrote {out_path.relative_to(ROOT)}  "
            f"({len(features):,} features, {out_path.stat().st_size:,} bytes)")

    if ungeocoded:
        with open(ungeo_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "label", "reason", "address"])
            w.writeheader()
            for u in ungeocoded:
                w.writerow({"id": u["id"], "label": u["label"],
                             "reason": u["reason"],
                             "address": u.get("address", "")})
        print(f"  · {len(ungeocoded):,} skipped → {ungeo_path.relative_to(ROOT)}")

    return out_path


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    src = find_input()
    print("\n→ Parsing Kumu export…")
    records = parse_kumu_export(src)
    print(f"  · parsed {len(records):,} records")
    if records:
        sample = records[0]
        print(f"  · sample row: #{sample['id']} {sample['Label']!r} "
                f"({sample['Type']!r}, addr={bool(sample['Address'])})")

    write_clean_csv(records)
    write_clean_json(records)

    build_geojson(records)

    print("\n→ Rebuilding taxonomy from full dataset…")
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_afcn_taxonomy.py")],
                    check=False)

    print("\n✓ Done. Refresh network/index.html to see all 802 orgs.")


if __name__ == "__main__":
    main()
