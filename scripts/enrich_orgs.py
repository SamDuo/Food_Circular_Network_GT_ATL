"""
Enrich AFCN orgs by fetching their websites once and pulling out
Open Graph metadata, favicons, and social handles. Stdlib-only —
no BeautifulSoup, no aiohttp.

INPUT:   data/afcn_directory/clean_export.csv     (must have URL column)
OUTPUT:  data/afcn_directory/enrichment.json      (keyed by org id)

Each enrichment record looks like:
  {
    "og_image":       "https://example.org/cover.jpg",
    "og_description": "One-line tagline pulled from the site.",
    "favicon":        "https://example.org/favicon.ico",
    "socials": {
        "instagram": "https://instagram.com/handle",
        "facebook":  "https://facebook.com/page",
        "linkedin":  "https://linkedin.com/company/x",
        "twitter":   "https://twitter.com/handle",
        "youtube":   "https://youtube.com/@handle"
    },
    "fetched_at": "2026-05-04T01:23:45Z",
    "status": "ok" | "404" | "timeout" | "error",
}

USAGE:
  python -X utf8 scripts/enrich_orgs.py             # all rows
  python -X utf8 scripts/enrich_orgs.py --limit 25  # smoke test
  python -X utf8 scripts/enrich_orgs.py --workers 12

Re-running is incremental: orgs already in enrichment.json with status=ok
are skipped. Pass --force to re-fetch everything.
"""
from __future__ import annotations
import argparse, csv, html as ihtml, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error  import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
CSV  = ROOT / "data" / "afcn_directory" / "clean_export.csv"
OUT  = ROOT / "data" / "afcn_directory" / "enrichment.json"

UA = ("Mozilla/5.0 (compatible; AFCN-Enricher/1.0; "
      "+https://github.com/Georgia-Tech-I2CE-Lab)")
TIMEOUT = 10
MAX_BYTES = 350_000   # only the head/top of each page; OG tags are early

# ── Regex extractors (case-insensitive, multi-line) ─────────────
RE_OG_IMAGE = re.compile(
    r'<meta[^>]+(?:property|name)=["\']?og:image["\']?[^>]*content=["\']?([^"\'>\s]+)',
    re.I)
RE_OG_DESC = re.compile(
    r'<meta[^>]+(?:property|name)=["\']?og:description["\']?[^>]*content=["\']([^"\']+)["\']',
    re.I)
RE_TWITTER_DESC = re.compile(
    r'<meta[^>]+name=["\']?twitter:description["\']?[^>]*content=["\']([^"\']+)["\']',
    re.I)
RE_META_DESC = re.compile(
    r'<meta[^>]+name=["\']?description["\']?[^>]*content=["\']([^"\']+)["\']',
    re.I)
RE_ICON = re.compile(
    r'<link[^>]+rel=["\']?(?:shortcut icon|icon|apple-touch-icon)["\']?[^>]*'
    r'href=["\']?([^"\'>\s]+)',
    re.I)

