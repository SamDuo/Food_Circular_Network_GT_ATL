# Real-Time Food Surplus Map + Logistics Optimizer — Implementation Plan
5 only need fridged truck fleet lougistic optimizetion 
## Problem Statement

Food surplus at GT campus dining halls and Atlanta restaurants expires before it reaches people in need. There is no visibility into what's available, how urgent pickup is, or what vehicle type is needed. Dispatchers and volunteer drivers operate blind — leading to wasted food, missed pickups, and inefficient routing.

## Solution

An intelligence layer overlaid on the existing AFCN dashboard that provides:

1. **Live Surplus Pins** — every active food surplus report on the map, color-coded by urgency (Critical / Soon / Stable), sized by quantity, filterable by food type (Prepared Meals, Packaged Goods, Produce, Bakery, Perishable <6hrs)
2. **Route Optimizer Panel** — starting from GT North Avenue Dining Hall, calculate the optimal circular chain route (Source → Shelter → Pantry → Compost) using real-time road network and live traffic data

**Target Users:** Campus food recovery coordinators, volunteer drivers, AFCN dispatchers

**Key Interactions:** Filter by food type → click a pin to see details + expiration countdown → click "Route From Here" to auto-plan an optimized pickup route

## Confirmed Decisions
- API Key: User HAS an ArcGIS API key — build with real routing + fallback
- Pin spread: All Atlanta (~12 GT campus + ~18 citywide)
- UI mode: Overlay on existing City/Campus modes (not a separate mode)
- Origin point: North Avenue Dining Hall at `[-84.3918, 33.7716]`

---

## Design Inspiration (Research Summary)

> Full research notes with detailed platform analyses available in [`Design Research Notes.md`](Design%20Research%20Notes.md)

### Food Rescue Platforms (MealConnect, Too Good To Go, Food Rescue US)
- Min **24px pins** — Too Good To Go's tiny dots are a known UX failure
- Pair color with **icons + text labels** — never rely on color alone (accessibility)
- **Map + List split view** — let users browse as list OR on map
- **"Available Rescues"** tab pattern — task-focused, not data-focused
- Include **photos** of available food in popups (builds trust)

### Logistics Dashboards (Onfleet, Circuit, Route4Me, Routific)
- **Drag-reorderable stop list** with numbered sequence and six-dot handles
- **Two-way binding** — click list item = zoom to marker, click marker = highlight in list
- **Stats cards**: Distance, Duration, Cost, Savings % (max 4-6 primary metrics)
- **Polyline**: 3-5px solid, traffic-aware coloring (green/yellow/red segments)
- **Progressive disclosure**: Show essential controls first, hide advanced settings

### Real-Time Map Dashboards (ArcGIS Ops, Kepler.gl, PulsePoint, Waze)
- Dark theme base: `#1a1a1a` NOT pure black (causes eye strain / halation)
- **Pulse animation only for critical** urgency — not all pins
- **Glow/halo effect** via `filter: drop-shadow()` for real-time overlay pop
- ArcGIS **blend mode `lighten`** for overlay data against dark basemap
- **Live indicator**: pulsing green dot + "Updated 2s ago" ticker
- Confidence scoring: higher opacity = more reliable data

### Surplus Inventory UIs (Leanpath, Winnow, Wasteless, Flashfood, OLIO)
- **Card hierarchy**: Urgency badge → Name + Quantity → Location → Action button
- **Dual units**: "25 lbs (~15 servings)" not just weight alone
- Expiration countdown: **color progression** green → yellow → orange → red
- **Impact gamification**: lbs diverted, CO2 avoided, meals served
- Transport requirements as **icon row**: refrigerated / fragile / pickup-only

---

## File to Modify

**Single file:** `resources/Layers & Packages/index.html` (all CSS/HTML/JS inline)

