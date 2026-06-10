# Fleet Analytics Dashboard â€” Implementation Review & Plan

**Date:** 2026-02-28
**Status:** Pre-implementation review
**Source file:** `fleet-analytics (1).html` (current prototype)
**Target file:** `resources/Layers & Packages/fleet-analytics.html`

---

## 1. Review Summary

The current `fleet-analytics (1).html` prototype is a well-structured 4-panel operational dashboard (Logistics Fleet â†’ Food Donors â†’ Food Redistribution â†’ Approve & Assign Routes). It has strong component design (funnel, donut, entity cards, route cards) and uses appropriate mock data with real Atlanta organizations.

**However, two critical issues prevent alignment with the existing AFCN dashboards:**

| # | Issue | Severity |
|---|-------|----------|
| A | **No embedded ArcGIS map** â€” both "map" areas are CSS placeholders with positioned dots, not real maps | Critical |
| B | **Background / layout model mismatch** â€” fleet analytics is a scrollable page with solid `#0c1118` body; existing dashboards use a full-viewport `#app` wrapper with ArcGIS map as the background | High |

Plus several smaller alignment gaps detailed below.

---

## 2. Issue A â€” Missing Embedded ArcGIS Map

### Current state
The prototype has two `.map-area` divs (Panel 1: "Live Fleet Map", Panel 4: "Route Preview") that use:
- A CSS grid background pattern (`.map-grid-bg`)
- Radial gradient glows (`.map-glow`)
- Absolutely-positioned colored dots (`.map-pin`)

These are **static visual mockups** â€” they don't render real geography, don't support zoom/pan, and can't show actual fleet positions.

### What the existing dashboards do
- `index.html` and `surplus-map.html` both load `ArcGIS Maps SDK for JavaScript v4.30` via CDN
- They create a real `MapView` attached to a `#viewDiv` container
- Layers (GeoJSONLayer, GraphicsLayer, FeatureLayer) render actual geospatial data

### Recommended fix
Replace the CSS placeholder maps with real ArcGIS `MapView` instances:

1. **Panel 1 â€” Live Fleet Map**: Embed a `MapView` with `dark-gray-vector` basemap showing:
   - A `GraphicsLayer` for vehicle positions (teal markers)
   - Optionally show donor/recipient markers from existing GeoJSON layers
   - Center on Atlanta `[-84.388, 33.749]`, zoom ~11

2. **Panel 4 â€” Route Preview**: Embed a second `MapView` (or reuse the first) showing:
   - Route polylines between donor â†’ recipient stops
   - Vehicle, pickup, and delivery markers
   - Styled to match surplus-map's route visualization

3. **ArcGIS SDK loading**: Add the standard CDN includes:
   ```html
   <link rel="stylesheet" href="https://js.arcgis.com/4.30/esri/themes/light/main.css" />
   <script src="https://js.arcgis.com/4.30/"></script>
   ```

4. **API key flow**: Use the same `/api/config` fetch pattern as the other dashboards.

### Implementation note
The maps will live inside card containers (not full-viewport like in index.html), so they need explicit `width`/`height` on the container div and `MapView` should be initialized after the panel becomes visible (or use `view.when()` to handle lazy init).

---

## 3. Issue B â€” Background & Layout Model Mismatch

### Current state (fleet-analytics)
```css
html, body {
  width: 100%; min-height: 100vh;      /* scrollable page */
  background: var(--bg-body);            /* solid #0c1118 */
}
#topbar { position: sticky; }           /* sticks on scroll */
#main { padding: 12px 20px 40px; }      /* scrollable content area */
```

### Existing dashboards (index.html, surplus-map.html, gt-campus-hub.html)
```css
html, body, #app {
  width: 100%; height: 100%; overflow: hidden;   /* fixed viewport */
}
#app { position: relative; background: #0c1118; }
#topbar { position: absolute; top: 0; }           /* fixed at top */
#viewDiv { position: absolute; inset: 0; }        /* map fills viewport */
```

### Decision required
The fleet analytics page is fundamentally **not map-centric** â€” it's a data dashboard with charts, tables, and cards. A scrollable layout is actually appropriate here (unlike the map-first pages). Two options:

