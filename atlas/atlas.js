/* AFCN Atlas — browse the 42-cell matrix.
 * Three columns: scrollable layer rail · left map · right map.
 * Click any layer's L button to load it into the left panel; R for right.
 * Maps stay synced (toggle with the SYNC button at the bottom of the rail).
 *
 * Reuses the same renderer dispatch + legend builder pattern as the
 * showcase, but here the user picks layers freely instead of stepping
 * through a fixed scene script. Loaders import the showcase's render
 * helpers via inline duplication (kept small enough to be maintained
 * here without module bundling).
 */

const MANIFEST_URL = "manifest.json";
const GEOJSON_DIR  = "../geojson/";

// City of Atlanta bounding box — keeps the visual focus tight to the city
// proper instead of drifting across all of Fulton + DeKalb. Used both as the
// initial extent and as a pan constraint via view.constraints.geometry.
const ATLANTA_EXTENT_WGS84 = {
  xmin: -84.5510, ymin: 33.6479,
  xmax: -84.2895, ymax: 33.8868,
  spatialReference: { wkid: 4326 },
};

let MANIFEST  = null;
let leftView, rightView, leftMap, rightMap;
let leftLayer = null,  rightLayer = null;
let suppressSync = false;
let syncOn = true;
let selected = { left: null, right: null };  // { catIdx, layerIdx }

const LENSES = ["base", "density", "accessibility", "equity", "trend", "flow"];

let mapsReady = null;

(async function boot() {
  MANIFEST = await (await fetch(MANIFEST_URL)).json();
  const total = MANIFEST.categories.reduce((n, c) => n + c.layers.length, 0);
  document.getElementById("dataMeta").textContent =
    `${MANIFEST.categories.length} subsystems · ${total} layers`;
  document.getElementById("railCount").textContent = `${total} layers`;

  document.body.classList.add("view-grid");

  // Render the synchronous UI first — these do not depend on the maps,
  // so the matrix grid + view toggle + rail are interactive immediately.
  renderMatrixGrid();
  renderRail();
  bindRailActions();
  bindViewToggle();

  // Maps boot in parallel; click handlers will await mapsReady before loading.
  mapsReady = initMaps().catch(err => {
    console.error("map init failed:", err);
    throw err;
  });
})();


/* ── View toggle (Matrix Grid ↔ Layer Browser) ───────────── */
function bindViewToggle() {
  const grid = document.getElementById("viewGridBtn");
  const browse = document.getElementById("viewBrowseBtn");
  const home = document.getElementById("atlasHomeBtn");
  const goGrid = () => {
    document.body.classList.add("view-grid");
    document.body.classList.remove("view-browse");
    grid.classList.add("active"); browse.classList.remove("active");
    const drawer = document.getElementById("cellDrawer");
    if (drawer) drawer.classList.remove("open");
    if (history && history.replaceState) history.replaceState(null, "", "#grid");
  };
  const goBrowse = () => {
    document.body.classList.add("view-browse");
    document.body.classList.remove("view-grid");
    browse.classList.add("active"); grid.classList.remove("active");
    if (history && history.replaceState) history.replaceState(null, "", "#browse");
  };
  grid.onclick = goGrid;
  browse.onclick = goBrowse;
  if (home) home.onclick = goGrid;

  // Honor hash deep-links so collaborators can share #grid / #browse
  if (location.hash === "#browse") goBrowse();
  window.addEventListener("hashchange", () => {
    if (location.hash === "#browse") goBrowse();
    else if (location.hash === "#grid" || location.hash === "") goGrid();
  });
}


