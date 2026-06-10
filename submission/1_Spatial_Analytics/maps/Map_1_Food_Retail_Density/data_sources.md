# Map 1 — Food Retail Density (mRFEI)

## Sources
| Layer | File | Source | Date | License |
|---|---|---|---|---|
| Retail food env. index | `geojson/map1_food_retail_mrfei.geojson` | CDC mRFEI (Modified Retail Food Environment Index) | 2023 | Public domain |
| Classified grocery | `geojson/atl_grocery_stores_classified.geojson` | Workshop classification (Tier 1/2/3) | April 2026 | I2CE Lab |
| Convenience stores | `geojson/convenience_stores_atl.geojson` | USDA SNAP retailer roster | 2024 | Public |
| Fast food | `geojson/pkg_atlanta_fast_food_restaurants.geojson` | OpenStreetMap | March 2026 | ODbL |
| Tract boundaries | `geojson/census_tracts_tiger.geojson` | US Census TIGER/Line | 2022 | Public |

## Methodology
mRFEI = (healthy retailers) / (healthy + less-healthy retailers) × 100
- **Healthy** = supermarkets + farmers markets + grocery (Tier 1/2)
- **Less-healthy** = fast food + convenience + Tier 3 grocery
- Computed per Census tract; tracts with <3 total retailers reported as "low confidence"

## Caveats
- mRFEI does not weight by store size, hours, or product mix
- A 5,000 sqft supermarket counts equally with a 50,000 sqft Kroger
- Farmers markets are seasonally biased; not all are open year-round
