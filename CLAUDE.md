# AFCN — Atlanta Food Circular Network

## Project Overview
A citywide food system mapping platform for Atlanta, built with **ArcGIS Maps SDK for JavaScript v4.30** (AMD modules via CDN). The platform visualizes food recovery sources, redistribution nodes, beneficiary access points, and circular economy infrastructure across Atlanta and the Georgia Tech campus.

The project has **six web dashboards**, supporting Python scripts, Netlify deployment config, and 35 GeoJSON data layers.

---

## Key Files

### Web Dashboards (all inline CSS/HTML/JS, no build step)
| File | Purpose | Lines |
|------|---------|-------|
| `resources/Layers & Packages/index.html` | **AFCN Dashboard** — main citywide + campus map with all data layers, mode toggle (Atlanta / GT Campus), dock tabs, layer panel | ~535 |
| `resources/Layers & Packages/surplus-map.html` | **Real-Time Food Surplus Map** — standalone surplus pins + urgency-aware route optimizer + fleet intelligence, no AFCN layers | ~1358 |
| `resources/Layers & Packages/fleet-analytics.html` | **Fleet Analytics** — fleet vehicle tracking, driver table, pipeline visualization, route assignment dock | ~162 |
| `resources/Layers & Packages/gt-campus-hub.html` | **GT Campus Food Circular Hub** — campus-focused map with admin dashboard, Chart.js analytics, light theme | ~2655 |
| `resources/Layers & Packages/gt_fch_preview.html` | **GT-FCH Preview Map** — lightweight local preview of GT Food Circular Hub with dynamic host origin | ~377 |
| `resources/Layers & Packages/gt_fch_map.html` | **GT-FCH ArcGIS Feature Map** — earlier GT campus map version | ~793 |

Dashboards link to each other via nav links in the header.

#### IAC-VLABA-2021 Variants
| File | Purpose |
|------|---------|
| `resources/Layers & Packages/index-iac-vlaba-2021.html` | Variant of AFCN dashboard for IAC-VLABA-2021 dataset |
| `geojson/*-iac-vlaba-2021.geojson` | Matching GeoJSON layers for the IAC-VLABA-2021 variant |
| `geojson/manifest-iac-vlaba-2021.json` | Manifest for IAC-VLABA-2021 layers |
| `Python Script/serve-iac-vlaba-2021.py` | Dev server variant for IAC-VLABA-2021 |

### Python Scripts
| File | Purpose |
|------|---------|
| `Python Script/serve.py` | Local dev server (port 8080), serves project root with CORS, `/api/config` endpoint returns ArcGIS API key from `.env`, auto-opens browser, lists all dashboards on startup |
| `Python Script/publish_dashboards.py` | Builds a publish-ready static bundle in `publish/` — copies `geojson/` + `resources/`, writes `api/config` JSON, generates a landing page linking all discovered dashboards |
| `Python Script/build_ppkx.py` | ArcGIS Pro packaging script — creates File GDB from GeoPackage, builds .ppkx |
| `Python Script/export_geopackage.py` | Exports layers to GeoPackage format |
| `Python Script/convert_shapefiles.py` | Shapefile conversion utility |
| `Python Script/serve-iac-vlaba-2021.py` | Dev server variant for IAC-VLABA-2021 dataset |

### Deployment (Netlify)
| File | Purpose |
|------|---------|
| `netlify.toml` | Netlify build config — runs `publish_dashboards.py --out publish --clean`, publishes `publish/` dir, redirects `/api/config` to serverless function |
| `netlify/functions/config.js` | Serverless function returning `ARCGIS_API_KEY` env var as JSON (set in Netlify dashboard) |

### Data
| Path | Description |
|------|-------------|
| `geojson/` | 35 GeoJSON files — campus dining, food recovery sources, redistribution nodes, beneficiary access points, circular economy, buildings, sidewalks, network flows, campus boundary, compost locations, food deserts, street centerlines, vending machines, trash/recycling (indoor + outdoor), and 15+ `pkg_*` package layers |
| `geojson/manifest.json` | Metadata manifest for all GeoJSON layers |
| `fulton_permitted_compost_sites (2).csv` | 10 real Fulton County permitted compost facilities (used in route optimizer) |
| `.env` | ArcGIS API key (`ARCGIS_API_KEY=AAPK...`) — **do not commit** |
| `exports/` | Generated GeoPackage and File GDB outputs |

