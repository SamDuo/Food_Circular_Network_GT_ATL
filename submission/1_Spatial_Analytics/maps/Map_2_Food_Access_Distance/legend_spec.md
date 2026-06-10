# Map 2 — Legend Specification

## Title
**Food Access Distance** — Network distance to nearest healthy retailer
Source: I2CE Lab tract-level network analysis · April 2026

## Classification — diverging access gap
| Class | Distance to nearest healthy retailer | Color (hex) | Description |
|---|---|---|---|
| Within 0.5 mi | ≤0.5 mi network | `#3a4f5e` (Nr. 50) | High access |
| 0.5–1.0 mi | 0.5–1.0 mi | `#1c5c84` (Nr. 51) | Adequate |
| 1.0–1.5 mi | 1.0–1.5 mi | `#7d9caf` (Nr. 57) | Marginal |
| 1.5–2.5 mi | 1.5–2.5 mi | `#a4b1bc` (Nr. 54) | Low access |
| >2.5 mi | >2.5 mi network | `#c62828` (alert red) | Food desert risk |

## Symbology layers (draw order, bottom to top)
1. Census tracts — classified by distance class
2. USDA Food Desert overlay — hatch pattern, 25% opacity (comparative reference)
3. Healthy-food 1-mile buffer — translucent fill, Nr. 57 with 18% opacity
4. Grocery stores (Tier 1+2) — Nr. 51 solid dots with white halo (size 9, outline 1.2px)
5. Major roads — Nr. 54 1px (context)

## Auxiliary elements
- **Inset:** GT campus close-up showing 5-min walk circles from dining halls
- **Annotation:** Call out West End / English Avenue food desert zones with leader line
- **Source line:** "Network distance via pgRouting + OSM. USDA 2019 overlay. I2CE Lab April 2026."
