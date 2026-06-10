---
name: afcn-dashboard-agent
description: >
  Use this skill whenever working on AFCN dashboard files: index.html,
  surplus-map.html, gt-campus-hub.html, fleet-analytics.html. Covers ArcGIS
  SDK 4.30 patterns, data integration, UI changes, adding layers, updating mock
  data, fixing routing, and all frontend work on the AFCN platform.
---

# AFCN Dashboard Agent

You are the AFCN Dashboard Developer. You know this codebase inside-out and
follow its conventions exactly. Never introduce build steps, package.json, or
frameworks — all files are single-file inline HTML/CSS/JS.

---

## Project Layout

```
resources/Layers & Packages/
├── index.html          Main AFCN map (citywide + GT campus mode)
├── surplus-map.html    Real-time surplus pins + route optimizer (STANDALONE)
├── gt-campus-hub.html  GT Campus Hub dashboard
└── fleet-analytics.html Fleet operations dashboard

geojson/                30 GeoJSON files — campus_dining, food_recovery_sources,
                        redistribution_nodes, beneficiary_access_points,
                        circular_economy, network_flows, buildings, sidewalks, etc.

Python Script/
├── serve.py            Dev server: python serve.py → http://localhost:8080
└── publish_dashboards.py  Static bundle builder

.env                    ARCGIS_API_KEY=AAPK...  (never commit)
data/leanpath_surplus.js  Real LeanPath MOCK_SURPLUS + MOCK_FLEET (drop-in)
```

Dev URL: `http://localhost:8080/resources/Layers%20%26%20Packages/index.html`
Surplus: `http://localhost:8080/resources/Layers%20%26%20Packages/surplus-map.html`

---

## ArcGIS SDK Patterns

### Module Loading (AMD require — always this pattern)
```javascript
require([
  "esri/config",
  "esri/Map",
  "esri/views/MapView",
  "esri/layers/GeoJSONLayer",
  "esri/layers/GraphicsLayer",
  "esri/Graphic",
  "esri/geometry/Point",
  "esri/rest/route",
  "esri/rest/support/RouteParameters",
  "esri/rest/support/Stop",
], function(esriConfig, Map, MapView, GeoJSONLayer, GraphicsLayer,
            Graphic, Point, route, RouteParameters, Stop) {
  // ALL code inside this callback
});
```

### API Key (fetched from serve.py, never hardcoded)
```javascript
fetch('/api/config')
  .then(r => r.json())
  .then(cfg => { esriConfig.apiKey = cfg.apiKey; })
  .catch(() => showApiKeyNotice());
```

### Adding a GeoJSONLayer
```javascript
const myLayer = new GeoJSONLayer({
  url: "../../geojson/redistribution_nodes.geojson",
  renderer: { type: "simple", symbol: { type: "simple-marker", color: [0,191,165], size: 8 }},
  popupTemplate: { title: "{name}", content: "{address}" }
});
map.add(myLayer);
```

### GraphicsLayer (for surplus pins, routes)
```javascript
const surplusLayer = new GraphicsLayer();
map.add(surplusLayer);

// Add a graphic
surplusLayer.add(new Graphic({
  geometry: new Point({ longitude: -84.3918, latitude: 33.7716 }),
  symbol: { type: "simple-marker", color: [239,83,80], size: 14, outline: { color: "white", width: 1 }},
  attributes: { id: 1, name: "North Ave", urgency: "Critical" },
  popupTemplate: { title: "{name}", content: "Urgency: {urgency}" }
}));
```

### Routing (ArcGIS Route Service)
```javascript
const routeUrl = "https://route-api.arcgis.com/arcgis/rest/services/World/Route/NAServer/Route_World";

const stops = new FeatureSet({ features: coords.map(([lng, lat]) =>
  new Graphic({ geometry: new Point({ longitude: lng, latitude: lat }) })
)});

const params = new RouteParameters({
  stops,
  returnDirections: true,
  startTime: new Date()  // enables live traffic
});

route.solve(routeUrl, params)
  .then(result => { /* result.routeResults[0].route */ })
  .catch(() => drawFallbackGeodesicLine()); // always implement fallback
```

---

## surplus-map.html — Key Constants (replace these with real data)

### MOCK_SURPLUS schema
```javascript
const MOCK_SURPLUS = [
  {
    id: 1,
    name: "North Ave Dining Hall",
    lng: -84.3918, lat: 33.7716,
    food_type: "Prepared Meals",     // Prepared Meals | Packaged Goods | Produce | Bakery | Perishable
    quantity_lbs: 63.8,
    expiration: "2026-03-11T02:00:00",
    urgency: "Critical",             // Critical | Soon | Stable
    transport: "Refrigerated Van",   // Refrigerated Van | Dry Vehicle | Bike Courier
    source_category: "GT Campus",
    notes: "Overproduction · Rice, Beans · International, Mindful Bites",
    cost_usd: 39.68,
    leanpath_category: "Starch"      // raw LeanPath food category
  }
];
```

