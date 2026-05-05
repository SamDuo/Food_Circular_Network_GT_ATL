/* ════════════════════════════════════════════════════════════
   AFCN Transformation-Map · network/script.js
   ─────────────────────────────────────────────────────────────
   Two-level radial network:

     LEVEL 0 (root)
       center       = anchor (AFCN)
       inner ring   = 7-8 type categories
       outer ring   = activity tags (with cross-cutting connections
                       drawn as dotted lines to the inner ring)

     LEVEL 1 (drilled into one type)
       center       = the selected type
       inner ring   = up to 40 organizations of that type, sorted by
                       degree (kumu metric); spillover paginates
       outer ring   = activity tags filtered to those orgs

   Inspired by WEF Strategic Intelligence transformation maps.
   D3 v7 only (no other deps).
   ════════════════════════════════════════════════════════════ */

const DATA_URLS = ['../data/afcn_network.json',
                    './data/afcn_network.json'];
const HERO_DEFAULT = '../resources/Layers & Packages/img/hero_food.jpg';
const PAGE_SIZE = 40;

// Layout constants — tuned to match WEF's spacing
const INNER_RING_R = 0.46;    // fraction of viewBox half-width
const OUTER_RING_R = 0.78;
const CENTER_R     = 0.18;

// ── Boot ──────────────────────────────────────────────────────
let DATA = null;
let state = {
  view:    'root',     // 'root' | 'type' | 'activity'
  typeId:  null,
  activityId: null,
  page:    0,
  selected: null,      // org id or activity id
};
let history = [];      // [{ view, typeId, label }]

