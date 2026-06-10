/* AFCN Showcase — synced dual-pane ArcGIS kiosk for final presentation.
 * Loads scenes.json, builds two MapViews, syncs their viewports, swaps
 * layers per scene. Keyboard-driven, autoplay-capable, big-screen safe.
 *
 * Hotkeys:  ← →  prev/next         Space  play/pause autoplay
 *           S    toggle viewport sync     M  toggle presenter bar
 *           F    fullscreen               H  show/hide help
 *           1–9  jump to scene N          Esc fullscreen exit / hide help
 */

const SCENES_URL = "scenes.json";
const GEOJSON_DIR = "../geojson/";
const SCENE_AUTOADVANCE_MS_DEFAULT = 30_000;

// City of Atlanta bounding box — keeps the visual focus tight to the city
// proper instead of drifting across all of Fulton + DeKalb. Used both as the
// initial extent and as a pan constraint via view.constraints.geometry.
const ATLANTA_EXTENT_WGS84 = {
  xmin: -84.5510, ymin: 33.6479,
  xmax: -84.2895, ymax: 33.8868,
  spatialReference: { wkid: 4326 },
};

let scenes      = [];
let sceneIdx    = 0;
let autoplay    = false;
let autoTimer   = null;
let progTimer   = null;
let progStart   = 0;
let syncOn      = true;
let leftView, rightView;
let leftMap,  rightMap;
let suppressSync = false;     // re-entry guard for the watcher
let layerCache = new Map();   // url → loaded GeoJSON Layer (avoid re-fetch)

(async function boot() {
  scenes = (await (await fetch(SCENES_URL)).json()).scenes;
  document.getElementById("sceneTotal").textContent = scenes.length;

  await initMaps();
  bindControls();
  bindKeyboard();
  trackIdleCursor();
  await renderScene(0);
})();


/* ── ArcGIS init ─────────────────────────────────────────── */
function initMaps() {
  return new Promise((resolve) => {
    require([
      "esri/Map", "esri/views/MapView",
      "esri/layers/GeoJSONLayer", "esri/config",
    ], (Map, MapView, GeoJSONLayer, esriConfig) => {

      // Pull API key from serve.py — same as Map View dashboard
      fetch("/api/config").then(r => r.json()).then(cfg => {
        if (cfg && cfg.arcgisApiKey) esriConfig.apiKey = cfg.arcgisApiKey;
      }).catch(() => {});

      // Light cream-toned basemap to match the editorial Atlanta Story theme
      leftMap  = new Map({ basemap: "gray-vector" });
      rightMap = new Map({ basemap: "gray-vector" });

      const viewOpts = {
        extent: ATLANTA_EXTENT_WGS84,
        ui: { components: ["zoom"] },
        constraints: {
          geometry: ATLANTA_EXTENT_WGS84,   // pan locked to Atlanta city
          minZoom: 10,                       // no zooming out past city scale
          maxZoom: 18,
          rotationEnabled: false,
        },
      };
      leftView  = new MapView({ ...viewOpts, container: "leftMap",  map: leftMap  });
      rightView = new MapView({ ...viewOpts, container: "rightMap", map: rightMap });

      // Stash factories on window for renderScene
      window._GeoJSONLayer = GeoJSONLayer;

      // Sync each view's camera onto the other
      leftView.when(() => rightView.when(() => {
        wireSync();
        resolve();
      }));
    });
  });
}

function wireSync() {
  const propagate = (src, dst) => src.watch("center, zoom, rotation", () => {
    if (!syncOn || suppressSync) return;
    suppressSync = true;
    dst.goTo({ center: src.center, zoom: src.zoom, rotation: src.rotation },
              { duration: 0, animate: false })
        .finally(() => { suppressSync = false; });
  });
  propagate(leftView,  rightView);
  propagate(rightView, leftView);
}


