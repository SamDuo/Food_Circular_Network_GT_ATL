/* ════════════════════════════════════════════════════════════
   AFCN Force-Directed Graph — vanilla force-graph (no React).
   Same engine as react-force-graph (vasturiano), Canvas + d3-force.

   Nodes: 9 type categories + 26 activity tags + 802 orgs
   Links: type↔activity (per connects_to) · org↔type · org↔activity
   ════════════════════════════════════════════════════════════ */

const DATA_URLS = ['../data/afcn_network.json',
                    './data/afcn_network.json'];
const HERO_FALLBACK_DEK = 'Click any node to inspect. Drag to rearrange. Scroll to zoom.';

const NODE_KIND = { type: 'type', activity: 'activity', org: 'org' };
const KIND_COLOR = {
  activity: '#ff8a5b',     // warm clay accent
};
const BG_COLOR        = '#0b0d12';
const LINK_COLOR      = 'rgba(255, 255, 255, 0.10)';
const LINK_HOT_COLOR  = 'rgba(255, 255, 255, 0.85)';
const LABEL_BG_COLOR  = 'rgba(11, 13, 18, 0.85)';
const LABEL_TEXT      = '#e6e9ef';
const HALO_COLOR      = 'rgba(255, 138, 91, 0.22)';

let DATA = null;
let GRAPH = null;
let NODES = [];
let LINKS = [];
let highlighted = new Set();
let highlightedLinks = new Set();
let hovered = null;
let visibility = { orgs: true, types: true, activities: true };
let typeVisible = {};   // type id -> bool

(async function boot() {
  try {
    DATA = await loadData();
  } catch (err) {
    console.error('Could not load network data', err);
    document.getElementById('forceHint').textContent =
      'Could not load data — run python scripts/build_afcn_taxonomy.py first.';
    return;
  }

  document.getElementById('dataMeta').textContent =
    `${DATA.n_orgs} orgs · ${DATA.types.length} categories · ${DATA.activities.length} activity tags · generated ${DATA.generated}`;

  buildGraphData();
  initToolsUI();
  initGraph();
  applyVisibility();

  window.addEventListener('resize', () => {
    if (GRAPH) {
      const wrap = document.getElementById('graph');
      GRAPH.width(wrap.clientWidth).height(wrap.clientHeight);
    }
  });
})();


async function loadData() {
  for (const url of DATA_URLS) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) continue;
      return await r.json();
    } catch { /* try next */ }
  }
  throw new Error('no data file found');
}


/* ── Build graph nodes + links from taxonomy ─────────────── */
function buildGraphData() {
  const typeById = Object.fromEntries(DATA.types.map(t => [t.id, t]));
  const actById  = Object.fromEntries(DATA.activities.map(a => [a.id, a]));

  NODES = [];

  // Types — sized by org count. With no center anchor, the type nodes
  // become the natural cluster centers (each one repels the others via
  // d3-force; their attached orgs orbit close in).
  DATA.types.forEach(t => {
    NODES.push({
      id: 't:' + t.id, kind: NODE_KIND.type, typeId: t.id,
      label: t.label, color: t.color, val: 8 + Math.sqrt(t.count) * 1.4,
    });
    typeVisible[t.id] = true;
  });

  // Activities
  DATA.activities.forEach(a => {
    NODES.push({
      id: 'a:' + a.id, kind: NODE_KIND.activity, activityId: a.id,
      label: a.label, color: KIND_COLOR.activity, val: 4 + Math.sqrt(a.count || 1) * 1.1,
    });
    (a.connects_to || []).forEach(tid => {
      LINKS.push({ source: 't:' + tid, target: 'a:' + a.id, kind: 'type-activity' });
    });
  });

  // Orgs
  (DATA.orgs || []).forEach(o => {
    const t = typeById[o.type_id];
    NODES.push({
      id: 'o:' + o.id, kind: NODE_KIND.org, orgId: o.id,
      label: o.label, color: t ? t.color : '#9e9e9e',
      typeId: o.type_id,
      val: 2.2 + Math.min(6, (o.degree || 0) * 0.4),
      _org: o,
    });
    if (o.type_id) {
      LINKS.push({ source: 'o:' + o.id, target: 't:' + o.type_id, kind: 'org-type' });
    }
    (o.activities || []).forEach(aid => {
      if (actById[aid]) {
        LINKS.push({ source: 'o:' + o.id, target: 'a:' + aid, kind: 'org-activity' });
      }
    });
  });

  document.getElementById('cntOrgs').textContent  = `(${(DATA.orgs || []).length})`;
  document.getElementById('cntTypes').textContent = `(${DATA.types.length})`;
  document.getElementById('cntActs').textContent  = `(${DATA.activities.length})`;
}