(async function boot() {
  try {
    DATA = await loadData();
    document.getElementById('dataMeta').textContent =
      `${DATA.n_orgs} organizations · ${DATA.types.length} types · ${DATA.activities.length} activity tags · generated ${DATA.generated}`;
    pushHistory({ view: 'root', label: DATA.anchor.label });
    render();
  } catch (err) {
    console.error('Could not load network data', err);
    document.getElementById('chartHint').textContent =
      `Could not load data — run python scripts/build_afcn_taxonomy.py first.`;
  }

  document.getElementById('hidePanel').addEventListener('click', () => {
    document.body.classList.toggle('panel-hidden');
    const btn   = document.getElementById('hidePanel');
    const label = btn.querySelector('.hidePanelLabel') || btn;
    label.textContent = document.body.classList.contains('panel-hidden')
      ? '← Show Panel' : 'Hide Panel →';
    // Re-render so the chart resizes into the new space
    setTimeout(render, 50);
  });

  document.getElementById('backBtn').addEventListener('click', () => {
    if (history.length > 1) {
      history.pop();
      const prev = history[history.length - 1];
      state = {
        view: prev.view,
        typeId: prev.typeId || null,
        activityId: prev.activityId || null,
        page: 0,
        selected: null,
      };
      render(/* skipHistoryPush */ true);
    }
  });

  window.addEventListener('resize', () => render(true));
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


/* ── State + history ─────────────────────────────────────── */
function pushHistory(entry) {
  // de-dupe consecutive
  if (history.length && history[history.length - 1].view === entry.view
      && history[history.length - 1].typeId === entry.typeId) return;
  history.push(entry);
  renderHistory();
}

function goToType(typeId) {
  const t = DATA.types.find(t => t.id === typeId);
  if (!t) return;
  state = { view: 'type', typeId, activityId: null, page: 0, selected: null };
  pushHistory({ view: 'type', typeId, label: t.label });
  render();
}

function goToActivity(activityId) {
  const a = DATA.activities.find(a => a.id === activityId);
  if (!a) return;
  state = { view: 'activity', typeId: null, activityId, page: 0, selected: null };
  pushHistory({ view: 'activity', activityId, label: a.label });
  render();
}

function goToRoot() {
  state = { view: 'root', typeId: null, activityId: null, page: 0, selected: null };
  pushHistory({ view: 'root', label: DATA.anchor.label });
  render();
}


/* ── Top breadcrumb + history dropdown ───────────────────── */
function renderHistory() {
  // Breadcrumb (current path: root → type if drilled in)
  const bcEl = document.getElementById('breadcrumb');
  bcEl.innerHTML = '';
  // Always show anchor
  const anchorLi = document.createElement('li');
  const anchorBtn = document.createElement('button');
  anchorBtn.textContent = DATA.anchor.label;
  anchorBtn.addEventListener('click', () => {
    if (state.view !== 'root') goToRoot();
  });
  anchorLi.appendChild(anchorBtn);
  bcEl.appendChild(anchorLi);

  if (state.view === 'type' && state.typeId) {
    const t = DATA.types.find(x => x.id === state.typeId);
    if (t) {
      const li = document.createElement('li');
      const b  = document.createElement('button');
      b.textContent = t.label;
      li.appendChild(b);
      bcEl.appendChild(li);
    }
  } else if (state.view === 'activity' && state.activityId) {
    const a = DATA.activities.find(x => x.id === state.activityId);
    if (a) {
      const li = document.createElement('li');
      const b  = document.createElement('button');
      b.textContent = a.label;
      li.appendChild(b);
      bcEl.appendChild(li);
    }
  }

  document.getElementById('backBtn').disabled = history.length <= 1;

  // History dropdown
  const hl = document.getElementById('historyList');
  hl.innerHTML = '';
  history.slice().reverse().forEach((h, i) => {
    const li = document.createElement('li');
    const b  = document.createElement('button');
    b.textContent = h.label;
    b.addEventListener('click', () => {
      // Walk back to that state
      const target = history.length - 1 - i;
      history = history.slice(0, target + 1);
      const e = history[target];
      state = { view: e.view, typeId: e.typeId || null, page: 0, selected: null };
      render(true);
      document.getElementById('historyMenu').open = false;
    });
    li.appendChild(b);
    hl.appendChild(li);
  });
}


/* ── Render dispatcher ───────────────────────────────────── */
function render(skipHistoryPush) {
  if (!DATA) return;
  if      (state.view === 'root')     renderRootChart();
  else if (state.view === 'type')     renderTypeChart();
  else if (state.view === 'activity') renderActivityChart();
  renderHistory();
  renderPanel();
}


/* ── Geometry helpers ────────────────────────────────────── */
function chartDims() {
  const wrap = document.getElementById('chartWrap');
  const w = wrap.clientWidth;
  const h = wrap.clientHeight;
  const size = Math.min(w, h) - 24;
  return { w, h, size, cx: w / 2, cy: h / 2, half: size / 2 };
}

function ringPositions(n, radiusFrac, half, rotateOffset = -Math.PI / 2) {
  const r = radiusFrac * half;
  const out = [];
  for (let i = 0; i < n; i++) {
    const angle = rotateOffset + (i / n) * 2 * Math.PI;
    out.push({
      i,
      angle,
      x: r * Math.cos(angle),
      y: r * Math.sin(angle),
      r,
    });
  }
  return out;
}


/* ── Common SVG plumbing ─────────────────────────────────── */
function svg() {
  const s = d3.select('#chart');
  const { w, h, cx, cy } = chartDims();
  s.attr('viewBox', `${-cx} ${-cy} ${w} ${h}`);
  s.selectAll('*').interrupt();
  return s;
}


/* ════════════════════════════════════════════════════════════
   LEVEL 0 — root view
   ════════════════════════════════════════════════════════════ */
function renderRootChart() {
  const s = svg();
  s.selectAll('*').remove();

  const { half } = chartDims();

  // Concentric guide rings (drawn first so connections + nodes layer over them).
  // WEF uses two visible rings: a soft grey outer ring and a blue inner halo.
  s.append('circle')
    .attr('class', 'outer-ring-circle')
    .attr('r', OUTER_RING_R * half);

  s.append('circle')
    .attr('class', 'inner-ring-circle')
    .attr('r', INNER_RING_R * half);

  const types      = DATA.types;
  const activities = DATA.activities;
  const innerPos   = ringPositions(types.length,      INNER_RING_R, half);
  const outerPos   = ringPositions(activities.length, OUTER_RING_R, half);

  // Connection paths: each activity connects to the type ids in its connects_to[]
  const lines = s.append('g').attr('class', 'connections');
  const connectionData = [];
  activities.forEach((a, i) => {
    const op = outerPos[i];
    a.connects_to.forEach(tid => {
      const ti = types.findIndex(t => t.id === tid);
      if (ti < 0) return;
      const ip = innerPos[ti];
      connectionData.push({
        a_id: a.id, t_id: tid,
        x1: op.x, y1: op.y,
        x2: ip.x, y2: ip.y,
      });
    });
  });
  lines.selectAll('line')
    .data(connectionData)
    .join('line')
      .attr('class', d => `connection a-${d.a_id} t-${d.t_id}`)
      .attr('x1', d => d.x1).attr('y1', d => d.y1)
      .attr('x2', d => d.x2).attr('y2', d => d.y2);

  // Center anchor (image-clipped circle + title)
  drawCenter(s, DATA.anchor.label, DATA.anchor.image, CENTER_R * half, null,
              `${DATA.n_orgs} organizations`);

  // Inner-ring nodes (types)
  const innerG = s.append('g').attr('class', 'inner-ring');
  const inner = innerG.selectAll('g.node.inner')
    .data(types).join('g')
      .attr('class', d => `node inner t-${d.id}`)
      .attr('transform', (d, i) => `translate(${innerPos[i].x},${innerPos[i].y})`)
      .style('opacity', 0)
      .on('mouseenter', (e, d) => highlightTypeConnections(d.id, true))
      .on('mouseleave', (e, d) => highlightTypeConnections(d.id, false))
      .on('click',      (e, d) => goToType(d.id));

  inner.append('circle');
  inner.append('text')
    .attr('text-anchor', (d, i) => labelAnchor(innerPos[i].angle))
    .attr('dx',          (d, i) => labelDx(innerPos[i].angle, 14))
    .attr('dy',          '0.35em')
    .each(function(d) {
      // Multi-line wrapping for inner labels
      const lines = wrapText(d.label, 16);
      const sel = d3.select(this);
      sel.text('');
      lines.forEach((ln, k) => {
        sel.append('tspan')
          .attr('x', 0)
          .attr('dy', k === 0 ? '0em' : '1.05em')
          .text(ln);
      });
      sel.attr('y', `-${(lines.length - 1) * 0.5}em`);
    });

  inner.transition().duration(400).delay((d, i) => i * 30).style('opacity', 1);

  // Outer-ring nodes (activities) — clickable to drill into an
  // activity-focused view that lists every org tagged with it.
  const outerG = s.append('g').attr('class', 'outer-ring');
  const outer = outerG.selectAll('g.node.outer')
    .data(activities).join('g')
      .attr('class', d => `node outer a-${d.id}`)
      .attr('transform', (d, i) => `translate(${outerPos[i].x},${outerPos[i].y})`)
      .style('opacity', 0)
      .style('cursor', 'pointer')
      .on('mouseenter', (e, d) => highlightActivityConnections(d.id, true))
      .on('mouseleave', (e, d) => highlightActivityConnections(d.id, false))
      .on('click',      (e, d) => goToActivity(d.id));

  outer.append('circle');
  outer.append('text')
    .attr('text-anchor', (d, i) => labelAnchor(outerPos[i].angle))
    .attr('transform',   (d, i) => labelRotate(outerPos[i].angle, 12))
    .text(d => d.label);

  outer.transition().duration(400).delay((d, i) => 200 + i * 18).style('opacity', 1);
}

function highlightTypeConnections(typeId, on) {
  const s = d3.select('#chart');
  // Outer-ring nodes connected to this type
  s.selectAll('g.node.outer').each(function(d) {
    const connected = d.connects_to.includes(typeId);
    d3.select(this).classed('connected', on && connected);
  });
  // Connection lines
  s.selectAll(`line.connection.t-${typeId}`).classed('hot', on);
  // The inner-ring node itself
  s.select(`g.node.inner.t-${typeId}`).classed('active', on);
}

function highlightActivityConnections(activityId, on) {
  const s = d3.select('#chart');
  s.selectAll(`line.connection.a-${activityId}`).classed('hot', on);
  s.select(`g.node.outer.a-${activityId}`).classed('active', on);
  // Inner-ring nodes that this activity connects to
  const a = DATA.activities.find(x => x.id === activityId);
  if (a) {
    a.connects_to.forEach(tid => {
      s.select(`g.node.inner.t-${tid}`).classed('active', on);
    });
  }
}


/* ════════════════════════════════════════════════════════════
   LEVEL 1 — drilled into one type
   ════════════════════════════════════════════════════════════ */
function renderTypeChart() {
  const s = svg();
  s.selectAll('*').remove();

  const { half } = chartDims();

  const t = DATA.types.find(x => x.id === state.typeId);
  if (!t) return;

  // All orgs of this type, sorted by degree (descending) then label
  const allOrgs = DATA.orgs
    .filter(o => o.type_id === state.typeId)
    .sort((a, b) => (b.degree - a.degree) || a.label.localeCompare(b.label));

  const start = state.page * PAGE_SIZE;
  const orgs  = allOrgs.slice(start, start + PAGE_SIZE);

  // Activities present in this type's orgs → outer ring
  const activityIds = new Set();
  allOrgs.forEach(o => o.activities.forEach(a => activityIds.add(a)));
  const activities = DATA.activities.filter(a => activityIds.has(a.id));

  s.append('circle')
    .attr('class', 'outer-ring-circle')
    .attr('r', OUTER_RING_R * half);

  s.append('circle')
    .attr('class', 'inner-ring-circle')
    .attr('r', INNER_RING_R * half);

  const innerPos = ringPositions(orgs.length,        INNER_RING_R, half);
  const outerPos = ringPositions(activities.length,  OUTER_RING_R, half);

  // Connection lines: each org → its activities
  const lines = s.append('g').attr('class', 'connections');
  const connectionData = [];
  orgs.forEach((org, oi) => {
    const ip = innerPos[oi];
    org.activities.forEach(aid => {
      const ai = activities.findIndex(a => a.id === aid);
      if (ai < 0) return;
      const op = outerPos[ai];
      connectionData.push({
        org_id: org.id, a_id: aid,
        x1: ip.x, y1: ip.y,
        x2: op.x, y2: op.y,
      });
    });
  });
  lines.selectAll('line')
    .data(connectionData)
    .join('line')
      .attr('class', d => `connection org-${d.org_id} a-${d.a_id}`)
      .attr('x1', d => d.x1).attr('y1', d => d.y1)
      .attr('x2', d => d.x2).attr('y2', d => d.y2);

  // Center anchor — the type
  drawCenter(s, t.label, DATA.anchor.image, CENTER_R * half, t.color,
              `${allOrgs.length} organizations`);

  // Inner ring = orgs
  const innerG = s.append('g').attr('class', 'inner-ring');
  const inner = innerG.selectAll('g.node.inner')
    .data(orgs).join('g')
      .attr('class', d => `node inner org-${d.id}`)
      .attr('transform', (d, i) => `translate(${innerPos[i].x},${innerPos[i].y})`)
      .style('opacity', 0)
      .on('mouseenter', (e, d) => highlightOrg(d.id, true))
      .on('mouseleave', (e, d) => highlightOrg(d.id, false))
      .on('click',      (e, d) => selectOrg(d.id));

  inner.append('circle');
  inner.append('text')
    .attr('text-anchor', (d, i) => labelAnchor(innerPos[i].angle))
    .attr('transform',   (d, i) => labelRotate(innerPos[i].angle, 12))
    .text(d => d.label.length > 28 ? d.label.slice(0, 26) + '…' : d.label);

  inner.transition().duration(380).delay((d, i) => i * 12).style('opacity', 1);

  // Outer ring = activities present in this type — clickable to drill
  // into the activity-focused view.
  const outerG = s.append('g').attr('class', 'outer-ring');
  const outer = outerG.selectAll('g.node.outer')
    .data(activities).join('g')
      .attr('class', d => `node outer a-${d.id}`)
      .attr('transform', (d, i) => `translate(${outerPos[i].x},${outerPos[i].y})`)
      .style('opacity', 0)
      .style('cursor', 'pointer')
      .on('mouseenter', (e, d) => highlightActivityForOrgs(d.id, true))
      .on('mouseleave', (e, d) => highlightActivityForOrgs(d.id, false))
      .on('click',      (e, d) => goToActivity(d.id));

  outer.append('circle');
  outer.append('text')
    .attr('text-anchor', (d, i) => labelAnchor(outerPos[i].angle))
    .attr('transform',   (d, i) => labelRotate(outerPos[i].angle, 12))
    .text(d => d.label);

  outer.transition().duration(380).delay((d, i) => 200 + i * 18).style('opacity', 1);

  // Pagination hint
  if (allOrgs.length > PAGE_SIZE) {
    const pageLabel = `Showing ${start + 1}–${Math.min(start + PAGE_SIZE, allOrgs.length)} of ${allOrgs.length}`;
    document.getElementById('chartHint').textContent =
      pageLabel + ' · click an org to inspect · scroll the panel for the full list';
  }
}

function highlightOrg(orgId, on) {
  const s = d3.select('#chart');
  s.selectAll(`line.connection.org-${orgId}`).classed('hot', on);
  s.select(`g.node.inner.org-${orgId}`).classed('active', on);
  // Connected outer nodes
  const org = DATA.orgs.find(o => o.id === orgId);
  if (org) {
    org.activities.forEach(aid => {
      s.select(`g.node.outer.a-${aid}`).classed('connected', on);
    });
  }
}


/* ════════════════════════════════════════════════════════════
   LEVEL 1 (alt) — drilled into one activity tag
   center  = activity label
   inner   = orgs tagged with this activity (across all types)
   outer   = the type categories represented by those orgs
   ════════════════════════════════════════════════════════════ */
function renderActivityChart() {
  const s = svg();
  s.selectAll('*').remove();

  const { half } = chartDims();
  const a = DATA.activities.find(x => x.id === state.activityId);
  if (!a) return;

  const allOrgs = DATA.orgs
    .filter(o => Array.isArray(o.activities) && o.activities.includes(state.activityId))
    .sort((x, y) => (y.degree - x.degree) || x.label.localeCompare(y.label));

  const start = state.page * PAGE_SIZE;
  const orgs  = allOrgs.slice(start, start + PAGE_SIZE);

  // Outer ring = the type categories these orgs belong to
  const typeIds = new Set();
  allOrgs.forEach(o => { if (o.type_id) typeIds.add(o.type_id); });
  const types = DATA.types.filter(t => typeIds.has(t.id));

  // Concentric guide rings
  s.append('circle')
    .attr('class', 'outer-ring-circle')
    .attr('r', OUTER_RING_R * half);
  s.append('circle')
    .attr('class', 'inner-ring-circle')
    .attr('r', INNER_RING_R * half);

  const innerPos = ringPositions(orgs.length,  INNER_RING_R, half);
  const outerPos = ringPositions(types.length, OUTER_RING_R, half);

  // Connection lines: each org → its type
  const lines = s.append('g').attr('class', 'connections');
  const connectionData = [];
  orgs.forEach((org, oi) => {
    const ip = innerPos[oi];
    const ti = types.findIndex(t => t.id === org.type_id);
    if (ti < 0) return;
    const op = outerPos[ti];
    connectionData.push({
      org_id: org.id, t_id: org.type_id,
      x1: ip.x, y1: ip.y,
      x2: op.x, y2: op.y,
    });
  });
  lines.selectAll('line')
    .data(connectionData)
    .join('line')
      .attr('class', d => `connection org-${d.org_id} t-${d.t_id}`)
      .attr('x1', d => d.x1).attr('y1', d => d.y1)
      .attr('x2', d => d.x2).attr('y2', d => d.y2);

  // Center = activity label
  drawCenter(s, a.label, DATA.anchor.image, CENTER_R * half, null,
              `Activity tag · ${allOrgs.length} orgs`);

  // Inner ring = orgs tagged with this activity
  const innerG = s.append('g').attr('class', 'inner-ring');
  const inner = innerG.selectAll('g.node.inner')
    .data(orgs).join('g')
      .attr('class', d => `node inner org-${d.id}`)
      .attr('transform', (d, i) => `translate(${innerPos[i].x},${innerPos[i].y})`)
      .style('opacity', 0)
      .on('mouseenter', (e, d) => highlightOrg(d.id, true))
      .on('mouseleave', (e, d) => highlightOrg(d.id, false))
      .on('click',      (e, d) => selectOrg(d.id));

  inner.append('circle');
  inner.append('text')
    .attr('text-anchor', (d, i) => labelAnchor(innerPos[i].angle))
    .attr('transform',   (d, i) => labelRotate(innerPos[i].angle, 12))
    .text(d => d.label.length > 28 ? d.label.slice(0, 26) + '…' : d.label);

  inner.transition().duration(380).delay((d, i) => i * 12).style('opacity', 1);

  // Outer ring = parent type categories — clickable to drill into a type
  const outerG = s.append('g').attr('class', 'outer-ring');
  const outer = outerG.selectAll('g.node.outer')
    .data(types).join('g')
      .attr('class', d => `node outer t-${d.id}`)
      .attr('transform', (d, i) => `translate(${outerPos[i].x},${outerPos[i].y})`)
      .style('opacity', 0)
      .style('cursor', 'pointer')
      .on('click', (e, d) => goToType(d.id));

  outer.append('circle');
  outer.append('text')
    .attr('text-anchor', (d, i) => labelAnchor(outerPos[i].angle))
    .attr('transform',   (d, i) => labelRotate(outerPos[i].angle, 12))
    .text(d => d.label);

  outer.transition().duration(380).delay((d, i) => 200 + i * 18).style('opacity', 1);

  // Pagination hint
  if (allOrgs.length > PAGE_SIZE) {
    const pageLabel = `Showing ${start + 1}–${Math.min(start + PAGE_SIZE, allOrgs.length)} of ${allOrgs.length}`;
    document.getElementById('chartHint').textContent =
      pageLabel + ' · click an org to inspect · scroll the panel for the full list';
  } else {
    document.getElementById('chartHint').textContent =
      `${allOrgs.length} org${allOrgs.length === 1 ? '' : 's'} tagged "${a.label}" · click an org to inspect`;
  }
}

function highlightActivityForOrgs(aid, on) {
  const s = d3.select('#chart');
  s.selectAll(`line.connection.a-${aid}`).classed('hot', on);
  s.select(`g.node.outer.a-${aid}`).classed('active', on);
}

function selectOrg(orgId) {
  state.selected = orgId;
  renderPanel();
  // Just update the panel; no chart transformation per the 2-level decision.
}


/* ── Center anchor (image clip + label) ──────────────────── */
function drawCenter(s, label, imageUrl, radius, ringColor, sublabel) {
  const g = s.append('g').attr('class', 'center-anchor-group');

  // Defs / clipPath for the round image
  const defsId = 'centerClip-' + Math.random().toString(36).slice(2, 8);
  const defs = s.append('defs');
  defs.append('clipPath')
    .attr('id', defsId)
    .append('circle').attr('r', radius);

  g.append('circle')
    .attr('r', radius + 6)
    .attr('fill', 'transparent')
    .attr('stroke', ringColor || 'rgba(0,0,0,0.0)')
    .attr('stroke-width', ringColor ? 4 : 0);

  g.append('image')
    .attr('href', imageUrl)
    .attr('x', -radius)
    .attr('y', -radius)
    .attr('width',  2 * radius)
    .attr('height', 2 * radius)
    .attr('preserveAspectRatio', 'xMidYMid slice')
    .attr('clip-path', `url(#${defsId})`)
    .style('opacity', 0)
    .on('error', function() { d3.select(this).remove(); })
    .transition().duration(400).style('opacity', 0.85);

  g.append('circle')
    .attr('r', radius)
    .attr('fill', 'rgba(0,0,0,0.55)')
    .style('opacity', 0)
    .transition().duration(400).style('opacity', 1);

  // Center label (multi-line wrap) — WEF-spec sizing.
  const lines = wrapText(label, 18);
  const tg = g.append('text').attr('class', 'center-anchor-label')
    .style('opacity', 0);
  lines.forEach((ln, k) => {
    tg.append('tspan')
      .attr('x', 0)
      .attr('dy', k === 0 ? `${-(lines.length - 1) * 0.5}em` : '1.05em')
      .text(ln);
  });
  tg.transition().duration(450).delay(150).style('opacity', 1);

  // Optional small uppercase sublabel under the title (the role hint
  // shown beneath WEF center labels).
  if (sublabel) {
    g.append('text').attr('class', 'center-anchor-sublabel')
      .attr('y', radius * 0.55)
      .text(sublabel)
      .style('opacity', 0)
      .transition().duration(450).delay(220).style('opacity', 1);
  }
}


/* ── Label helpers ───────────────────────────────────────── */
function labelAnchor(angle) {
  // Convert from radial: angle 0 = right, π = left
  const deg = (angle * 180 / Math.PI + 360) % 360;
  if (deg > 100 && deg < 260) return 'end';     // left half
  if (deg < 80 || deg > 280)  return 'start';   // right half
  return 'middle';                              // top / bottom
}

function labelDx(angle, padding) {
  const deg = (angle * 180 / Math.PI + 360) % 360;
  if (deg > 100 && deg < 260) return -padding;
  if (deg < 80 || deg > 280)  return  padding;
  return 0;
}

function labelRotate(angle, padding) {
  // Rotate outer-ring labels to follow the circle perimeter.
  // Top half: tangential and upright; bottom half: flipped 180°.
  const deg = (angle * 180 / Math.PI + 360) % 360;
  let rot = deg;
  let dx  = padding;
  // Flip if label would be upside-down
  if (deg > 90 && deg < 270) {
    rot -= 180;
    dx  = -padding;
  }
  return `rotate(${rot}) translate(${dx},0)`;
}

function wrapText(text, maxLen) {
  const words = text.split(/\s+/);
  const out = [];
  let cur = '';
  words.forEach(w => {
    const candidate = cur ? cur + ' ' + w : w;
    if (candidate.length > maxLen && cur) {
      out.push(cur);
      cur = w;
    } else {
      cur = candidate;
    }
  });
  if (cur) out.push(cur);
  return out.slice(0, 4);
}


/* ════════════════════════════════════════════════════════════
   Right panel
   ════════════════════════════════════════════════════════════ */
function renderPanel() {
  const titleEl    = document.getElementById('panelTitle');
  const subtitleEl = document.getElementById('panelSubtitle');
  const dekEl      = document.getElementById('panelDek');
  const metaEl     = document.getElementById('panelMeta');
  const orgsEl     = document.getElementById('panelOrgs');
  const orgsHdr    = document.getElementById('panelOrgsHeader');
  const orgsCount  = document.getElementById('panelOrgsCount');
  const parentEl   = document.getElementById('panelParent');
  const parentBtn  = document.getElementById('parentPill');
  const imgEl      = document.getElementById('panelImage');

  // ── If an org is selected, show its detail card ─────────
  if (state.selected !== null) {
    const o = DATA.orgs.find(x => x.id === state.selected);
    if (o) {
      const t = DATA.types.find(t => t.id === o.type_id);
      titleEl.textContent    = o.label;
      subtitleEl.textContent = t ? `${t.label}` : '';
      imgEl.src              = o.image || DATA.anchor.image || HERO_DEFAULT;
      dekEl.textContent      = o.description || '—';
      metaEl.innerHTML       = orgMetaHTML(o);
      orgsHdr.style.display  = 'none';
      orgsEl.innerHTML       = '';
      parentEl.hidden        = false;
      parentBtn.textContent  = (t && t.label) || DATA.anchor.label;
      parentBtn.onclick      = () => {
        state.selected = null;
        renderPanel();
      };
      return;
    }
  }

  orgsHdr.style.display = 'flex';

  // ── Otherwise, show whatever level we're at ─────────────
  if (state.view === 'root') {
    titleEl.textContent    = DATA.anchor.label;
    subtitleEl.textContent = DATA.anchor.subtitle;
    imgEl.src              = DATA.anchor.image || HERO_DEFAULT;
    dekEl.textContent =
      `Atlanta's food system spans ${DATA.n_orgs} mapped organizations across ${DATA.types.length} role categories. Click any inner-ring topic to explore the orgs in that role.`;
    metaEl.innerHTML = `
      <strong>Total orgs</strong><span>${DATA.n_orgs}</span>
      <strong>Categories</strong><span>${DATA.types.length}</span>
      <strong>Activity tags</strong><span>${DATA.activities.length}</span>`;
    orgsEl.innerHTML = '';
    DATA.types.forEach(t => {
      const li = document.createElement('li');
      li.innerHTML =
        `<span class="org-name">${t.label}</span>
         <span class="org-meta">${t.count} org${t.count === 1 ? '' : 's'} · ${t.subtitle}</span>`;
      li.addEventListener('click', () => goToType(t.id));
      orgsEl.appendChild(li);
    });
    orgsCount.textContent = `${DATA.types.length} categories`;
    parentEl.hidden = true;
    return;
  }

  if (state.view === 'type') {
    const t = DATA.types.find(x => x.id === state.typeId);
    if (!t) return;
    const orgs = DATA.orgs.filter(o => o.type_id === state.typeId)
                          .sort((a, b) => (b.degree - a.degree) || a.label.localeCompare(b.label));
    titleEl.textContent    = t.label;
    subtitleEl.textContent = `Curation: Georgia Tech I2CE Lab · ${t.subtitle}`;
    imgEl.src              = DATA.anchor.image || HERO_DEFAULT;
    dekEl.textContent =
      `${orgs.length} mapped organization${orgs.length === 1 ? '' : 's'} ` +
      `with role "${t.label}". Click any inner-ring node on the chart to inspect, ` +
      `or pick from the list below.`;
    metaEl.innerHTML = `
      <strong>Orgs in this view</strong><span>${orgs.length}</span>
      <strong>Color in network</strong><span><span style="display:inline-block;width:12px;height:12px;background:${t.color};border-radius:50%;vertical-align:middle;margin-right:6px"></span>${t.color}</span>`;
    orgsEl.innerHTML = '';
    orgs.forEach(o => {
      const li = document.createElement('li');
      const meta = [
        o.address ? o.address.split(',').slice(-2).join(',').trim() : '',
        o.demographics, o.business
      ].filter(Boolean).slice(0, 2).join(' · ');
      li.innerHTML =
        `<span class="org-name">${o.label}</span>
         <span class="org-meta">${meta || '—'}</span>`;
      li.addEventListener('click', () => selectOrg(o.id));
      orgsEl.appendChild(li);
    });
    orgsCount.textContent = `${orgs.length} ${orgs.length === 1 ? 'org' : 'orgs'}`;

    parentEl.hidden = false;
    parentBtn.textContent = DATA.anchor.label;
    parentBtn.onclick = () => goToRoot();
    return;
  }

  if (state.view === 'activity') {
    const a = DATA.activities.find(x => x.id === state.activityId);
    if (!a) return;
    const orgs = DATA.orgs
      .filter(o => Array.isArray(o.activities) && o.activities.includes(state.activityId))
      .sort((x, y) => (y.degree - x.degree) || x.label.localeCompare(y.label));
    titleEl.textContent    = a.label;
    subtitleEl.textContent = `Curation: Georgia Tech I2CE Lab · activity tag`;
    imgEl.src              = DATA.anchor.image || HERO_DEFAULT;
    dekEl.textContent =
      `${orgs.length} mapped organization${orgs.length === 1 ? '' : 's'} ` +
      `tagged with activity "${a.label}", spanning ${a.connects_to.length} ` +
      `category${a.connects_to.length === 1 ? '' : 'ies'}. Click any node to inspect.`;
    metaEl.innerHTML = `
      <strong>Orgs with this tag</strong><span>${orgs.length}</span>
      <strong>Categories spanned</strong><span>${a.connects_to.length}</span>`;
    orgsEl.innerHTML = '';
    orgs.forEach(o => {
      const t = DATA.types.find(t => t.id === o.type_id);
      const meta = [t && t.label, o.address ? o.address.split(',').slice(-2).join(',').trim() : '']
        .filter(Boolean).slice(0, 2).join(' · ');
      const li = document.createElement('li');
      li.innerHTML =
        `<span class="org-name">${o.label}</span>
         <span class="org-meta">${meta || '—'}</span>`;
      li.addEventListener('click', () => selectOrg(o.id));
      orgsEl.appendChild(li);
    });
    orgsCount.textContent = `${orgs.length} ${orgs.length === 1 ? 'org' : 'orgs'}`;

    parentEl.hidden = false;
    parentBtn.textContent = DATA.anchor.label;
    parentBtn.onclick = () => goToRoot();
    return;
  }
}

function orgMetaHTML(o) {
  const rows = [];

  // Tagline / og:description (italic pull-quote on top)
  let head = '';
  if (o.tagline) {
    head += `<div class="org-tagline">${escapeHtml(o.tagline)}</div>`;
  }

  // Region + Demographics surface as colored chips, not key/value rows
  const chips = [];
  if (o.region)      chips.push(`<span class="chip chip-region">${escapeHtml(o.region)}</span>`);
  if (o.demographics) {
    o.demographics.split(/\s*[|;,]\s*/).filter(Boolean).forEach(d => {
      chips.push(`<span class="chip chip-demo">${escapeHtml(d)}</span>`);
    });
  }
  if (o.business)    chips.push(`<span class="chip chip-business">${escapeHtml(o.business)}</span>`);
  if (chips.length) head += `<div class="org-chips">${chips.join('')}</div>`;

  if (o.address)     rows.push(`<strong>Address</strong><span>${escapeHtml(o.address)}</span>`);

  // Website with favicon
  if (o.url) {
    const display = o.url.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const fav = o.favicon
      ? `<img class="favicon" src="${escapeHtml(o.favicon)}" alt="" width="14" height="14" referrerpolicy="no-referrer" onerror="this.remove()">`
      : '';
    rows.push(`<strong>Website</strong><span class="with-fav">${fav}<a href="${escapeHtml(o.url)}" target="_blank" rel="noopener">${escapeHtml(display)}</a></span>`);
  }

  if (o.email)       rows.push(`<strong>Email</strong><span>${escapeHtml(o.email)}</span>`);
  if (o.phone)       rows.push(`<strong>Phone</strong><span>${escapeHtml(o.phone)}</span>`);

  if (o.activity_labels && o.activity_labels.length)
    rows.push(`<strong>Activities</strong><span>${o.activity_labels.map(escapeHtml).join(' · ')}</span>`);

  // Social icons row
  if (o.socials && Object.keys(o.socials).length) {
    rows.push(`<strong>Follow</strong><span class="socials">${socialIconsHTML(o.socials)}</span>`);
  }

  return head + rows.join('');
}

const SOCIAL_ICONS = {
  instagram: 'IG', facebook: 'FB', linkedin: 'IN',
  twitter: 'X',  youtube: 'YT', tiktok: 'TT',
};
function socialIconsHTML(socials) {
  return Object.entries(socials).map(([net, url]) => {
    const lbl = SOCIAL_ICONS[net] || net.slice(0, 2).toUpperCase();
    return `<a class="social-pill" href="${escapeHtml(url)}" target="_blank" rel="noopener" title="${escapeHtml(net)}">${lbl}</a>`;
  }).join('');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
