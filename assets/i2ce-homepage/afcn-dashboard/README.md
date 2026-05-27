# AFCN — Citywide Dashboard

## What the images show

| File | Dimensions | Content |
|---|---|---|
| `hero.png` | 1600x900 | The AFCN citywide dashboard in Atlanta mode, with food recovery sources, redistribution nodes, beneficiary access points, and circular economy infrastructure layers visible. Stats rail at the bottom shows live feature counts. |
| `card.png` | 800x600 | Same dashboard at card scale. |
| `thumb.png` | 240x150 | Downscaled card. |

## Source

Live dashboard at `resources/Layers & Packages/index.html` served via `Python Script/serve.py` on `localhost:8080`. Captured with Playwright headless Chromium at native viewport size.

## Data date

Composite layer set as of **March 2026**. Census tracts from 2022 TIGER, MARTA GTFS 2025, Atlanta Community Food Bank pantry network, USDA, CDC PLACES, OSM March 2026 snapshot.

## Repo

`github.com/SamDuo/Food_Circular_Network_GT_ATL`

## 1 sentence caption

A citywide platform mapping 11,314 food recovery sources, 2,629 redistribution nodes, and the circular economy infrastructure of metro Atlanta.
