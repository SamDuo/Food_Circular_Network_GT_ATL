"""
Parse the AFCN food-network directory paste, geocode each org's address,
and emit a GeoJSON layer the AFCN dashboard can render.

Input:  data/afcn_directory/raw_paste.tsv  (chat-pasted Kumu export)
Output: geojson/afcn_directory.geojson     (~85 organizations)
        data/afcn_directory/parsed.json    (debug — pre-geocode records)
        data/afcn_directory/ungeocoded.csv (rows we couldn't place)

Why a custom parser: the paste comes from a Kumu / Google-Sheet export where
cells contain newlines. Tabs are not preserved as separators in the chat
medium, so each row spans many lines.  We split records by the leading
record-number sentinel ("^\\d+$" on its own line) and then heuristically
pull fields from the line block (label always = first non-empty line, then
type, then description+address by content sniffing).

Geocoding: Mapbox Geocoding API v6 (forward search), token from .env or env
var MAPBOX_PUBLIC_KEY.  Falls back to OpenStreetMap Nominatim (free, no
key) if the Mapbox call fails — Nominatim is throttled to 1 req/s.

Run:
    python scripts/build_afcn_directory_geojson.py
"""

import csv, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent
SRC   = ROOT / "data" / "afcn_directory" / "raw_paste.tsv"
OUT   = ROOT / "geojson" / "afcn_directory.geojson"
DEBUG = ROOT / "data" / "afcn_directory" / "parsed.json"
UNGEO = ROOT / "data" / "afcn_directory" / "ungeocoded.csv"

ENOWN_TYPES = {
    "Recovery & Redistribution", "Farm / Producer", "Consumption & Retail",
    "Supporting Resources & Services", "Public & Education Sector",
    "Food Aggregation & Distribution", "Network", "Organics Recycling & Composting",
}

# ── Token loading ─────────────────────────────────────────────────────────
def load_mapbox_token() -> str:
    tok = os.environ.get("MAPBOX_PUBLIC_KEY", "").strip()
    if tok:
        return tok
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("MAPBOX_PUBLIC_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

MAPBOX_TOKEN = load_mapbox_token()


# ── Parser ────────────────────────────────────────────────────────────────
ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.\-' ]+,?\s+(?:[A-Za-z .]+,\s+)?(?:GA|Georgia)\s+\d{5}",
    re.IGNORECASE,
)
URL_RE      = re.compile(r"https?://[^\s)]+|www\.[^\s)]+")
EMAIL_RE    = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE    = re.compile(r"\(?\d{3}\)?[\s\.-]?\d{3}[\s\.-]?\d{4}")
RECORD_RE   = re.compile(r"^\d+$")