**Option A â€” Keep scrollable layout (Recommended)**
- The fleet analytics page is an admin KPI dashboard, not a map exploration tool
- Scrollable pages are standard for analytics dashboards
- Keep `min-height: 100vh` and `position: sticky` topbar
- Embedded maps live inside card containers at fixed heights (340pxâ€“460px)
- Update the background color and surface variables to exactly match the other pages' palette

**Option B â€” Switch to fixed viewport with scrollable inner panel**
- Wrap content in an `#app` container matching other dashboards
- Use `overflow-y: auto` on the main content area only
- Topbar becomes `position: absolute`
- More consistent structure but awkward for a dashboard with many sections

### Recommendation
**Go with Option A** but ensure the color palette and topbar styling exactly match the other pages so it looks like part of the same app.

---

## 4. CSS Variable & Color Alignment

### Variables in fleet-analytics NOT present in existing dashboards

The fleet-analytics prototype defines many CSS variables that the existing dashboards use as raw values. This is actually an improvement â€” but the values must match exactly.

| Fleet Variable | Value | Match in existing pages? |
|----------------|-------|--------------------------|
| `--bg-dark` | `#07090f` | Yes â€” same in all pages |
| `--bg-body` | `#0c1118` | Yes â€” used as raw `#0c1118` in `#app` background |
| `--surface` | `#111722` | New â€” not in other pages |
| `--surface-raised` | `#141924` | New â€” not in other pages |
| `--surface-hover` | `#1a2230` | New â€” not in other pages |
| `--border` | `#222a3b` | Yes â€” used as raw value in topbar border |
| `--border-light` | `#2b3446` | Yes â€” used as raw `#2b3446` in `.statCard` |
| `--border-hover` | `#3a4254` | Yes â€” used as raw `#3a4254` in `#modeToggle` |
| `--teal` | `#00bfa5` | Yes â€” used as `--route-teal` in surplus-map/gt-campus-hub |
| `--gold` | `#b3a369` | Yes â€” same across all pages |

### Card background comparison
- Fleet: `.card { background: rgba(10, 14, 22, 0.88); }`
- Index/Surplus: `.statCard { background: rgba(10, 14, 22, 0.88); }`
- **Match confirmed** â€” same semi-transparent dark

### What to fix
The fleet prototype's palette is **correctly derived** from the existing pages. No color changes needed â€” just ensure no drift during implementation.

---

## 5. Navigation Inconsistencies

### Current nav links across all pages

| Page | Nav links shown | Active indicator |
|------|----------------|------------------|
| `index.html` | Campus Hub, Surplus Map + Mode Toggle | None (no active class on links) |
| `surplus-map.html` | AFCN Dashboard, Campus Hub | None |
| `gt-campus-hub.html` | AFCN Dashboard, Campus Hub, Surplus Map | `.navLink.active` class |
| `fleet-analytics.html` | AFCN Dashboard, Surplus Map, Fleet Analytics, GT Campus | `.navLink.active-page` class |

### Issues to fix

1. **Active class name**: Fleet uses `.active-page`, gt-campus-hub uses `.active`. Standardize to one.

2. **Link label mismatch**: Fleet calls it "GT Campus" â†’ `gt-campus-hub.html`; other pages call it "Campus Hub". Use "Campus Hub" consistently.

3. **No pages link TO Fleet Analytics**: None of the existing pages (index.html, surplus-map.html, gt-campus-hub.html) currently have a nav link to the Fleet Analytics page. These need to be added.

4. **Recommended unified nav order** (all pages):
   ```
   AFCN Dashboard | Surplus Map | Fleet Analytics | Campus Hub
   ```
   With the current page highlighted using a consistent `.active` class.

5. **LIVE badge**: Fleet analytics adds a pulsing "LIVE" badge in the topbar. This is not present in other pages. Decision: keep it (it makes sense for a real-time monitoring dashboard) but only on this page.

---

## 6. Topbar & Branding Alignment

### Logo source
| Page | Logo path |
|------|-----------|
| `index.html` | `/resources/GT%20logo/Primary%20Logos/Georgia%20Tech%20One%20Line/GTOneLine_White.svg` (local) |
| `surplus-map.html` | Same local path |
| `gt-campus-hub.html` | Same local path |
| `fleet-analytics.html` | `https://raw.githubusercontent.com/jhuang0420/AFCN/main/assets/logos/gt_i2ce_logo.png` (external GitHub) |

**Fix:** Use the same local SVG path as the other pages.

