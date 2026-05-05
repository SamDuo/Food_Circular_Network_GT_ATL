"""
Build a static, deploy-ready bundle of the Atlanta Food Story.

Output: ./dist/  with this layout

    dist/
    ├── index.html              # forwards to story/ (so root URL works)
    ├── story/
    │   ├── index.html
    │   ├── style.css
    │   └── script.js
    ├── geojson/                # only files referenced by the story
    │   └── …
    ├── data/
    │   └── analysis_findings.json
    ├── config.json             # Mapbox public token (replaces /api/config)
    ├── _headers                # Cloudflare Pages / Netlify cache rules
    └── README.md

Drop the dist/ folder into Cloudflare Pages or Netlify Drop and you have a
permanent public URL with no Python server required.
"""

import json, os, re, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# ── 1. Wipe and recreate dist/ ───────────────────────────────────────────
def _safe_rmtree(p: Path, attempts: int = 3) -> None:
    """OneDrive on Windows occasionally holds locks on freshly-touched files.
    Retry rmtree a few times before giving up."""
    last = None
    for i in range(attempts):
        try:
            shutil.rmtree(p)
            return
        except PermissionError as e:
            last = e
            time.sleep(0.6 * (i + 1))
    print(f"  ! could not fully clean {p} after {attempts} tries; continuing")
    if last:
        print(f"    last error: {last}")

if DIST.exists():
    _safe_rmtree(DIST)
DIST.mkdir(parents=True, exist_ok=True)
(DIST / "story").mkdir(exist_ok=True)
(DIST / "geojson").mkdir(exist_ok=True)
(DIST / "data").mkdir(exist_ok=True)

# ── 2. Copy story files ──────────────────────────────────────────────────
for fn in ["index.html", "style.css", "script.js"]:
    shutil.copy(ROOT / "story" / fn, DIST / "story" / fn)
print(f"  ✓ story/ copied")

# ── 3. Discover GeoJSON files referenced by the story script ────────────
script_text = (DIST / "story" / "script.js").read_text(encoding="utf-8")
referenced = set(re.findall(r"source:\s*'([^']+\.geojson)'", script_text))
referenced.add("map1_food_retail_mrfei.geojson")  # used by small-multiples fetch
# Always include these too — the inline-stat narrative references them
referenced.update({
    "atl_pro_food_deserts.geojson",
    "atl_pro_marta_bus_routes.geojson",
})
print(f"  · {len(referenced)} GeoJSON files referenced by story:")
for fn in sorted(referenced):
    src = ROOT / "geojson" / fn
    if not src.exists():
        print(f"      MISSING: {fn}")
        continue
    shutil.copy(src, DIST / "geojson" / fn)
    print(f"      {fn}  ({src.stat().st_size / 1024:.0f} KB)")

# ── 4. Copy findings JSON ────────────────────────────────────────────────
findings = ROOT / "data" / "analysis_findings.json"
if findings.exists():
    shutil.copy(findings, DIST / "data" / "analysis_findings.json")
    print(f"  ✓ data/analysis_findings.json copied ({findings.stat().st_size:,} bytes)")
else:
    print("  ! data/analysis_findings.json not found — run scripts/spatial_analysis.py first")

# ── 5. Generate config.json — env vars first (Netlify), then .env (local) ─
mapbox = os.environ.get("MAPBOX_PUBLIC_KEY", "")
arcgis = os.environ.get("ARCGIS_API_KEY",   "")
tomtom = os.environ.get("TOMTOM_API_KEY",   "")
env_path = ROOT / ".env"
if env_path.exists() and not mapbox:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if   k == "MAPBOX_PUBLIC_KEY" and not mapbox: mapbox = v
        elif k == "ARCGIS_API_KEY"    and not arcgis: arcgis = v
        elif k == "TOMTOM_API_KEY"    and not tomtom: tomtom = v

if not mapbox:
    print("  ! WARN: no MAPBOX_PUBLIC_KEY found in env or .env — story will fail to render maps")
    print("    On Netlify: Site Settings → Environment Variables → add MAPBOX_PUBLIC_KEY=pk.…")