**Reference data files (read-only):**
- `geojson/campus_dining.geojson` — 12 GT dining locations (origin candidates)
- `geojson/food_recovery_sources.geojson` — 11,314 food recovery points
- `geojson/redistribution_nodes.geojson` — 2,629 redistribution points
- `geojson/beneficiary_access_points.geojson` — 17 beneficiary points
- `geojson/circular_economy.geojson` — 127 circular economy points
- `geojson/network_flows.geojson` — 12 flow LineStrings with lbs_per_week

---

## Part 1: Real-Time Surplus Map (Mock Data Layer)

### 1A. Mock Surplus Data Generation

Generate ~30 mock surplus entries inline in JS, using **real coordinates** from existing layers. Each entry represents a food surplus report with these fields:

```js
const MOCK_SURPLUS = [
  {
    id: 1,
    name: "North Ave Dining Hall",
    lng: -84.3918, lat: 33.7716,
    food_type: "Prepared Meals",         // filter category
    quantity_lbs: 120,
    expiration: "2026-02-27T14:00:00",   // ISO timestamp
    urgency: "Critical",                 // Critical | Soon | Stable
    transport: "Refrigerated Van",       // Refrigerated Van | Dry Vehicle | Bike Courier | Walk-in
    source_category: "GT Campus",
    notes: "Post-lunch surplus, needs pickup by 2pm"
  },
  // ... 29 more entries spread across Atlanta
];
```

**Source locations for mock data (use real coords from existing layers):**
- 12 GT campus dining locations → Prepared Meals, Bakery
- ~8 food recovery sources (restaurants in Atlanta) → Prepared Meals, Packaged Goods
- ~5 redistribution nodes → Produce, Perishable
- ~5 circular economy locations → Produce, Bakery

**Urgency logic based on expiration time:**
- Critical (red) = expires within 2 hours
- Soon (yellow) = expires within 6 hours
- Stable (green) = expires in 6+ hours

### 1B. Surplus Filter Panel (Left Side)

Add a new section inside the existing `#layerPanel` sidebar, under a new group title "Real-Time Surplus Filters":

```
┌─ Real-Time Surplus ──────────┐
│ [x] Prepared Meals     (14)  │
│ [x] Packaged Goods      (6)  │
│ [x] Produce              (4) │
│ [x] Bakery               (3) │
│ [x] Perishable < 6hrs   (3)  │
│                               │
│ Total: 1,840 lbs available   │
│ Critical: 5 pickups needed   │
└───────────────────────────────┘
```

HTML to add inside `<aside id="layerPanel">` after the GT Base Map group:

```html
<div class="groupTitle" style="color:#ffc107">Real-Time Surplus</div>
<label class="layerRow">
  <input type="checkbox" data-surplus="Prepared Meals" checked />
  <span class="dot" style="background:#ef5350"></span>
  <span>Prepared Meals <small id="countPrepared" style="color:var(--muted)"></small></span>
</label>
<label class="layerRow">
  <input type="checkbox" data-surplus="Packaged Goods" checked />
  <span class="dot" style="background:#42a5f5"></span>
  <span>Packaged Goods <small id="countPackaged" style="color:var(--muted)"></small></span>
</label>
<label class="layerRow">
  <input type="checkbox" data-surplus="Produce" checked />
  <span class="dot" style="background:#66bb6a"></span>
  <span>Produce <small id="countProduce" style="color:var(--muted)"></small></span>
</label>
<label class="layerRow">
  <input type="checkbox" data-surplus="Bakery" checked />
  <span class="dot" style="background:#ffa726"></span>
  <span>Bakery <small id="countBakery" style="color:var(--muted)"></small></span>
</label>
<label class="layerRow">
  <input type="checkbox" data-surplus="Perishable" checked />
  <span class="dot" style="background:#ec407a"></span>
  <span>Perishable &lt;6hrs <small id="countPerishable" style="color:var(--muted)"></small></span>
</label>
<div id="surplusSummary" style="margin-top:8px;padding:6px;background:#141924;border-radius:6px;font-size:11px;color:var(--muted)"></div>
```

