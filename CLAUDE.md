# AFCN — Atlanta Food Circular Network
> Last updated: March 2026 · Georgia Tech I2CE Lab

## Project Overview
A citywide food system mapping platform for Atlanta, built with **ArcGIS Maps SDK for JavaScript v4.30** (AMD modules via CDN). The platform visualizes food recovery sources, redistribution nodes, beneficiary access points, and circular economy infrastructure across Atlanta and the Georgia Tech campus.

**Strategic position:** First platform to combine real-time spatial surplus mapping + campus-to-community pipeline + fleet optimization. Addresses uncontested Gap 2 (spatial intelligence) and Gap 3 (campus-to-community) in the food rescue market.

---

## AI Agent Skills

Three skill files are available for Claude agents working in this project.
**Always read the relevant SKILL.md before starting any task.**

| Task | Skill File | Use When |
|------|-----------|----------|
| Dashboard code changes | `skills/dashboard-agent/SKILL.md` | Any edit to .html files, ArcGIS layers, UI, routing logic |
| Data analysis | `skills/analyst-agent/SKILL.md` | LeanPath analysis, waste reports, NutriSlice insights |
| Data pipeline | `skills/data-agent/SKILL.md` | Parsing new LeanPath exports, updating leanpath_surplus.js |

---

## Key Files

### Web Dashboards (single-file inline HTML/CSS/JS — no build step)
| File | Purpose |
|------|---------|
| `resources/Layers & Packages/index.html` | **AFCN Dashboard** — citywide + GT campus map, all 30 GeoJSON layers, mode toggle |
| `resources/Layers & Packages/surplus-map.html` | **Real-Time Surplus Map** — surplus pins + urgency route optimizer (standalone) |
| `resources/Layers & Packages/gt-campus-hub.html` | GT Campus Hub — dining menus, events, pantry, admin analytics |
| `resources/Layers & Packages/fleet-analytics.html` | Fleet operations dashboard |

### Data Files (source of truth for dashboards)
| File | Purpose |
|------|---------|
| `data/leanpath_surplus.js` | **Drop-in surplus data** — real LeanPath MOCK_SURPLUS + MOCK_FLEET. Regenerate with `python scripts/parse_leanpath.py data/Waste-Data.csv` |
| `data/Waste-Data.csv` | Raw LeanPath export (GT campus, Mar 4–10 2026, 408 entries) |
| `data/Engagement_overview.csv` | NutriSlice / GA4 user data (Feb 10 – Mar 9 2026) |
| `geojson/` | 30 GeoJSON layers (campus_dining, food_recovery_sources, redistribution_nodes, etc.) |
| `.env` | `ARCGIS_API_KEY=AAPK...` — never commit |

### Python Scripts
| File | Purpose |
|------|---------|
| `Python Script/serve.py` | Dev server → `http://localhost:8080` |
| `scripts/parse_leanpath.py` | LeanPath CSV → `data/leanpath_surplus.js` |
| `Python Script/publish_dashboards.py` | Static bundle for Cloudflare/Netlify |

---

## LeanPath Data Snapshot (Mar 4–10 2026)

Real data powering `data/leanpath_surplus.js`. Regenerate whenever a new export arrives.

| Metric | Value |
|--------|-------|
| Total entries | 408 |
| Total weight wasted | **2,316 lbs** |
| Total food cost wasted | **$2,380** |
| Donated (rescue-ready) | **80 lbs (3.5%)** |
| Composted | **2,236 lbs (96.5%)** |
| Preventable (overproduction) | **1,392 lbs (60%)** |
| Rescuable entries in surplus map | **30 grouped pins** |
| Surplus map total lbs shown | **1,051 lbs** |

**By location:** North Ave 1,632 · West Village 441 · Student Center 94 · Exhibition Hall 75 · Carnegie 43 · Vending 31

**Top loss reasons:** Overproduction-Line 915 lbs · Trimmings 707 lbs · Overproduction-Holding 405 lbs

**NutriSlice users:** 3,385 total · 2,174 new · ~52 sec avg engagement · 69% referral

---

## Architecture

### AFCN Dashboard (`index.html`)
- **Mode toggle**: Atlanta (citywide) vs GT Campus
- **Dock tabs**: Food Recovery Sources, Redistribution Nodes, Beneficiary Access, Circular Economy, Network Flows / Campus All, Campus Dining, Campus Infrastructure
- **Layer panel** (left sidebar): checkboxes per layer grouped by category
- **Beneficiary layer**: off by default in Atlanta mode
- **Popup**: undocked (floating), `dockEnabled: false`
- **Stats rail** (bottom): live feature counts

### Surplus Map (`surplus-map.html`) — STANDALONE
- **Does NOT include AFCN layers** — only `surplusLayer` + `routeLayer` on `dark-gray-vector`
- **Data source**: `MOCK_SURPLUS` — currently populated from `data/leanpath_surplus.js` (real LeanPath data, GT Campus Mar 2026)
- **30 surplus entries**: 6 Critical, 12 Soon, 12 Stable; 1,051 total lbs
- **Surplus filters** (left panel): 5 food type checkboxes with live counts
- **Fleet Intelligence panel**: powered by `MOCK_FLEET` (real LeanPath numbers)
- **AI Suggested Route**: urgency-aware algorithm on load
- **Route Optimizer**: 4-stop chain from North Ave origin, ArcGIS Route API + geodesic fallback