def parse_records(text: str) -> list[dict]:
    """Walk the pasted paragraph and split into per-record blocks keyed by
    the record-number sentinel.  Every record is a dict with whatever fields
    we could pull out heuristically."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    records, current, current_id = [], [], None

    def flush():
        if current_id is None:
            return
        records.append(parse_block(current_id, current))

    for ln in lines[1:]:                         # skip header row
        s = ln.strip()
        if not s:
            continue
        if RECORD_RE.match(s) and len(s) <= 4:
            # New record sentinel
            flush()
            current_id, current = int(s), []
        else:
            current.append(ln)
    flush()
    return records


def parse_block(rid: int, block: list[str]) -> dict:
    """Heuristically split a record block into structured fields."""
    rec = {"id": rid, "label": "", "type": "", "address": "", "description": "",
            "url": "", "image_url": "", "email": "", "phone": "",
            "tags": "", "raw": "\n".join(block)}
    # First non-empty line: name
    nonempty = [ln.strip() for ln in block if ln.strip()]
    if not nonempty:
        return rec
    rec["label"] = nonempty[0]
    # Find the type line (matches a known category)
    for ln in nonempty[1:5]:
        if ln in ENOWN_TYPES:
            rec["type"] = ln
            break
    # Address: first line that looks like a US address
    for ln in nonempty:
        m = ADDRESS_RE.search(ln)
        if m:
            rec["address"] = m.group(0).strip(" ,")
            break
    # If still no address, try cleaner address-like lines (City, GA zip)
    if not rec["address"]:
        for ln in nonempty:
            if re.search(r"\b(?:GA|Georgia)\b\s+\d{5}", ln) and len(ln) < 120:
                rec["address"] = ln.strip(" ,")
                break
    # URL: first http(s)
    for ln in nonempty:
        u = URL_RE.search(ln)
        if u:
            url = u.group(0)
            if any(s in url for s in ("squarespace-cdn", "wixstatic", "gstatic", "fbcdn", "cdn-website")):
                if not rec["image_url"]:
                    rec["image_url"] = url
            else:
                if not rec["url"]:
                    rec["url"] = url
    # Email + phone (best-effort)
    for ln in nonempty:
        if not rec["email"]:
            m = EMAIL_RE.search(ln)
            if m: rec["email"] = m.group(0)
        if not rec["phone"]:
            m = PHONE_RE.search(ln)
            if m: rec["phone"] = m.group(0)
    # Description: longest sentence-like line that isn't the label/type/address/URL
    candidates = []
    for ln in nonempty:
        if ln in (rec["label"], rec["type"], rec["address"]):
            continue
        if URL_RE.search(ln) or EMAIL_RE.search(ln):
            continue
        if len(ln) >= 60:
            candidates.append(ln)
    if candidates:
        rec["description"] = max(candidates, key=len)
    return rec


# ── Geocoding ─────────────────────────────────────────────────────────────
class Geocoder:
    def __init__(self, mapbox_token: str = ""):
        self.mb = mapbox_token
        self.cache: dict[str, tuple[float, float] | None] = {}

    def geocode(self, address: str) -> tuple[float, float] | None:
        if not address:
            return None
        if address in self.cache:
            return self.cache[address]
        coords = self._mapbox(address) if self.mb else None
        if coords is None:
            coords = self._nominatim(address)
        self.cache[address] = coords
        return coords

    def _mapbox(self, addr: str) -> tuple[float, float] | None:
        try:
            url = ("https://api.mapbox.com/search/geocode/v6/forward?"
                   + urllib.parse.urlencode({
                       "q": addr,
                       "limit": 1,
                       "country": "us",
                       "proximity": "-84.388,33.749",   # bias toward Atlanta
                       "access_token": self.mb,
                   }))
            with urllib.request.urlopen(url, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
            f = (data.get("features") or [None])[0]
            if not f: return None
            lon, lat = f["geometry"]["coordinates"]
            return (float(lon), float(lat))
        except Exception as e:
            print(f"    [mapbox fail] {addr[:60]}: {e}")
            return None

    def _nominatim(self, addr: str) -> tuple[float, float] | None:
        try:
            url = ("https://nominatim.openstreetmap.org/search?"
                   + urllib.parse.urlencode({"q": addr, "format": "json", "limit": 1}))
            req = urllib.request.Request(url, headers={"User-Agent": "AFCN/build_directory 1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
            if not data: return None
            return (float(data[0]["lon"]), float(data[0]["lat"]))
        except Exception as e:
            print(f"    [nominatim fail] {addr[:60]}: {e}")
            return None
        finally:
            time.sleep(1.05)   # respect Nominatim 1 req/s


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    if not SRC.exists():
        sys.exit(f"missing input: {SRC}")
    text = SRC.read_text(encoding="utf-8", errors="replace")
    records = parse_records(text)
    print(f"→ parsed {len(records)} records")
    DEBUG.parent.mkdir(parents=True, exist_ok=True)
    DEBUG.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"  ✓ wrote {DEBUG}")

    if not MAPBOX_TOKEN:
        print("  ! no MAPBOX_PUBLIC_KEY; falling back to Nominatim only "
              "(slower, ~1 req/s)")
    geo = Geocoder(MAPBOX_TOKEN)

    features, ungeocoded = [], []
    for rec in records:
        if not rec["address"]:
            ungeocoded.append({"id": rec["id"], "label": rec["label"],
                                "reason": "no address parsed"})
            continue
        ll = geo.geocode(rec["address"])
        if not ll:
            ungeocoded.append({"id": rec["id"], "label": rec["label"],
                                "reason": "geocoder returned no result",
                                "address": rec["address"]})
            continue
        lon, lat = ll
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "id":          rec["id"],
                "label":       rec["label"],
                "type":        rec["type"],
                "address":     rec["address"],
                "description": rec["description"][:600],
                "url":         rec["url"],
                "image":       rec["image_url"],
                "email":       rec["email"],
                "phone":       rec["phone"],
            },
        })
        print(f"  ✓ #{rec['id']:>3} {rec['label'][:36]:36s}  ({lat:.4f}, {lon:.4f})")

    fc = {
        "type": "FeatureCollection",
        "features": features,
        "_source": "AFCN food-network directory paste · "
                    + time.strftime("%Y-%m-%d"),
    }
    OUT.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    print(f"\n✓ wrote {OUT}  ({len(features)} features, "
            f"{OUT.stat().st_size/1024:,.0f} KB)")

    if ungeocoded:
        with open(UNGEO, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "label", "reason", "address"])
            w.writeheader()
            for r in ungeocoded:
                w.writerow({"id": r["id"], "label": r["label"],
                            "reason": r["reason"],
                            "address": r.get("address", "")})
        print(f"  · {len(ungeocoded)} ungeocoded → {UNGEO}")


if __name__ == "__main__":
    main()
