"""Build a side-by-side Beirut vs. AFCN visual-comparison panel.

Two modes:
  (a) If local Beirut screenshots exist at:
          references/beirut/beirut_homepage.png   (BBED platform homepage)
          references/beirut/beirut_landing.png    (Beirut Urban Lab projects page)
      → pair them with two AFCN screenshots (Surplus map + Showcase).
  (b) Otherwise, attempt to capture Beirut via Playwright (needs internet).
  (c) Otherwise, fall back to text placeholder cards on the Beirut side.

Output: submission/4_Dashboard/screenshots/beirut_vs_afcn_comparison.png
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE     = Path(__file__).resolve().parent
OUT_DIR  = HERE / "screenshots"
REF_DIR  = HERE / "references" / "beirut"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "beirut_vs_afcn_comparison.png"

# Local reference paths — drop the Beirut screenshots here
BEIRUT_HOMEPAGE = REF_DIR / "beirut_homepage.png"   # BBED platform (dark map)
BEIRUT_LANDING  = REF_DIR / "beirut_landing.png"    # Beirut Urban Lab projects index

# AFCN local URLs
AFCN_URLS = {
    "surplus":  "http://localhost:8090/resources/Layers%20%26%20Packages/surplus-map.html",
    "showcase": "http://localhost:8090/showcase/index.html",
}
BEIRUT_URL = "https://beirut-built-environment-db.aub.edu.lb/"  # online fallback

try:
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    sys.exit(f"Missing dependency: {e.name}. Install: pip install playwright pillow")


def _capture(url: str, wait_ms: int = 4500) -> Image.Image | None:
    """Capture a single page screenshot at 960x1080 (half-width)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 1080})
        page = ctx.new_page()
        try:
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"  (could not load {url}: {e})")
            browser.close()
            return None
        page.wait_for_timeout(wait_ms)
        png_bytes = page.screenshot(full_page=False)
        browser.close()
        import io
        img = Image.open(io.BytesIO(png_bytes))
        return img.resize((960, 1080), Image.LANCZOS)


def _placeholder(label: str, sublabel: str) -> Image.Image:
    """Create a Farbton-themed placeholder card."""
    img = Image.new("RGB", (960, 1080), "#2a363c")
    d = ImageDraw.Draw(img)
    try:
        f_big = ImageFont.truetype("seguisb.ttf", 40)
        f_sm  = ImageFont.truetype("segoeui.ttf", 18)
    except OSError:
        f_big = ImageFont.load_default()
        f_sm = ImageFont.load_default()
    d.text((60, 460), label,    fill="#d2dadf", font=f_big)
    d.text((60, 520), sublabel, fill="#7d9caf", font=f_sm)
    d.line([(60, 510), (320, 510)], fill="#1c5c84", width=3)
    return img


def _load_or_placeholder(path: Path, fallback_label: str, fallback_sub: str) -> Image.Image:
    """Load a local PNG/JPG, else return a placeholder card."""
    if path.exists():
        img = Image.open(path).convert("RGB")
        return img.resize((960, 540), Image.LANCZOS)
    return _placeholder(fallback_label, fallback_sub).resize((960, 540), Image.LANCZOS)