### Urgency-Aware Scoring (do not change without updating this file)
```
priority = (0.50 × urgency_decay) + (0.30 × volume_score) + (0.20 × proximity_score)
urgency_decay  = 100 × e^(-0.5 × hours_remaining)
volume_score   = min(100, 20 × log10(lbs + 1))
proximity_score = 100 / (1 + distance_miles)
```

### Transport Hierarchy
```
Refrigerated Van (4) > Dry Vehicle (3) > Bike Courier (2) > Walk-in (1)
Vehicle must meet or exceed required level for the surplus item
```

### API Key Flow
1. `.env`: `ARCGIS_API_KEY=AAPK...`
2. `serve.py` serves it at `GET /api/config`
3. Dashboard JS fetches on load → sets `esriConfig.apiKey`
4. Fallback: yellow notice bar + geodesic line routing

### Dev Server
```bash
cd "Python Script" && python serve.py
# Dashboard: http://localhost:8080/resources/Layers%20%26%20Packages/index.html
# Surplus:   http://localhost:8080/resources/Layers%20%26%20Packages/surplus-map.html
```

---

## GeoJSON Layers
| File | Features | Description |
|------|----------|-------------|
| `campus_dining.geojson` | 12 | GT dining locations |
| `food_recovery_sources.geojson` | 11,314 | Food recovery points |
| `redistribution_nodes.geojson` | 2,629 | Food banks, pantries, shelters |
| `beneficiary_access_points.geojson` | 17 | Community beneficiary points |
| `circular_economy.geojson` | 127 | Compost, recycling, gardens |
| `network_flows.geojson` | 12 | Flow LineStrings |
| `pkg_*.geojson` (15 files) | — | Grocery, farmers markets, restaurants, fast food, hospitals, etc. |

---

## Design System
| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#07090f` | Page background |
| `--surface` | `#111722` | Cards, panels |
| `--teal` | `#00bfa5` | Primary accent, route lines, confirmed actions |
| `--critical` | `#ef5350` | Urgency Critical pins |
| `--soon` | `#ffc107` | Urgency Soon pins |
| `--stable` | `#66bb6a` | Urgency Stable pins |
| `--muted` | `#5a6a7e` | Secondary text, route chain dots |
| Font | Segoe UI / system-ui | All text |

**Pin sizing:** <50 lbs = 10px · 50–200 lbs = 14px · 200+ lbs = 18px
**Critical pins only** get pulse animation
**Route line:** solid teal #00bfa5 width 4 + glow underlay width 8 opacity 0.3

---

## Design Decisions Log

1. **Surplus map is a separate page** — not overlaid on AFCN (user preference)
2. **No AFCN layers on surplus map** — only surplus + route graphics (clusters confusing)
3. **Route chain dots are gray with numbers** — avoid confusion with colored map pins
4. **Compost stops use real Fulton County data** — 10 permitted sites
5. **Urgency-aware routing over pure distance** — weighted scoring (urgency 50%, volume 30%, distance 20%)
6. **Transport hierarchy as numeric levels** — vehicle must meet or exceed required level
7. **Capacity penalties at destination** — >90% full gets score penalty, not excluded
8. **MOCK_SURPLUS is real LeanPath data** — replaced mock placeholders with actual GT campus waste data (Mar 2026)
9. **MOCK_FLEET uses real LeanPath stats** — lbsWeekRecovered, donationRatePct, costAtRisk are real numbers

---

## Common Tasks

### Update surplus data when new LeanPath export arrives
```bash
# Place new CSV in data/ folder, then:
python scripts/parse_leanpath.py data/Waste-Data-YYYY-MM-DD.csv
# Output overwrites data/leanpath_surplus.js
# Refresh browser — no rebuild needed
```

### Add a new GeoJSON layer to AFCN dashboard
1. Place `.geojson` in `geojson/`
2. Define `GeoJSONLayer` in `index.html` with renderer + popupTemplate
3. Add checkbox in appropriate `#layerPanel` group
4. Wire visibility toggle in mode/tab JS
5. Add to `updateStatsRail()` for feature count

### Modify surplus scoring weights
Edit `SCORING_WEIGHTS` in `surplus-map.html` **AND** update the Design Decisions section above.

### Modify fleet stats display
Edit `MOCK_FLEET` in `data/leanpath_surplus.js` (or regenerate from CSV). `populateFleetPanel()` reads all fields automatically.

### Add a new surplus filter type
1. Add checkbox in `#layerPanel` with `data-surplus="NewType"`
2. Add entry to `FOOD_TYPE_COLORS` in `surplus-map.html`
3. `renderSurplusLayer()` reads all `data-surplus` checkboxes dynamically
