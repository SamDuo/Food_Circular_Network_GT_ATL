# AFCN Matrix Atlas — Evaluation Rubric

> Scoring sheet for every cell in the 42-cell matrix atlas (plus the
> Typology capstone). Each map is scored 1–5 on six criteria; the
> weighted aggregate determines publication readiness.

---

## How to use this rubric

1. Open the cell at `atlas/viewer.html?row=<row>&lens=<lens>`.
2. Copy the table below into a Google Form / sheet.
3. Two reviewers score independently (one technical, one design).
4. Average the scores. Disagreement > 1 point on any criterion → sync call.
5. **≥ 4.0 weighted = publish · 3.0–3.9 = revise · < 3.0 = rework**.

---

## The 6 criteria (5-point scale)

### 1. Data Quality (weight 25 %)

| Score | Meaning |
|:-:|---|
| 5 | Source authoritative (Census, CDC, EPA, county GIS), fetched within 90 days, all key fields populated, geometries valid, CRS = EPSG:4326, sibling `.meta.json` records URL + date + SHA-256 |
| 4 | Authoritative source but > 90 days old, or 1–5 % null in key field |
| 3 | Mixed / aggregated source, 5–15 % null, or geometry has minor self-intersects |
| 2 | Crowdsourced (OSM only) without cross-check, or > 15 % null |
| 1 | Source unverifiable or geometry invalid |

### 2. Visual Clarity (weight 20 %)

| Score | Meaning |
|:-:|---|
| 5 | Palette colorblind-safe (passes Coblis simulator for deuteranopia + protanopia), 3–7 classes, ColorBrewer-compliant, legend complete + readable, labels collide-free at all zooms |
| 4 | Minor legend gaps OR slight contrast issue at one zoom level |
| 3 | Palette readable but not colorblind-safe, OR legend missing some categories |
| 2 | Palette unfit for data type (e.g., divergent used for sequential), OR legend absent |
| 1 | Map is unreadable / labels overlap heavily / no legend |

### 3. Analytical Insight (weight 25 %)

| Score | Meaning |
|:-:|---|
| 5 | Cell ships with a 1-sentence research question. Reviewer answers "yes" — the map clearly visualizes the answer. Lens choice is correct (e.g., density not used where accessibility was needed) |
| 4 | Question answered, but lens could be sharper |
| 3 | Question partly answered; viewer must look at multiple cells to triangulate |
| 2 | Question stated but map doesn't visibly support it |
| 1 | No research question stated, or map answers a different question than claimed |

### 4. Technical Performance (weight 10 %)

| Score | Meaning |
|:-:|---|
| 5 | Lighthouse FCP < 2 s, LCP < 3 s, TTI < 4 s. Layer file < 3 MB. 60 fps during pan/zoom on mid-tier laptop |
| 4 | LCP 3–4 s, file 3–5 MB, occasional frame drops |
| 3 | LCP 4–6 s, file 5–8 MB, smooth at static but stutters during interaction |
| 2 | LCP > 6 s OR file > 10 MB OR < 30 fps |
| 1 | Crashes, freezes, or fails to load on any tested device |

### 5. Accessibility — a11y (weight 10 %)

| Score | Meaning |
|:-:|---|
| 5 | axe-core scan: 0 violations. Keyboard nav reaches every interactive control. Legend has alt-text. Color contrast ≥ 4.5:1 for text. Screen reader announces tract / point on focus |
| 4 | 1–2 minor axe issues OR one missing alt-text |
| 3 | Some keyboard traps OR low-contrast labels at extremes of zoom |
| 2 | Mostly mouse-only interaction; screen reader gets generic "map" only |
| 1 | No a11y considerations; relies on color-only info channels |

### 6. Reproducibility (weight 10 %)