# Find any link/image src whose URL points at a social network. We then
# collapse to the canonical handle so each network gets at most one entry.
SOCIAL_HOSTS = {
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/([^/?\"'\s>]+)", re.I),
    "facebook":  re.compile(r"https?://(?:www\.)?facebook\.com/([^/?\"'\s>]+)",  re.I),
    "linkedin":  re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in|school)/([^/?\"'\s>]+)", re.I),
    "twitter":   re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/([^/?\"'\s>]+)", re.I),
    "youtube":   re.compile(r"https?://(?:www\.)?youtube\.com/(?:c/|channel/|user/|@)([^/?\"'\s>]+)", re.I),
    "tiktok":    re.compile(r"https?://(?:www\.)?tiktok\.com/@([^/?\"'\s>]+)", re.I),
}
# Skip these obviously-not-org accounts (nav links to platform shareability).
SOCIAL_HANDLE_BLOCKLIST = {
    "instagram": {"sharer", "explore", "p", "reel", "tv", "share"},
    "facebook":  {"sharer", "sharer.php", "dialog", "tr", "share"},
    "linkedin":  {"sharing", "shareArticle"},
    "twitter":   {"intent", "share", "search", "home"},
    "youtube":   {"watch", "results"},
}


def normalize_url(u: str) -> str | None:
    if not u:
        return None
    u = u.strip()
    if not u:
        return None
    if not u.lower().startswith(("http://", "https://")):
        u = "http://" + u
    try:
        p = urlparse(u)
        if not p.netloc or "." not in p.netloc:
            return None
    except Exception:
        return None
    return u


def fetch(url: str) -> bytes | None:
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    with urlopen(req, timeout=TIMEOUT) as r:
        # Only read the first MAX_BYTES — OG/icon tags are in <head>.
        return r.read(MAX_BYTES)


def first_match(html: str, *patterns) -> str | None:
    for pat in patterns:
        m = pat.search(html)
        if m:
            return ihtml.unescape(m.group(1)).strip()
    return None


def extract_socials(html: str, base_url: str) -> dict[str, str]:
    out = {}
    for net, pat in SOCIAL_HOSTS.items():
        for m in pat.finditer(html):
            handle = m.group(1).rstrip("/").split("?")[0]
            if not handle or handle.lower() in SOCIAL_HANDLE_BLOCKLIST.get(net, set()):
                continue
            # First good handle wins
            full = m.group(0).split("'")[0].split('"')[0].split(" ")[0]
            out[net] = full.rstrip("/")
            break
    return out


def enrich(org_id: str, url: str) -> dict:
    rec = {"status": "error", "fetched_at": datetime.now(timezone.utc)
                                                  .replace(microsecond=0).isoformat() + "Z"}
    norm = normalize_url(url)
    if not norm:
        rec["status"] = "no_url"
        return rec
    try:
        body = fetch(norm)
        if body is None:
            rec["status"] = "empty"
            return rec
        # Decode liberally — many small-org sites mis-declare encoding.
        try:
            html_text = body.decode("utf-8", errors="replace")
        except Exception:
            html_text = body.decode("latin-1", errors="replace")
        # Only inspect the head + first ~80KB to keep regex cheap.
        head = html_text[:120_000]

        og_image = first_match(head, RE_OG_IMAGE)
        og_desc  = first_match(head, RE_OG_DESC, RE_TWITTER_DESC, RE_META_DESC)
        icon     = first_match(head, RE_ICON)

        if og_image: og_image = urljoin(norm, og_image)
        if icon:     icon     = urljoin(norm, icon)
        if og_desc:
            # Trim and de-bloat
            og_desc = re.sub(r"\s+", " ", og_desc).strip()
            if len(og_desc) > 280:
                og_desc = og_desc[:277].rstrip() + "…"

        rec.update({
            "status":         "ok",
            "og_image":       og_image,
            "og_description": og_desc,
            "favicon":        icon or urljoin(norm, "/favicon.ico"),
            "socials":        extract_socials(head, norm),
            "final_url":      norm,
        })
    except HTTPError as e:
        rec["status"] = f"{e.code}"
    except URLError:
        rec["status"] = "url_error"
    except TimeoutError:
        rec["status"] = "timeout"
    except Exception as e:
        rec["status"] = f"error:{type(e).__name__}"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",   type=int, default=0,    help="stop after N orgs")
    ap.add_argument("--workers", type=int, default=10,   help="concurrent fetchers")
    ap.add_argument("--force",   action="store_true",    help="re-fetch even rows already enriched ok")
    args = ap.parse_args()

    if not CSV.exists():
        print(f"missing {CSV}", file=sys.stderr); sys.exit(1)

    with open(CSV, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("URL") or "").strip()]
    print(f"  · {len(rows):,} rows have URLs (of total in CSV)")

    existing: dict = {}
    if OUT.exists() and not args.force:
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
        print(f"  · {len(existing):,} previously enriched (skip ok rows)")

    queue = []
    for r in rows:
        oid = str(r.get("id") or "").strip()
        if not oid: continue
        if (not args.force) and existing.get(oid, {}).get("status") == "ok":
            continue
        queue.append((oid, (r.get("URL") or "").strip(), r.get("Label", "")))
        if args.limit and len(queue) >= args.limit:
            break

    print(f"  · enriching {len(queue):,} org{'s' if len(queue) != 1 else ''} "
          f"with {args.workers} workers …\n")

    done, ok, fail = 0, 0, 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(enrich, oid, url): (oid, label) for oid, url, label in queue}
        for fut in as_completed(futs):
            oid, label = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = {"status": f"error:{type(e).__name__}"}
            existing[oid] = rec
            done += 1
            if rec.get("status") == "ok":
                ok += 1
                tag = "✓" if rec.get("og_image") else "·"
            else:
                fail += 1
                tag = "✗"
            if done % 25 == 0 or done == len(queue):
                rate = done / max(0.1, time.time() - t0)
                print(f"  {tag} {done:>4}/{len(queue):>4}  ok={ok:<4} fail={fail:<4} "
                      f"rate={rate:4.1f}/s  → {label[:48]}")

            # Persist incrementally so a Ctrl+C doesn't lose work.
            if done % 50 == 0:
                OUT.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    OUT.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    elapsed = time.time() - t0
    print(f"\n  ✓ wrote {OUT.relative_to(ROOT)}  ({len(existing):,} records, {elapsed:.0f}s)")

    # Quick coverage stats
    n_image = sum(1 for v in existing.values() if v.get("og_image"))
    n_desc  = sum(1 for v in existing.values() if v.get("og_description"))
    n_fav   = sum(1 for v in existing.values() if v.get("favicon"))
    n_soc   = sum(1 for v in existing.values() if v.get("socials"))
    print(f"  · og_image: {n_image:,} · og_description: {n_desc:,} · "
          f"favicon: {n_fav:,} · socials: {n_soc:,}")


if __name__ == "__main__":
    main()
