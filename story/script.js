/* ════════════════════════════════════════════════════════════
   The Atlanta Food Story — script.js
   ────────────────────────────────────────────────────────────
   • Fetches Mapbox public token from /api/config (served by serve.py)
   • Lazy-initializes a Mapbox mini-map per chapter via IntersectionObserver
   • Each chapter loads only the GeoJSON layers it needs
   • Adds chapter-specific click popups using Source Serif / Inter styling
   • Handles fade-in figure animation and a top scroll-progress bar
   ════════════════════════════════════════════════════════════ */

const GEOJSON_BASE = `${window.location.origin}/geojson`;

const ATL_CENTER  = [-84.388, 33.749];
const ATL_BBOX    = [[-84.55, 33.65], [-84.20, 33.86]];

/* ─── Chapter map definitions ─────────────────────────────── */
const CHAPTERS = {
  'big-picture': {
    center: ATL_CENTER, zoom: 10.4, pitch: 0, bearing: 0,
    layers: [
      {
        id: 'lila', kind: 'fill',
        source: 'atl_pro_food_deserts.geojson',
        paint: {
          'fill-color': 'rgba(239, 83, 80, 0.45)',
          'fill-outline-color': 'rgba(183, 28, 28, 0.85)',
        },
        popup: p => `<strong>USDA Food Desert</strong>
          <div class="pop-row"><span>Tract</span><b>${p.NAMELSAD || p.NAME || '—'}</b></div>
          <div class="pop-row"><span>Population (2010)</span><b>${(p.Pop2010 || 0).toLocaleString()}</b></div>
          <div class="pop-row"><span>LILA 1mi/10mi</span><b>${p.LILATracts_1And10 ? 'Yes' : 'No'}</b></div>`,
      },
      {
        id: 'mbr', kind: 'line',
        source: 'atl_pro_marta_bus_routes.geojson',
        // route_type=3 → bus only (file mixes bus + heavy rail)
        filter: ['==', ['to-number', ['get', 'route_type']], 3],
        paint: { 'line-color': '#26a69a', 'line-width': 1.0, 'line-opacity': 0.55 },
      },
      {
        id: 'grocery', kind: 'circle',
        source: 'atl_grocery_stores_classified.geojson',
        paint: {
          'circle-color': '#2e7d32',
          'circle-radius': 4,
          'circle-stroke-color': '#fff',
          'circle-stroke-width': 1,
        },
        popup: p => `<strong>${p.name || p.NAME || 'Grocery store'}</strong>
          <div class="pop-row"><span>Tier</span><b>${p.tier || p.category || '—'}</b></div>
          <div class="pop-row"><span>Address</span><b>${p.address || '—'}</b></div>`,
      },
    ],
  },

  'grocery-gap': {
    center: ATL_CENTER, zoom: 10.6, pitch: 0, bearing: 0,
    layers: [
      {
        id: 'cov', kind: 'fill',
        source: 'healthy_food_1mile_coverage.geojson',
        paint: {
          'fill-color': 'rgba(76, 175, 80, 0.35)',
          'fill-outline-color': 'rgba(46, 125, 50, 0.7)',
        },
      },
      {
        id: 'sup', kind: 'circle',
        source: 'pkg_supermarkets_metroatl.geojson',
        paint: {
          'circle-color': '#ab47bc', 'circle-radius': 5,
          'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2,
        },
        popup: p => `<strong>${p.name || 'Supermarket'}</strong>
          <div class="pop-row"><span>Address</span><b>${p.address || '—'}</b></div>`,
      },
      {
        id: 'fm', kind: 'circle',
        source: 'pkg_atlanta_metro_area_farmers_markets.geojson',
        paint: {
          'circle-color': '#66bb6a', 'circle-radius': 5,
          'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2,
        },
        popup: p => `<strong>${p.name || 'Farmers market'}</strong>
          <div class="pop-row"><span>Address</span><b>${p.address || '—'}</b></div>`,
      },
      {
        id: 'ff', kind: 'circle',
        source: 'pkg_all_fast_food_locations_in_metro_atlanta.geojson',
        paint: {
          'circle-color': 'rgba(239, 83, 80, 0.55)',
          'circle-radius': 2.4,
          'circle-stroke-color': 'rgba(183, 28, 28, 0.6)',
          'circle-stroke-width': 0.4,
        },
      },
    ],
  },

  'left-behind': {
    center: ATL_CENTER, zoom: 10.4, pitch: 0, bearing: 0,
    layers: [
      {
        id: 'gap', kind: 'fill',
        source: 'map1_food_retail_mrfei.geojson',
        paint: {
          'fill-color': [
            'interpolate', ['linear'], ['coalesce', ['get', 'food_access_gap'], 0],
            10, 'rgba(76,175,80,0.35)',
            30, 'rgba(255,193,7,0.45)',
            60, 'rgba(239,83,80,0.55)',
            90, 'rgba(183,28,28,0.65)',
          ],
          'fill-outline-color': 'rgba(120, 70, 50, 0.35)',
        },
        popup: p => {
          const gap = p.food_access_gap || 0;
          const label = p.gap_label || '—';
          const clr = gap >= 70 ? '#b71c1c' : gap >= 50 ? '#ef5350' : gap >= 30 ? '#ff9800' : '#4caf50';
          return `<strong>${p.tract_name || 'Census Tract'}</strong>
            <div class="pop-row"><span>Gap score</span><b style="color:${clr}">${gap}/100 · ${label}</b></div>
            <div class="pop-row"><span>mRFEI</span><b>${p.mrfei != null ? p.mrfei : '—'}</b></div>
            <div class="pop-row"><span>Median income</span><b>$${Number(p.median_income || 0).toLocaleString()}</b></div>
            <div class="pop-row"><span>Poverty rate</span><b>${p.poverty_rate || 0}%</b></div>
            <div class="pop-row"><span>No-vehicle households</span><b>${p.pct_no_vehicle || 0}%</b></div>`;
        },
      },
      {
        id: 'lila-out', kind: 'line',
        source: 'atl_pro_food_deserts.geojson',
        paint: { 'line-color': 'rgba(120, 20, 20, 0.85)', 'line-width': 1.4, 'line-dasharray': [4, 2] },
      },
    ],
  },

  'last-mile': {
    center: ATL_CENTER, zoom: 10.4, pitch: 0, bearing: 0,
    layers: [
      {
        id: 'veh', kind: 'fill',
        source: 'map3_transport_accessibility.geojson',
        paint: {
          'fill-color': [
            'interpolate', ['linear'], ['coalesce', ['get', 'pct_no_vehicle'], 0],
            0,  'rgba(150, 20, 180, 0.05)',
            10, 'rgba(150, 20, 180, 0.25)',
            25, 'rgba(150, 20, 180, 0.50)',
            50, 'rgba(80, 0, 100, 0.65)',
          ],
          'fill-outline-color': 'rgba(150, 20, 180, 0.4)',
        },
        popup: p => `<strong>${p.tract_name || 'Census Tract'}</strong>
          <div class="pop-row"><span>No-vehicle HH</span><b>${p.pct_no_vehicle || 0}%</b></div>
          <div class="pop-row"><span>Nearest grocery</span><b>${p.nearest_grocery_miles || 0} mi</b></div>
          <div class="pop-row"><span>Median income</span><b>$${Number(p.median_income || 0).toLocaleString()}</b></div>`,
      },
      {
        // Bus routes: GTFS route_type=3
        id: 'mbr', kind: 'line',
        source: 'atl_pro_marta_bus_routes.geojson',
        filter: ['==', ['to-number', ['get', 'route_type']], 3],
        paint: { 'line-color': '#26a69a', 'line-width': 1.0, 'line-opacity': 0.55 },
        popup: p => `<strong>${p.route_long_name || p.route_short_name || 'MARTA bus'}</strong>
          <div class="pop-row"><span>Route #</span><b>${p.route_short_name || '—'}</b></div>
          <div class="pop-row"><span>Type</span><b>Bus</b></div>`,
      },
      {
        // Heavy rail only: GTFS route_type=1 (Red, Gold, Blue, Green lines)
        id: 'mr', kind: 'line',
        source: 'atl_pro_marta_bus_routes.geojson',
        filter: ['==', ['to-number', ['get', 'route_type']], 1],
        paint: {
          'line-color': [
            'match', ['get', 'route_short_name'],
            'RED',   '#e53935',
            'GOLD',  '#fdd835',
            'BLUE',  '#1e88e5',
            'GREEN', '#43a047',
            '#1e88e5'   // fallback
          ],
          'line-width': 4.0,
          'line-opacity': 0.95,
        },
        popup: p => `<strong>${p.route_long_name || 'MARTA rail'}</strong>
          <div class="pop-row"><span>Line</span><b>${p.route_short_name || '—'}</b></div>
          <div class="pop-row"><span>Type</span><b>Heavy rail</b></div>`,
      },
      {
        id: 'lila-out', kind: 'line',
        source: 'atl_pro_food_deserts.geojson',
        paint: { 'line-color': 'rgba(239, 83, 80, 0.9)', 'line-width': 1.6 },
      },
    ],
  },

  'safety-net': {
    center: ATL_CENTER, zoom: 10.5, pitch: 0, bearing: 0,
    layers: [
      {
        id: 'fi', kind: 'fill',
        // CDC PLACES food insecurity (live ArcGIS REST GeoJSON)
        sourceUrl: 'https://services3.arcgis.com/ZvidGQkLaDJxRSJ2/arcgis/rest/services/PLACES_LocalData_for_BetterHealth/FeatureServer/3/query?where=StateAbbr+%3D+%27GA%27+AND+(CountyName+%3D+%27Fulton%27+OR+CountyName+%3D+%27DeKalb%27)&f=geojson&outFields=FOODINSECU_CrudePrev,CountyName,TotalPopulation,TractFIPS&resultRecordCount=3000',
        paint: {
          'fill-color': [
            'interpolate', ['linear'], ['coalesce', ['get', 'FOODINSECU_CrudePrev'], 0],
            0,  'rgba(197,108,240,0.05)',
            12, 'rgba(197,108,240,0.20)',
            22, 'rgba(155, 50, 200, 0.45)',
            32, 'rgba(110, 0, 160, 0.60)',
          ],
          'fill-outline-color': 'rgba(120, 0, 160, 0.35)',
        },
        popup: p => `<strong>Tract ${p.TractFIPS || ''}</strong>
          <div class="pop-row"><span>County</span><b>${p.CountyName || '—'}</b></div>
          <div class="pop-row"><span>Food insecurity</span><b>${p.FOODINSECU_CrudePrev || 0}%</b></div>
          <div class="pop-row"><span>Population</span><b>${(p.TotalPopulation || 0).toLocaleString()}</b></div>`,
      },
      {
        id: 'pantry', kind: 'circle',
        source: 'food_pantries_atl.geojson',
        paint: {
          'circle-color': '#f4a261', 'circle-radius': 6,
          'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5,
        },
        popup: p => `<strong>${p.name || p.NAME || 'Food pantry'}</strong>
          <div class="pop-row"><span>Type</span><b>Food pantry</b></div>
          <div class="pop-row"><span>Address</span><b>${p.address || p.ADDRESS || '—'}</b></div>`,
      },
      {
        id: 'church', kind: 'circle',
        source: 'church_pantries_atl.geojson',
        paint: {
          'circle-color': '#9c27b0', 'circle-radius': 5,
          'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2,
        },
        popup: p => `<strong>${p.name || p.NAME || 'Church-based pantry'}</strong>
          <div class="pop-row"><span>Type</span><b>Faith-based pantry</b></div>
          <div class="pop-row"><span>Address</span><b>${p.address || p.ADDRESS || '—'}</b></div>`,
      },
      {
        id: 'redist', kind: 'circle',
        source: 'redistribution_nodes.geojson',
        paint: {
          'circle-color': '#00d2ff', 'circle-radius': 5,
          'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2,
        },
        popup: p => `<strong>${p.location_name || p.name || 'Redistribution node'}</strong>
          <div class="pop-row"><span>Node type</span><b>${p.node_type || '—'}</b></div>
          <div class="pop-row"><span>Capacity</span><b>${p.capacity_lbs ? p.capacity_lbs + ' lbs' : '—'}</b></div>`,
      },
    ],
  },
};