/* ── Scene rendering ─────────────────────────────────────── */
async function renderScene(idx) {
  sceneIdx = (idx + scenes.length) % scenes.length;
  const s = scenes[sceneIdx];

  document.getElementById("sceneIdx").textContent  = sceneIdx + 1;
  document.getElementById("sceneTitle").textContent  = s.title;
  document.getElementById("captionText").textContent = s.caption;
  document.getElementById("captionLayers").textContent =
      `${s.left.title}  ↔  ${s.right.title}`;
  document.getElementById("captionInsight").textContent = s.insight || "";
  document.getElementById("leftTitle").textContent  = s.left.title;
  document.getElementById("rightTitle").textContent = s.right.title;

  // Clear panels
  leftMap.removeAll();
  rightMap.removeAll();

  await Promise.all([
    addLayers(leftMap,  s.left.layers,  s.left.field,  s.left.mode,  "left"),
    addLayers(rightMap, s.right.layers, s.right.field, s.right.mode, "right"),
  ]);

  // Move camera (both, since synced). If a scene asks for a zoom wider than
  // the Atlanta city scale (zoom < 10), clamp it back to the Atlanta extent
  // so the layers stay visually focused on the city, not the metro.
  if (s.camera) {
    const z = Math.max(s.camera.zoom || 11, 11);
    leftView.goTo({ center: s.camera.center, zoom: z },
                  { duration: 1100, easing: "out-cubic" });
  } else {
    leftView.goTo(ATLANTA_EXTENT_WGS84, { duration: 1100, easing: "out-cubic" });
  }

  // Reset autoplay timer for this scene
  if (autoplay) startAutoTimer(s.duration_sec ? s.duration_sec * 1000
                                              : SCENE_AUTOADVANCE_MS_DEFAULT);
}

async function addLayers(targetMap, layerNames, field, mode, side) {
  if (!layerNames) return;
  // Side panel ("left" | "right") receives the legend for the dominant layer.
  let legendDescriptor = null;
  for (const [idx, name] of layerNames.entries()) {
    const url = `${GEOJSON_DIR}${name}.geojson`;
    const renderer = defaultRenderer(name, field, mode);
    const layerOpts = {
      url,
      title: name,
      renderer,
      popupEnabled: false,
      labelsVisible: false,
    };
    // marta_stops_atl is a 8,456-point file mixing rail stations with bus stops.
    // We only want rail station markers — filter via definitionExpression.
    if (name === "marta_stops_atl") {
      layerOpts.definitionExpression = "stop_name LIKE '%STATION%'";
    }
    const layer = new window._GeoJSONLayer(layerOpts);
    try {
      targetMap.add(layer);
    } catch (e) {
      console.warn(`Could not add layer ${name}:`, e);
    }
    // The first layer per panel drives the legend. (Subsequent layers are
    // overlays — points on top of polygons etc.)
    if (idx === 0) legendDescriptor = renderer;
  }
  if (side) renderLegend(side, legendDescriptor, field);
}