### 1C. Surplus GraphicsLayer with Custom Symbols

Create a `GraphicsLayer` populated from `MOCK_SURPLUS`. Each pin uses:

- **Color** by urgency: Critical=#ef5350, Soon=#ffc107, Stable=#66bb6a
- **Size** by quantity: small (<50 lbs)=10px, medium (50-200)=14px, large (200+)=18px
- **Icon shape** by food type: circle for all (simple-marker), differentiated by color ring

**Popup template** for each surplus pin:

```
┌─────────────────────────────┐
│ North Ave Dining Hall       │
│ ─────────────────────────── │
│ Food Type:  Prepared Meals  │
│ Quantity:   120 lbs         │
│ Expires:    2:00 PM (1h 23m)│
│ Urgency:    ● Critical      │
│ Transport:  Refrigerated Van│
│ Notes:      Post-lunch...   │
│                             │
│ [Route From Here]           │
└─────────────────────────────┘
```

The popup uses a custom HTML content function that calculates remaining time dynamically.

### 1D. Filter Logic

When surplus filter checkboxes change:
1. Read checked food types from `input[data-surplus]` checkboxes
2. Loop through surplus graphics, set `graphic.visible` based on matching food_type
3. Update count badges and summary stats

### 1E. New CSS Variables

```css
--surplus-critical: #ef5350;
--surplus-soon: #ffc107;
--surplus-stable: #66bb6a;
```

---

## Part 2: Logistics Optimization Panel (Route Optimizer)

A dispatch-grade logistics optimizer with urgency-aware routing, fleet intelligence, and AI-suggested route planning.

### 2A. Panel UI — Collapsible Right Panel

`<aside id="routePanel">` positioned on the right side, toggled by a floating button.

```
┌── LOGISTICS OPTIMIZER ──── [x] ─┐
│                                   │
│ ┌─ FLEET STATUS ────────────────┐│
│ │  38       8      24 min 12,400││
│ │Active  Refrig  Avg Pick lbs/d ││
│ └───────────────────────────────┘│
│                                   │
│ ┌─ AI SUGGESTED ROUTE ──────────┐│
│ │ North Ave → Chipotle → CVI → ││
│ │ West Village → GT Recovery    ││
│ │ Time Saved: 37%  Food: 480lbs ││
│ │ [Accept Plan]      [Dismiss]  ││
│ └───────────────────────────────┘│
│                                   │
│ Origin                            │
│ [North Ave Dining Hall      v]    │
│ Vehicle Type                      │
│ [Refrigerated Van           v]    │
│                                   │
│ Route Chain                       │
│ ● 1. Recovery     [smart pri v]  │
│ ● 2. Redistrib.   [capacity  v]  │
│ ● 3. Beneficiary  [capacity  v]  │
│ ● 4. Compost      [nearest   v]  │
│                                   │
│ [Smart Auto-Select]               │
│ [====  OPTIMIZE ROUTE  ====]      │
│ [Clear]                           │
│                                   │
│ ┌─────────┬──────────┐            │
│ │Distance │ Time     │            │
│ │ 8.3 mi  │ 24 min   │            │
│ ├─────────┼──────────┤            │
│ │Volume   │ Saved    │            │
│ │3200 lbs │ 37%      │            │
│ └─────────┴──────────┘            │
│                                   │
│ Leg Breakdown:                    │
│ ─ Origin → Chipotle     2.1 mi   │
│ ─ Chipotle → CVI        3.4 mi   │
│ ─ CVI → West Village    1.8 mi   │
│ ─ West Village → Compost 1.0 mi  │
│                                   │
│ CRITICAL pickup: 80 lbs — 2.0h   │
│ Transport: Refrigerated Van       │
│                                   │
│ [Open in Google Maps]             │
└───────────────────────────────────┘
```