def main() -> None:
    # Try local references first; only invoke Playwright if both are missing
    have_local = BEIRUT_HOMEPAGE.exists() or BEIRUT_LANDING.exists()

    if BEIRUT_HOMEPAGE.exists():
        print(f"+ Found {BEIRUT_HOMEPAGE.name}")
        beirut_top = Image.open(BEIRUT_HOMEPAGE).convert("RGB").resize((960, 540), Image.LANCZOS)
    else:
        print(f"  (missing: {BEIRUT_HOMEPAGE} — using placeholder)")
        beirut_top = _placeholder("Beirut Built Environment Database (BBED)",
                                  "Save the homepage screenshot to references/beirut/beirut_homepage.png").resize((960, 540), Image.LANCZOS)

    if BEIRUT_LANDING.exists():
        print(f"+ Found {BEIRUT_LANDING.name}")
        beirut_bot = Image.open(BEIRUT_LANDING).convert("RGB").resize((960, 540), Image.LANCZOS)
    else:
        print(f"  (missing: {BEIRUT_LANDING} — using placeholder)")
        beirut_bot = _placeholder("Beirut Urban Lab — projects index",
                                  "Save the landing-page screenshot to references/beirut/beirut_landing.png").resize((960, 540), Image.LANCZOS)

    # AFCN — try the running dev server for one fresh capture each
    print("Capturing AFCN counterparts (Showcase + Surplus)…")
    afcn_top = _capture(AFCN_URLS["showcase"], 3500)
    afcn_bot = _capture(AFCN_URLS["surplus"], 4500)
    if afcn_top is None:
        afcn_top = _placeholder("AFCN Showcase",  "Start dev server: python -m http.server 8090 (no-suffix OneDrive)").resize((960, 540), Image.LANCZOS)
    else:
        afcn_top = afcn_top.resize((960, 540), Image.LANCZOS)
        print("  + AFCN Showcase")
    if afcn_bot is None:
        afcn_bot = _placeholder("AFCN Real-Time Surplus Map", "Start dev server :8090").resize((960, 540), Image.LANCZOS)
    else:
        afcn_bot = afcn_bot.resize((960, 540), Image.LANCZOS)
        print("  + AFCN Surplus Map")

    # 2-row stitched panel: 1920×1200 (60 header + 2×540 + 60 row label)
    panel_h = 60 + 540 + 30 + 540 + 30
    panel = Image.new("RGB", (1920, panel_h), "#1a1f25")
    d = ImageDraw.Draw(panel)

    try:
        f_lbl  = ImageFont.truetype("seguisb.ttf", 20)
        f_sub  = ImageFont.truetype("segoeui.ttf", 13)
        f_head = ImageFont.truetype("seguisb.ttf", 28)
        f_row  = ImageFont.truetype("seguisb.ttf", 16)
    except OSError:
        f_lbl = f_sub = f_head = f_row = ImageFont.load_default()

    # Header bar
    d.rectangle([(0, 0), (1920, 60)], fill="#2a363c")
    d.text((28, 16),  "Beirut Urban Lab × AFCN — Design Lineage", fill="#d2dadf", font=f_head)
    d.line([(960, 0), (960, panel_h)], fill="#393f44", width=2)

    # Row 1: BBED dark-map platform <> AFCN Surplus map
    y1 = 60
    d.text((28, y1 + 6),   "BBED platform — dark editorial map", fill="#7d9caf", font=f_row)
    d.text((988, y1 + 6),  "AFCN — Real-Time Surplus map", fill="#7a958c", font=f_row)
    panel.paste(beirut_top, (0, y1 + 30))
    panel.paste(afcn_bot,   (960, y1 + 30))

    # Row 2: Urban Lab landing <> AFCN Showcase
    y2 = y1 + 540 + 30
    d.text((28, y2 + 6),   "Beirut Urban Lab — projects index (editorial)", fill="#7d9caf", font=f_row)
    d.text((988, y2 + 6),  "AFCN — Showcase scenes (editorial)", fill="#7a958c", font=f_row)
    panel.paste(beirut_bot, (0, y2 + 30))
    panel.paste(afcn_top,   (960, y2 + 30))

    panel.save(OUT_FILE, optimize=True)
    print(f"\n+ {OUT_FILE.name}  ({OUT_FILE.stat().st_size:,} bytes, 1920x{panel_h})")
    if not have_local:
        print()
        print("  TIP: Save the two Beirut screenshots locally for a richer comparison:")
        print(f"       1. {BEIRUT_HOMEPAGE}")
        print(f"       2. {BEIRUT_LANDING}")
        print("       Then re-run this script.")


if __name__ == "__main__":
    main()
