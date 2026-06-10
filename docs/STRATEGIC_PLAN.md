# AFCN Matrix Atlas — Strategic Plan
> Companion to `Mapping Types Status May 4, 2026.xlsx` (supervisor brief) and
> `docs/MAPPING_MATRIX.md` (coverage scorecard).
> Goal: ship a complete **7×6 matrix-of-maps atlas** for Atlanta — 7 subsystems
> (Demographics, Food, Transportation, Infrastructure, Health, Land Use,
> Social Systems) × 6 analytical lenses (Base, Density, Accessibility, Equity,
> Trend, Flow) — plus a Typology synthesis layer.

---

## 1. Executive summary

| | |
|---|---|
| **Scope** | 42 matrix cells + 1 capstone typology layer = **43 maps** |
| **Existing coverage** | ~50% of subsystems have base layers; ~6 derived analytical maps already exist |
| **Tech direction** | Add a parallel **Matrix Atlas** page using **MapLibre GL JS + deck.gl + Observable Plot + Turf.js + OpenTripPlanner** alongside the existing ArcGIS Maps SDK dashboard (no rewrite) |
| **Timeline** | 6 sprints × 1 week each = 6 weeks to full atlas |
| **Headline deliverable** | `geojson/atl_typology_classified.geojson` — every Atlanta tract classified into one of the 5 supervisor-named typologies |

---

## 2. Style reference — supervisor's 6 sample images → library mapping

The Excel embedded 6 sample maps. Each one is a worked example of one of the
6 analytical lenses. Style decisions below reference these directly.

| Image | Map type shown | Matches matrix cell | Recommended library |
|---|---|---|---|
| 1 — LA heatmap with red point overlay | **Density / Intensity** (kernel density of facilities) | Food×Density, Health×Density | **Mapbox/MapLibre `heatmap-layer`** (built-in, GPU) or **deck.gl `HeatmapLayer`** |
| 2 — Chicago Accessibility Explorer (side-by-side travel-time choropleth) | **Accessibility / Proximity** (isochrone-based travel time choropleth) | Food×Accessibility, Health×Accessibility | **OpenTripPlanner** (multimodal) or **Valhalla** (HTTP API) for isochrones, MapLibre for rendering |
| 3 — DC three-panel transport (roads / public-transit / overlay) | **Network / Flow** (categorical line + multi-modal compare) | Transport×Base, Transport×Flow | **MapLibre GL JS** with synced viewports, categorical `line-color` from `route_type` |
| 4 — Seattle/LA obesity choropleth (multi-city) | **Equity / Disparity** (sequential blue ramp) | Health×Equity, Demographics×Equity | **Observable Plot** (static, paper-quality) + **D3** (interactive) |
| 5 — Salt Lake City UrbanFootprint zoning | **Base Distribution** (categorical zoning) | Land Use×Base | **MapLibre + vector tiles** (UrbanFootprint runs on this stack) |
| 6 — NYC vacant lots + community gardens | **Network / Flow** (point + polygon multi-layer with green palette) | Land Use×Density, Land Use×Flow | **MapLibre GL JS** layered approach |

### Why this stack and not the existing ArcGIS

| Requirement | ArcGIS Maps SDK (current) | MapLibre + deck.gl (proposed for atlas) |
|---|---|---|
| Cost | Paid API key, monthly limits | Free, OSS |
| Code-style | AMD modules via CDN | ES modules + npm or CDN |
| Heatmap quality | Good | Better (GPU-accelerated WebGL) |
| Custom shaders / 3D | Limited | Full WebGL access |
| Open-data integration | Strong (Esri Hub) | Strong (any GeoJSON / vector tile / PMTiles) |
| Already in repo | ✅ Map View dashboard | New |

**Decision: keep the ArcGIS Map View as the public flagship** (it's done, it
loads fast, the API key is wired). Add a sibling **Matrix Atlas** page in
`atlas/` that uses MapLibre + deck.gl for the systematic 42-cell matrix. The
two coexist via the existing topbar nav (Map View / Network View / Story /
Atlas).

