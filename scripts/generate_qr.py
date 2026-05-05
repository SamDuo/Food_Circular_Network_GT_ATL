"""
Generate a QR code (PNG + SVG) pointing at the deployed Atlanta Food Story.

USAGE
─────
    python scripts/generate_qr.py https://atl-food-story.pages.dev

Outputs (next to this script's parent project root):
    dist/qr-code.png        300×300 PNG, suitable for slides / handouts
    dist/qr-code.svg        vector — scales cleanly for poster prints
    dist/qr-code-card.html  a printable card (A6) with QR + title + URL

Falls back to the goqr.me public API if the local `qrcode` package is not
installed.  No `pip install` step is strictly required, but `pip install
qrcode[pil]` produces nicer output.
"""

import io, os, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "dist"
OUT.mkdir(exist_ok=True)


def build_with_local(url: str) -> bool:
    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage
    except ImportError:
        return False

    # PNG, generous quiet zone
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#111418", back_color="#fbfaf6")
    img.save(OUT / "qr-code.png")
    print(f"  ✓ {OUT / 'qr-code.png'}")

    # SVG (vector)
    svg_img = qrcode.make(url, image_factory=SvgPathImage)
    svg_img.save(OUT / "qr-code.svg")
    print(f"  ✓ {OUT / 'qr-code.svg'}")
    return True


def build_with_remote(url: str) -> None:
    """Fallback: ask goqr.me to render the PNG so we don't need `pip install`."""
    api = ("https://api.qrserver.com/v1/create-qr-code/?"
           "size=600x600&margin=24&color=111418&bgcolor=fbfaf6&data="
           + urllib.parse.quote(url, safe=""))
    print(f"  · fetching {api}")
    with urllib.request.urlopen(api, timeout=15) as r:
        data = r.read()
    (OUT / "qr-code.png").write_bytes(data)
    print(f"  ✓ {OUT / 'qr-code.png'}  (via goqr.me)")


def write_card(url: str) -> None:
    """A standalone HTML card you can print / screenshot at A6 size."""
    short = url.replace("https://", "").replace("http://", "").rstrip("/")
    card = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Scan to read · Atlanta Food Story</title>
<style>
  @page {{ size: A6 portrait; margin: 0; }}
  html, body {{ margin: 0; padding: 0; background: #fbfaf6; font-family: 'Inter', system-ui, sans-serif; color: #111418; }}
  .card {{
    width: 105mm; height: 148mm; padding: 12mm 10mm;
    display: flex; flex-direction: column; align-items: center; justify-content: space-between;
    box-sizing: border-box;
    background: #fbfaf6;
  }}
  .kicker {{ font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #b3603a; font-weight: 700; }}
  h1 {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 900; font-size: 22px; line-height: 1.1; margin: 8px 0 0; max-width: 80mm; text-align: center; }}
  .dek {{ font-size: 11px; color: #555a63; max-width: 80mm; text-align: center; margin-top: 6px; line-height: 1.4; }}
  .qr {{ width: 70mm; height: 70mm; margin: 6mm 0; }}
  .qr img {{ width: 100%; height: 100%; }}
  .url {{ font-family: ui-monospace, "SF Mono", Monaco, monospace; font-size: 11px; color: #111418;
          background: #f3ddd0; padding: 5px 10px; border-radius: 4px; word-break: break-all; text-align: center; }}
  footer {{ font-size: 9px; color: #555a63; margin-top: 4mm; text-align: center; }}
</style>
</head><body>
  <div class="card">
    <div>
      <div class="kicker">Scan to read</div>
      <h1>The Atlanta Food Story</h1>
      <div class="dek">A scrollable map of access, gaps, and the network filling them. 5 chapters, 530 census tracts, 1.8M people.</div>
    </div>
    <div class="qr"><img src="qr-code.png" alt="QR code"></div>
    <div>
      <div class="url">{short}</div>
      <footer>Georgia Tech · I2CE Lab · Atlanta Food Circular Network</footer>
    </div>
  </div>
</body></html>
"""
    (OUT / "qr-code-card.html").write_text(card, encoding="utf-8")
    print(f"  ✓ {OUT / 'qr-code-card.html'}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_qr.py https://your-deployed-url")
        sys.exit(2)
    url = sys.argv[1].strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    print(f"→ generating QR for: {url}")
    if not build_with_local(url):
        print("  · qrcode package not installed; falling back to remote API")
        build_with_remote(url)
    write_card(url)
    print("\nDone. To preview the printable card, open:")
    print(f"  file:///{OUT / 'qr-code-card.html'}".replace("\\", "/"))


if __name__ == "__main__":
    main()