| Score | Meaning |
|:-:|---|
| 5 | `make rebuild_<layer>` regenerates the GeoJSON exactly. `*.meta.json` records source URL + fetch ISO-8601 date + SHA-256 of fetched bytes + script path. Script committed to repo |
| 4 | Script committed + sources documented, but rebuild requires manual env step |
| 3 | Script exists but undocumented inputs / external state |
| 2 | Layer was hand-edited in QGIS without a script |
| 1 | Origin of data unknown / no script / no provenance file |

---

## Weighted aggregate

```
weighted_score
  = 0.25 × data_quality
  + 0.20 × visual_clarity
  + 0.25 × analytical_insight
  + 0.10 × technical_performance
  + 0.10 × accessibility
  + 0.10 × reproducibility
```

| Aggregate | Status |
|:-:|---|
| **≥ 4.0** | ✅ **Publish** — appears in `atlas/index.html` grid |
| 3.0 – 3.9 | 🔧 **Revise** — flagged in viewer with rework note |
| < 3.0 | ⛔ **Rework** — pulled from grid; rebuild from source |

---

## Per-lens emphasis

Some criteria carry more weight for specific lenses. When two cells tie on
weighted score, break the tie in favor of the higher score on the
lens-specific dominant criterion below.

| Lens | Dominant criterion | Why |
|---|---|---|
| Base Distribution | Data Quality | Wrong dots = wrong everything downstream |
| Density | Visual Clarity | Bandwidth + palette carry the message |
| Accessibility | Analytical Insight | Must specify "accessible to *what*?" |
| Equity | Visual Clarity + Insight | Bivariate / divergent palettes carry the story |
| Trend | Data Quality | Two-snapshot alignment is fragile |
| Flow | Technical Performance | Edge bundles can crater FPS |

---

## Worked example — `food:density`

| Criterion | Score | Notes |
|---|:-:|---|
| Data Quality | 5 | Source: `pkg_atlanta_grocery_stores.geojson` (296 stores), 0 null, valid geom, fetched 2026-04-23, SHA recorded |
| Visual Clarity | 4 | Sequential YlOrRd palette, 5 classes, colorblind OK; legend present but cuts off "very high" label at narrow viewport |
| Analytical Insight | 5 | Question: *"Where is grocery retail concentrated?"* — map plainly shows Buckhead/Midtown clusters and South-side voids |
| Technical Performance | 5 | LCP 1.6 s, layer 1.2 MB, 60 fps |
| Accessibility | 3 | axe-core: 1 contrast violation on legend tick labels; keyboard nav OK |
| Reproducibility | 4 | Script committed; rebuild requires manual ArcGIS sign-in (not yet automated) |

**Weighted = 4.50** — ✅ Publish.

---

## CI integration

`scripts/qa_layer.py` runs the **mechanical** subset of this rubric on every
push. It cannot judge insight or clarity (those are reviewer-only), but it
can score Data Quality and Reproducibility automatically:

```bash
python scripts/qa_layer.py geojson/atl_demographics_acs.geojson
# →  data_quality: 5/5  (530 features, 0% null, valid geom, EPSG:4326)
# →  reproducibility: 4/5  (.meta.json present, script committed, manual env step)
# →  visual_clarity: SKIP (manual review)
# →  analytical_insight: SKIP (manual review)
# →  technical_performance: SKIP (run Lighthouse separately)
# →  accessibility: SKIP (run axe-core separately)
```

CI fails the build if any *automated* score drops below 3.

---

## Reviewer assignments (suggested)

| Sprint | Technical reviewer | Design reviewer |
|---|---|---|
| 1 — Demographics | Quan (data) | Supervisor |
| 2 — Health | Quan | Supervisor |
| 3 — Land Use | Supervisor | A peer in I2CE Lab |
| 4 — Transportation | Quan | Supervisor |
| 5 — Social + Infra | Quan | Peer reviewer |
| 6 — Typology capstone | Quan + Supervisor | External reviewer (e.g., Atlanta Regional Commission contact) |

The capstone gets the heaviest review because it's the public-facing synthesis.
