"""Rename extracted board photos to <Org_##>_<short>.png by matching the workshop
Excel's per-org tabs to image indices. Falls back to leaving generic names if a
specific mapping cannot be inferred (which is fine — they're still archived).
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# Best-guess mapping based on the embed order seen in the workbook (per-org
# *_Photo tabs are in this order):
ORG_ORDER = [
    ("01", "ACFB",            "Atlanta Community Food Bank"),
    ("02", "Braves",          "Atlanta Braves Foundation"),
    ("03", "CityATL",         "City of Atlanta / Welcoming Atlanta"),
    ("04", "CommFdn",         "Community Foundation for Greater Atlanta"),
    ("05", "ConcreteJungle",  "Concrete Jungle"),
    ("06", "Goodr",           "Goodr"),
    ("07", "GrocerySpot",     "Grocery Spot"),
    ("08", "MetroConsort",    "Metro Atlanta Food Consortium"),
    ("09", "NFCC",            "North Fulton Community Charities"),
    ("10", "NourishBloom",    "Nourish + Bloom"),
    ("11", "OpenHand",        "Open Hand Atlanta"),
    ("12", "Retazza",         "Retazza"),
    ("13", "SecondHelpings",  "Second Helpings Atlanta"),
    ("14", "Umi",             "Umi Feeds"),
]

BASE = Path(__file__).resolve().parent / "photos" / "board_photos"
mapping = []
for idx, (n, short, full) in enumerate(ORG_ORDER, start=1):
    src = BASE / f"image{idx}.png"
    if not src.exists():
        # try alternate suffix
        alt = BASE / f"image{idx}.jpg"
        src = alt if alt.exists() else src
    if not src.exists():
        print(f"  (no source for #{n} {short})")
        continue
    dst = BASE / f"Org_{n}_{short}.png"
    if dst.exists():
        dst.unlink()
    src.rename(dst)
    mapping.append((n, short, full, dst.name))
    print(f"  Org {n} ({full}) -> {dst.name}")

print(f"\nRenamed {len(mapping)} board photos")
