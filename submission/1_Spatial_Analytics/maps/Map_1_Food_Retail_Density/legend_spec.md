# Map 1 — Legend Specification

## Title
**Food Retail Density (mRFEI)** — City of Atlanta, 2023
Source: CDC mRFEI · classified by I2CE Lab April 2026

## Classification — 5-class quantile
| Class | mRFEI range | Color (hex) | Farbton # | Description |
|---|---|---|---|---|
| 1 (lowest) | 0–10 | `#d2dadf` | Nr. 55 — lichtgrau | Healthy-food desert |
| 2 | 10–20 | `#a4b1bc` | Nr. 54 | Limited healthy |
| 3 | 20–35 | `#7d9caf` | Nr. 57 — lichtblau | Mixed |
| 4 | 35–50 | `#1c5c84` | Nr. 51 — spinellblau | Healthy-leaning |
| 5 (highest) | 50+ | `#3a4f5e` | Nr. 50 — dunkelblau | Healthy-dominant |
| no data | <3 retailers | `#5b7282` 30% | Nr. 52 | Low confidence |

## Symbology layers (draw order, bottom to top)
1. Census tracts polygon — Nr. 55 fill, Nr. 54 0.4px outline
2. mRFEI choropleth — 5-class quantile fill, no outline
3. MARTA rail lines — official MARTA colors, 1.5px (context only)
4. Tract centroids labeled with mRFEI value when zoomed in

## Auxiliary elements
- **North arrow:** simple chevron, top-right
- **Scale bar:** 0 — 1 — 2 miles
- **Inset:** 5-county metro context box, bottom-left
- **Source line:** "CDC mRFEI 2023 · USDA SNAP retailers · OSM. I2CE Lab April 2026."