/* ─── Mapbox token + style ────────────────────────────────── */
let mapboxToken  = null;
let resolveToken = null;
const tokenReady = new Promise(r => { resolveToken = r; });

async function loadToken() {
  // Try /api/config (local serve.py with .env). If unavailable (= deployed
  // to a static host like Cloudflare Pages / Netlify / GitHub Pages),
  // fall back to a sibling config.json that ships in the bundle.
  const candidates = ['/api/config', './config.json', '../config.json'];
  for (const url of candidates) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) continue;
      const cfg = await res.json();
      const tok = cfg.mapboxPublicKey || cfg.MAPBOX_PUBLIC_KEY || '';
      if (tok) {
        mapboxToken = tok;
        console.info(`[story] Mapbox token loaded from ${url}`);
        break;
      }
    } catch (err) {
      // try next candidate silently
    }
  }
  if (!mapboxToken) {
    console.warn('[story] No Mapbox token found in /api/config or ./config.json');
  }
  if (!mapboxToken) {
    // graceful degradation — show a notice in each map container
    document.querySelectorAll('.map-loading').forEach(el => {
      el.innerHTML = 'Map preview unavailable — set MAPBOX_PUBLIC_KEY in <code>.env</code> to render live maps. <br><a href="../resources/Layers%20%26%20Packages/index.html" style="color:#b3603a">Open the interactive dashboard →</a>';
      el.style.padding = '20px';
      el.style.textAlign = 'center';
    });
  }
  mapboxgl.accessToken = mapboxToken;
  resolveToken();
}