/* ── Sidebar UI: filter, sliders, legend ─────────────────── */
function initToolsUI() {
  const tf = document.getElementById('typeFilter');
  tf.innerHTML = '';
  DATA.types.forEach(t => {
    const row = document.createElement('div');
    row.className = 'type-row';
    row.dataset.tid = t.id;
    row.innerHTML =
      `<span class="swatch" style="background:${t.color}"></span>
       <span class="name">${t.label}</span>
       <span class="count">${t.count}</span>`;
    row.addEventListener('click', () => {
      typeVisible[t.id] = !typeVisible[t.id];
      row.classList.toggle('dimmed', !typeVisible[t.id]);
      applyVisibility();
    });
    tf.appendChild(row);
  });

  // Top-level kind toggles
  ['Orgs', 'Types', 'Activities'].forEach(k => {
    const cb = document.getElementById('show' + k);
    if (!cb) return;
    cb.addEventListener('change', () => {
      visibility[k.toLowerCase()] = cb.checked;
      applyVisibility();
    });
  });

  // Physics sliders
  document.getElementById('chargeStrength').addEventListener('input', e => {
    GRAPH.d3Force('charge').strength(+e.target.value);
    GRAPH.d3ReheatSimulation();
  });
  document.getElementById('linkDistance').addEventListener('input', e => {
    GRAPH.d3Force('link').distance(+e.target.value);
    GRAPH.d3ReheatSimulation();
  });
  document.getElementById('reheat').addEventListener('click', () => {
    GRAPH.d3ReheatSimulation();
  });

  // Legend
  const legend = document.getElementById('legendList');
  legend.innerHTML = '';
  [
    { color: '#5aa6ff',          label: 'Type categories' },
    { color: KIND_COLOR.activity, label: 'Activity tags' },
    { color: '#9e9e9e',          label: 'Organizations (colored by type)' },
  ].forEach(({ color, label }) => {
    const row = document.createElement('div');
    row.className = 'legend-row';
    row.innerHTML = `<span class="legend-dot" style="background:${color}"></span><span>${label}</span>`;
    legend.appendChild(row);
  });
}


/* ── Initialize the force graph ──────────────────────────── */
function initGraph() {
  const wrap = document.getElementById('graph');
  const W = wrap.clientWidth;
  const H = wrap.clientHeight;

  GRAPH = ForceGraph()(wrap)
    .graphData({ nodes: NODES, links: LINKS })
    .width(W).height(H)
    .backgroundColor(BG_COLOR)
    .nodeRelSize(3)
    .nodeVal(n => n.val)
    .nodeId('id')
    .nodeLabel(n => `<div style="font-family:DM Sans,sans-serif;font-size:12px;color:#e6e9ef;background:#11151c;padding:4px 8px;border:1px solid #1f242d;border-radius:4px;box-shadow:0 4px 16px rgba(0,0,0,0.4)">${escapeHtml(n.label)}</div>`)
    .nodeCanvasObjectMode(() => 'replace')
    .nodeCanvasObject(drawNode)
    .linkColor(l => highlightedLinks.has(l) ? LINK_HOT_COLOR : LINK_COLOR)
    .linkWidth(l => highlightedLinks.has(l) ? 1.4 : 0.5)
    .linkDirectionalParticles(l => highlightedLinks.has(l) ? 2 : 0)
    .linkDirectionalParticleWidth(2.2)
    .linkDirectionalParticleColor(() => '#ff8a5b')
    .onNodeHover(handleHover)
    .onNodeClick(handleClick)
    .onBackgroundClick(() => { selectNode(null); })
    .cooldownTicks(280)
    .d3VelocityDecay(0.32);

  // Tweak the underlying d3-force layout for the WEF-ish "halo" feel.
  GRAPH.d3Force('charge').strength(-120);
  GRAPH.d3Force('link').distance(60).strength(0.55);

  // (No pinned center node now — force-graph's built-in center force
  // keeps the cluster from drifting off-screen.)

  GRAPH.onEngineStop(() => {
    document.getElementById('forceStats').textContent =
      `${NODES.length} nodes · ${LINKS.length} links · cooled`;
  });
  document.getElementById('forceStats').textContent =
    `${NODES.length} nodes · ${LINKS.length} links · simulating…`;
}