cfg = {
    "mapboxPublicKey": mapbox,
    # arcgis + tomtom are not needed by the story page; omit them from the
    # public bundle so we don't broadcast keys we aren't actively using.
}
(DIST / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
mp = (mapbox[:14] + "…") if mapbox else "(empty)"
print(f"  ✓ config.json written  mapboxPublicKey: {mp}")

# ── 6. Root index.html — forwards to /story/ ─────────────────────────────
root_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Atlanta Food Circular Network</title>
  <meta http-equiv="refresh" content="0; url=story/">
  <link rel="canonical" href="story/">
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; padding: 40px;
            color: #111; background: #fbfaf6; max-width: 600px; margin: 0 auto; }
    a { color: #b3603a; }
  </style>
</head>
<body>
  <h1>Atlanta Food Circular Network</h1>
  <p>Redirecting to <a href="story/">the food-system story…</a></p>
</body>
</html>
"""
(DIST / "index.html").write_text(root_html, encoding="utf-8")
print(f"  ✓ index.html (redirect) written")

# ── 7. _headers (cache rules for Cloudflare Pages / Netlify) ────────────
headers = """\
# GeoJSON tiles can be cached aggressively — they only change when we
# re-publish, and the build pipeline replaces the whole bundle.
/geojson/*
  Cache-Control: public, max-age=3600, stale-while-revalidate=86400
  Access-Control-Allow-Origin: *

/data/*
  Cache-Control: public, max-age=600, stale-while-revalidate=3600
  Access-Control-Allow-Origin: *

# HTML / JS / CSS — short cache so updates show up quickly
/*.html
  Cache-Control: public, max-age=60
/*.css
  Cache-Control: public, max-age=300
/*.js
  Cache-Control: public, max-age=300

/config.json
  Cache-Control: public, max-age=300
"""
(DIST / "_headers").write_text(headers, encoding="utf-8")
print(f"  ✓ _headers written")

# ── 8. Deployment README ────────────────────────────────────────────────
readme = """\
# Atlanta Food Story — Static Deploy Bundle

This directory is a self-contained static website. Drop it into any of the
following hosts and you have a public URL the story can be QR-coded to.

## One-line deploy options

### Netlify Drop (zero signup, instant)
1. Go to https://app.netlify.com/drop
2. Drag the entire `dist/` folder onto the page.
3. You get a URL like `https://lucent-bunny-7f3a92.netlify.app` immediately.
4. (Optional) Sign in to claim it and rename it.

### Cloudflare Pages (free, custom subdomain on `*.pages.dev`)
1. Install Wrangler once: `npm install -g wrangler` then `wrangler login`.
2. From the project root: `wrangler pages deploy dist --project-name atl-food-story`
3. URL: `https://atl-food-story.pages.dev`

### GitHub Pages (free if the repo is public)
1. Commit `dist/` to a branch.
2. In repo Settings → Pages, set source to that branch / `dist` folder.
3. URL: `https://<user>.github.io/<repo>/`

## After deploy

The Mapbox public token is in `config.json`. Mapbox public tokens (`pk.…`)
are designed to be exposed in client-side code — restrict the token by URL
on https://account.mapbox.com/access-tokens/ to your deployed domain so it
can't be lifted and reused.

## Updating the data

1. Re-run `python scripts/spatial_analysis.py` in the project root to refresh
   `data/analysis_findings.json`.
2. Re-run `python scripts/build_dist.py` to rebuild this folder.
3. Re-deploy.
"""
(DIST / "README.md").write_text(readme, encoding="utf-8")
print(f"  ✓ README.md written")

# ── 9. Final summary ─────────────────────────────────────────────────────
total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
n_files = sum(1 for _ in DIST.rglob("*") if _.is_file())
print(f"\n✓ dist/ built — {n_files} files, {total / 1024 / 1024:.1f} MB total")
print(f"  Root: {DIST}")