**Sources:** [deck.gl docs](https://deck.gl/) ·
[Mapbox heatmap example](https://docs.mapbox.com/mapbox-gl-js/example/heatmap-layer/) ·
[kepler.gl polygon layer](https://docs.kepler.gl/docs/user-guides/c-types-of-layers) ·
[OpenTripPlanner accessibility](https://xang1234.github.io/isochrone/) ·
[Valhalla isochrones](https://valhalla.github.io/valhalla/) ·
[Bivariate choropleth best practice (School of Cities)](https://schoolofcities.github.io/urban-data-storytelling/urban-data-visualization/bivariate-choropleth-maps/bivariate-choropleth-maps.html) ·
[Joshua Stevens bivariate guide](https://www.joshuastevens.net/cartography/make-a-bivariate-choropleth-map/)

---

## 3. Architecture — the Matrix Atlas page

```
atlas/
├── index.html         ← landing page: 7 subsystem rows × 6 lens cards = grid of 42 thumbnails
├── viewer.html        ← detail page: full-screen map for one cell, takes ?row=health&lens=equity
├── style.css          ← shared theme (matches network/style.css cream + serif headers)
├── app.js             ← MapLibre + deck.gl init, layer registry, lens routing
├── lenses/            ← one module per analytical lens
│   ├── base.js
│   ├── density.js
│   ├── accessibility.js
│   ├── equity.js
│   ├── trend.js
│   └── flow.js
├── typology.html      ← capstone — colored classified-tract map of the 5 typologies
└── data-manifest.json ← maps each (row, lens) cell to its GeoJSON source(s)
```

**Layer registry pattern** — `data-manifest.json` is the single source of truth:
```json
{
  "demographics:base":          { "src": "geojson/atl_demographics_acs.geojson",  "field": "B01003_001E" },
  "demographics:density":       { "src": "geojson/atl_demographics_acs.geojson",  "field": "pop_density" },
  "demographics:equity":        { "src": "geojson/atl_demographics_acs.geojson",  "field": "income_gini" },
  "food:base":                  { "src": "geojson/all_food_pantries_atl.geojson + grocery + ...", "merge": true },
  "food:density":               { "src": "geojson/map1_food_retail_density.geojson", "field": "kde" },
  "food:accessibility":         { "src": "geojson/map2_food_access_distance.geojson", "field": "min_distance" },
  "food:equity":                { "src": "geojson/atl_pro_food_deserts.geojson",      "field": "lila" },
  "health:density":             { "src": "geojson/cdc_places_atl.geojson",            "field": "OBESITY_CrudePrev" },
  ...
}
```

`viewer.html` reads `?row=&lens=` from URL, looks up the manifest, applies the
correct lens module, and renders. Adding a new cell = adding one row to the
manifest. Zero special-casing.

---

## 4. Phased build plan (6 sprints × 1 week)

### Sprint 1 — Demographics ACS join (the big unlock)
- **`scripts/fetch_acs.py`** — pull 2022 ACS 5-year tables for state=GA, counties=Fulton/DeKalb/Cobb/Gwinnett/Clayton/Cherokee/Henry. Variables: B19013 (median income), B02001 (race), B01001 (age × sex), B15003 (education), B25010 (household size), B08301 (commute mode).
- Join onto `census_tracts_tiger.geojson` → output `geojson/atl_demographics_acs.geojson` (530 polygons, ~25 properties each).
- **Deliverable:** 6 demographic rows × 6 lenses = **36 maps unlocked** from one fetch.

### Sprint 2 — Health (CDC PLACES)
- **`scripts/fetch_cdc_places.py`** — pull tract-level prevalence for obesity (`OBESITY_CrudePrev`), diabetes (`DIABETES_CrudePrev`), depression (`DEPRESSION_CrudePrev`), poor mental health (`MHLTH_CrudePrev`), poor physical health, lack of insurance.
- Join onto `census_tracts_tiger.geojson` → `geojson/atl_health_places.geojson`.
- **Deliverable:** Health row complete (4 sub-rows × 6 lenses = 24 maps).

### Sprint 3 — Land Use
- **`scripts/fetch_atlanta_zoning.py`** — City of Atlanta Open Data Hub.
- **`scripts/fetch_atlanta_parks.py`** — same source, parks layer.
- **`scripts/fetch_tree_canopy.py`** — NLCD 2021 USFS tree-canopy raster, clip to Atlanta MSA, vectorize at 30m for choropleth.
- **`scripts/fetch_parcels_fulton.py`** — Fulton County GIS parcels with owner names.
- **Deliverable:** Land Use row complete (7 sub-rows × 6 lenses = 42 maps).

### Sprint 4 — Transportation gaps
- **`scripts/fetch_bike_infra.py`** — Overpass API, `cycleway=*` + Atlanta BeltLine alignment.
- **`scripts/fetch_atl_airport.py`** — Overpass API, `aeroway=aerodrome` for Hartsfield-Jackson.
- Add **OpenTripPlanner** Docker container + GTFS feed → generate isochrones for each Census-tract centroid (transit + walk, 30 min) → `geojson/atl_transit_isochrones.geojson`.
- **Deliverable:** Transport row complete + accessibility lens activated for *every* row that depends on travel time.

### Sprint 5 — Social Systems + Infrastructure
- **`scripts/fetch_universities.py`** — NCES IPEDS for colleges in 7-county area.
- **`scripts/fetch_fcc_broadband.py`** — FCC National Broadband Map at block level, aggregate to tract.
- **`scripts/fetch_hifld_utilities.py`** — HIFLD electric transmission + gas pipelines.
- **`scripts/fetch_epa_landfills.py`** — EPA Envirofacts RCRA waste facilities.
- **Deliverable:** Social Systems + Infrastructure rows complete.

### Sprint 6 — Capstone: Typology synthesis
- **`scripts/build_typology.py`** — for each of the 530 tracts, compute:
  - `income_score` from ACS (z-score)
  - `transit_access_score` from isochrones (Sprint 4)
  - `food_access_score` from `atl_pro_food_deserts.geojson`
  - `vulnerability_score` from CDC PLACES (Sprint 2)
  - `density_score` from buildings + zoning (Sprint 3)
- Apply k-means (k=5) classifier seeded with the supervisor's 5 named typologies, validate with Davies-Bouldin index.
- Output `geojson/atl_typology_classified.geojson` — one polygon per tract, colored by typology.
- **`atlas/typology.html`** — full-screen view with classifier explanation, per-typology stat cards, click-tract-to-explain panel.
- **Deliverable:** Headline output the supervisor explicitly asked for.

### Risk register
| Risk | Mitigation |
|---|---|
| OpenTripPlanner container heavy to run | Pre-compute isochrones once locally, ship as static GeoJSON — no live routing in browser |
| Parcel ownership data incomplete across counties | Start with Fulton (covers most of city), note gaps for Sprint 7+ |
| Census API rate limits | Free tier = 500 req/day, enough for 7 counties × 1 tract pull |
| ArcGIS API key tied to existing dashboard | Atlas page uses MapLibre = no Esri key needed |
| Tile provider for basemap | MapLibre demotiles (free) for dev → Stadia/Maptiler/Protomaps for prod |

---

## 5. Evaluation methodology

Every map produced gets scored against this 6-criterion rubric. Score 1–5
each; aggregate weighted score is the cell's "publication readiness". The
rubric file ships as `docs/EVALUATION_RUBRIC.md` with worked examples.

### 5.1 The 6 criteria

| # | Criterion | Weight | What it measures | How to test |
|---|---|---:|---|---|
| 1 | **Data Quality** | 25% | Completeness, currency, source authority, geometry validity | `scripts/qa_layer.py` runs: % null in key field · max age of source · CRS check · geometry self-intersect count · feature count vs source-of-truth |
| 2 | **Visual Clarity** | 20% | Colorblind-safe palette, legend present, label legibility, classification breaks | Pass through Coblis colorblind simulator; check 5+ classes use ColorBrewer; legend covers all classes |
| 3 | **Analytical Insight** | 25% | Does the map answer a stated research question? Is the chosen lens the right one? | Each cell ships with a 1-sentence "research question" in `data-manifest.json`. Reviewer answers Y/N: does the map make the answer visible? |
| 4 | **Technical Performance** | 10% | First-paint time, frame rate during interaction, mobile load size | Lighthouse: FCP < 2 s, LCP < 3 s, TTI < 4 s. Layer file size budget: < 5 MB per cell |
| 5 | **Accessibility (a11y)** | 10% | Keyboard nav, screen-reader labels, alt-text on legend, sufficient contrast | axe-core scan in CI; manual NVDA test for typology page |
| 6 | **Reproducibility** | 10% | Source script + dataset URL + SHA recorded; `make rebuild_<layer>` re-creates exactly | Each `geojson/*.geojson` has a sibling `*.meta.json` with source URL, fetch date, SHA-256 of fetched bytes, processing script path |

### 5.2 Per-lens scoring guidance

Some criteria matter more for certain lenses:

| Lens | Heaviest criterion | Why |
|---|---|---|
| Base Distribution | Data Quality | If the dots are wrong, nothing downstream is right |
| Density | Visual Clarity | Bandwidth choice and palette dominate the message |
| Accessibility | Analytical Insight | Travel time *to what?* must be specified per cell |
| Equity | Visual Clarity + Insight | Bivariate / divergent palettes carry the equity story |
| Trend | Data Quality | Comparing two snapshots requires both be aligned (same vintage, same geography) |
| Flow | Performance | Edge bundles can crater frame rate; budget hard |

### 5.3 Reviewer protocol

Each cell scored by **two independent reviewers** (one technical, one design):
1. Open the cell's URL (`atlas/viewer.html?row=...&lens=...`)
2. Fill the 6-criterion rubric in a Google Form (auto-populates a sheet)
3. Reviewers' scores averaged; disagreements > 1 point trigger a sync call
4. Cells scoring < 3.5 weighted go to "rework"; ≥ 4.0 go to "publish"

### 5.4 Continuous evaluation in CI

`scripts/qa_layer.py` runs on every push for every changed `geojson/*.geojson`:
- ✅ valid GeoJSON
- ✅ CRS = EPSG:4326
- ✅ all geometries valid (no self-intersect)
- ✅ feature count within ±5 % of last published
- ✅ key fields not all-null
- ✅ file size < 5 MB (warn at 3 MB)

Failures block the commit. This is the same pattern as the existing
`scripts/build_dist.py` for Netlify deploys.

---

## 6. Concrete first-week deliverables

To keep momentum, by end of Sprint 1 you should have:

1. `scripts/fetch_acs.py` — committed, runnable
2. `geojson/atl_demographics_acs.geojson` — generated, < 5 MB
3. `geojson/atl_demographics_acs.meta.json` — provenance record
4. `atlas/index.html` — 42-cell grid landing page with 6 working cells (the demographic row)
5. `atlas/viewer.html` — detail viewer working for `?row=demographics&lens=*`
6. `docs/EVALUATION_RUBRIC.md` — the 6-criterion scoring sheet
7. Demographics row scored end-to-end by 2 reviewers

Each subsequent sprint adds a row to the grid + the data + the QA records,
with the typology page as the Sprint-6 capstone.

---

## 7. Framework integration paths — bolting viz libraries onto the existing dashboard

> Earlier sections proposed a parallel `atlas/` page running MapLibre. That's
> still the safest option, but it's not the only one. Below is a side-by-side
> evaluation of three integration paths for the *existing* ArcGIS-based
> dashboard, plus a path if you want to drop ArcGIS entirely.

### 7.1 The current Map View dashboard

- File: `resources/Layers & Packages/index.html`
- Stack: **ArcGIS Maps SDK for JavaScript v4.30** (AMD modules via CDN) + Esri basemaps
- Auth: `ARCGIS_API_KEY` injected via `serve.py` → `GET /api/config`
- Free-tier limit: 2,000,000 basemap tiles / month (you're well under)

That stack is fine. The question is whether to rewrite it or **add** to it.

### 7.2 Path A — Add deck.gl as a layer inside ArcGIS *(recommended)*

deck.gl ships an official ArcGIS adapter package. The integration is a real
ArcGIS layer subclass — `@deck.gl/arcgis` exports `DeckLayer` which inherits
from `Layer`. You add it to your existing `Map` exactly like a `GeoJSONLayer`:

```js
require([
  "esri/Map", "esri/views/MapView",
  "https://unpkg.com/@deck.gl/[email protected]/dist.min.js"
], (Map, MapView) => {
  const map = new Map({ basemap: "dark-gray-vector" });   // existing
  const view = new MapView({ container: "viewDiv", map, zoom: 11, center: [-84.39, 33.75] });

  // Bolt-on: a deck.gl heatmap of grocery stores
  const deckLayer = new DeckLayer({
    "deck.layers": [
      new HeatmapLayer({
        id: "grocery-density",
        data: "geojson/pkg_atlanta_grocery_stores.geojson",
        getPosition: f => f.geometry.coordinates,
        getWeight: 1,
        radiusPixels: 60,
      })
    ]
  });
  map.add(deckLayer);
});
```

| Pros | Cons |
|---|---|
| **No rewrite** — keep the entire existing dashboard | Two libraries to learn instead of one |
| ArcGIS basemap stays | Bundle size grows ~250 KB |
| All 6 matrix lenses available as deck.gl layers (`HeatmapLayer`, `GeoJsonLayer`, `ArcLayer` for flow, `H3HexagonLayer` for density grids, `ContourLayer` for isochrones, `TripsLayer` for animated flow) | Some advanced 3D modes unavailable in the ArcGIS adapter (only 2D supported as of writing) |
| Esri API key already wired | — |

**Verdict for AFCN:** ✅ this is the path of least friction.

**Source:**
[Esri sample: Build a custom layer view using deck.gl](https://developers.arcgis.com/javascript/latest/sample-code/custom-lv-deckgl/) ·
[@deck.gl/arcgis API reference](https://deck.gl/docs/api-reference/arcgis/overview) ·
[DeckLayer class docs](https://deck.gl/docs/api-reference/arcgis/deck-layer)

### 7.3 Path B — Add D3 / Observable Plot for static "paper-quality" maps

deck.gl is for *interactive* WebGL maps. The **Equity** lens (e.g.
Seattle/LA obesity choropleth in supervisor's image 4) is often best served
by a static SVG that prints well in the supervisor's report.

```js
// In any HTML page — no ArcGIS, no Mapbox, no key required
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot/+esm";
import * as d3 from "https://cdn.jsdelivr.net/npm/d3/+esm";

const tracts = await fetch("geojson/atl_health_places.geojson").then(r => r.json());
const chart = Plot.plot({
  projection: { type: "mercator", domain: tracts },
  color: { scheme: "blues", legend: true, label: "Obesity prevalence (%)" },
  marks: [
    Plot.geo(tracts, { fill: d => d.properties.OBESITY_CrudePrev, stroke: "#fff", strokeWidth: 0.3 })
  ]
});
document.getElementById("chart").append(chart);
```

| Pros | Cons |
|---|---|
| Zero-key, zero-cost | Not interactive (no pan/zoom by default) |
| Print-quality SVG | Heavy DOM (one path per tract = 530 paths) |
| Pairs perfectly with the existing `story/` page | — |

**Verdict:** ✅ use it for the Story page's choropleths and any printable
deliverable for the supervisor.

**Source:**
[Choropleth maps best practices — School of Cities](https://schoolofcities.github.io/urban-data-storytelling/urban-data-visualization/choropleth-maps/choropleth-maps.html) ·
[Bivariate guide — Joshua Stevens](https://www.joshuastevens.net/cartography/make-a-bivariate-choropleth-map/)

### 7.4 Path C — Drop ArcGIS for MapLibre (only if you must)

If the lab decides to abandon Esri (e.g. for full open-source posture, or
the 2M-tile free tier becomes a concern), MapLibre GL JS is the drop-in
replacement. It's the OSS fork of Mapbox v1, free forever, and it speaks
the same Mapbox vector-tile spec.

```html
<link href="https://unpkg.com/maplibre-gl@^4/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@^4/dist/maplibre-gl.js"></script>
<div id="map" style="height: 100vh"></div>
<script>
  const map = new maplibregl.Map({
    container: "map",
    style: "https://demotiles.maplibre.org/style.json",   // free, OSS
    center: [-84.39, 33.75], zoom: 11
  });
  map.on("load", async () => {
    map.addSource("grocery", { type: "geojson", data: "geojson/pkg_atlanta_grocery_stores.geojson" });
    map.addLayer({ id: "grocery-heat", type: "heatmap", source: "grocery", paint: { "heatmap-radius": 30 } });
  });
</script>
```

| Pros | Cons |
|---|---|
| Free forever, no key | Have to redo every layer renderer in the existing dashboard |
| Same `style.json` spec as Mapbox — easy migration later | Different API surface than ArcGIS — your existing code doesn't port directly |
| deck.gl integrates the same way (`MapboxOverlay`) | Demotiles basemap is OSS-spartan; pretty basemaps need a tile provider (Stadia, MapTiler, Protomaps) |

**Free basemap providers** (drop-in `style.json` URLs):

| Provider | Free tier | Style |
|---|---|---|
| **MapLibre demotiles** | Unlimited (low-detail) | `https://demotiles.maplibre.org/style.json` |
| **Stadia Maps** | 200k tiles/mo free | Stamen Toner / Terrain styles ported |
| **MapTiler Cloud** | 100k requests/mo free | Multi-style |
| **Protomaps** | Self-host PMTiles, fully free | Single-file vector tile bundle |
| **Carto basemaps** | Public free (with attribution) | Positron / Voyager / Dark Matter |

**Verdict:** Don't switch unless cost or licensing forces you to. The
existing ArcGIS dashboard is already built; Path A bolts the missing
viz capability onto it for free.

### 7.5 Final integration recommendation for AFCN

| Layer in matrix | Recommended viz library | Rendered where |
|---|---|---|
| Base distribution (point layers) | ArcGIS `GeoJSONLayer` (existing) | Map View dashboard |
| Density / heatmap | **deck.gl `HeatmapLayer`** via `@deck.gl/arcgis` | Map View dashboard (Path A) |
| Accessibility (isochrones from OTP / Valhalla) | ArcGIS `GeoJSONLayer` for the polygons + deck.gl `ContourLayer` for animated reveal | Map View dashboard |
| Equity choropleths (interactive) | ArcGIS `GeoJSONLayer` with `ClassBreaksRenderer` (existing) | Map View dashboard |
| Equity choropleths (static / paper) | **Observable Plot** | Story page / Atlas thumbnails |
| Trend (two-snapshot compare) | ArcGIS `swipe widget` or two side-by-side `MapView`s | Map View dashboard |
| Flow (animated origin → destination) | **deck.gl `ArcLayer` + `TripsLayer`** | Map View dashboard |
| Capstone typology (classified tracts) | ArcGIS `GeoJSONLayer` for the polygons; click-to-reveal panel | Map View dashboard |

The **Atlas page** (Section 3) becomes a *systematic browser* of all 42
matrix cells, each rendered by whichever library above is appropriate, but
the dashboard itself stays ArcGIS.

---

## 8. What this gives the supervisor

- **One URL** (`atlas/index.html`) showing the entire 42-cell matrix as a navigable grid
- **One canonical typology layer** (the synthesis the brief explicitly asks for)
- **A reproducible pipeline** — every map regenerable via `make rebuild_<row>`
- **A scored rubric** — every cell rated against the 6 criteria, no subjective hand-waving
- **Free of lock-in** — MapLibre + OSM-derived stack means no Esri / Mapbox key required for the atlas (existing flagship Map View keeps using ArcGIS)

The matrix becomes the lab's reusable framework: any future city we map (Birmingham? Memphis? Houston?) gets the same atlas template populated with its own data.