function defaultRenderer(name, field, mode) {
  // ── Heatmap: opt-in via mode === "heatmap". Used for point layers
  //    where density is the message (grocery clusters, fast-food rings).
  if (mode === "heatmap") {
    return heatmapRenderer();
  }

  // ── Bivariate choropleth: obesity tertile × LILA-strictness class
  //    (Stevens 2015 method — 3×3 grid). Driven by the precomputed
  //    bivar_class field in bivariate_obesity_lila.geojson.
  if (name === "bivariate_obesity_lila" || field === "bivar_class") {
    return bivariateObesityLilaRenderer();
  }

  // ── Categorical: zoning by ZONECLASS, typology by label, or any
  //    categorical field passed in.
  if (field === "ZONECLASS" || name === "atl_zoning") {
    return zoningRenderer();
  }
  if (field === "typology_label" || field === "typology_id") {
    return uniqueTypologyRenderer(field);
  }

  // ── Numeric class breaks (income, prevalence, etc.)
  if (field) {
    const breaks = breaksForField(field);
    return {
      type: "class-breaks",
      field,
      classBreakInfos: breaks.map(([min, max, color]) => ({
        minValue: min, maxValue: max, symbol: poly(color, 0.78),
      })),
    };
  }

  // ── Generic per-layer-name styling
  if (name.includes("food_desert"))return { type: "simple", symbol: poly("#c62828", 0.55) };
  if (name.includes("typology"))   return { type: "simple", symbol: poly("#1c5c84", 0.5)  };
  // ── Transit hierarchy (Walker 2011, NACIS GTFS conventions)
  //    marta_stops_atl is filtered to STATIONs by definitionExpression upstream;
  //    render those as outlined dots so they read as nodes on top of lines.
  if (name === "marta_stops_atl") {
    return { type: "simple", symbol: {
      type: "simple-marker", style: "circle", color: "#ffffff", size: 8,
      outline: { color: "#1a1a1a", width: 2 },
    }};
  }
  // atl_pro_marta_bus_routes is mis-named — it carries BOTH MARTA bus and
  // rail (route_type 3 vs 1), with official line colors in route_color.
  if (name === "atl_pro_marta_bus_routes" || name.includes("marta_routes")) {
    return martaRouteRenderer();
  }
  // atl_pro_rails is TIGER all-rail (CSX, NS freight + MARTA) — render as
  // subordinate grey dashed so it reads as base infrastructure, not transit.
  if (name.includes("rails")) {
    return { type: "simple", symbol: {
      type: "simple-line", color: "#8e98aa", width: 1, style: "dash",
    }};
  }
  if (name.includes("freeways") || name.includes("transport"))
                                   return { type: "simple", symbol: line("#a4b1bc", 1.5) };
  if (name.includes("bike"))      return { type: "simple", symbol: line("#1c5c84", 1.8) };
  if (name.includes("electric"))  return { type: "simple", symbol: line("#3a4f5e", 1.3) };
  if (name.includes("campus") || name.includes("boundary"))
                                   return { type: "simple", symbol: poly("#7d9caf", 0.25) };
  // ── Land-use polygon layers (BeltLine corridor + historic districts + plans).
  //    Without these, ArcGIS falls back to the default point-marker symbol and
  //    the polygons render as centroids — see the "How atlanta is zoned" scene.
  if (name.includes("beltline"))           return { type: "simple", symbol: poly("#3a4f5e", 0.55) };
  if (name.includes("historic_district"))  return { type: "simple", symbol: poly("#b6c0c9", 0.45) };
  if (name.includes("neighborhood_plan"))  return { type: "simple", symbol: poly("#a4b1bc", 0.30) };
  if (name.includes("zoning_overlay"))     return { type: "simple", symbol: poly("#7d9caf", 0.30) };
  if (name.includes("census_tracts"))      return { type: "simple", symbol: poly("#a4b1bc", 0.18) };
  if (name.includes("buildings"))          return { type: "simple", symbol: poly("#3a4f5e", 0.55) };
  // ── Catch-all for tract-level analytical polygons that arrive without a
  //    field hint (e.g. atl_health_places used as overlay outline). Render
  //    as a transparent fill with hairline outline — NOT centroid dots.
  if (name.startsWith("atl_health") || name.startsWith("atl_demographics") ||
      name.startsWith("atl_typology") || name.startsWith("atl_transit") ||
      name.startsWith("census_") || name.startsWith("atl_pro_health")) {
    return { type: "simple", symbol: {
      type: "simple-fill",
      color: [0, 0, 0, 0],
      outline: { color: "rgba(86, 90, 99, 0.35)", width: 0.4 },
    }};
  }
  // points
  return { type: "simple", symbol: dot("#1c5c84", 9) };
}

// ── MARTA rail + bus renderer — uses official MARTA colors keyed off
//    the GTFS route_short_name field (rail = colored thick line; bus
//    falls through to a subordinate grey-teal thinner line).
const MARTA_RAIL_COLORS = {
  "RED":   "#E51937",
  "GOLD":  "#FFC72C",
  "BLUE":  "#0072CE",
  "GREEN": "#00A551",
};
function martaRouteRenderer() {
  return {
    type: "unique-value",
    field: "route_short_name",
    defaultSymbol: { type: "simple-line", color: "rgba(90, 106, 126, 0.55)", width: 1 },
    uniqueValueInfos: Object.entries(MARTA_RAIL_COLORS).map(([name, color]) => ({
      value: name,
      symbol: { type: "simple-line", color, width: 4.5 },
      label: `MARTA ${name.charAt(0)}${name.slice(1).toLowerCase()} Line`,
    })),
  };
}