### I2CE link
| Page | URL | Text |
|------|-----|------|
| `index.html` | `https://sites.gatech.edu/i2ce/` | "Georgia Tech Circular Economy Lab [I2CE]" |
| `surplus-map.html` | Same | Same |
| `gt-campus-hub.html` | Same | "GT Circular Economy Lab [IÂ²CE]" |
| `fleet-analytics.html` | `https://research.gatech.edu/i2ce` | "IÂ²CE" |

**Fix:** Use `https://sites.gatech.edu/i2ce/` and match the text style from gt-campus-hub: "GT Circular Economy Lab [IÂ²CE]"

### Title h1 font size
| Page | Size |
|------|------|
| `index.html` | 27px |
| `surplus-map.html` | 27px |
| `gt-campus-hub.html` | 22px |
| `fleet-analytics.html` | 22px |

**Note:** There's already inconsistency between existing pages. The fleet analytics matches gt-campus-hub at 22px. This is acceptable â€” both are "sub-dashboards" while the main AFCN page and surplus map use the larger 27px.

---

## 7. Process Flow Bar (Unique to Fleet Analytics)

The 4-step process flow bar is a **good UX pattern** unique to this page:

```
1. Logistics Fleet â†’ 2. Food Donors â†’ 3. Food Redistribution â†’ 4. Approve & Assign Routes
```

This effectively tells the operational story: check the fleet â†’ see available food â†’ understand where it goes â†’ assign routes.

**No changes needed** â€” this is well-designed and appropriate for an admin workflow dashboard.

---

## 8. Feature Mapping: Requirements Doc vs Prototype

Checking the requirements document against what's actually built:

| Requirement | Status in Prototype | Notes |
|-------------|-------------------|-------|
| **Donut chart** â€” food destination breakdown | Built (Panel 3) | SVG donut with 4 categories, working |
| **Gauge** â€” Network Efficiency % | Partially built | Shown as stat value "87%" in Panel 3, not a visual gauge. Acceptable. |
| **Ring** â€” On-Time Pickup Rate | Partially built | Shown as stat value "94%" in Panel 1, not a visual ring. Acceptable. |
| **Avg pickup time** (24 min) | Built (Panel 1) | Stat card with trend |
| **Lbs recovered today** (12,400) | Built (Panel 1) | With meal equivalent sub-text |
| **Meals equivalent** (10,333) | Built (Panel 1) | Using 1.2 lbs/meal formula |
| **CO2 avoided** (2.6 metric tons) | Built (Panel 1) | EPA lifecycle note |
| **14-day trend chart** | Built (Panel 1) | CSS bar chart, functional |
| **Driver Leaderboard** | Not built | Requirements say "top 15 drivers ranked by lbs transported." Prototype has "Fleet Distribution" (vehicle table) instead. Consider adding a driver table or merging. |
| **Food Type Breakdown** (bar chart) | Built (Panel 2) | 5 categories with colored bars |
| **Urgency Pipeline** (funnel) | Built (Panel 2) | 42 â†’ 38 â†’ 35 â†’ 33 funnel with drop-off % |

### Missing from requirements
- **Driver Leaderboard table**: The prototype has a vehicle fleet table but no driver performance table. The requirements specifically call for "Top 15 drivers ranked by lbs transported, with routes completed and on-time rate." This could be added to Panel 1 or as a 5th panel.

### Added beyond requirements
- **Food Donors panel** (Panel 2) with donor entity cards, contact buttons, urgency tags â€” not in the original requirements but valuable
- **Redistribution Recipients panel** (Panel 3) with recipient entity cards â€” not in requirements but valuable
- **Route Approval panel** (Panel 4) with route cards and dispatch button â€” extends beyond monitoring into operational action

These additions are good â€” they make the dashboard more operationally useful.

---

## 9. Implementation Steps

### Phase 1: File setup & structural alignment
1. Copy `fleet-analytics (1).html` â†’ `resources/Layers & Packages/fleet-analytics.html`
2. Fix logo to use local SVG path
3. Fix I2CE link URL and text
4. Fix nav link labels ("Campus Hub" not "GT Campus")
5. Standardize active nav class to `.active`
6. Remove `LIVE` badge or keep as fleet-analytics-only feature (decision point)