**Position:** `absolute; top: var(--header-h); right: 0; width: 360px; z-index: 27`
**Toggle button:** Circular button at `right: 12px; bottom: 88px`

### 2B. Fleet Intelligence Panel

Mock fleet data displayed at the top of the route panel:

| Metric | Value | Description |
|--------|-------|-------------|
| Active Drivers | 38 | Drivers currently on shift |
| Refrigerated Vehicles | 8 | Cold-chain capable vehicles |
| Avg Pickup Time | 24 min | Mean time per pickup stop |
| lbs Recovered Today | 12,400 | Running daily total |

Data source: `MOCK_FLEET` constant (will connect to real fleet API in production).

### 2C. AI Suggested Route

On page load, the system runs the urgency-aware algorithm and displays a recommendation:

1. Scores all surplus items by `priority = (0.50 × urgency) + (0.30 × volume) + (0.20 × proximity)`
2. Filters by vehicle transport compatibility
3. Selects redistribution/beneficiary nodes by capacity availability
4. Displays chain with time saved % and food-at-risk lbs
5. **Accept Plan** → populates dropdowns and triggers route calculation
6. **Dismiss** → hides the suggestion card
7. Re-generates when origin or vehicle type changes

### 2D. Urgency-Aware Scoring (Smart Auto-Select)

Replaces the old greedy nearest-neighbor with a weighted scoring system:

```
priority_score = (0.50 × urgency_decay) + (0.30 × volume_score) + (0.20 × proximity_score)

urgency_decay  = 100 × e^(-0.5 × hours_remaining)  // exponential cliff at <1hr
volume_score   = min(100, 20 × log10(lbs + 1))      // diminishing returns above 500 lbs
proximity_score = 100 / (1 + distance_miles)
```

**Scoring examples:**
| Item | Hours Left | Lbs | Distance | Score | Selected? |
|------|-----------|-----|----------|-------|-----------|
| Chipotle (Critical) | 0.5h | 200 | 3 mi | ~52 | YES |
| Moe's (Stable) | 12h | 30 | 0.5 mi | ~15 | No |
| Alibaba's (Critical) | 0.8h | 40 | 1 mi | ~40 | No |

### 2E. Transport Compatibility

Vehicle type selector in the route panel. Hierarchy:

| Vehicle Capability | Can Handle |
|-------------------|-----------|
| Refrigerated Van (level 4) | All transport types |
| Dry Vehicle (level 3) | Dry Vehicle, Bike Courier, Walk-in |
| Bike Courier (level 2) | Bike Courier, Walk-in |

During smart selection, surplus items requiring transport above the vehicle's capability are filtered out.

### 2F. Storage Capacity at Destination

Redistribution and beneficiary nodes now have capacity fields:

| Field | Type | Description |
|-------|------|-------------|
| `cold_pct` | 0-100 | Cold storage usage percentage |
| `dry_pct` | 0-100 | Dry storage usage percentage |
| `accepting_perishable` | bool | Whether node accepts perishable items |

**Capacity scoring:**
- Nodes >90% cold storage get -50 penalty
- Nodes >90% dry storage get -30 penalty
- `accepting_perishable: false` nodes are skipped when carrying perishable loads
- Dropdown labels show capacity: `"American Stroke Assoc. [92%]"`

### 2G. Traffic-Aware Routing

`RouteParameters` includes `startTime: new Date()` which enables the ArcGIS route service to use live traffic data for travel time estimates.

### 2H. Route Display

