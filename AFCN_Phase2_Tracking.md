# AFCN Phase 2 — 8-Map Framework Expansion & Food System Vulnerability Map

**Project:** Atlanta Food Circular Network Map (AFCN)
**Phase:** 2 — Spatial Analysis Framework Expansion
**Status:** In Progress
**Last Updated:** 2026-03-15
**Preceding:** Phase 1 (Data Collection — 4 subagent categories)
**Reference:** `Food_System_Framework_Analysis.md` (framework matrix + methodology)

---

## Phase 2 Overview

Phase 1 built the AFCN's core data layers (food recovery sources, redistribution nodes, beneficiary access points, circular economy). Phase 2 expands the platform from a **single-purpose food recovery map** into the full **8-Map Spatial Analysis Framework** used in university food system studies, culminating in a **Food System Vulnerability Map** (composite risk index).

### Phase 2 Objectives

| # | Objective | Output |
|:-:|-----------|--------|
| 1 | Convert priority ArcGIS Online layers to GeoJSON | 10 new GeoJSON files in `geojson/` |
| 2 | Fetch supplementary data from Census ACS + CDC PLACES APIs | Python scripts + additional GeoJSON data |
| 3 | Compute Food Insecurity Risk Score per census tract | `food_insecurity_risk_index.geojson` |
| 4 | Integrate all 8 framework maps into AFCN dashboard | Updated `index.html` with new layer groups |
| 5 | Build standalone Vulnerability Map page | New `vulnerability-map.html` |

---

## Work Package Structure

### WP-1: Layer Conversion (ArcGIS Online → GeoJSON)
### WP-2: API Data Acquisition (Census ACS + CDC PLACES)
### WP-3: Risk Score Computation
### WP-4: Dashboard Integration (index.html)
### WP-5: Standalone Vulnerability Map

---

---

## WP-1: Layer Conversion (ArcGIS Online → GeoJSON)

**Owner:** Team members (manual ArcGIS Online export)
**Method:** ArcGIS Online → Export Data → GeoJSON → place in `geojson/` folder
**Status:** Not Started

### Conversion Queue (10 Priority Layers)

| # | ArcGIS Online Title | Owner | Framework Map | Risk Score? | Target GeoJSON Filename | Status |
|:-:|-------|-------|:---:|:-----------:|-------------------------|:------:|
| 1 | Poverty 2021 (all geographies, statewide) - GA | Miranda Gillaspy | M6, M8 | Indicator #1 | `census_poverty_ga.geojson` | Not Started |
| 2 | Georgia Median Household Income | Judie Chekfeh | M6, M8 | Income overlay | `census_income_ga.geojson` | Not Started |
| 3 | Vehicle Availability 2022 (all geographies, statewide) | Swathi Kovvur | M3, M8 | Indicator #4 | `census_vehicle_availability_ga.geojson` | Not Started |
| 4 | MARTA Routes - ATL | Miranda Gillaspy | M3 | Context | `marta_routes_atl.geojson` | Not Started |
| 5 | MARTA Stops - ATL | Miranda Gillaspy | M3 | Context | `marta_stops_atl.geojson` | Not Started |
| 6 | County_Health_Rankings_(2020) - GA | Miranda Gillaspy | M7, M8 | Indicator #7 | `county_health_rankings_ga.geojson` | Not Started |
| 7 | Midtown Convenience Stores | Miranda Gillaspy | M1 | Context | `midtown_convenience_stores.geojson` | Not Started |
| 8 | 10 Min Walk Access to Grocery Stores 2024 | Ashley Wilson | M2 | Alt #2 | `walk_access_grocery_2024.geojson` | Not Started |
| 9 | Population Density - Atlanta | Luca Maalouli | M6 | Denominator | `population_density_atl.geojson` | Not Started |
| 10 | 10 Min Walk Food Pantries Atlanta | Samuel Panatera | M4 | Context | `walk_access_pantries_atl.geojson` | Not Started |

### Export Instructions (for team members)

```
1. Log into ArcGIS Online → My Content
2. Find the layer package (.lpkx)
3. Click "..." menu → "Export Data" → "Export to GeoJSON"
4. Download the GeoJSON file
5. Rename to the target filename above
6. Place in: GT campus Dataset/geojson/
7. Mark Status as "Complete" in this table
```

### Data Quality Checklist (per converted layer)

- [ ] File opens in a text editor / QGIS without errors
- [ ] Features have geometry (Point, LineString, or Polygon)
- [ ] Properties contain expected fields (names, values, IDs)
- [ ] Coordinates are in WGS84 (longitude, latitude)
- [ ] Feature count is reasonable (not empty, not 1M+ records)
- [ ] Atlanta / Georgia extent (not national or global)

