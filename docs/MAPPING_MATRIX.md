# Urban Design Spatial Analysis Matrix — AFCN Coverage

> Companion document to `Mapping Types Status May 4, 2026.xlsx` (supervisor brief).
> Maps the 7-row × 6-column analytical framework onto the AFCN repo's existing
> 67 GeoJSON layers and identifies the data still needed to complete the matrix.

## The framework (from supervisor's brief)

Every map in the matrix is one **subsystem (row)** rendered through one
**analytical lens (column)**:

| Subsystem | Base Distribution | Density | Accessibility | Equity | Trend | Flow |
|---|---|---|---|---|---|---|
| Demographics | Population dist. | Pop. density | Service access | Income/race disparity | Growth/decline | Migration |
| Food System | All food locations | Food density | Distance to food | Food deserts | Supply change | Supply chains |
| Transportation | Full network | Network density | Multimodal access | Mobility inequality | Infra growth | Movement |
| Infrastructure | Utility maps | Load/usage density | Service access | Environmental justice | Demand trend | Distribution |
| Health | Facilities | Disease density | Healthcare access | Health disparity | Health trend | Patient flow |
| Land Use | Built form | Density | Walk access | Spatial equity | Conversion | Movement |
| Social Systems | Schools / churches / broadband | Coverage density | Service access | Opportunity gap | Enrollment trend | Student/data flow |

Each subsystem also has fine-grained sub-layers — Demographics breaks into
6 (income, race, age, edu, household size, gender); Food breaks into 9
(farms, fisheries, pantries, grocery, fast food, restaurants, distribution,
processors, startups); etc. The full taxonomy is in the spreadsheet's
"General Maps" sheet.

The synthesis output (last sheet section) is **5 Atlanta typologies**:

| Typology | Where | Defining intersections |
|---|---|---|
| **High-growth Core** | Midtown / BeltLine | Dense + wealthy + transit-served |
| **Affluent Suburban** | North Atlanta | Car-based + high income |
| **Disinvested Urban** | South / West Atlanta | Low access + high vulnerability |
| **Industrial Logistics** | Near Hartsfield-Jackson | Freight + distribution |
| **Emerging Mixed-use** | BeltLine edges | Gentrifying transition |

## Coverage scorecard

Score = % of the row that has a usable layer in `geojson/`.

| Row (subsystem) | Score | Layers in repo | Gaps |
|---|---:|---|---|
| **Demographics** | 30% | `census_tracts_tiger`, `census_vehicle_availability_ga` | Need ACS variables (income, race, age, edu, household size, gender) joined to tracts |
| **Food — Sources** | 95% | grocery (×2), fast food (×3), restaurants (×2), pantries (×3), farms / gardens, farmers markets, processing, recovery, redistribution, convenience, food_deserts (×2), MRFEI, retail density | Fisheries (N/A inland), food startups as own layer |
| **Transportation** | 70% | MARTA rail + bus + stops, freeways, street centerlines, sidewalks, ports, transit_routes | Bike infra, airport polygons, traffic volumes |
| **Infrastructure** | 20% | recycling_trash_cans, trash_recycling_indoor, compost_locations | Electricity, water, gas, sewer, landfills |
| **Health** | 40% | atl_pro_health_risk_score, atl_pro_hospitals, pkg_hospitals_clinics, places_food_insecurity | Obesity / diabetes / depression prevalence by tract (CDC PLACES) |
| **Land Use** | 25% | buildings, campus_boundary, southfulton_city_limits | Zoning, parks, parcels + ownership, tree canopy |
| **Social Systems** | 50% | atl_pro_public_schools, pkg_religious_institutions, afcn_directory | Colleges/universities, broadband coverage |
| **Typologies** | 0% | — | Derived synthesis layer (capstone) |

