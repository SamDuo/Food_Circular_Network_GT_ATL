"""Extract embedded board photos from the workshop Excel into photos/board_photos/."""
import sys, zipfile, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

XLSX = Path(__file__).resolve().parents[2] / "workshop" / "outputs" / "Workshop_Deliverables_April15" / "Food_Network_Framework_and_Gaps.xlsx"
OUT  = Path(__file__).resolve().parent / "photos" / "board_photos"
OUT.mkdir(parents=True, exist_ok=True)

# .xlsx is a zip; embedded media lives in xl/media/
with zipfile.ZipFile(XLSX) as zf:
    media = [n for n in zf.namelist() if n.startswith("xl/media/")]
    print(f"Found {len(media)} embedded media files")
    for src in sorted(media):
        target = OUT / Path(src).name
        with zf.open(src) as fp:
            target.write_bytes(fp.read())
        print(f"  + {target.name}")

print(f"\nDone. {len(media)} images in {OUT}")