// ── Bivariate choropleth (Stevens 2015) — 3 obesity tertiles × 3 LILA
//    classes = 9 colors. Adapted to the AFCN editorial cream→clay palette.
//    bivar_class layout: row = obesity tertile (Low/Mid/High), col = LILA
//    strictness (None/Some/Strict) → bivar_class = obesity*3 + lila (0..8).
const BIVARIATE_OBESITY_LILA = [
  // Farbton 1929 9-class blue ramp — Nr. 55 → Nr. 51 → Nr. 50 → Nr. 49
  // Low obesity (lichtgrau row)
  { value: 0, color: "#d2dadf", label: "Low obesity · No LILA" },        /* Nr. 55 */
  { value: 1, color: "#c4cdd2", label: "Low obesity · Some LILA" },      /* Nr. 56 */
  { value: 2, color: "#a4b1bc", label: "Low obesity · Strict LILA" },    /* Nr. 54 */
  // Mid obesity (lichtblau row)
  { value: 3, color: "#b6c0c9", label: "Mid obesity · No LILA" },
  { value: 4, color: "#7d9caf", label: "Mid obesity · Some LILA" },      /* Nr. 57 */
  { value: 5, color: "#4d6f8a", label: "Mid obesity · Strict LILA" },
  // High obesity (spinellblau / dunkelblau row)
  { value: 6, color: "#6f8688", label: "High obesity · No LILA" },       /* Nr. 58 */
  { value: 7, color: "#1c5c84", label: "High obesity · Some LILA" },     /* Nr. 51 */
  { value: 8, color: "#3a4f5e", label: "High obesity · Strict LILA" },   /* Nr. 50 */
];
function bivariateObesityLilaRenderer() {
  return {
    type: "unique-value",
    field: "bivar_class",
    defaultSymbol: { type: "simple-fill", color: "rgba(200,200,200,0.35)",
                      outline: { color: "rgba(86,90,99,0.4)", width: 0.3 } },
    uniqueValueInfos: BIVARIATE_OBESITY_LILA.map(({ value, color, label }) => ({
      value,
      symbol: { type: "simple-fill", color: hexToRgba(color, 0.85),
                outline: { color: hexToRgba(color, 1), width: 0.3 } },
      label,
    })),
  };
}

// ── Heatmap renderer — ArcGIS HeatmapRenderer; drape a soft kernel over
//    point features. Color stops follow the editorial cream → clay ramp
//    so density blooms read as warm hot-spots, fading to translucent cream
//    at the edges.
function heatmapRenderer() {
  return {
    type: "heatmap",
    radius: 28,
    maxDensity: 0.04,
    minDensity: 0,
    colorStops: [
      // Farbton ramp: Nr. 55 lichtgrau → Nr. 54 → Nr. 57 lichtblau → Nr. 51 spinellblau → Nr. 50 dunkelblau
      { ratio: 0,     color: "rgba(210, 218, 223, 0)" },     /* Nr. 55 transparent */
      { ratio: 0.05,  color: "rgba(210, 218, 223, 0.35)" },
      { ratio: 0.20,  color: "rgba(164, 177, 188, 0.65)" },  /* Nr. 54 */
      { ratio: 0.45,  color: "rgba(125, 156, 175, 0.85)" },  /* Nr. 57 */
      { ratio: 0.75,  color: "rgba(28, 92, 132, 0.95)" },    /* Nr. 51 */
      { ratio: 1.0,   color: "rgba(58, 79, 94, 1.0)" },      /* Nr. 50 */
    ],
  };
}