/* ── Matrix grid (8 subsystems × 6 lenses) ───────────────── */
function renderMatrixGrid() {
  const root = document.getElementById("matrixGrid");
  root.innerHTML = "";
  for (const cat of MANIFEST.categories) {
    // Row label
    const head = document.createElement("div");
    head.className = "row-head";
    const layerCount = cat.layers.length;
    head.innerHTML = `
      <div class="row-head-label">${cat.label}</div>
      <div class="row-head-sub">${cat.subtitle || ""}</div>
      <div class="row-head-count">${layerCount} layer${layerCount === 1 ? "" : "s"}</div>
    `;
    root.appendChild(head);

    // 6 lens columns — bucket the row's layers by lens
    for (const lens of LENSES) {
      const matches = cat.layers.filter(l => (l.lens || "base") === lens);
      // Synthesis row uses a single cell — show under "base" column for it
      const isSynthesisRow = cat.id === "typology";
      const display = isSynthesisRow && lens === "base"
                       ? cat.layers
                       : matches;
      const empty   = display.length === 0;
      const lensThumb = isSynthesisRow && lens === "base"
                        ? "synthesis"
                        : lens;
      const cell = document.createElement("div");
      cell.className = "cell" + (empty ? " empty" : "");
      cell.dataset.cat = cat.id;
      cell.dataset.lens = lens;
      cell.innerHTML = `
        <div class="cell-thumb" data-lens="${lensThumb}"></div>
        <div class="cell-meta">
          <div class="cell-count">${empty ? "—" : `${display.length} ${display.length === 1 ? "map" : "maps"}`}</div>
          <div class="cell-preview">${empty ? "waiting on data" : display[0].label}</div>
        </div>
      `;
      if (!empty) {
        cell.addEventListener("click", () => openDrawer(cat, lens, display));
      }
      root.appendChild(cell);
    }
  }
}


/* ── Drawer that lists layers for a clicked cell ─────────── */
function ensureDrawer() {
  let d = document.getElementById("cellDrawer");
  if (d) return d;
  d = document.createElement("aside");
  d.id = "cellDrawer";
  d.innerHTML = `
    <div class="drawer-head">
      <button class="drawer-close" type="button" aria-label="Close drawer">×</button>
      <div class="drawer-eyebrow" id="drawerEyebrow"></div>
      <div class="drawer-title"   id="drawerTitle"></div>
      <div class="drawer-sub"     id="drawerSub"></div>
    </div>
    <div class="drawer-list" id="drawerList"></div>
    <div class="drawer-foot">L = load into LEFT panel · R = load into RIGHT panel · auto-switches to map view</div>
  `;
  document.body.appendChild(d);
  d.querySelector(".drawer-close").onclick = () => d.classList.remove("open");
  // Click outside drawer also closes
  document.addEventListener("click", (e) => {
    if (!d.classList.contains("open")) return;
    if (e.target.closest("#cellDrawer")) return;
    if (e.target.closest(".cell")) return;
    d.classList.remove("open");
  });
  return d;
}

function openDrawer(category, lens, layers) {
  const d = ensureDrawer();
  document.getElementById("drawerEyebrow").textContent =
    `${category.label.toUpperCase()} · ${lens.toUpperCase()} LENS`;
  document.getElementById("drawerTitle").textContent =
    layers.length === 1 ? layers[0].label
                        : `${layers.length} maps in this cell`;
  document.getElementById("drawerSub").textContent =
    category.subtitle || "";
  const list = document.getElementById("drawerList");
  list.innerHTML = "";
  layers.forEach(lay => {
    const card = document.createElement("div");
    card.className = "drawer-card";
    card.innerHTML = `
      <div class="drawer-card-info">
        <div class="drawer-card-label">${lay.label}</div>
        <div class="drawer-card-source">${lay.layer}${lay.field ? " · " + lay.field : ""}${lay.mode ? " · " + lay.mode : ""}</div>
      </div>
      <div class="drawer-card-buttons">
        <button class="lr-btn left"  type="button">L</button>
        <button class="lr-btn right" type="button">R</button>
      </div>
    `;
    const cIdx = MANIFEST.categories.findIndex(c => c.id === category.id);
    const lIdx = MANIFEST.categories[cIdx].layers.findIndex(l => l.layer === lay.layer && l.field === lay.field && l.label === lay.label);
    card.querySelector(".lr-btn.left").onclick = () => {
      pickLayer("left", cIdx, lIdx);
      switchToBrowseView();
      d.classList.remove("open");
    };
    card.querySelector(".lr-btn.right").onclick = () => {
      pickLayer("right", cIdx, lIdx);
      switchToBrowseView();
      d.classList.remove("open");
    };
    list.appendChild(card);
  });
  d.classList.add("open");
}

