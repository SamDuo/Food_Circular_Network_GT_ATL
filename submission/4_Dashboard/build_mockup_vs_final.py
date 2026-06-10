"""Build a side-by-side mockup-vs-final visual comparison panel."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MOCKUPS = HERE / "mockups"
SHOTS   = HERE / "screenshots"
OUT     = SHOTS / "mockup_vs_final_panel.png"

PAIRS = [
    ("Mockup_02_dashboard_Group3.jpg", "09_campus_hub.png",
     "Mockup 02 (Group 3) — CAMPUS half",
     "GT Campus Hub (live)"),
    ("Mockup_02_dashboard_Group3.jpg", "07_surplus_map.png",
     "Mockup 02 — 'AVAILABLE NOW' claim flow",
     "Real-Time Surplus Map (live)"),
    ("Mockup_01_site_architecture.jpg", "01_atlas_matrix.png",
     "Mockup 01 — filter-by-group grid (block 4)",
     "Atlas matrix (live)"),
    ("Mockup_01_site_architecture.jpg", "05_network_radial.png",
     "Mockup 01 — projects/teams block",
     "Network radial — 802 orgs × 9 categories"),
]

ROW_H = 540
W = 1920
panel = Image.new("RGB", (W, ROW_H * len(PAIRS) + 80), "#1a1f25")
d = ImageDraw.Draw(panel)

try:
    f_lbl  = ImageFont.truetype("seguisb.ttf", 22)
    f_sub  = ImageFont.truetype("segoeui.ttf", 14)
    f_head = ImageFont.truetype("seguisb.ttf", 28)
except OSError:
    f_lbl = f_sub = f_head = ImageFont.load_default()

d.rectangle([(0, 0), (W, 70)], fill="#2a363c")
d.text((28, 16), "AFCN — Mockup vs. Final (visual deltas)", fill="#d2dadf", font=f_head)
d.text((28, 50), "Georgia Tech I2CE Lab · April 2026", fill="#7d9caf", font=f_sub)

y = 80
for mockup_file, final_file, mockup_label, final_label in PAIRS:
    # Left = mockup
    try:
        mk = Image.open(MOCKUPS / mockup_file).convert("RGB")
        # fit mockup keeping aspect, max 940×460
        mk.thumbnail((940, 460), Image.LANCZOS)
        panel.paste(mk, (15 + (940 - mk.size[0]) // 2, y + 60 + (460 - mk.size[1]) // 2))
    except FileNotFoundError:
        pass

    # Right = final
    try:
        fn = Image.open(SHOTS / final_file).convert("RGB")
        fn.thumbnail((940, 460), Image.LANCZOS)
        panel.paste(fn, (965 + (940 - fn.size[0]) // 2, y + 60 + (460 - fn.size[1]) // 2))
    except FileNotFoundError:
        pass

    # Labels
    d.line([(0, y), (W, y)], fill="#393f44", width=1)
    d.text((20,  y + 20), mockup_label, fill="#7d9caf", font=f_lbl)
    d.text((970, y + 20), final_label,  fill="#7a958c", font=f_lbl)
    d.line([(960, y), (960, y + ROW_H)], fill="#393f44", width=1)
    y += ROW_H

panel.save(OUT, optimize=True)
print(f"+ {OUT.name} ({OUT.stat().st_size:,} bytes, {W}x{panel.size[1]})")