// ── Zoning categorical renderer — color each zone class by its broad
//    family. R-* = residential (warm tans), C-* = commercial (clay),
//    I-* = industrial (slate), MR/MRC = mixed-use (gold), SPI = overlay
//    (deep clay), PD = planned (teal). Anything unknown → neutral grey.
const ZONING_FAMILIES = [
  { match: /^R[0-9-]/i,    color: "#c4cdd2", label: "Residential" },
  { match: /^MR/i,         color: "#b6c0c9", label: "Mixed Residential" },
  { match: /^MRC/i,        color: "#7d9caf", label: "Mixed-Use Comm." },
  { match: /^C[0-9-]/i,    color: "#7d9caf", label: "Commercial" },
  { match: /^I[0-9-]/i,    color: "#3a4f5e", label: "Industrial" },
  { match: /^O[I-]/i,      color: "#7a958c", label: "Office/Inst." },
  { match: /^SPI/i,        color: "#3a4f5e", label: "Special Public Interest" },
  { match: /^PD/i,         color: "#7a958c", label: "Planned Development" },
  { match: /^LW/i,         color: "#a4b1bc", label: "Live-Work" },
  { match: /^NC/i,         color: "#1c5c84", label: "Neighborhood Comm." },
];
function zoningRenderer() {
  // Build a unique-value renderer keyed on ZONECLASS using regex families.
  // We can't put a regex directly in ArcGIS unique-value renderers, so we
  // instead emit a synthetic categorical renderer with a special hook
  // (handled in legend builder). Practical approach: precompute the broad
  // family per feature isn't possible without geoprocessing, so we use a
  // class-breaks-by-string-prefix workaround via uniqueValueInfos: list
  // every common Atlanta zoning code keyed to its family color.
  const codes = [
    // Residential
    ["R-1", "Residential"], ["R-2", "Residential"], ["R-2A", "Residential"],
    ["R-2B", "Residential"], ["R-3", "Residential"], ["R-3A", "Residential"],
    ["R-4", "Residential"], ["R-4A", "Residential"], ["R-4B", "Residential"],
    ["R-5", "Residential"], ["R-G", "Residential"], ["R-LC", "Residential"],
    // Mixed
    ["MR-1", "Mixed Residential"], ["MR-2", "Mixed Residential"],
    ["MR-3", "Mixed Residential"], ["MR-4", "Mixed Residential"],
    ["MR-4A", "Mixed Residential"], ["MR-5A", "Mixed Residential"],
    ["MRC-1", "Mixed-Use Comm."], ["MRC-2", "Mixed-Use Comm."],
    ["MRC-3", "Mixed-Use Comm."],
    // Commercial
    ["C-1", "Commercial"], ["C-2", "Commercial"], ["C-3", "Commercial"],
    ["C-4", "Commercial"], ["C-5", "Commercial"],
    // Industrial
    ["I-1", "Industrial"], ["I-2", "Industrial"],
    // Office / institutional
    ["O-I", "Office/Inst."], ["OI", "Office/Inst."],
    // Special public interest
    ["SPI-1", "Special Public Interest"], ["SPI-2", "Special Public Interest"],
    ["SPI-3", "Special Public Interest"], ["SPI-4", "Special Public Interest"],
    ["SPI-5", "Special Public Interest"], ["SPI-6", "Special Public Interest"],
    ["SPI-7", "Special Public Interest"], ["SPI-8", "Special Public Interest"],
    ["SPI-9", "Special Public Interest"], ["SPI-10", "Special Public Interest"],
    ["SPI-11", "Special Public Interest"], ["SPI-12", "Special Public Interest"],
    ["SPI-15", "Special Public Interest"], ["SPI-16", "Special Public Interest"],
    ["SPI-17", "Special Public Interest"], ["SPI-22", "Special Public Interest"],
    // Planned, Live-work, Neighborhood
    ["PD-H", "Planned Development"], ["PD-MU", "Planned Development"],
    ["PD-OC", "Planned Development"], ["PD-BP", "Planned Development"],
    ["LW", "Live-Work"],
    ["NC-1", "Neighborhood Comm."], ["NC-2", "Neighborhood Comm."],
    ["NC-3", "Neighborhood Comm."], ["NC-4", "Neighborhood Comm."],
  ];
  const familyColor = Object.fromEntries(
    ZONING_FAMILIES.map(f => [f.label, f.color]));
  return {
    type: "unique-value",
    field: "ZONECLASS",
    defaultSymbol: poly("#a4b1bc", 0.55),
    uniqueValueInfos: codes.map(([code, family]) => ({
      value: code,
      symbol: poly(familyColor[family] || "#a4b1bc", 0.78),
      label: `${code} — ${family}`,
    })),
  };
}

// Categorical renderer for the 5 named typologies. Each typology gets a
// distinct hue from the editorial Atlanta Story palette so the synthesis
// map reads as a print-quality legend strip.
const TYPOLOGY_PALETTE = {
  // Farbton 1929 typology palette — distinct hues for the 5 named regions.
  // Five well-separated families pulled from the standard chart so each
  // typology stays distinguishable at choropleth opacity.
  "High-growth Core":     "#1c5c84",   /* Nr. 51 spinellblau — primary anchor */
  "Affluent Suburban":    "#7a958c",   /* Nr. 59 petrolgrün */
  "Disinvested Urban":    "#c62828",   /* alert red — alarm hue (kept for clarity) */
  "Industrial Logistics": "#5b7282",   /* Nr. 52 slate */
  "Emerging Mixed-use":   "#7d9caf",   /* Nr. 57 lichtblau */
};
function uniqueTypologyRenderer(field) {
  return {
    type: "unique-value",
    field,
    defaultSymbol: poly("#a4b1bc", 0.55),
    uniqueValueInfos: Object.entries(TYPOLOGY_PALETTE).map(([label, color]) => ({
      value: label,
      symbol: poly(color, 0.72),
      label,
    })),
  };
}