- **Route line:** solid teal (#00bfa5, width 4) with faint underlay (width 8, 30% opacity)
- **Stop markers:** uniform teal circles with white number labels
- **Urgency context:** colored badge below leg breakdown showing pickup urgency, lbs, time remaining, and transport type
- **Zoom:** `view.goTo(routeGeometry.extent.expand(1.3))`

### 2I. Surplus Pin Integration

The "Route From Here" button in surplus pin popups will:
1. Set that surplus location as the route origin
2. Open the route panel
3. Run smart auto-select (urgency-aware, capacity-aware)
4. Trigger route calculation

---

## Part 3: Implementation Steps (Ordered)

### Step 1: CSS Additions (~100 lines)
Add inside existing `<style>` block before closing `</style>`:
- New CSS variables (surplus colors, route colors, panel width)
- `#routeToggle` button styles
- `#routePanel` and all `.rp-*` sub-component styles
- Surplus summary card styles
- Loading spinner animation
- Mobile responsive rules for route panel

### Step 2: HTML — Surplus Filters (~20 lines)
Add inside `<aside id="layerPanel">` after the GT Base Map group (after line 396):
- New group title "Real-Time Surplus"
- 5 food type filter checkboxes with count badges
- Summary stats div

### Step 3: HTML — Route Panel (~70 lines)
Add after `<nav id="dock"></nav>` (after line 399):
- Route toggle button
- `<aside id="routePanel">` with:
  - Header with close button
  - API key notice (hidden by default)
  - Origin dropdown
  - 4 chain stop dropdowns with category dots
  - Auto-select button
  - Optimize / Clear buttons
  - Results grid (distance, time, volume, saved)
  - Leg breakdown container
  - Directions toggle
  - Loading spinner

### Step 4: JS — Expand require() modules (line 423)
Add 9 new AMD modules: route, RouteParameters, Stop, FeatureSet, GraphicsLayer, Graphic, Point, geometryEngine, esriConfig

### Step 5: JS — Mock Surplus Data (~80 lines)
Define `MOCK_SURPLUS` array with 30 entries using real coordinates from existing layers. Add surplus GraphicsLayer to map.

### Step 6: JS — Surplus Filter Logic (~40 lines)
- `renderSurplusLayer()` — creates/updates graphics from MOCK_SURPLUS
- `filterSurplus()` — reads checkbox state, toggles graphic visibility
- `updateSurplusCounts()` — updates badge counts and summary

### Step 7: JS — Route Panel Logic (~200 lines)
- API key management (localStorage)
- `loadDestinationOptions()` — query layers, populate dropdowns
- `autoSelectNearest()` — greedy nearest-neighbor
- `calculateRoute()` — real routing or fallback
- `displayResults()` — populate stats grid and leg breakdown
- `drawRouteOnMap()` / `drawStopMarkers()` — route graphics
- Event wiring: toggle, optimize, clear, directions, surplus "Route From Here"

### Step 8: JS — Wire surplus filters to checkbox events
Connect `input[data-surplus]` change events to `filterSurplus()`

---

## Verification Plan

1. **Start server:** `cd "Python Script" && python serve.py`
2. **Open dashboard:** `http://localhost:8080/resources/Layers%20%26%20Packages/index.html`
3. **Check surplus pins:** Colored pins should appear on map, popup shows all 6 fields
4. **Test filters:** Uncheck "Prepared Meals" — those pins should disappear, counts update
5. **Open route panel:** Click route toggle button on right side
6. **Test auto-select:** Click "Auto-Select Nearest" — all 4 dropdowns should fill
7. **Test route (no API key):** Click "Optimize" — dashed lines appear, stats show "(est.)"
8. **Test route (with API key):** Paste ArcGIS API key, click Save, re-optimize — solid road-following polyline appears with real travel time
9. **Test mobile:** Resize browser to <760px — route panel should become bottom sheet
10. **Test surplus → route:** Click a surplus pin, click "Route From Here" — route panel opens with that location as origin

---

## Estimated Size Impact

| Component | Lines Added |
|-----------|-------------|
| CSS | ~100 |
| HTML (surplus filters) | ~20 |
| HTML (route panel) | ~70 |
| JS (mock data) | ~80 |
| JS (surplus logic) | ~40 |
| JS (route logic) | ~200 |
| **Total** | **~510 lines** |

Final file size: ~1,390 lines (from current 878)