/* ─── Build a single chapter map ──────────────────────────── */
function buildChapterMap(container, chapterKey) {
  const def = CHAPTERS[chapterKey];
  if (!def) return;

  const map = new mapboxgl.Map({
    container,
    style: 'mapbox://styles/mapbox/light-v11',
    center: def.center,
    zoom: def.zoom,
    pitch: def.pitch || 0,
    bearing: def.bearing || 0,
    cooperativeGestures: true,    // requires Ctrl+scroll to zoom — better for editorial reading
    attributionControl: true,
  });

  map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');

  map.on('load', () => {
    // hide loading curtain
    container.classList.add('ready');

    def.layers.forEach((L, i) => {
      const srcId = `${chapterKey}-src-${L.id}`;
      const url   = L.sourceUrl || `${GEOJSON_BASE}/${L.source}`;

      map.addSource(srcId, { type: 'geojson', data: url });

      const lyrId = `${chapterKey}-lyr-${L.id}`;
      const layerSpec = {
        id: lyrId,
        type: L.kind,
        source: srcId,
        paint: L.paint,
      };
      map.addLayer(layerSpec);

      // popup wiring
      if (L.popup) {
        map.on('click', lyrId, e => {
          if (!e.features || !e.features.length) return;
          const html = L.popup(e.features[0].properties || {});
          new mapboxgl.Popup({ closeButton: true, maxWidth: '320px' })
            .setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map);
        });
        map.on('mouseenter', lyrId, () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', lyrId, () => { map.getCanvas().style.cursor = ''; });
      }
    });
  });

  return map;
}

/* ─── IntersectionObserver: lazy init + fade-in ───────────── */
async function initObserver() {
  await tokenReady;

  const figs = document.querySelectorAll('figure.full');
  const initialized = new WeakSet();

  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const fig = entry.target;
      fig.classList.add('in');

      if (initialized.has(fig)) return;
      initialized.add(fig);

      const container = fig.querySelector('.map-container');
      if (!container) return;
      const key = container.getAttribute('data-map');
      if (!key || !CHAPTERS[key]) return;
      if (!mapboxToken) return;     // fallback notice already shown

      // give the figure a tick to fade in before the heavy map init
      setTimeout(() => buildChapterMap(container, key), 80);
    });
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -10% 0px',
  });

  figs.forEach(f => obs.observe(f));
}