// Per-field class breaks. 5 bins each; ColorBrewer-friendly ramps. Income
// ramps cool-to-warm so wealth concentrates as warm clay (matches the
// editorial palette). Health prevalence ramps cream-to-clay (low-to-high).
function breaksForField(field) {
  // Income (USD): 0-30k, 30-50k, 50-75k, 75-120k, 120k-300k
  if (field === "median_income" || field === "B19013_001E") return [
    [0,        30000,    "#d2dadf"],
    [30000,    50000,    "#a4b1bc"],
    [50000,    75000,    "#7d9caf"],
    [75000,    120000,   "#1c5c84"],
    [120000,   400000,   "#3a4f5e"],
  ];
  // Population density (people / km²): 0-500, 500-2k, 2k-5k, 5k-10k, 10k+
  if (field === "pop_density") return [
    [0,        500,      "#d2dadf"],
    [500,      2000,     "#a4b1bc"],
    [2000,     5000,     "#7d9caf"],
    [5000,     10000,    "#1c5c84"],
    [10000,    100000,   "#3a4f5e"],
  ];
  // CDC PLACES crude prevalence (%): 0-15, 15-25, 25-35, 35-45, 45+
  if (field.endsWith("_CrudePrev")) return [
    [0,        15,       "#d2dadf"],
    [15,       25,       "#a4b1bc"],
    [25,       35,       "#7d9caf"],
    [35,       45,       "#1c5c84"],
    [45,       100,      "#3a4f5e"],
  ];
  // Generic 0–100 percentage fallback
  if (field.startsWith("pct_")) return [
    [0,        20,       "#d2dadf"],
    [20,       40,       "#a4b1bc"],
    [40,       60,       "#7d9caf"],
    [60,       80,       "#1c5c84"],
    [80,       100,      "#3a4f5e"],
  ];
  // Transit access score (0–100, but most data lives in lower half so finer bins)
  if (field === "access_score") return [
    [0,        5,        "#d2dadf"],   // "none"
    [5,        15,       "#a4b1bc"],   // "low"
    [15,       30,       "#7d9caf"],   // "medium-low"
    [30,       60,       "#1c5c84"],   // "medium-high"
    [60,       100,      "#3a4f5e"],   // "high"
  ];
  // Last-resort generic ramp
  return [
    [0,    25,   "#d2dadf"],
    [25,   50,   "#a4b1bc"],
    [50,   75,   "#7d9caf"],
    [75,  200,   "#1c5c84"],
  ];
}

/* ── Legend builder ───────────────────────────────────────────────
   Reads the renderer descriptor and DOMs out a small legend overlay
   on the requested side. Auto-clears between scenes.                */