function switchToBrowseView() {
  document.body.classList.add("view-browse");
  document.body.classList.remove("view-grid");
  document.getElementById("viewGridBtn").classList.remove("active");
  document.getElementById("viewBrowseBtn").classList.add("active");
}


/* ── ArcGIS init ─────────────────────────────────────────── */
function initMaps() {
  return new Promise((resolve) => {
    require([
      "esri/Map", "esri/views/MapView", "esri/layers/GeoJSONLayer", "esri/config",
    ], (Map, MapView, GeoJSONLayer, esriConfig) => {
      fetch("/api/config").then(r => r.json()).then(cfg => {
        if (cfg && cfg.arcgisApiKey) esriConfig.apiKey = cfg.arcgisApiKey;
      }).catch(() => {});

      leftMap  = new Map({ basemap: "dark-gray-vector" });
      rightMap = new Map({ basemap: "dark-gray-vector" });
      const viewOpts = {
        extent: ATLANTA_EXTENT_WGS84,
        ui: { components: ["zoom"] },
        constraints: {
          geometry: ATLANTA_EXTENT_WGS84,   // pan locked to Atlanta city
          minZoom: 10,                       // can't zoom out past city scale
          maxZoom: 18,
          rotationEnabled: false,
        },
      };
      leftView  = new MapView({ ...viewOpts, container: "leftMap",  map: leftMap  });
      rightView = new MapView({ ...viewOpts, container: "rightMap", map: rightMap });

      window._GeoJSONLayer = GeoJSONLayer;
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


/* ── Render the layer rail ───────────────────────────────── */
function renderRail() {
  const root = document.getElementById("railContent");
  root.innerHTML = "";
  MANIFEST.categories.forEach((cat, ci) => {
    const sec = document.createElement("section");
    sec.className = "category" + (ci > 1 ? " collapsed" : "");  // first 2 open
    sec.innerHTML = `
      <div class="category-head">
        <div class="category-label">
          ${cat.label}
          <span class="category-count">${cat.layers.length}</span>
          <span class="category-chev">▾</span>
        </div>
        <div class="category-subtitle">${cat.subtitle || ""}</div>
      </div>
      <div class="category-body"></div>
    `;
    sec.querySelector(".category-head").addEventListener("click", () => {
      sec.classList.toggle("collapsed");
    });
    const body = sec.querySelector(".category-body");
    cat.layers.forEach((lay, li) => {
      body.appendChild(buildCard(ci, li, cat, lay));
    });
    root.appendChild(sec);
  });
  bindSearch();
}

function buildCard(ci, li, cat, lay) {
  const el = document.createElement("div");
  el.className = "layer-card";
  el.dataset.cat = ci;
  el.dataset.idx = li;
  el.dataset.label = lay.label.toLowerCase();
  el.dataset.layer = lay.layer;
  el.innerHTML = `
    <div class="layer-info">
      <div class="layer-label">${lay.label}</div>
      <div class="layer-meta">
        <span class="lens-badge" data-lens="${lay.lens}">${lay.lens}</span>
        <span class="layer-source">${lay.layer}${lay.field ? " · " + lay.field : ""}</span>
      </div>
    </div>
    <div class="layer-buttons">
      <button class="lr-btn left"  data-side="left"  title="Load into LEFT panel">L</button>
      <button class="lr-btn right" data-side="right" title="Load into RIGHT panel">R</button>
    </div>
  `;
  el.querySelector(".lr-btn.left").onclick  = () => pickLayer("left",  ci, li);
  el.querySelector(".lr-btn.right").onclick = () => pickLayer("right", ci, li);
  return el;
}

function bindSearch() {
  const input = document.getElementById("railSearch");
  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    document.querySelectorAll(".layer-card").forEach(card => {
      const hay = card.dataset.label + " " + card.dataset.layer;
      card.style.display = q && !hay.includes(q) ? "none" : "";
    });
    // Auto-expand categories that contain matches
    document.querySelectorAll(".category").forEach(cat => {
      const visible = [...cat.querySelectorAll(".layer-card")].some(
        c => c.style.display !== "none");
      cat.classList.toggle("collapsed", q && !visible);
    });
  });
}

function bindRailActions() {
  document.getElementById("clearLeftBtn").onclick  = () => clearPanel("left");
  document.getElementById("clearRightBtn").onclick = () => clearPanel("right");
  document.getElementById("syncToggle").onclick = () => {
    syncOn = !syncOn;
    const btn = document.getElementById("syncToggle");
    btn.textContent = syncOn ? "SYNC ON" : "SYNC OFF";
    btn.classList.toggle("active", syncOn);
  };
}


/* ── Loading layers into a panel ─────────────────────────── */
async function pickLayer(side, ci, li) {
  const cat = MANIFEST.categories[ci];
  const lay = cat.layers[li];
  selected[side] = { catIdx: ci, layerIdx: li };

  // Update the panel label
  const titleEl = document.getElementById(side === "left" ? "leftTitle" : "rightTitle");
  titleEl.textContent = lay.label;
  titleEl.classList.remove("empty");

  // Wait for maps to finish booting if they haven't yet
  if (mapsReady) await mapsReady;

  // Load layer
  const targetMap  = side === "left" ? leftMap  : rightMap;
  if (side === "left"  && leftLayer)  targetMap.remove(leftLayer);
  if (side === "right" && rightLayer) targetMap.remove(rightLayer);

  const renderer = defaultRenderer(lay.layer, lay.field, lay.mode, lay.lens);
  const layerOpts = {
    url: `${GEOJSON_DIR}${lay.layer}.geojson`,
    title: lay.label,
    renderer,
    popupEnabled: true,
    labelsVisible: false,
  };
  if (lay.layer === "marta_stops_atl") {
    layerOpts.definitionExpression = "stop_name LIKE '%STATION%'";
  }
  const layer = new window._GeoJSONLayer(layerOpts);
  targetMap.add(layer);
  if (side === "left")  leftLayer  = layer;
  else                  rightLayer = layer;

  renderLegend(side, renderer, lay.field);
  highlightSelectedCards();
}

function clearPanel(side) {
  const targetMap  = side === "left" ? leftMap  : rightMap;
  const layer      = side === "left" ? leftLayer : rightLayer;
  if (layer) targetMap.remove(layer);
  if (side === "left")  leftLayer  = null;
  else                  rightLayer = null;
  selected[side] = null;
  const titleEl = document.getElementById(side === "left" ? "leftTitle" : "rightTitle");
  titleEl.textContent = "Pick a layer →";
  titleEl.classList.add("empty");
  document.getElementById(`${side}Legend`).innerHTML = "";
  document.getElementById(`${side}Legend`).classList.add("legend-hidden");
  highlightSelectedCards();
}

function highlightSelectedCards() {
  document.querySelectorAll(".layer-card").forEach(card => {
    const ci = +card.dataset.cat, li = +card.dataset.idx;
    const isLeft  = selected.left  && selected.left.catIdx === ci  && selected.left.layerIdx === li;
    const isRight = selected.right && selected.right.catIdx === ci && selected.right.layerIdx === li;
    card.classList.toggle("is-left",  isLeft);
    card.classList.toggle("is-right", isRight);
    card.querySelector(".lr-btn.left").classList.toggle("active", isLeft);
    card.querySelector(".lr-btn.right").classList.toggle("active", isRight);
  });
}


/* ════════════════════════════════════════════════════════════
   Renderer + legend helpers — duplicated from showcase.js so
   atlas can stand alone without a module bundler.
   ════════════════════════════════════════════════════════════ */

function defaultRenderer(name, field, mode, lens) {
  if (mode === "heatmap") return heatmapRenderer();
  if (name === "bivariate_obesity_lila" || field === "bivar_class")
    return bivariateObesityLilaRenderer();
  if (field === "ZONECLASS" || name === "atl_zoning") return zoningRenderer();
  if (field === "typology_label" || field === "typology_id") return uniqueTypologyRenderer(field);
  if (field) {
    const breaks = breaksForField(field);
    return {
      type: "class-breaks", field,
      classBreakInfos: breaks.map(([min, max, color]) => ({
        minValue: min, maxValue: max, symbol: poly(color, 0.78),
      })),
    };
  }
  if (name.includes("food_desert"))return { type: "simple", symbol: poly("#c62828", 0.55) };
  if (name.includes("typology"))   return { type: "simple", symbol: poly("#1c5c84", 0.5)  };
  if (name === "marta_stops_atl") {
    return { type: "simple", symbol: {
      type: "simple-marker", style: "circle", color: "#ffffff", size: 8,
      outline: { color: "#1a1a1a", width: 2 },
    }};
  }
  if (name === "atl_pro_marta_bus_routes" || name.includes("marta_routes"))
    return martaRouteRenderer();
  if (name.includes("rails")) {
    return { type: "simple", symbol: {
      type: "simple-line", color: "#8e98aa", width: 1, style: "dash",
    }};
  }
  if (name.includes("freeways") || name.includes("transport"))
                                   return { type: "simple", symbol: line("#9aa0a6", 1.5) };
  if (name.includes("bike"))      return { type: "simple", symbol: line("#1c5c84", 1.8) };
  if (name.includes("electric"))  return { type: "simple", symbol: line("#3a4f5e", 1.3) };
  if (name.includes("campus") || name.includes("boundary"))
                                   return { type: "simple", symbol: poly("#7a958c", 0.25) };
  // Land-use polygon layers — keep parity with showcase.js so the "How atlanta is zoned" cell
  // shows actual polygons, not centroid dots.
  if (name.includes("beltline"))           return { type: "simple", symbol: poly("#3a4f5e", 0.55) };
  if (name.includes("historic_district"))  return { type: "simple", symbol: poly("#7e9099", 0.45) };
  if (name.includes("neighborhood_plan"))  return { type: "simple", symbol: poly("#a4b1bc", 0.30) };
  if (name.includes("zoning_overlay"))     return { type: "simple", symbol: poly("#7a958c", 0.30) };
  if (name.includes("census_tracts"))      return { type: "simple", symbol: poly("#a4b1bc", 0.18) };
  if (name.includes("buildings"))          return { type: "simple", symbol: poly("#7a8a92", 0.55) };
  // Tract-level analytical polygons used as overlays without a field hint —
  // render hairline outline only, never centroid dots.
  if (name.startsWith("atl_health") || name.startsWith("atl_demographics") ||
      name.startsWith("atl_typology") || name.startsWith("atl_transit") ||
      name.startsWith("census_") || name.startsWith("atl_pro_health")) {
    return { type: "simple", symbol: {
      type: "simple-fill",
      color: [0, 0, 0, 0],
      outline: { color: "rgba(86, 90, 99, 0.35)", width: 0.4 },
    }};
  }
  // Flow lens — directional/source vs sink coloring so the two halves of an OD pair are visually distinct
  if (lens === "flow") {
    if (name.includes("redistribution")) return { type: "simple", symbol: flowMarker("#7a958c", "triangle") }; /* Nr. 59 petrolgrün */
    if (name.includes("recovery"))       return { type: "simple", symbol: flowMarker("#1c5c84", "circle")   }; /* Nr. 51 spinellblau */
    if (name.includes("network_flows") || name.includes("flow_lines"))
      return { type: "simple", symbol: line("#1c5c84", 3.2) };
    return { type: "simple", symbol: flowMarker("#1c5c84", "circle") };
  }
  return { type: "simple", symbol: dot("#1c5c84", 9) };
}

function flowMarker(color, style = "circle") {
  return {
    type: "simple-marker",
    style,                        // "triangle" reads as a directional arrowhead
    color,
    size: 12,
    outline: { color: "rgba(255,255,255,0.95)", width: 1.6 },
  };
}

// MARTA rail + bus renderer (kept in sync with showcase.js)
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

// Bivariate Stevens (2015) — obesity tertile × LILA strictness (kept in sync with showcase.js)
const BIVARIATE_OBESITY_LILA = [
  { value: 0, color: "#d2dadf", label: "Low obesity · No LILA" },
  { value: 1, color: "#c4cdd2", label: "Low obesity · Some LILA" },
  { value: 2, color: "#a4b1bc", label: "Low obesity · Strict LILA" },
  { value: 3, color: "#b6c0c9", label: "Mid obesity · No LILA" },
  { value: 4, color: "#7d9caf", label: "Mid obesity · Some LILA" },
  { value: 5, color: "#4d6f8a", label: "Mid obesity · Strict LILA" },
  { value: 6, color: "#6f8688", label: "High obesity · No LILA" },
  { value: 7, color: "#3a5a76", label: "High obesity · Some LILA" },
  { value: 8, color: "#393f44", label: "High obesity · Strict LILA" },
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

function heatmapRenderer() {
  return {
    type: "heatmap",
    radius: 28, maxDensity: 0.04, minDensity: 0,
    colorStops: [
      { ratio: 0,    color: "rgba(210, 218, 223, 0)" },     /* Nr. 55 */
      { ratio: 0.05, color: "rgba(210, 218, 223, 0.35)" },
      { ratio: 0.20, color: "rgba(164, 177, 188, 0.70)" },   /* Nr. 54 */
      { ratio: 0.45, color: "rgba(125, 156, 175, 0.85)" },   /* Nr. 57 */
      { ratio: 0.75, color: "rgba(28, 92, 132, 0.95)" },     /* Nr. 51 spinellblau */
      { ratio: 1.0,  color: "rgba(58, 79, 94, 1.0)" },       /* Nr. 50 dunkelblau */
    ],
  };
}

const TYPOLOGY_PALETTE = {
  // Kept in sync with showcase.js — High-growth Core is the deep burnt-clay
  // endpoint so it reads distinct from Disinvested Urban red.
  "High-growth Core":     "#3a4f5e",
  "Affluent Suburban":    "#7a958c",
  "Disinvested Urban":    "#c62828",
  "Industrial Logistics": "#7a8a92",
  "Emerging Mixed-use":   "#c4cdd2",
};
function uniqueTypologyRenderer(field) {
  return {
    type: "unique-value", field,
    defaultSymbol: poly("#9aa0a6", 0.55),
    uniqueValueInfos: Object.entries(TYPOLOGY_PALETTE).map(([label, color]) => ({
      value: label, symbol: poly(color, 0.78), label,
    })),
  };
}

const ZONING_FAMILIES = [
  { match: /^R[0-9-]/i, color: "#c4cdd2", label: "Residential" },
  { match: /^MR/i,      color: "#7e9099", label: "Mixed Residential" },
  { match: /^MRC/i,     color: "#7a958c", label: "Mixed-Use Comm." },
  { match: /^C[0-9-]/i, color: "#7d9caf", label: "Commercial" },
  { match: /^I[0-9-]/i, color: "#7a8a92", label: "Industrial" },
  { match: /^O[I-]/i,   color: "#7a958c", label: "Office/Inst." },
  { match: /^SPI/i,     color: "#3a4f5e", label: "Special Public Interest" },
  { match: /^PD/i,      color: "#6f8688", label: "Planned Development" },
  { match: /^LW/i,      color: "#a4b1bc", label: "Live-Work" },
  { match: /^NC/i,      color: "#1c5c84", label: "Neighborhood Comm." },
];
function zoningRenderer() {
  const codes = [
    ["R-1","Residential"],["R-2","Residential"],["R-2A","Residential"],["R-2B","Residential"],
    ["R-3","Residential"],["R-3A","Residential"],["R-4","Residential"],["R-4A","Residential"],
    ["R-4B","Residential"],["R-5","Residential"],["R-G","Residential"],["R-LC","Residential"],
    ["MR-1","Mixed Residential"],["MR-2","Mixed Residential"],["MR-3","Mixed Residential"],
    ["MR-4","Mixed Residential"],["MR-4A","Mixed Residential"],["MR-5A","Mixed Residential"],
    ["MRC-1","Mixed-Use Comm."],["MRC-2","Mixed-Use Comm."],["MRC-3","Mixed-Use Comm."],
    ["C-1","Commercial"],["C-2","Commercial"],["C-3","Commercial"],["C-4","Commercial"],["C-5","Commercial"],
    ["I-1","Industrial"],["I-2","Industrial"],
    ["O-I","Office/Inst."],["OI","Office/Inst."],
    ["SPI-1","Special Public Interest"],["SPI-2","Special Public Interest"],
    ["SPI-3","Special Public Interest"],["SPI-4","Special Public Interest"],
    ["SPI-5","Special Public Interest"],["SPI-6","Special Public Interest"],
    ["SPI-7","Special Public Interest"],["SPI-8","Special Public Interest"],
    ["SPI-9","Special Public Interest"],["SPI-10","Special Public Interest"],
    ["SPI-11","Special Public Interest"],["SPI-12","Special Public Interest"],
    ["SPI-15","Special Public Interest"],["SPI-16","Special Public Interest"],
    ["SPI-17","Special Public Interest"],["SPI-22","Special Public Interest"],
    ["PD-H","Planned Development"],["PD-MU","Planned Development"],
    ["PD-OC","Planned Development"],["PD-BP","Planned Development"],
    ["LW","Live-Work"],
    ["NC-1","Neighborhood Comm."],["NC-2","Neighborhood Comm."],
    ["NC-3","Neighborhood Comm."],["NC-4","Neighborhood Comm."],
  ];
  const familyColor = Object.fromEntries(ZONING_FAMILIES.map(f => [f.label, f.color]));
  return {
    type: "unique-value", field: "ZONECLASS",
    defaultSymbol: poly("#a4b1bc", 0.55),
    uniqueValueInfos: codes.map(([code, family]) => ({
      value: code,
      symbol: poly(familyColor[family] || "#a4b1bc", 0.78),
      label: `${code} — ${family}`,
    })),
  };
}

function breaksForField(field) {
  if (field === "median_income" || field === "B19013_001E") return [
    [0,30000,"#d2dadf"],[30000,50000,"#a4b1bc"],[50000,75000,"#7d9caf"],
    [75000,120000,"#1c5c84"],[120000,400000,"#3a4f5e"],
  ];
  if (field === "pop_density") return [
    [0,500,"#d2dadf"],[500,2000,"#a4b1bc"],[2000,5000,"#7d9caf"],
    [5000,10000,"#1c5c84"],[10000,100000,"#3a4f5e"],
  ];
  if (typeof field === "string" && field.endsWith("_CrudePrev")) return [
    [0,15,"#d2dadf"],[15,25,"#a4b1bc"],[25,35,"#7d9caf"],
    [35,45,"#1c5c84"],[45,100,"#3a4f5e"],
  ];
  if (field === "HMM_Score") return [
    [-30,-10,"#d2dadf"],[-10,0,"#a4b1bc"],[0,5,"#7d9caf"],
    [5,12,"#1c5c84"],[12,40,"#3a4f5e"],
  ];
  if (typeof field === "string" && field.startsWith("pct_")) return [
    [0,20,"#d2dadf"],[20,40,"#a4b1bc"],[40,60,"#7d9caf"],
    [60,80,"#1c5c84"],[80,100,"#3a4f5e"],
  ];
  if (field === "access_score") return [
    [0,5,"#d2dadf"],[5,15,"#a4b1bc"],[15,30,"#7d9caf"],
    [30,60,"#1c5c84"],[60,100,"#3a4f5e"],
  ];
  return [[0,25,"#d2dadf"],[25,50,"#a4b1bc"],[50,75,"#7d9caf"],[75,200,"#1c5c84"]];
}

function poly(color, opacity = 0.55) {
  return {
    type: "simple-fill",
    color: hexToRgba(color, opacity),
    outline: { color: hexToRgba(color, 0.9), width: 0.6 },
  };
}
function line(color, width = 2) { return { type: "simple-line", color, width }; }
function dot(color, size = 9) {
  return { type: "simple-marker", color, size,
            outline: { color: "rgba(255,255,255,0.85)", width: 1.2 } };
}
function hexToRgba(hex, a) {
  const m = hex.replace("#", "");
  const n = parseInt(m, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255, a];
}


/* ── Legend builder ───────────────────────────────────────── */
function renderLegend(side, renderer, field) {
  const target = document.getElementById(`${side}Legend`);
  target.innerHTML = "";
  target.classList.add("legend-hidden");
  if (!renderer) return;

  let title = "";
  const items = [];
  if (renderer.type === "class-breaks") {
    title = labelForField(field) || "Value";
    renderer.classBreakInfos.forEach(b => items.push({
      color: arrToRgba(b.symbol.color),
      label: rangeLabel(b.minValue, b.maxValue, field),
    }));
  } else if (renderer.type === "unique-value") {
    if (field === "ZONECLASS") {
      title = "Zoning family";
      ZONING_FAMILIES.forEach(f => items.push({ color: f.color, label: f.label }));
    } else if (field === "typology_label") {
      title = "Urban typology";
      Object.entries(TYPOLOGY_PALETTE).forEach(([label, color]) =>
        items.push({ color, label }));
    } else if (field === "bivar_class") {
      // Special-case bivariate — render the 3×3 grid into the legend container.
      renderBivariateLegend(target, BIVARIATE_OBESITY_LILA);
      return;
    } else if (field === "route_short_name") {
      title = "MARTA route";
      Object.entries(MARTA_RAIL_COLORS).forEach(([key, color]) =>
        items.push({ color, label: `${key.charAt(0)}${key.slice(1).toLowerCase()} Line (rail)` }));
      items.push({ color: "rgba(90,106,126,0.55)", label: "Bus routes" });
    } else {
      title = labelForField(field) || "Category";
      renderer.uniqueValueInfos.forEach(uv => items.push({
        color: arrToRgba(uv.symbol.color), label: uv.label || uv.value,
      }));
    }
  } else if (renderer.type === "heatmap") {
    title = "Density (kernel)";
    items.push({ gradient: renderer.colorStops, label: "low → high concentration" });
  }
  if (!items.length) return;
  target.classList.remove("legend-hidden");

  const tEl = document.createElement("div");
  tEl.className = "legend-title";
  tEl.textContent = title;
  target.appendChild(tEl);
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "legend-row";
    const sw = document.createElement("span");
    sw.className = "legend-swatch";
    if (item.gradient) {
      const stops = item.gradient
        .map(s => `${s.color} ${(s.ratio*100).toFixed(0)}%`).join(", ");
      sw.style.background = `linear-gradient(90deg, ${stops})`;
      sw.style.width = "82px";
    } else sw.style.background = item.color;
    const lb = document.createElement("span");
    lb.className = "legend-label";
    lb.textContent = item.label;
    row.appendChild(sw); row.appendChild(lb);
    target.appendChild(row);
  }
}

function labelForField(field) {
  if (!field) return "";
  return ({
    median_income: "Median household income",
    pop_density: "Population density (people / km²)",
    OBESITY_CrudePrev: "Adult obesity prevalence (%)",
    DIABETES_CrudePrev: "Diabetes prevalence (%)",
    DEPRESSION_CrudePrev: "Depression prevalence (%)",
    MHLTH_CrudePrev: "Poor mental health (%)",
    PHLTH_CrudePrev: "Poor physical health (%)",
    ACCESS2_CrudePrev: "Lack of insurance (%)",
    BPHIGH_CrudePrev: "High blood pressure (%)",
    CHD_CrudePrev: "Coronary heart disease (%)",
    access_score: "Transit access score",
    pct_broadband: "% with broadband",
    pct_no_internet: "% with no internet",
    pct_white: "% White",
    pct_black: "% Black",
    pct_hispanic: "% Hispanic/Latino",
    pct_bachelor_or_higher: "% Bachelor's or higher",
    pct_unemployed: "% Unemployed",
    pct_public_transit: "% Public transit commute",
    typology_label: "Urban typology",
    ZONECLASS: "Zoning class",
    FOODINSECU_CrudePrev: "Food insecurity prevalence (%)",
    HMM_Score: "Composite health-risk score",
    bivar_class: "Obesity × Food access (bivariate)",
    route_short_name: "MARTA route",
  })[field] || field;
}

function rangeLabel(min, max, field) {
  if (field === "median_income") {
    const f = v => "$" + (v >= 1000 ? Math.round(v/1000) + "k" : v);
    return `${f(min)} – ${f(max)}`;
  }
  if (field === "pop_density") return `${min.toLocaleString()} – ${max.toLocaleString()}`;
  if (typeof field === "string" &&
      (field.endsWith("_CrudePrev") || field.startsWith("pct_") || field === "access_score")) {
    return `${min}% – ${Math.min(max, 100)}%`;
  }
  return `${min} – ${max}`;
}

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

function arrToRgba(arr) {
  if (!Array.isArray(arr)) return arr;
  const [r, g, b, a] = arr;
  return `rgba(${r}, ${g}, ${b}, ${a == null ? 1 : a})`;
}