### Phase 2: Embed real ArcGIS maps
7. Add ArcGIS SDK CDN includes (`<link>` + `<script>`)
8. Add `/api/config` API key fetch (same pattern as other dashboards)
9. Replace Panel 1 "Live Fleet Map" placeholder with real `MapView`:
   - `dark-gray-vector` basemap
   - `GraphicsLayer` for mock vehicle positions (use real Atlanta coordinates)
   - Optionally pull in food recovery / redistribution GeoJSON layers
10. Replace Panel 4 "Route Preview" placeholder with real `MapView`:
    - Show route polylines and stop markers
    - Match surplus-map route styling (teal lines, gray numbered dots)
11. Handle lazy initialization â€” maps in hidden panels need init when panel becomes visible

### Phase 3: Add missing features
12. Add Driver Leaderboard table to Panel 1 (below the 14-day trend chart, or as a separate card)
    - Columns: Rank, Driver, Lbs Transported, Routes Completed, On-Time Rate
    - Mock data for 10â€“15 drivers
13. Consider adding gauge/ring visualizations for Network Efficiency and On-Time Rate (optional â€” current stat values work fine)

### Phase 4: Cross-page navigation
14. Add "Fleet Analytics" nav link to all existing pages:
    - `index.html`: add `<a href="fleet-analytics.html" class="navLink">Fleet Analytics</a>`
    - `surplus-map.html`: add same
    - `gt-campus-hub.html`: add same
15. Ensure consistent nav order: AFCN Dashboard | Surplus Map | Fleet Analytics | Campus Hub

### Phase 5: Testing
16. Test with `python serve.py` at `http://localhost:8080/resources/Layers%20%26%20Packages/fleet-analytics.html`
17. Verify API key loads and maps render
18. Verify all 4 panels switch correctly
19. Verify nav links work between all 4 pages
20. Test responsive behavior at â‰¤960px

---

## 10. Open Questions for Stakeholder

1. **Driver Leaderboard**: Should this show named mock drivers (as in requirements), or is the current vehicle-focused table sufficient?

2. **Map depth**: How interactive should the embedded maps be? Options:
   - (a) Static view with plotted points (fast to implement, ~same as prototype but with real geography)
   - (b) Interactive with popups, zoom, layer toggling (matches the AFCN dashboard experience)
   - (c) Live-updating with simulated vehicle movement (ambitious but compelling for demos)

3. **Chart library**: The trend chart and category bars are currently pure CSS. Should we use Chart.js (already loaded in gt-campus-hub.html) for more polished charts with tooltips, animations, and hover states?

4. **Real-time simulation**: The "LIVE" badge implies real-time data. Should we add a mock data refresh timer (e.g., randomize stats every 30 seconds) to simulate live operations for demos?

5. **Page placement**: Should `fleet-analytics.html` live in `resources/Layers & Packages/` alongside the other dashboards, or at the project root where the current prototype sits?

---

## 11. File Dependency Map

```
fleet-analytics.html (new)
â”œâ”€â”€ ArcGIS Maps SDK 4.30 (CDN)
â”œâ”€â”€ /api/config (API key from serve.py)
â”œâ”€â”€ /resources/GT logo/... (local logo SVG)
â”œâ”€â”€ /geojson/food_recovery_sources.geojson (optional, for map overlay)
â”œâ”€â”€ /geojson/redistribution_nodes.geojson (optional, for map overlay)
â””â”€â”€ Links to:
    â”œâ”€â”€ index.html (AFCN Dashboard)
    â”œâ”€â”€ surplus-map.html (Surplus Map)
    â””â”€â”€ gt-campus-hub.html (Campus Hub)
```

---

## 12. Summary of Changes from Prototype

| Change | Type | Effort |
|--------|------|--------|
| Replace 2 CSS map placeholders with ArcGIS MapViews | Critical | Medium |
| Fix logo source to local SVG | Quick fix | Low |
| Fix I2CE link URL and text | Quick fix | Low |
| Fix nav labels ("Campus Hub") | Quick fix | Low |
| Standardize `.active` class | Quick fix | Low |
| Add ArcGIS SDK loading + API key fetch | Integration | Low |
| Handle lazy map init for hidden panels | Technical | Medium |
| Add Driver Leaderboard table | New feature | Medium |
| Add Fleet Analytics link to 3 existing pages | Cross-page | Low |
| Move file to `resources/Layers & Packages/` | File ops | Low |