function renderLegend(side, renderer, field) {
  const target = document.getElementById(`${side}Legend`);
  if (!target) return;
  target.innerHTML = "";
  target.classList.add("legend-hidden");
  if (!renderer) return;

  const items = [];
  let title = "";

  if (renderer.type === "class-breaks") {
    title = labelForField(field) || "Value";
    renderer.classBreakInfos.forEach((b, i) => {
      const c = arrToRgba(b.symbol.color);
      items.push({ color: c, label: rangeLabel(b.minValue, b.maxValue, field) });
    });
  } else if (renderer.type === "unique-value") {
    title = field === "ZONECLASS" ? "Zoning family"
          : field === "typology_label" ? "Typology"
          : field === "bivar_class" ? "Obesity × Food access"
          : field === "route_short_name" ? "MARTA route"
          : (labelForField(field) || "Category");
    if (field === "ZONECLASS") {
      // Collapse the per-code list into 10 family rows
      ZONING_FAMILIES.forEach(f => {
        items.push({ color: f.color, label: f.label });
      });
    } else if (field === "typology_label") {
      Object.entries(TYPOLOGY_PALETTE).forEach(([label, color]) => {
        items.push({ color, label });
      });
    } else if (field === "bivar_class") {
      // Bivariate gets a special 3×3 grid renderer instead of stacked rows.
      renderBivariateLegend(target, BIVARIATE_OBESITY_LILA);
      return;
    } else if (field === "route_short_name") {
      // Show only the rail lines + a single "Bus" row, not every bus number.
      Object.entries(MARTA_RAIL_COLORS).forEach(([key, color]) =>
        items.push({ color, label: `${key.charAt(0)}${key.slice(1).toLowerCase()} Line (rail)` }));
      items.push({ color: "rgba(90, 106, 126, 0.55)", label: "Bus routes" });
    } else {
      renderer.uniqueValueInfos.forEach(uv => {
        items.push({ color: arrToRgba(uv.symbol.color), label: uv.label || uv.value });
      });
    }
  } else if (renderer.type === "heatmap") {
    title = "Density (kernel)";
    items.push({ gradient: renderer.colorStops, label: "low → high concentration" });
  }

  if (!items.length) return;
  target.classList.remove("legend-hidden");

  const titleEl = document.createElement("div");
  titleEl.className = "legend-title";
  titleEl.textContent = title;
  target.appendChild(titleEl);

  for (const item of items) {
    const row = document.createElement("div");
    row.className = "legend-row";
    const swatch = document.createElement("span");
    swatch.className = "legend-swatch";
    if (item.gradient) {
      const stops = item.gradient
        .map(s => `${s.color} ${(s.ratio * 100).toFixed(0)}%`)
        .join(", ");
      swatch.style.background = `linear-gradient(90deg, ${stops})`;
      swatch.style.width = "82px";
    } else {
      swatch.style.background = item.color;
    }
    const label = document.createElement("span");
    label.className = "legend-label";
    label.textContent = item.label;
    row.appendChild(swatch);
    row.appendChild(label);
    target.appendChild(row);
  }
}

function labelForField(field) {
  if (!field) return "";
  return ({
    median_income:           "Median household income",
    pop_density:             "Population density (people / km²)",
    OBESITY_CrudePrev:       "Adult obesity prevalence (%)",
    DIABETES_CrudePrev:      "Diabetes prevalence (%)",
    DEPRESSION_CrudePrev:    "Depression prevalence (%)",
    MHLTH_CrudePrev:         "Poor mental health (%)",
    PHLTH_CrudePrev:         "Poor physical health (%)",
    FOODINSECU_CrudePrev:    "Food insecurity (%)",
    access_score:            "Transit access score",
    pct_broadband:           "% with broadband",
    pct_no_internet:         "% with no internet",
    pct_white:               "% White",
    pct_black:               "% Black",
    pct_bachelor_or_higher:  "% Bachelor's or higher",
    typology_label:          "Urban typology",
    ZONECLASS:               "Zoning class",
    FOODINSECU_CrudePrev:    "Food insecurity prevalence (%)",
    HMM_Score:               "Composite health-risk score",
    bivar_class:             "Obesity × Food access (bivariate)",
    route_short_name:        "MARTA route",
  })[field] || field;
}

function rangeLabel(min, max, field) {
  if (field === "median_income") {
    const f = v => "$" + (v >= 1000 ? Math.round(v / 1000) + "k" : v);
    return `${f(min)} – ${f(max)}`;
  }
  if (field === "pop_density") {
    return `${min.toLocaleString()} – ${max.toLocaleString()}`;
  }
  if (field && (field.endsWith("_CrudePrev") || field.startsWith("pct_") ||
                field === "access_score")) {
    return `${min}% – ${Math.min(max, 100)}%`;
  }
  return `${min} – ${max}`;
}

function arrToRgba(arr) {
  if (!Array.isArray(arr)) return arr;
  const [r, g, b, a] = arr;
  return `rgba(${r}, ${g}, ${b}, ${a == null ? 1 : a})`;
}

// ── Bivariate legend — renders the 3×3 matrix with axis labels so the
//    user can read both dimensions simultaneously (Stevens 2015 layout).
function renderBivariateLegend(target, palette) {
  target.classList.remove("legend-hidden");
  target.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.className = "legend-bivariate";
  wrap.innerHTML = `
    <div class="legend-title">Obesity × Food access</div>
    <div class="bivar-axes">
      <div class="bivar-y-label">Obesity →</div>
      <div class="bivar-grid">
        ${palette.map(p => `<span class="bivar-cell" title="${p.label}" style="background:${p.color}"></span>`).join("")}
      </div>
      <div class="bivar-x-label">LILA strictness →</div>
      <div class="bivar-corner-low">low / none</div>
      <div class="bivar-corner-high">high / strict</div>
    </div>
  `;
  target.appendChild(wrap);
}