Existing **derived analytical layers** (Equity / Accessibility lenses already
implemented): `atl_pro_food_deserts`, `atl_pro_health_risk_score`,
`map1_food_retail_density`, `map1_food_retail_mrfei`,
`map2_food_access_distance`, `map3_transport_accessibility`,
`map4_food_assistance_demand`.

## Atlanta-specific data sources (downloadable)

Each is a one-shot fetch suitable for a `scripts/fetch_*.py` script (using
the same pattern as `scripts/fetch_south_fulton.py`).

| Layer | Source | Endpoint |
|---|---|---|
| ACS demographics | US Census API | `https://api.census.gov/data/2022/acs/acs5?get=B19013_001E,B02001_002E,...&for=tract:*&in=state:13+county:121,089,063,067,135,151,247` |
| CDC PLACES (obesity/diabetes/MH) | CDC Open Data | `https://chronicdata.cdc.gov/resource/cwsq-ngmh.geojson?$where=stateabbr='GA'` |
| Atlanta Zoning | City of Atlanta GIS | `https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/Zoning/FeatureServer/0/query?where=1=1&outFields=*&f=geojson` |
| Atlanta Parks | City of Atlanta GIS | `https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/Parks/FeatureServer/0/query?...&f=geojson` |
| Tree canopy | NLCD 2021 USFS | https://www.mrlc.gov/data/nlcd-2021-usfs-tree-canopy-cover-conus |
| Bike infrastructure | Atlanta GIS / OSM Overpass | `cycleway=*` Overpass query |
| BeltLine alignment | ArcGIS Hub | search "BeltLine" on hub.arcgis.com |
| Hartsfield-Jackson airport | OSM | Overpass `aeroway=aerodrome` |
| Parcels + ownership | County GIS portals | Fulton / DeKalb / Cobb / Gwinnett — separate fetch per county |
| Electric transmission | HIFLD Open | https://hifld-geoplatform.opendata.arcgis.com/datasets/electric-power-transmission-lines |
| Gas pipelines (transmission) | HIFLD Open | https://hifld-geoplatform.opendata.arcgis.com/datasets/natural-gas-pipelines |
| Waste / landfills | EPA Envirofacts / GA EPD | https://enviro.epa.gov/envirofacts/services/rcra |
| Colleges/universities | NCES IPEDS / OSM | `amenity=university` Overpass |
| Broadband coverage | FCC National Broadband Map | https://broadbandmap.fcc.gov/data-download/nationwide-data |
| Traffic volumes | GDOT 511 | https://www.dot.ga.gov/DriveSmart/Pages/Traffic.aspx |

## Recommended build order

| Phase | Effort | What it unlocks |
|---|---|---|
| **1. ACS join** to `census_tracts_tiger` | ~2 h | Activates 36 cells (6 demographic sub-rows × 6 matrix columns) in one fetch |
| **2. CDC PLACES join** | ~1 h | Activates the entire Health row at tract granularity |
| **3. Zoning + Parks + Tree canopy** | ~3 h | Unlocks the Land Use row |
| **4. Bike + airport + traffic** | ~2 h | Closes Transportation gaps |
| **5. Broadband + colleges** | ~1 h | Closes Social Systems |
| **6. Typology synthesis** ← *capstone* | ~4 h | Classifies each tract into one of the 5 supervisor-named typologies. Output: `geojson/atl_typology_classified.geojson` |

The capstone (Phase 6) is the headline deliverable — it's the synthesis the
spreadsheet's last section explicitly asks for.

## Map-View dashboard reflection

Once Phases 1–5 land, the Map View dashboard (`resources/Layers & Packages/index.html`)
should expose them as toggleable layer groups matching the matrix rows:

```
Demographics ▾   Food ▾   Transportation ▾   Infrastructure ▾
Health ▾         Land Use ▾   Social Systems ▾   Typologies ▾
```

Within each group, the 6 analytical lenses (Base / Density / Accessibility /
Equity / Trend / Flow) become individual layer toggles. The current dashboard
already groups food layers; this just generalizes the pattern to all 7 systems.