---

---

## WP-2: API Data Acquisition

**Owner:** Developer (Python scripts)
**Method:** Automated API queries → join to tract polygons → GeoJSON output
**Status:** Not Started

### 2A: Census ACS Data

**API:** `api.census.gov/data/2022/acs/acs5`
**Geography:** Tract level, Fulton County (FIPS 13121) + DeKalb County (FIPS 13089)

| Variable | ACS Table | Field | Use in Risk Score |
|----------|-----------|-------|:-----------------:|
| SNAP Participation Rate | S2201 | `S2201_C03_001E` | Indicator #5 |
| Unemployment Rate | S2301 | `S2301_C04_001E` | Indicator #3 (if WP-1 #3 insufficient) |
| % No Vehicle | B08141 | `B08141_C01_002E` / `B08141_C01_001E` | Indicator #4 (supplement) |
| Poverty Rate | S1701 | `S1701_C03_001E` | Indicator #1 (if WP-1 #1 insufficient) |
| Median Household Income | B19013 | `B19013_001E` | Income overlay |
| Education (No HS Diploma) | S1501 | `S1501_C01_009E` | Vulnerability context |

**Script:** `scripts/fetch_census_acs.py`

**Requirements:**
- Census API key (free: https://api.census.gov/data/key_signup.html)
- Python `requests` library
- Join output to `food_deserts_atlanta.geojson` tract polygons by `census_tract_id`

**Output:** `geojson/census_acs_indicators.geojson` — tract polygons with ACS indicators as properties

### 2B: CDC PLACES Health Data

**API:** ArcGIS REST endpoint (same pattern already used in `index.html` line 508)
**Existing query format:**
```
https://services3.arcgis.com/ZvidGQkLaDJxRSJ2/arcgis/rest/services/
PLACES_LocalData_for_BetterHealth/FeatureServer/3/query?
where=StateAbbr='GA' AND (CountyName='Fulton' OR CountyName='DeKalb')
&f=geojson
&outFields={FIELDS}
&resultRecordCount=3000
```

| Health Measure | Field Name | Currently Queried? |
|---------------|------------|:------------------:|
| Food Insecurity | `FOODINSECU_CrudePrev` | YES (in index.html) |
| Obesity | `OBESITY_CrudePrev` | NO — add to query |
| Diabetes | `DIABETES_CrudePrev` | NO — add to query |
| Coronary Heart Disease | `CHD_CrudePrev` | NO — add to query |
| Physical Inactivity | `LPA_CrudePrev` | NO — optional |

**Script:** `scripts/fetch_cdc_places.py`

**Output:** `geojson/cdc_health_indicators.geojson` — tract-level health prevalence data

### 2C: Fast Food Density per Tract (Spatial Join)

**Method:** Count fast food locations per census tract, divide by population
**Input layers:**
- `geojson/pkg_all_fast_food_locations_in_metro_atlanta.geojson` (point locations)
- `geojson/food_deserts_atlanta.geojson` (tract polygons with population)

**Script:** `scripts/compute_fast_food_density.py`
**Output:** Adds `fast_food_count` and `fast_food_per_1000` to tract properties

---

---

## WP-3: Risk Score Computation

**Owner:** Developer (Python script)
**Status:** Not Started
**Depends on:** WP-1 (converted layers) + WP-2 (API data)

### Risk Score Formula

```
Risk_Score = w1*(Poverty) + w2*(GroceryDist) + w3*(Unemployment)
           + w4*(TransportBarrier) + w5*(FoodAssistUsage)
           + w6*(FastFoodDensity) + w7*(HealthDisparity)
```

### 7 Indicators — Data Source Mapping

| # | Indicator | Primary Source (WP-1) | Fallback Source (WP-2) | Field Name |
|:-:|-----------|----------------------|----------------------|------------|
| 1 | Poverty Rate | `census_poverty_ga.geojson` | Census ACS S1701 | `poverty_rate` |
| 2 | Grocery Distance | `food_deserts_atlanta.geojson` (existing) | — | `lila_score` (sum of LILA flags) |
| 3 | Unemployment | `census_labor_force.geojson` | Census ACS S2301 | `unemployment_rate` |
| 4 | Transport Barrier | `census_vehicle_availability_ga.geojson` | Census ACS B08141 | `pct_no_vehicle` |
| 5 | Food Assist Usage | Census ACS S2201 | — | `snap_participation_rate` |
| 6 | Fast Food Density | Spatial join (WP-2C) | — | `fast_food_per_1000` |
| 7 | Health Disparity | `county_health_rankings_ga.geojson` | CDC PLACES API | `avg_obesity_diabetes` |

### Computation Pipeline

```
Step 1: Load base geometry
        → food_deserts_atlanta.geojson (tract polygons)

Step 2: Join indicator data
        → Merge by census_tract_id / TractFIPS

Step 3: Normalize each indicator (Min-Max → 0 to 1)
        → normalized_i = (value - min) / (max - min)

Step 4: Compute composite score (equal weight sum)
        → risk_score = sum(normalized_i * w_i)

Step 5: Classify into quintiles
        → Very Low (0-20%) / Low (20-40%) / Moderate (40-60%)
           / High (60-80%) / Very High (80-100%)

Step 6: Write output
        → geojson/food_insecurity_risk_index.geojson
```

### Output GeoJSON Schema

```json
{
  "type": "Feature",
  "geometry": { "type": "MultiPolygon", "coordinates": [...] },
  "properties": {
    "census_tract_id": "13121001100",
    "tract_name": "11.00",
    "population": 4520,

    "poverty_rate": 0.32,
    "poverty_norm": 0.78,

    "lila_score": 2,
    "grocery_dist_norm": 0.67,

    "unemployment_rate": 0.09,
    "unemployment_norm": 0.55,

    "pct_no_vehicle": 0.18,
    "transport_norm": 0.62,

    "snap_participation_rate": 0.24,
    "food_assist_norm": 0.71,

    "fast_food_per_1000": 2.3,
    "fast_food_norm": 0.45,

    "avg_obesity_diabetes": 38.5,
    "health_norm": 0.83,

    "risk_score": 0.659,
    "risk_quintile": "High",
    "risk_rank": 78
  }
}
```

### Script

**File:** `scripts/compute_risk_score.py`

**Usage:**
```bash
python scripts/compute_risk_score.py
# Reads from geojson/ folder
# Outputs: geojson/food_insecurity_risk_index.geojson
```

### Validation Criteria

| Check | Expected Result |
|-------|----------------|
| Very High risk tracts overlap USDA food deserts | > 70% overlap |
| Known food-insecure areas rank High/Very High | South Fulton, Bankhead, Vine City, English Ave, Pittsburgh |
| Known affluent areas rank Low/Very Low | Buckhead, Midtown North, Druid Hills |
| Score range | 0.0 to 1.0 (continuous) |
| Quintile distribution | ~80 tracts per quintile (equal count) |
| Total tracts scored | ~400 (Fulton + DeKalb) |

---

---

## WP-4: Dashboard Integration

**Owner:** Developer
**File to modify:** `resources/Layers & Packages/index.html`
**Status:** Not Started
**Depends on:** WP-1 (converted layers) + WP-3 (risk index)

### 4A: Add Existing GeoJSON Layers (Quick Wins)

These layers are already converted to GeoJSON but not loaded in the dashboard:

| Layer | GeoJSON File | Layer Group | Renderer |
|-------|-------------|-------------|----------|
| Grocery Stores | `pkg_atlanta_grocery_stores.geojson` | Food Retail (M1) | Circle, green |
| Supermarkets | `pkg_supermarkets_metroatl.geojson` | Food Retail (M1) | Circle, dark green |
| Fast Food | `pkg_all_fast_food_locations_in_metro_atlanta.geojson` | Food Retail (M1) | Circle, red |
| Farmers Markets | `pkg_atlanta_metro_area_farmers_markets.geojson` | Food Retail (M1) | Circle, orange |
| Hospitals | `pkg_hospitals_and_health_clinics_atlanta.geojson` | Health (M7) | Circle, blue |
| Religious Institutions | `pkg_religious_institutions_metro_atlanta.geojson` | Assistance (M4) | Circle, purple |
| Gardens/Farms | `pkg_gardens_farms_and_orchards_atlanta.geojson` | Recovery (M5) | Circle, green |

**Implementation:** Add to `LAYER_CFG` object + checkboxes in `#layerPanel`.

### 4B: Add Converted Layers (After WP-1)

| Layer | GeoJSON File | Layer Group | Renderer |
|-------|-------------|-------------|----------|
| MARTA Routes | `marta_routes_atl.geojson` | Transportation (M3) | Line, blue |
| MARTA Stops | `marta_stops_atl.geojson` | Transportation (M3) | Circle, blue |
| Income | `census_income_ga.geojson` | Vulnerability (M6) | Choropleth, green ramp |
| Poverty | `census_poverty_ga.geojson` | Vulnerability (M6) | Choropleth, red ramp |
| Walk Access | `walk_access_grocery_2024.geojson` | Food Access (M2) | Choropleth, teal |

### 4C: Add Risk Index Layer

| Layer | GeoJSON File | Layer Group | Renderer |
|-------|-------------|-------------|----------|
| Food Insecurity Risk Index | `food_insecurity_risk_index.geojson` | Vulnerability (M8) | Choropleth, 5-color quintile |

**New layer panel structure:**
```
Layers
├── [existing] Food Recovery Sources      ✓
├── [existing] Redistribution Nodes       ✓
├── [existing] Beneficiary Access         ✓
├── [existing] Circular/Compost           ✓
├── [existing] Food Deserts               □
├── [existing] Food Insecurity (CDC)      □
├── [NEW] ─── Food Retail ─────────────────
│   ├── Grocery Stores                    □
│   ├── Supermarkets                      □
│   ├── Fast Food                         □
│   ├── Farmers Markets                   □
│   └── Convenience Stores               □
├── [NEW] ─── Food Access ─────────────────
│   └── 10-Min Walk Grocery Access        □
├── [NEW] ─── Transportation ──────────────
│   ├── MARTA Routes                      □
│   └── MARTA Stops                       □
├── [NEW] ─── Vulnerability ───────────────
│   ├── Income Choropleth                 □
│   ├── Poverty Choropleth               □
│   └── Food Insecurity Risk Index        □
├── [NEW] ─── Health ──────────────────────
│   └── Hospitals & Clinics              □
├── GT Campus Layers (I2CE)
│   ├── [existing] Campus Dining          ✓
│   ├── [existing] Compost                ✓
│   ├── [existing] Vending               ✓
│   └── [existing] Trash Cans            ✓
```

---

---

## WP-5: Standalone Vulnerability Map

**Owner:** Developer
**File to create:** `resources/Layers & Packages/vulnerability-map.html`
**Status:** Not Started
**Depends on:** WP-3 (risk index GeoJSON)

### Architecture (mirrors surplus-map.html)

```
┌──────────────────────────────────────────────────────────────┐
│  AFCN Food System Vulnerability Map                    [L]   │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                   │
│  Weight  │                                                   │
│  Sliders │            Choropleth Map                         │
│          │         (census tract polygons                    │
│  Poverty │          colored by risk quintile)                │
│  ████░░  │                                                   │
│          │                                                   │
│  Grocery │                                                   │
│  ████░░  │         ┌─────────────────────┐                   │
│          │         │ Tract: 11.00        │                   │
│  Unemp.  │         │ Risk: HIGH (0.72)   │  ← popup on      │
│  ███░░░  │         │ ████████ Poverty    │     click         │
│          │         │ ██████░░ Grocery    │                   │
│  Transit │         │ █████░░░ Health     │                   │
│  ████░░  │         └─────────────────────┘                   │
│          │                                                   │
│  SNAP    │                                                   │
│  ███░░░  │                                                   │
│          │                                                   │
│  F.Food  │                                                   │
│  ██░░░░  │                                                   │
│          │                                                   │
│  Health  │                                                   │
│  ████░░  │                                                   │
│          │                                                   │
│ [Reset]  │                                                   │
│ [Equal]  │                                                   │
│          │                                                   │
├──────────┴───────────────────────────────────────────────────┤
│ ■ Very High: 82 tracts (187K pop)  ■ High: 80  ■ Mod: 79   │
│ ■ Low: 80  ■ Very Low: 79  │  Total: 400 tracts             │
└──────────────────────────────────────────────────────────────┘
```

### Features

| Feature | Description |
|---------|-------------|
| Choropleth | Census tract polygons colored by risk quintile (5-color) |
| Weight sliders | 7 sliders (one per indicator), adjustable 0-100 |
| Live recalculation | Changing any slider recomputes scores + recolors map client-side |
| Tract popup | Click → shows tract name, composite score, 7 indicator bars |
| Stats rail | Bottom bar: tract counts per quintile, total affected population |
| Presets | "Equal Weight" (default), "Income-Focused", "Access-Focused" buttons |
| Legend | Graduated 5-color ramp with quintile break values |
| Link back | Nav link to AFCN dashboard + surplus map |

### Design Tokens (match AFCN system)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#07090f` | Page background |
| `--surface` | `#111722` | Panels |
| `--very-high` | `#ef5350` | 80-100th percentile |
| `--high` | `#ff9800` | 60-80th percentile |
| `--moderate` | `#ffc107` | 40-60th percentile |
| `--low` | `#a5d6a7` | 20-40th percentile |
| `--very-low` | `#66bb6a` | 0-20th percentile |

---

---

## Phase 2 — Dependency Graph

```
                    WP-1: Convert Layers
                    (team manual export)
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
              WP-2A: Census  WP-2B: CDC  WP-2C: Fast Food
              ACS API        PLACES API   Spatial Join
                    │         │           │
                    └────┬────┘───────────┘
                         ▼
                  WP-3: Risk Score
                  Computation
                         │
                    ┌────┴────┐
                    ▼         ▼
             WP-4: Dashboard  WP-5: Standalone
             Integration      Vulnerability Map
```

---

## Phase 2 — Timeline & Status Tracker

| WP | Task | Owner | Depends On | Status | Notes |
|:--:|------|-------|:----------:|:------:|-------|
| 1.1 | Export Poverty 2021 GA | Miranda | — | Not Started | |
| 1.2 | Export Median Household Income | Judie | — | Not Started | |
| 1.3 | Export Vehicle Availability 2022 | Swathi | — | Not Started | |
| 1.4 | Export MARTA Routes ATL | Miranda | — | Not Started | |
| 1.5 | Export MARTA Stops ATL | Miranda | — | Not Started | |
| 1.6 | Export County Health Rankings GA | Miranda | — | Not Started | |
| 1.7 | Export Midtown Convenience Stores | Miranda | — | Not Started | |
| 1.8 | Export 10-Min Walk Grocery Access 2024 | Ashley | — | Not Started | |
| 1.9 | Export Population Density ATL | Luca | — | Not Started | |
| 1.10 | Export 10-Min Walk Food Pantries ATL | Samuel | — | Not Started | |
| 2A | Write `fetch_census_acs.py` | Developer | — | Not Started | |
| 2B | Write `fetch_cdc_places.py` | Developer | — | Not Started | |
| 2C | Write `compute_fast_food_density.py` | Developer | — | Not Started | |
| 3 | Write `compute_risk_score.py` | Developer | 1.1, 1.3, 1.6, 2A, 2B, 2C | Not Started | |
| 4A | Add 7 existing pkg layers to dashboard | Developer | — | Not Started | Can start immediately |
| 4B | Add converted layers to dashboard | Developer | WP-1 | Not Started | |
| 4C | Add risk index layer to dashboard | Developer | WP-3 | Not Started | |
| 5 | Build vulnerability-map.html | Developer | WP-3 | Not Started | |

**Status Key:** Not Started | In Progress | Blocked | Complete

---

## Phase 2 — Completion Criteria

Phase 2 is complete when ALL of the following are true:

| Criterion | Status |
|-----------|:------:|
| All 10 priority layers converted to GeoJSON | Not Started |
| Census ACS script fetches 6 variables for Fulton + DeKalb tracts | Not Started |
| CDC PLACES script fetches obesity + diabetes prevalence | Not Started |
| Risk score computed for ~400 census tracts | Not Started |
| Risk index validated against known food desert tracts (>70% overlap) | Not Started |
| 7 existing pkg layers added to dashboard | Not Started |
| Risk index choropleth toggle added to index.html | Not Started |
| Standalone vulnerability-map.html built with weight sliders | Not Started |
| Dev server test passes (all pages load without errors) | Not Started |

**When all criteria met: proceed to Phase 3 (Campus-to-Community Pipeline + Fleet Integration)**

---

## Phase 2 — Quick Start (What Can Begin Immediately)

These tasks have **no dependencies** and can start right now:

1. **WP-4A:** Add 7 existing GeoJSON pkg layers to `index.html` — grocery, supermarkets, fast food, farmers markets, hospitals, religious institutions, gardens
2. **WP-2A:** Write `scripts/fetch_census_acs.py` — only needs a free Census API key
3. **WP-2B:** Write `scripts/fetch_cdc_places.py` — uses same API already in `index.html`
4. **WP-1 (all):** Team members export their layers from ArcGIS Online (parallel task)

---

## Appendix: Phase Roadmap Context

| Phase | Focus | Status |
|:-----:|-------|:------:|
| **1** | Data Collection (4 subagent categories) | Complete |
| **2** | 8-Map Framework Expansion + Vulnerability Map | **Current** |
| **3** | Campus-to-Community Pipeline + Fleet Integration | Planned |
| **4** | Real-Time Data Feeds + NutriSlice/LeanPath Automation | Planned |
| **5** | Public Deployment + Stakeholder Dashboard | Planned |