/* ─── Top scroll progress bar ─────────────────────────────── */
function setupScrollProgress() {
  const bar = document.createElement('div');
  bar.className = 'scroll-progress';
  document.body.appendChild(bar);

  const update = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    const pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
    bar.style.width = `${pct}%`;
  };
  document.addEventListener('scroll', update, { passive: true });
  update();
}

/* (loadFindingsChart removed — chart is now rendered inside the unified
    DOMContentLoaded fetch via drawLilaChartFromFindings) */

function prettyLabel(key) {
  const m = {
    obesity_rate:          'Obesity rate (%)',
    diabetes_rate:          'Diabetes rate (%)',
    food_insecurity_rate:   'Food insecurity (%)',
    nearest_healthy_miles:  'Distance to nearest healthy retailer (mi)',
    snap_rate:              'SNAP enrollment (%)',
    grocery_count:          'Grocery stores per tract',
    poverty_rate:           'Poverty rate (%)',
    unemployment_rate:      'Unemployment rate (%)',
    supermarket_count:      'Supermarkets per tract',
    convenience_count:      'Convenience / dollar stores',
    fastfood_count:         'Fast food per tract',
    pct_no_vehicle:         'No-vehicle households (%)',
  };
  return m[key] || key;
}
function unitFor(key) {
  if (key.endsWith('_rate'))           return '%';
  if (key === 'nearest_healthy_miles') return 'mi';
  if (key === 'pct_no_vehicle')        return '%';
  return '';
}