/* ── Draw a node on the canvas ───────────────────────────── */
function drawNode(node, ctx, globalScale) {
  const r = Math.max(2.5, node.val * 0.55);
  const isHi = highlighted.has(node) || hovered === node;

  // Outer halo ring on highlight
  if (isHi) {
    ctx.beginPath();
    ctx.arc(node.x, node.y, r + 4, 0, Math.PI * 2);
    ctx.fillStyle = HALO_COLOR;
    ctx.fill();
  }

  // Main circle
  ctx.beginPath();
  ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
  ctx.fillStyle =
    node.kind === NODE_KIND.activity ? KIND_COLOR.activity :
    node.kind === NODE_KIND.type     ? (node.color || '#5aa6ff') :
                                        (node.color || '#9e9e9e');
  ctx.fill();
  ctx.lineWidth = isHi ? 2 / globalScale : 0.6 / globalScale;
  ctx.strokeStyle = isHi ? '#ffffff' : 'rgba(255,255,255,0.25)';
  ctx.stroke();

  // Type labels always; activity labels at higher zoom; org labels on hover.
  const showLabel =
    node.kind === NODE_KIND.type ||
    (node.kind === NODE_KIND.activity && globalScale > 1.2) ||
    isHi;
  if (showLabel) {
    const fontSize = node.kind === NODE_KIND.type ? 11 : (isHi ? 11 : 10);
    const weight   = node.kind === NODE_KIND.type ? 700 : 600;
    ctx.font = `${weight} ${fontSize / globalScale}px DM Sans, system-ui, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const label = node.label.length > 28 ? node.label.slice(0, 26) + '…' : node.label;

    // Dark halo behind label for legibility against the canvas
    ctx.fillStyle = LABEL_BG_COLOR;
    const metrics = ctx.measureText(label);
    const padX = 4 / globalScale, padY = 2 / globalScale;
    const labelY = node.y + r + (fontSize + 2) / globalScale;
    ctx.fillRect(
      node.x - metrics.width / 2 - padX,
      labelY - fontSize / globalScale / 2 - padY,
      metrics.width + padX * 2,
      fontSize / globalScale + padY * 2
    );
    ctx.fillStyle = LABEL_TEXT;
    ctx.fillText(label, node.x, labelY);
  }
}


/* ── Hover / click handlers ──────────────────────────────── */
function handleHover(node) {
  hovered = node || null;
  highlighted = new Set();
  highlightedLinks = new Set();
  if (node) {
    highlighted.add(node);
    LINKS.forEach(l => {
      const s = typeof l.source === 'object' ? l.source : NODES.find(n => n.id === l.source);
      const t = typeof l.target === 'object' ? l.target : NODES.find(n => n.id === l.target);
      if (s === node || t === node) {
        highlightedLinks.add(l);
        if (s) highlighted.add(s);
        if (t) highlighted.add(t);
      }
    });
  }
  document.body.style.cursor = node ? 'pointer' : 'default';
}

function handleClick(node) {
  selectNode(node);
  if (node && (node.kind === NODE_KIND.type || node.kind === NODE_KIND.activity || node.kind === NODE_KIND.org)) {
    // Center on the clicked node
    GRAPH.centerAt(node.x, node.y, 600);
    GRAPH.zoom(node.kind === NODE_KIND.org ? 4 : 2.5, 600);
  }
}


/* ── Right detail panel ──────────────────────────────────── */
function selectNode(node) {
  const titleEl    = document.getElementById('forcePanelTitle');
  const subtitleEl = document.getElementById('forcePanelSubtitle');
  const dekEl      = document.getElementById('forcePanelDek');
  const metaEl     = document.getElementById('forcePanelMeta');

  if (!node) {
    titleEl.textContent    = DATA.anchor.label;
    subtitleEl.textContent = `Force-directed network`;
    dekEl.textContent      = HERO_FALLBACK_DEK;
    metaEl.innerHTML = `
      <strong>Total orgs</strong><span>${DATA.n_orgs}</span>
      <strong>Categories</strong><span>${DATA.types.length}</span>
      <strong>Activity tags</strong><span>${DATA.activities.length}</span>
      <strong>Total links</strong><span>${LINKS.length.toLocaleString()}</span>`;
    return;
  }

  if (node.kind === NODE_KIND.type) {
    const t = DATA.types.find(t => t.id === node.typeId);
    titleEl.textContent    = t.label;
    subtitleEl.textContent = 'Type category';
    dekEl.textContent      = `${t.count} mapped organization${t.count === 1 ? '' : 's'}. ${t.subtitle || ''}`;
    metaEl.innerHTML = `
      <strong>Orgs</strong><span>${t.count}</span>
      <strong>Color</strong><span><span class="legend-dot" style="background:${t.color};display:inline-block;margin-right:6px"></span>${t.color}</span>`;
    return;
  }

  if (node.kind === NODE_KIND.activity) {
    const a = DATA.activities.find(x => x.id === node.activityId);
    titleEl.textContent    = a.label;
    subtitleEl.textContent = `Activity tag · ${a.count || 0} orgs`;
    dekEl.textContent      = `Tagged on ${a.count || 0} organization${a.count === 1 ? '' : 's'}, ` +
                              `spanning ${(a.connects_to || []).length} categor${(a.connects_to || []).length === 1 ? 'y' : 'ies'}.`;
    metaEl.innerHTML = `
      <strong>Tagged orgs</strong><span>${a.count || 0}</span>
      <strong>Categories</strong><span>${(a.connects_to || []).length}</span>`;
    return;
  }

  // Organization detail
  const o = node._org;
  const t = DATA.types.find(t => t.id === o.type_id);
  titleEl.textContent    = o.label;
  subtitleEl.textContent = t ? t.label : 'Organization';
  dekEl.innerHTML = (o.tagline ? `<em class="fg-tagline">${escapeHtml(o.tagline)}</em><br><br>` : '')
                   + escapeHtml(o.description || '—');

  const rows = [];

  // Region/Demographics chips above the meta grid
  const chips = [];
  if (o.region)       chips.push(`<span class="fg-chip fg-chip-region">${escapeHtml(o.region)}</span>`);
  if (o.demographics) {
    o.demographics.split(/\s*[|;,]\s*/).filter(Boolean).forEach(d => {
      chips.push(`<span class="fg-chip fg-chip-demo">${escapeHtml(d)}</span>`);
    });
  }
  if (o.business)     chips.push(`<span class="fg-chip fg-chip-business">${escapeHtml(o.business)}</span>`);
  const chipsHtml = chips.length ? `<div class="fg-chips">${chips.join('')}</div>` : '';

  if (o.address)     rows.push(`<strong>Address</strong><span>${escapeHtml(o.address)}</span>`);
  if (o.url) {
    const display = o.url.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const fav = o.favicon
      ? `<img class="fg-favicon" src="${escapeHtml(o.favicon)}" alt="" width="14" height="14" referrerpolicy="no-referrer" onerror="this.remove()">`
      : '';
    rows.push(`<strong>Website</strong><span class="fg-with-fav">${fav}<a href="${escapeHtml(o.url)}" target="_blank" rel="noopener">${escapeHtml(display)}</a></span>`);
  }
  if (o.email)       rows.push(`<strong>Email</strong><span>${escapeHtml(o.email)}</span>`);
  if (o.phone)       rows.push(`<strong>Phone</strong><span>${escapeHtml(o.phone)}</span>`);
  if (o.activity_labels && o.activity_labels.length)
    rows.push(`<strong>Activities</strong><span>${o.activity_labels.map(escapeHtml).join(' · ')}</span>`);

  if (o.socials && Object.keys(o.socials).length) {
    rows.push(`<strong>Follow</strong><span class="fg-socials">${fgSocialIconsHTML(o.socials)}</span>`);
  }

  metaEl.innerHTML = chipsHtml + rows.join('');
}

const FG_SOCIAL_ICONS = {
  instagram: 'IG', facebook: 'FB', linkedin: 'IN',
  twitter: 'X',  youtube: 'YT', tiktok: 'TT',
};
function fgSocialIconsHTML(socials) {
  return Object.entries(socials).map(([net, url]) => {
    const lbl = FG_SOCIAL_ICONS[net] || net.slice(0, 2).toUpperCase();
    return `<a class="fg-social-pill" href="${escapeHtml(url)}" target="_blank" rel="noopener" title="${escapeHtml(net)}">${lbl}</a>`;
  }).join('');
}


/* ── Visibility filter ──────────────────────────────────── */
function applyVisibility() {
  if (!GRAPH) return;
  const filteredNodes = NODES.filter(n => {
    if (n.kind === NODE_KIND.type)     return visibility.types     && typeVisible[n.typeId];
    if (n.kind === NODE_KIND.activity) return visibility.activities;
    if (n.kind === NODE_KIND.org)      return visibility.orgs      && typeVisible[n.typeId];
    return true;
  });
  const allowed = new Set(filteredNodes.map(n => n.id));
  const filteredLinks = LINKS.filter(l => {
    const sId = typeof l.source === 'object' ? l.source.id : l.source;
    const tId = typeof l.target === 'object' ? l.target.id : l.target;
    return allowed.has(sId) && allowed.has(tId);
  });
  GRAPH.graphData({ nodes: filteredNodes, links: filteredLinks });
  document.getElementById('forceStats').textContent =
    `${filteredNodes.length} nodes · ${filteredLinks.length} links`;
}


/* ── Misc ────────────────────────────────────────────────── */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
