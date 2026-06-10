# Map 2 — Food Access Distance

## Sources
| Layer | File | Source | Date | License |
|---|---|---|---|---|
| Grocery (Tier 1+2) | `geojson/atl_grocery_stores_classified.geojson` | Workshop classification | April 2026 | I2CE Lab |
| Healthy food 1mi coverage | `geojson/healthy_food_1mile_coverage.geojson` | Computed network buffer (pgRouting) | March 2026 | Derived |
| Grocery access distance | `geojson/grocery_access_distance.geojson` | Per-tract nearest-grocery distance | March 2026 | Derived |
| USDA Food Deserts | `geojson/food_deserts_atlanta.geojson` | USDA Food Access Research Atlas 2019 | 2019 | Public |
| Tract boundaries | `geojson/census_tracts_tiger.geojson` | US Census TIGER/Line | 2022 | Public |

## Methodology
- Network distance from tract centroid to nearest healthy-food retailer (Tier 1 supermarket or Tier 2 grocery)
- 1.0 mile and 0.5 mile threshold buffers (USDA LILA convention)
- USDA Food Desert overlay shown as comparative reference (low income + low access tracts)

## Caveats
- Network distance ≠ travel time (no transit, no traffic, no barriers like highways)
- Tract centroid assumption flattens within-tract variation
- USDA 2019 vintage is stale; commercial closures since (e.g. Save-A-Lot West End) not reflected