### Documentation
| File | Purpose |
|------|---------|
| `PUBLISH.md` | Publishing guide — build bundle, deploy to Cloudflare Pages or Netlify, dashboard URLs |
| `PRESENTATION_SCRIPT.md` | Presentation script / demo walkthrough |
| `AFCN_Phase1_Tracking.md` | Phase 1 project tracking |
| `Real-time Surplus Map.md` | Surplus map design notes |
| `fleet-analytics-implementation.md` | Fleet analytics implementation notes |
| `Design Research Notes.md` | Design research documentation |
| `GT Campus Circular Hub — Design Review.md` | GT campus hub design review |

---

## Architecture

### AFCN Dashboard (`index.html`)
- **Mode toggle**: Atlanta (citywide) vs GT Campus
- **Dock tabs**: Food Recovery Sources, Redistribution Nodes, Beneficiary Access, Circular Economy, Network Flows (Atlanta mode) / Campus All, Campus Dining, Campus Infrastructure (GT mode)
- **Layer panel** (left sidebar): Checkboxes to toggle each layer on/off, grouped by category
- **Layers**: GeoJSONLayer for most data, FeatureLayer for CDC food insecurity + Atlanta boundary
- **Default campus tab**: `campusDining` (not campusAll)
- **Beneficiary layer**: Off by default in Atlanta mode
- **Popup**: Undocked (floating) — `dockEnabled: false`
- **No basemap gallery** — removed intentionally
- **Stats rail** (bottom): Live feature counts

### Surplus Map (`surplus-map.html`)
- **Standalone page** — does NOT include any AFCN layers
- **Map layers**: Only `surplusLayer` (GraphicsLayer) and `routeLayer` (GraphicsLayer) on `dark-gray-vector` basemap
- **30 mock surplus entries** with real coordinates from Atlanta — each has: name, lat/lng, food_type, quantity_lbs, expiration, urgency (Critical/Soon/Stable), transport requirement, source_category, notes
- **Surplus filters** (left panel): 5 food type checkboxes — Prepared Meals, Packaged Goods, Produce, Bakery, Perishable <6hrs
- **Fleet Intelligence panel** (top of route panel):
  - Fleet Status: 2×2 grid showing Active Drivers (42), Refrigerated Vehicles (8), Avg Pickup (24 min), lbs Today (12,400) from `MOCK_FLEET`
  - AI Suggested Route: runs urgency-aware algorithm on load, displays recommended chain with time/food saved metrics, Accept Plan / Dismiss buttons
- **Route Optimizer panel** (right side, open by default):
  - Origin: North Avenue Dining Hall `[-84.3918, 33.7716]`
  - Vehicle Type selector: Refrigerated Van / Dry Vehicle / Bike Courier
  - 4-stop chain: Food Recovery → Redistribution → Beneficiary → Compost
  - Route chain dots: neutral gray `#3a4254` with numbers only (no category colors)
  - Stop markers on map: uniform teal `#00bfa5`
  - **Urgency-aware smart routing** (replaces old greedy nearest-neighbor):
    - Priority score: `(0.50 × urgency) + (0.30 × volume) + (0.20 × proximity)`
    - Urgency: exponential decay `100 × e^(-0.5 × hours_remaining)` — cliff at <1hr
    - Volume: logarithmic `min(100, 20 × log10(lbs + 1))` — diminishing returns >500 lbs
    - Proximity: inverse `100 / (1 + distance_miles)`
  - **Transport compatibility filtering**: hierarchy Refrigerated Van (4) > Dry Vehicle (3) > Bike Courier (2) > Walk-in (1); vehicle must meet or exceed required level
  - **Capacity-aware destination selection**: redistribution/beneficiary nodes scored by proximity with penalties for >90% cold storage (-50) or >90% dry storage (-30); nodes not accepting perishables are skipped when carrying perishable loads
  - Dropdown labels show capacity badges: `[FULL]`, `[92%]`, transport type
  - Traffic-aware routing via `startTime: new Date()` in RouteParameters
  - Real routing via ArcGIS Route Service when API key is available
  - Fallback: dashed geodesic lines at 25 mph estimated speed
  - Stats: distance, time, volume, savings %, urgency context (colored badge with lbs + time remaining)