function drawLilaChart(container, rows, findings) {
  // Guard: figure may have opacity:0 + tiny width during early DOMContentLoaded.
  // Use offsetWidth fallback and a sane minimum so the SVG is always renderable.
  const measuredW = container.clientWidth || container.offsetWidth || 0;
  const W   = Math.max(720, measuredW - 60);
  const rowH = 60;
  const labelW = 250;
  const barW   = Math.max(W - labelW - 80, 280);
  const H = rows.length * rowH + 90;

  // Find scale per row (separate scale per row — values vary widely)
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMin meet');

  // Title
  const title = document.createElementNS(ns, 'text');
  title.setAttribute('x', 0); title.setAttribute('y', 22);
  title.setAttribute('class', 'chart-title');
  title.textContent = 'Where LILA tracts differ from the rest of metro Atlanta';
  svg.appendChild(title);

  // Subtitle
  const sub = document.createElementNS(ns, 'text');
  sub.setAttribute('x', 0); sub.setAttribute('y', 42);
  sub.setAttribute('class', 'row-meta');
  sub.textContent = `n = ${findings.n_tracts_analyzed} tracts · 57 LILA · ranked by Cohen's d`;
  svg.appendChild(sub);

  // Legend
  const legend = document.createElementNS(ns, 'g');
  legend.setAttribute('transform', `translate(${W - 220}, 32)`);
  const lEntries = [
    { c: 'var(--accent)', t: 'LILA tracts (n=57)' },
    { c: '#4a8fb5',       t: 'Non-LILA (n=473)' },
  ];
  lEntries.forEach((e, i) => {
    const g = document.createElementNS(ns, 'g');
    g.setAttribute('transform', `translate(${i * 110}, 0)`);
    const rect = document.createElementNS(ns, 'rect');
    rect.setAttribute('width', 12); rect.setAttribute('height', 12);
    rect.setAttribute('y', -10); rect.setAttribute('fill', e.c);
    g.appendChild(rect);
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', 18); t.setAttribute('y', 0);
    t.setAttribute('class', 'legend-text');
    t.textContent = e.t;
    g.appendChild(t);
    legend.appendChild(g);
  });
  svg.appendChild(legend);

  // Bars
  const startY = 70;
  rows.forEach((r, i) => {
    const y = startY + i * rowH;
    const max = Math.max(r.lila, r.non) * 1.25 || 1;

    // Row label
    const rlabel = document.createElementNS(ns, 'text');
    rlabel.setAttribute('x', 0); rlabel.setAttribute('y', y + 16);
    rlabel.setAttribute('class', 'row-label');
    rlabel.textContent = r.label;
    svg.appendChild(rlabel);

    // Effect-size meta line
    const meta = document.createElementNS(ns, 'text');
    meta.setAttribute('x', 0); meta.setAttribute('y', y + 33);
    meta.setAttribute('class', 'row-meta');
    const dStr = r.d != null ? `Cohen d = ${r.d.toFixed(2)}` : '';
    const pStr = r.p < 0.001 ? 'p < 0.001' : `p = ${r.p.toFixed(3)}`;
    meta.textContent = `${dStr} · ${pStr}`;
    svg.appendChild(meta);

    // LILA bar
    const lilaW = (r.lila / max) * barW;
    const bL = document.createElementNS(ns, 'rect');
    bL.setAttribute('x', labelW); bL.setAttribute('y', y);
    bL.setAttribute('width',  lilaW); bL.setAttribute('height', 16);
    bL.setAttribute('class', 'bar-lila');
    svg.appendChild(bL);
    const lLabel = document.createElementNS(ns, 'text');
    lLabel.setAttribute('x', labelW + lilaW + 6);
    lLabel.setAttribute('y', y + 13);
    lLabel.setAttribute('class', 'row-meta');
    lLabel.setAttribute('style', 'font-weight:600;fill:var(--accent)');
    lLabel.textContent = `${r.lila}${r.unit}`;
    svg.appendChild(lLabel);

    // Non-LILA bar
    const nonW = (r.non / max) * barW;
    const bN = document.createElementNS(ns, 'rect');
    bN.setAttribute('x', labelW); bN.setAttribute('y', y + 22);
    bN.setAttribute('width', nonW); bN.setAttribute('height', 16);
    bN.setAttribute('class', 'bar-nonlila');
    svg.appendChild(bN);
    const nLabel = document.createElementNS(ns, 'text');
    nLabel.setAttribute('x', labelW + nonW + 6);
    nLabel.setAttribute('y', y + 35);
    nLabel.setAttribute('class', 'row-meta');
    nLabel.setAttribute('style', 'font-weight:600;fill:#4a8fb5');
    nLabel.textContent = `${r.non}${r.unit}`;
    svg.appendChild(nLabel);
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

/* ─── GT campus callout (Chapter 5.5) ─────────────────────── */
function fillGtCallout(findings) {
  const g = findings.georgia_tech_tract;
  if (!g) return;
  const $ = id => document.getElementById(id);
  const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
  set('gt-gap',         g.food_access_gap ?? '—');
  set('gt-mrfei',       g.mrfei != null ? g.mrfei : '—');
  set('gt-novehicle',  (g.pct_no_vehicle ?? '—') + '%');
  set('gt-poverty',    (g.poverty_rate ?? '—') + '%');
  set('gt-supermarket', g.supermarket_count ?? '—');
  set('gt-near',       (g.nearest_healthy_miles ?? '—') + ' mi');
  // Pill colour by gap label
  const pill = $('gt-pill-band');
  if (pill && g.gap_label) {
    pill.textContent = `${g.gap_label} gap band`;
    const lab = g.gap_label.toLowerCase();
    pill.style.background = lab === 'critical' ? '#7f0000'
                          : lab === 'severe'   ? '#b71c1c'
                          : lab === 'moderate' ? '#ef6c00'
                          : lab === 'low'      ? '#558b2f'
                                                : '#2e7d32';
  }
  // Tract name into the badge
  const badge = document.querySelector('.gt-badge');
  if (badge && g.tract_name && g.neighborhood) {
    badge.textContent = `${g.tract_name} · "${g.neighborhood}"`;
  }
}

/* ─── Named extremes table (Chapter 6) ───────────────────── */
function renderExtremes(findings) {
  const host = document.getElementById('extremesTable');
  if (!host) return;
  const ex = findings.named_extremes && findings.named_extremes.food_access_gap;
  if (!ex) { host.textContent = '—'; return; }

  const gtNeighborhood = findings.georgia_tech_tract?.neighborhood || '';
  const gtTract        = findings.georgia_tech_tract?.tract_name || '';

  const row = (r, side) => {
    const isGT = r.neighborhood === gtNeighborhood && r.tract_name === gtTract;
    return `
      <tr class="ext-row ${isGT ? 'is-gt' : ''}">
        <td class="ext-rank"></td>
        <td>
          <div class="ext-name">${r.neighborhood || '—'}${isGT ? '<span class="ext-tag">our office</span>' : ''}</div>
          <span class="ext-tract">${r.tract_name || ''}</span>
        </td>
        <td class="ext-meta">${r.gap_label || '—'}${r.is_lila ? ' · LILA' : ''}</td>
        <td class="ext-meta">$${(r.median_income || 0).toLocaleString()}</td>
        <td class="ext-meta">${r.supermarket_count || 0} super · ${r.convenience_count || 0} conv</td>
        <td class="ext-score ${side === 'top' ? 'worst' : 'best'}">${r.food_access_gap}</td>
      </tr>`;
  };

  let html = `<table>
    <thead><tr>
      <th></th><th>Neighborhood / Tract</th><th>Band</th>
      <th>Median income</th><th>Retail mix</th><th>Gap</th>
    </tr></thead><tbody>`;

  html += `<tr class="ext-section"><td colspan="6">Five widest gaps</td></tr>`;
  ex.top.forEach((r, i) => {
    html += row({...r, _rank: i + 1}, 'top').replace('class="ext-rank"></td>',
                                                      `class="ext-rank">${i + 1}</td>`);
  });

  html += `<tr class="ext-section"><td colspan="6">Five narrowest gaps</td></tr>`;
  ex.bottom.forEach((r, i) => {
    html += row({...r, _rank: i + 1}, 'bottom').replace('class="ext-rank"></td>',
                                                         `class="ext-rank">${i + 1}</td>`);
  });

  html += `</tbody></table>`;
  host.innerHTML = html;
}

/* ─── Moran's I list (Chapter 7) ──────────────────────────── */
function renderMorans(findings) {
  const host = document.getElementById('moransList');
  if (!host) return;
  const m = findings.morans_i || {};
  const order = ['food_insecurity_rate', 'pct_no_vehicle',
                 'food_access_gap',      'mrfei',
                 'convenience_count'];
  const labels = {
    food_insecurity_rate: 'Food insecurity rate (CDC)',
    pct_no_vehicle:        '% households with no vehicle',
    food_access_gap:       'Food Access Gap Score',
    mrfei:                 'mRFEI (healthy:unhealthy ratio)',
    convenience_count:     'Convenience / dollar stores',
  };
  let html = '';
  order.forEach(k => {
    const r = m[k]; if (!r) return;
    const pStr = r.p_value < 0.001 ? 'p < 0.001' : `p = ${r.p_value.toFixed(3)}`;
    html += `<li>
      <span class="mor-var">${labels[k] || k}</span>
      <span class="mor-i">${r.I >= 0 ? '+' : ''}${r.I.toFixed(2)}</span>
      <span class="mor-p">${pStr}</span>
      <span class="mor-int">${r.interpretation}</span>
    </li>`;
  });
  host.innerHTML = html;
}

/* ─── Twin tracts grid ────────────────────────────────────── */
function renderTwins(findings) {
  const host = document.getElementById('twinGrid');
  if (!host) return;
  const twins = (findings.twin_tracts || []).slice(0, 4);
  if (!twins.length) { host.textContent = '—'; return; }
  host.innerHTML = twins.map(t => `
    <div class="twin-card">
      <div class="twin-band">Income band · ${t.income_band}</div>
      <div class="twin-pair">
        <div class="twin-side high">
          <div class="twin-name">${t.high_gap.neighborhood}</div>
          <div class="twin-meta">${t.high_gap.tract_name} · $${(t.high_gap.median_income).toLocaleString()}</div>
          <div class="twin-gap">${t.high_gap.food_access_gap}</div>
          <div class="twin-meta">${t.high_gap.supermarket_count} super · ${t.high_gap.convenience_count} conv${t.high_gap.is_lila ? ' · LILA' : ''}</div>
        </div>
        <div class="twin-arrow">↔</div>
        <div class="twin-side low">
          <div class="twin-name">${t.low_gap.neighborhood}</div>
          <div class="twin-meta">${t.low_gap.tract_name} · $${(t.low_gap.median_income).toLocaleString()}</div>
          <div class="twin-gap">${t.low_gap.food_access_gap}</div>
          <div class="twin-meta">${t.low_gap.supermarket_count} super · ${t.low_gap.convenience_count} conv${t.low_gap.is_lila ? ' · LILA' : ''}</div>
        </div>
      </div>
    </div>
  `).join('');
}

/* ═══════════════════════════════════════════════════════════
   Small-multiple choropleths (Chapter 7c)
   Three side-by-side mini-maps showing the top three
   contributors to the Food Access Gap Score: convenience-store
   density, % no-vehicle households, and poverty rate.
   ═══════════════════════════════════════════════════════════ */
const SMALL_MULT_PANELS = [
  {
    key:    'convenience_count',
    label:  'Convenience / dollar stores per tract',
    note:   'POI driver',
    ramp:   ['#fff5e8', '#f5b577', '#d36c2f', '#7c3e1f'],
    domain: [0, 4],
  },
  {
    key:    'pct_no_vehicle',
    label:  '% households with no vehicle',
    note:   'transit driver',
    ramp:   ['#f3eef7', '#c89cd6', '#9c50ba', '#5e1d80'],
    domain: [0, 30],
  },
  {
    key:    'poverty_rate',
    label:  'Poverty rate (%)',
    note:   'income driver',
    ramp:   ['#eaf3ee', '#9ec9b1', '#4a8f6f', '#1c5a3f'],
    domain: [0, 50],
  },
];

function rampColor(v, domain, ramp) {
  if (v == null || isNaN(v)) return '#e8e6df';
  const t = Math.max(0, Math.min(1, (v - domain[0]) / (domain[1] - domain[0])));
  const seg = t * (ramp.length - 1);
  const i = Math.floor(seg);
  const f = seg - i;
  if (i >= ramp.length - 1) return ramp[ramp.length - 1];
  return mix(ramp[i], ramp[i + 1], f);
}
function mix(a, b, t) {
  const pa = parseHex(a), pb = parseHex(b);
  const r = Math.round(pa[0] + (pb[0] - pa[0]) * t);
  const g = Math.round(pa[1] + (pb[1] - pa[1]) * t);
  const b2 = Math.round(pa[2] + (pb[2] - pa[2]) * t);
  return `rgb(${r},${g},${b2})`;
}
function parseHex(h) {
  h = h.replace('#', '');
  return [parseInt(h.slice(0, 2), 16),
          parseInt(h.slice(2, 4), 16),
          parseInt(h.slice(4, 6), 16)];
}

async function renderSmallMultiples(findings) {
  const host = document.getElementById('smallMultiples');
  if (!host) return;
  let gj;
  try {
    const res = await fetch(`${GEOJSON_BASE}/map1_food_retail_mrfei.geojson`);
    gj = await res.json();
  } catch (err) {
    host.innerHTML = '<p style="color:#999;font-family:Inter,sans-serif">Could not load tract polygons.</p>';
    return;
  }

  // Atlanta study area bbox (Fulton + DeKalb)
  const BBOX = { minLon: -84.66, maxLon: -84.05, minLat: 33.55, maxLat: 33.94 };
  const PANEL_W = 320, PANEL_H = 380;
  const PAD = 14;
  const TOTAL_W = PANEL_W * 3 + PAD * 4;
  const TOTAL_H = PANEL_H + 92;

  const project = ([lon, lat]) => {
    const x = (lon - BBOX.minLon) / (BBOX.maxLon - BBOX.minLon);
    const y = 1 - (lat - BBOX.minLat) / (BBOX.maxLat - BBOX.minLat);
    return [x * (PANEL_W - 18) + 9, y * (PANEL_H - 50) + 36];
  };

  const ringToPath = ring => {
    if (!ring || !ring.length) return '';
    const pts = ring.map(project);
    return 'M' + pts.map(p => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join('L') + 'Z';
  };

  const featurePath = feat => {
    const g = feat.geometry; if (!g) return '';
    if (g.type === 'Polygon') {
      return g.coordinates.map(ringToPath).join(' ');
    }
    if (g.type === 'MultiPolygon') {
      return g.coordinates.map(poly => poly.map(ringToPath).join(' ')).join(' ');
    }
    return '';
  };

  // Identify highlights
  const gtTractId  = findings.georgia_tech_tract?.census_tract_id;
  const worstIds   = (findings.named_extremes?.food_access_gap?.top || [])
                       .slice(0, 3).map(r => r.census_tract_id);

  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${TOTAL_W} ${TOTAL_H}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMin meet');

  SMALL_MULT_PANELS.forEach((panel, idx) => {
    const ox = PAD + idx * (PANEL_W + PAD);
    const oy = 0;
    const g = document.createElementNS(ns, 'g');
    g.setAttribute('transform', `translate(${ox}, ${oy})`);

    // Title
    const title = document.createElementNS(ns, 'text');
    title.setAttribute('x', 4); title.setAttribute('y', 18);
    title.setAttribute('class', 'sm-panel-title');
    title.textContent = panel.label;
    g.appendChild(title);

    const meta = document.createElementNS(ns, 'text');
    meta.setAttribute('x', 4); meta.setAttribute('y', 32);
    meta.setAttribute('class', 'sm-panel-meta');
    meta.textContent = `${panel.note} · range ${panel.domain[0]}–${panel.domain[1]}`;
    g.appendChild(meta);

    // Tract polygons
    gj.features.forEach(feat => {
      const p = feat.properties || {};
      const v = p[panel.key];
      const path = document.createElementNS(ns, 'path');
      path.setAttribute('d', featurePath(feat));
      path.setAttribute('class', 'sm-tract');
      path.setAttribute('fill', rampColor(v, panel.domain, panel.ramp));
      g.appendChild(path);
    });

    // Highlight: GT tract — bold accent outline
    if (gtTractId) {
      const f = gj.features.find(f => f.properties.census_tract_id === gtTractId);
      if (f) {
        const path = document.createElementNS(ns, 'path');
        path.setAttribute('d', featurePath(f));
        path.setAttribute('class', 'sm-highlight-gt');
        g.appendChild(path);
        if (idx === 0) {  // label only on first panel to avoid clutter
          const c = projectCentroid(f, project);
          if (c) {
            const lbl = document.createElementNS(ns, 'text');
            lbl.setAttribute('x', c[0] + 6); lbl.setAttribute('y', c[1] + 4);
            lbl.setAttribute('class', 'sm-label gt');
            lbl.textContent = 'GT';
            g.appendChild(lbl);
          }
        }
      }
    }
    // Highlight: worst-3 tracts
    worstIds.forEach((wid, i) => {
      const f = gj.features.find(f => f.properties.census_tract_id === wid);
      if (!f) return;
      const path = document.createElementNS(ns, 'path');
      path.setAttribute('d', featurePath(f));
      path.setAttribute('class', 'sm-highlight-worst');
      g.appendChild(path);
      if (idx === 2) {  // label on rightmost panel
        const c = projectCentroid(f, project);
        if (c) {
          const lbl = document.createElementNS(ns, 'text');
          lbl.setAttribute('x', c[0] + 5); lbl.setAttribute('y', c[1]);
          lbl.setAttribute('class', 'sm-label worst');
          lbl.textContent = (f.properties.neighborhood || '').slice(0, 16) || 'Worst';
          g.appendChild(lbl);
        }
      }
    });

    // Legend gradient bar
    const lg = document.createElementNS(ns, 'g');
    lg.setAttribute('transform', `translate(4, ${PANEL_H + 6})`);
    const legendW = PANEL_W - 8;
    const segs = 32;
    for (let s = 0; s < segs; s++) {
      const t = s / (segs - 1);
      const v = panel.domain[0] + t * (panel.domain[1] - panel.domain[0]);
      const r = document.createElementNS(ns, 'rect');
      r.setAttribute('x', s * (legendW / segs));
      r.setAttribute('y', 0);
      r.setAttribute('width', legendW / segs + 0.5);
      r.setAttribute('height', 8);
      r.setAttribute('fill', rampColor(v, panel.domain, panel.ramp));
      lg.appendChild(r);
    }
    const lt0 = document.createElementNS(ns, 'text');
    lt0.setAttribute('x', 0); lt0.setAttribute('y', 22);
    lt0.setAttribute('class', 'sm-legend-text');
    lt0.textContent = String(panel.domain[0]);
    lg.appendChild(lt0);
    const lt1 = document.createElementNS(ns, 'text');
    lt1.setAttribute('x', legendW); lt1.setAttribute('y', 22);
    lt1.setAttribute('class', 'sm-legend-text');
    lt1.setAttribute('text-anchor', 'end');
    lt1.textContent = String(panel.domain[1]);
    lg.appendChild(lt1);
    g.appendChild(lg);

    svg.appendChild(g);
  });

  // Footer legend (highlight key)
  const foot = document.createElementNS(ns, 'g');
  foot.setAttribute('transform', `translate(${PAD}, ${TOTAL_H - 28})`);
  const items = [
    { dash: false,  c: 'var(--accent)', t: 'Georgia Tech (Tract 10.02)' },
    { dash: true,   c: '#b71c1c',       t: 'Top-3 worst on Food Access Gap (named on right panel)' },
  ];
  items.forEach((it, i) => {
    const xx = i * 360;
    const r  = document.createElementNS(ns, 'rect');
    r.setAttribute('x', xx); r.setAttribute('y', 0);
    r.setAttribute('width', 22); r.setAttribute('height', 12);
    r.setAttribute('fill', 'transparent');
    r.setAttribute('stroke', it.c);
    r.setAttribute('stroke-width', it.dash ? 1.6 : 2.4);
    if (it.dash) r.setAttribute('stroke-dasharray', '2 2');
    foot.appendChild(r);
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', xx + 30); t.setAttribute('y', 10);
    t.setAttribute('class', 'sm-legend-text');
    t.textContent = it.t;
    foot.appendChild(t);
  });
  svg.appendChild(foot);

  host.innerHTML = '';
  host.appendChild(svg);
}

function projectCentroid(feat, project) {
  const g = feat.geometry; if (!g) return null;
  let ring;
  if (g.type === 'Polygon')      ring = g.coordinates[0];
  else if (g.type === 'MultiPolygon') {
    ring = g.coordinates.reduce((a, p) => p[0].length > (a?.length || 0) ? p[0] : a, null);
  }
  if (!ring) return null;
  let sx = 0, sy = 0, n = 0;
  ring.forEach(pt => { sx += pt[0]; sy += pt[1]; n++; });
  return project([sx / n, sy / n]);
}

/* ─── Boot ────────────────────────────────────────────────── */
loadToken();
setupScrollProgress();

document.addEventListener('DOMContentLoaded', async () => {
  initObserver();

  // All findings-driven renderers share a single fetch.
  // Try multiple locations so it works locally (story/ under project root,
  // ../data/ relative) AND when deployed flat to a static host (./data/).
  const fjCandidates = ['../data/analysis_findings.json',
                        './data/analysis_findings.json',
                        'data/analysis_findings.json',
                        'analysis_findings.json'];
  let findings = null;
  for (const url of fjCandidates) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) continue;
      findings = await res.json();
      console.info(`[story] analysis_findings.json loaded from ${url} (${Object.keys(findings).length} sections)`);
      break;
    } catch (err) {
      // try next
    }
  }
  if (!findings) {
    console.warn('[story] analysis_findings.json not found in any candidate path');
    return;
  }

  // Each renderer is wrapped so one failure doesn't kill the others.
  // safe() handles both sync and async renderers (returned promises).
  const targets = {
    fillGtCallout:             'gtCallout',
    renderExtremes:            'extremesTable',
    renderMorans:              'moransList',
    renderTwins:               'twinGrid',
    drawLilaChartFromFindings: 'lilaChart',
    renderSmallMultiples:      'smallMultiples',
  };
  const showError = (name, err) => {
    console.error(`[story] ${name} failed:`, err);
    const id = targets[name];
    if (!id) return;
    const host = document.getElementById(id);
    if (host) host.innerHTML = `<p style="color:#b71c1c;font-family:Inter,sans-serif;padding:14px">Renderer "${name}" failed: ${err && err.message || err}. See browser console for stack trace.</p>`;
  };
  const safe = async (name, fn) => {
    try {
      await fn(findings);
      console.info(`[story] ${name} ✓`);
    } catch (err) {
      showError(name, err);
    }
  };

  // Run all renderers; failures are isolated and reported inline.
  await safe('fillGtCallout',             fillGtCallout);
  await safe('renderExtremes',            renderExtremes);
  await safe('renderMorans',              renderMorans);
  await safe('renderTwins',               renderTwins);
  await safe('drawLilaChartFromFindings', drawLilaChartFromFindings);
  await safe('renderSmallMultiples',      renderSmallMultiples);
});

/* shim so the existing loadFindingsChart still works after we
   inlined the findings fetch above. */
function drawLilaChartFromFindings(findings) {
  const container = document.getElementById('lilaChart');
  if (!container) return;
  const rows = (findings.lila_vs_nonlila_ttests || [])
    .filter(r => Math.abs(r.cohen_d || 0) >= 0.4)
    .filter(r => !['median_income'].includes(r.predictor))
    .slice(0, 8)
    .map(r => ({
      key: r.predictor,
      label: prettyLabel(r.predictor),
      lila: Math.abs(r.lila_mean),
      non:  Math.abs(r.non_lila_mean),
      lila_higher: r.lila_mean >= r.non_lila_mean,
      d:    r.cohen_d,
      p:    r.p_value,
      unit: unitFor(r.predictor),
    }));
  drawLilaChart(container, rows, findings);
}
