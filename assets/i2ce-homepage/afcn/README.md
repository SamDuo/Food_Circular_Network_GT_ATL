# AFCN — Real Time Surplus Map

## What the images show

| File | Dimensions | Content |
|---|---|---|
| `hero.png` | 1600x900 | Full Atlanta map view of the AFCN real time surplus dashboard, with 30 surplus pins (urgency tiered: Critical / Soon / Stable), the AI Suggested Route in the Logistics Optimizer side panel, and the 4 stop route chain across GT campus. |
| `card.png` | 800x600 | Same dashboard, zoomed to GT campus where the 6 Critical pins cluster. |
| `thumb.png` | 240x150 | Downscaled card showing the GT campus pin cluster. |

## Source

Live dashboard at `resources/Layers & Packages/surplus-map.html` served via `Python Script/serve.py` on `localhost:8080`. Captured with Playwright headless Chromium at native viewport size.

## Data date

LeanPath waste audit, GT campus, **March 4 to 10, 2026**. 408 entries totaling 2,316 lbs, 30 grouped rescuable surplus pins shown on the map.

## Repo

`github.com/SamDuo/Food_Circular_Network_GT_ATL`

## 1 sentence caption

A real time spatial intelligence dashboard mapping surplus food across the GT campus with urgency aware route optimization.