- **Compost stops**: 10 real Fulton County permitted sites (GT Resource Recovery Yard, CHaRM, Ben's Backyard, CO-Collegetown Farm, CompostNow, Goodr Inc., Truly Living Well, Urban Food Forest at Browns Mill, Southern Green Industries, Old Rucker Farm)
- **Key constants**: `MOCK_FLEET`, `SCORING_WEIGHTS`, `TRANSPORT_HIERARCHY`
- **Key functions**: `computePriorityScore()`, `smartSelectRecovery()`, `smartSelectCapacityNode()`, `computeCapacityScore()`, `isTransportCompatible()`, `populateFleetPanel()`, `generateAISuggestion()`, `acceptAISuggestion()`

### Fleet Analytics (`fleet-analytics.html`)
- **Dark theme** — ArcGIS dark theme, `#0c1118` background
- **Left rail**: Fleet table with vehicle rows (name, status, utilization), 3-column mini stats grid
- **Center**: ArcGIS MapView with vehicle position markers, map legend, mode control
- **Bottom strip**: 4-step pipeline visualization (Food Recovery → Redistribution → Beneficiary → Compost) with cards, scoring badges, and route builder
- **Right dock**: Assigned routes list with accept/dismiss actions

### GT Campus Hub (`gt-campus-hub.html`)
- **Light theme** — ArcGIS light theme with admin palette (glaucous base + warm accents)
- **Largest dashboard** (~2655 lines) with Chart.js analytics loaded lazily to avoid AMD/UMD conflict with ArcGIS Dojo loader
- **Admin dashboard** with charts and campus-specific circular economy data

### API Key Flow
1. **Local dev**: `.env` file at project root → `serve.py` reads it → served at `GET /api/config`
2. **Netlify production**: `ARCGIS_API_KEY` env var in Netlify dashboard → `netlify/functions/config.js` serverless function → redirected from `/api/config`
3. Dashboard JS fetches `/api/config` on load, sets `esriConfig.apiKey`
4. If no key: yellow notice bar shown, routing falls back to geodesic estimates

### Dev Server
```bash
cd "Python Script"
python serve.py          # http://localhost:8080
python serve.py 3000     # http://localhost:3000
```
Dashboard URL: `http://localhost:8080/resources/Layers%20%26%20Packages/index.html`
Surplus Map: `http://localhost:8080/resources/Layers%20%26%20Packages/surplus-map.html`

### Publishing / Deployment
```bash
# Build static bundle locally
python "Python Script/publish_dashboards.py"
python "Python Script/publish_dashboards.py" --clean          # full clean rebuild
python "Python Script/publish_dashboards.py" --api-key "KEY"  # override API key

# Netlify auto-builds via netlify.toml on push
```
The `publish/` folder (gitignored) contains the deploy-ready bundle with a generated landing page.

---

## GeoJSON Layer Summary
| File | Features | Description |
|------|----------|-------------|
| `campus_dining.geojson` | 12 | GT dining locations |
| `food_recovery_sources.geojson` | 11,314 | Food recovery points (restaurants, institutions) |
| `redistribution_nodes.geojson` | 2,629 | Food banks, pantries, shelters |
| `beneficiary_access_points.geojson` | 17 | Beneficiary community points |
| `circular_economy.geojson` | 127 | Compost, recycling, gardens |
| `network_flows.geojson` | 12 | Flow LineStrings with lbs_per_week |
| `buildings.geojson` | — | GT campus buildings |
| `campus_boundary.geojson` | — | GT campus boundary polygon |
| `compost_locations.geojson` | — | Compost facility locations |
| `food_deserts_atlanta.geojson` | — | Atlanta food desert areas |
| `recycling_trash_cans.geojson` | — | Outdoor recycling/trash locations |
| `trash_recycling_indoor.geojson` | — | Indoor recycling/trash locations |
| `sidewalks.geojson` | — | GT campus sidewalks |
| `street_centerlines.geojson` | — | GT campus street centerlines |
| `vending_machines.geojson` | — | GT vending machine locations |
| `pkg_*.geojson` (15 files) | — | Package layers: grocery stores, farmers markets, restaurants, fast food, hospitals, religious institutions, community orgs, food processing, Kroger network, supermarkets, etc. |
| `*-iac-vlaba-2021.geojson` (5 files) | — | IAC-VLABA-2021 dataset variants of core layers |

---

## Design Decisions Log

1. **Surplus map is a separate page** — not overlaid on AFCN dashboard (user preference for clean separation)
2. **No AFCN layers on surplus map** — only surplus pins and route graphics (user found clusters confusing)
3. **Route chain dots are gray with numbers** — avoid confusion with color-coded map pins
4. **Compost stops use real Fulton County data** — not school gardens (schools may become beneficiary points later)
5. **Popup undocked** — floating near the pin, not docked to bottom-left
6. **No basemap gallery** — removed to simplify UI
7. **GT Campus defaults to Campus Dining tab** — not Campus All
8. **Urgency-aware routing over pure distance** — weighted scoring (urgency 50%, volume 30%, distance 20%) ensures critical/large loads are prioritized even if farther away
9. **Transport hierarchy as numeric levels** — Refrigerated Van (4) > Dry Vehicle (3) > Bike Courier (2) > Walk-in (1); vehicle must meet or exceed the pickup's required level
10. **Capacity penalties at destination** — nodes >90% full get score penalties rather than being excluded, so they're still available as last resort
11. **Fleet Intelligence uses mock data** — `MOCK_FLEET` constant provides realistic fleet stats; designed to be replaceable with live API data later
12. **Chart.js loaded lazily in gt-campus-hub** — avoids AMD/UMD conflict with ArcGIS Dojo loader
13. **gt_fch_preview uses dynamic host origin** — no localhost lock-in, works in any deployment environment
14. **Netlify serverless function for API key** — keeps key secret in production vs. static `api/config` JSON in local dev
15. **publish/ folder is gitignored** — generated artifact, rebuilt on each deploy

---

## Common Tasks

### Adding a new GeoJSON layer to the AFCN dashboard
1. Place `.geojson` file in `geojson/` folder
2. In `index.html`, define a new `GeoJSONLayer` with url, renderer, popupTemplate
3. Add a checkbox in the appropriate group in `<aside id="layerPanel">`
4. Wire visibility toggle in the mode/tab JS logic
5. Add to `updateStatsRail()` if it should show feature counts

### Adding a new dashboard page
1. Create `.html` file in `resources/Layers & Packages/`
2. Add nav links to/from existing dashboards in the header
3. The file will be auto-discovered by `publish_dashboards.py` and `serve.py`
4. Optionally add to `PRIORITY_DASHBOARDS` and `DISPLAY_NAMES` in `publish_dashboards.py` for ordering/naming on the landing page

### Modifying mock surplus data
- Edit `MOCK_SURPLUS` array in `surplus-map.html` (inline JS)
- Each entry needs: id, name, lng, lat, food_type, quantity_lbs, expiration (ISO), urgency, transport, source_category, notes

### Modifying route optimizer behavior
- **Scoring weights**: Edit `SCORING_WEIGHTS` constant — `{ URGENCY: 0.50, VOLUME: 0.30, DISTANCE: 0.20 }`
- **Transport hierarchy**: Edit `TRANSPORT_HIERARCHY` constant — maps vehicle names to numeric levels
- **Capacity thresholds**: In `computeCapacityScore()` — cold >90% gets -50, dry >90% gets -30
- **Route stops with capacity**: `ROUTE_STOPS.redistribution` and `.beneficiary` have `cold_pct`, `dry_pct`, `accepting_perishable` fields
- **Route stops with transport**: `ROUTE_STOPS.foodRecovery` entries have `transport` field
- **Fleet mock data**: Edit `MOCK_FLEET` constant to change fleet stats display

### Updating compost sites
- Reference: `fulton_permitted_compost_sites (2).csv`
- Route stops defined in `ROUTE_STOPS.compost` array in `surplus-map.html`

### Deploying to Netlify
1. Push to the repo — Netlify auto-builds via `netlify.toml`
2. Set `ARCGIS_API_KEY` in Netlify dashboard → Site settings → Environment variables
3. The build runs `publish_dashboards.py --out publish --clean` and publishes the `publish/` folder
4. `/api/config` is redirected to the serverless function in `netlify/functions/config.js`

---

## Conventions

- **No build step** — all dashboards are self-contained HTML with inline CSS and JS
- **ArcGIS Maps SDK v4.30** via CDN (AMD modules) — do not upgrade without testing all dashboards
- **Dark theme** for AFCN dashboard, surplus map, and fleet analytics; **light theme** for GT campus hub
- **GT branding**: Navy `#003057`, Tech Gold `#B3A369`
- **Font**: "Avenir Next", "Segoe UI", Arial, sans-serif
- **File naming**: kebab-case for new files (e.g., `fleet-analytics.html`), underscores acceptable for legacy (e.g., `gt_fch_map.html`)
- **GeoJSON files**: lowercase with underscores, `pkg_` prefix for package/external layers
- **No external JS frameworks** — vanilla JS only, Chart.js loaded lazily where needed
- **Secrets**: Never commit `.env`; API keys go through `/api/config` endpoint (local server or Netlify function)