function poly(color, opacity = 0.55) {
  return {
    type: "simple-fill",
    color: hexToRgba(color, opacity),
    outline: { color: hexToRgba(color, 0.9), width: 0.6 },
  };
}
function line(color, width = 2) {
  return { type: "simple-line", color, width };
}
function dot(color, size = 9) {
  return {
    type: "simple-marker", color,
    size,
    outline: { color: "rgba(255,255,255,0.85)", width: 1.2 },
  };
}
function hexToRgba(hex, a) {
  const m = hex.replace("#", "");
  const n = parseInt(m, 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  return [r, g, b, a];
}


/* ── Controls (mouse + keyboard) ─────────────────────────── */
function bindControls() {
  document.getElementById("prevBtn").onclick = () => renderScene(sceneIdx - 1);
  document.getElementById("nextBtn").onclick = () => renderScene(sceneIdx + 1);
  document.getElementById("playBtn").onclick = togglePlay;
  document.getElementById("syncBtn").onclick = toggleSync;
  document.getElementById("fullBtn").onclick = toggleFullscreen;
  document.getElementById("hideBtn").onclick = togglePresenter;
}

function bindKeyboard() {
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    switch (e.key) {
      case "ArrowLeft":  renderScene(sceneIdx - 1); break;
      case "ArrowRight": renderScene(sceneIdx + 1); break;
      case " ":          e.preventDefault(); togglePlay(); break;
      case "s": case "S": toggleSync(); break;
      case "f": case "F": toggleFullscreen(); break;
      case "m": case "M": togglePresenter(); break;
      case "h": case "H": toggleHelp(); break;
      case "Escape":
        if (document.fullscreenElement) document.exitFullscreen();
        else hideHelp();
        break;
      default:
        if (/^[1-9]$/.test(e.key)) {
          const n = parseInt(e.key, 10) - 1;
          if (n < scenes.length) renderScene(n);
        }
    }
  });
}

function togglePlay() {
  autoplay = !autoplay;
  document.getElementById("playBtn").textContent = autoplay ? "❙❙" : "▶";
  document.getElementById("playBtn").classList.toggle("active", autoplay);
  if (autoplay) {
    const s = scenes[sceneIdx];
    startAutoTimer(s.duration_sec ? s.duration_sec * 1000
                                  : SCENE_AUTOADVANCE_MS_DEFAULT);
  } else {
    stopAutoTimer();
  }
}

function startAutoTimer(ms) {
  stopAutoTimer();
  progStart = performance.now();
  document.getElementById("progressFill").style.width = "0%";
  progTimer = setInterval(() => {
    const pct = Math.min(100, ((performance.now() - progStart) / ms) * 100);
    document.getElementById("progressFill").style.width = pct + "%";
  }, 100);
  autoTimer = setTimeout(() => renderScene(sceneIdx + 1), ms);
}
function stopAutoTimer() {
  if (autoTimer) clearTimeout(autoTimer);
  if (progTimer) clearInterval(progTimer);
  autoTimer = progTimer = null;
  document.getElementById("progressFill").style.width = "0%";
}

function toggleSync() {
  syncOn = !syncOn;
  document.getElementById("syncBtn").classList.toggle("active", syncOn);
}

function toggleFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen();
}

function togglePresenter() {
  document.getElementById("presenter").classList.toggle("presenter-hidden");
}
function toggleHelp() {
  document.getElementById("helpOverlay").classList.toggle("help-hidden");
}
function hideHelp() {
  document.getElementById("helpOverlay").classList.add("help-hidden");
}


/* ── Idle-cursor hide ────────────────────────────────────── */
function trackIdleCursor() {
  let t;
  const wake = () => {
    document.body.classList.remove("idle");
    clearTimeout(t);
    t = setTimeout(() => document.body.classList.add("idle"), 3000);
  };
  ["mousemove", "keydown", "click"].forEach(ev =>
    document.addEventListener(ev, wake));
  wake();
}