### MOCK_FLEET schema
```javascript
const MOCK_FLEET = {
  activeDrivers: 38,
  refrigeratedVehicles: 8,
  avgPickupMin: 24,
  lbsTodayRecovered: 281,
  lbsWeekRecovered: 2316,
  donationRatePct: 3.5,
  costAtRisk: 2380,
  topLocation: "North Ave Dining Hall",
  topLocationLbs: 1632
};
```

### Urgency scoring (do not change weights without updating CLAUDE.md)
```javascript
const SCORING_WEIGHTS = { URGENCY: 0.50, VOLUME: 0.30, DISTANCE: 0.20 };
function computePriorityScore(item, originLng, originLat, vehicleLevel) {
  const hoursLeft = (new Date(item.expiration) - new Date()) / 3600000;
  if (hoursLeft <= 0 || !isTransportCompatible(item.transport, vehicleLevel)) return -1;
  const urgencyScore  = 100 * Math.exp(-0.5 * hoursLeft);
  const volumeScore   = Math.min(100, 20 * Math.log10(item.quantity_lbs + 1));
  const dist          = getDistance(item.lng, item.lat, originLng, originLat);
  const proximityScore = 100 / (1 + dist);
  return SCORING_WEIGHTS.URGENCY * urgencyScore
       + SCORING_WEIGHTS.VOLUME  * volumeScore
       + SCORING_WEIGHTS.DISTANCE * proximityScore;
}
```

### Transport hierarchy
```javascript
const TRANSPORT_HIERARCHY = {
  "Refrigerated Van": 4, "Dry Vehicle": 3, "Bike Courier": 2, "Walk-in": 1
};
function isTransportCompatible(required, vehicleType) {
  return TRANSPORT_HIERARCHY[vehicleType] >= TRANSPORT_HIERARCHY[required];
}
```

---

## Design System

| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#07090f` | Page background |
| `--surface` | `#111722` | Cards, panels |
| `--teal` | `#00bfa5` | Primary accent, route lines |
| `--critical` | `#ef5350` | Urgency Critical |
| `--soon` | `#ffc107` | Urgency Soon |
| `--stable` | `#66bb6a` | Urgency Stable |
| `--muted` | `#5a6a7e` | Secondary text |
| Font | Segoe UI / system-ui | All text |

**Pin sizing:** small <50lbs=10px, medium 50–200=14px, large 200+=18px
**Critical pins only** get pulse animation — not Soon or Stable
**Route line:** solid teal #00bfa5 width 4, glow underlay width 8 opacity 0.3

---

## gt-campus-hub.html — Key Mock Data

### ADMIN_DATA
```javascript
const ADMIN_DATA = {
  todayRecovered: 281,     // ← update from LeanPath lbs TODAY
  weeklyRecovered: 2316,   // ← update from LeanPath 7-day total
  donationRate: 3.5,       // ← real: 80/2316 = 3.5%
  costSaved: 2380,         // ← real: 7-day cost wasted
  volunteers: 24,
  activeRoutes: 6
};
```

---

## Workflow for Code Changes

1. **Read the relevant section of the file first** — never assume structure
2. **Make targeted edits** — avoid rewriting whole files; use str_replace
3. **Never add `<script src>` for external libs** — only ArcGIS CDN AMD modules
4. **Test flow:** `cd "Python Script" && python serve.py` → open in browser
5. **After any MOCK_SURPLUS change:** verify counts in filter panel update correctly
6. **After any routing change:** test both API-key path AND geodesic fallback path

---

## Common Tasks

### Swap in real LeanPath surplus data
Replace `const MOCK_SURPLUS = [...]` in surplus-map.html with contents of
`data/leanpath_surplus.js`. Run `updateSurplusCounts()` after any data change.

### Add a new surplus filter type
1. Add checkbox in `#layerPanel` with `data-surplus="NewType"`
2. Add color entry in `FOOD_TYPE_COLORS`
3. `renderSurplusLayer()` already reads all `data-surplus` checkboxes dynamically

### Update fleet stats in surplus map
Edit `MOCK_FLEET` constant. `populateFleetPanel()` reads all fields automatically.

### Add a new GeoJSON layer to index.html
1. Place `.geojson` in `geojson/`
2. Define `GeoJSONLayer` with renderer + popupTemplate
3. Add checkbox in `#layerPanel` appropriate group
4. Wire visibility toggle in mode/tab JS logic
5. Add to `updateStatsRail()` for feature count

### Modify urgency scoring weights
Edit `SCORING_WEIGHTS` — but also update `CLAUDE.md` Design Decisions section.
