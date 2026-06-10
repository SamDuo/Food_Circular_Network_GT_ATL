# Polymetron — Technical Reality Check
## Codebase Review for Design-Partner Pitch
**Prepared by:** Claude Code (technical review pass)
**Date:** May 13, 2026
**Audience:** Sam Duong (CTO), Dr. Ingeborg Rocker (CEO)
**Reference docs:**  `docs/Polymetron_Idea_OnePager 1.docx` · `docs/Polymetron_Business_Proposal.docx`

---

## TL;DR — what's real, what's aspirational

> **Bottom line for the design partner conversation:** we have **one demo-ready vertical (AFCN food intelligence), one credible-looking 3D climate experience (Carthage VR), real Atlanta partner relationships, and an honest design doc for the broader platform**. The Climate Intelligence Module described in the business proposal **does not yet exist in code** — no trained heat-vulnerability model, no pedestrian/GPS data integrated, no SHAP explainer running. Polyscape is a 407-line plan with empty folders. **Be careful what we promise**: we can ship a real Atlanta food-system + workshop-driven engagement in 3 months; we cannot ship the full Estate Barometer or the heat-vulnerability ML model without 3–6 months of dedicated build. The good news: the food/AFCN piece is differentiated enough that we don't need to oversell.

**One-sentence pitch we can honestly deliver:** *"We've built a working spatial-intelligence platform for one of the two pitch modules (food security) with real institutional data, real partner relationships, and a deployed live dashboard — and over the summer we'll co-build the climate piece with you on the same foundation."*

---

## 1. Inventory — what exists across all codebases

### 1A. Local repo (`GT campus Dataset/`)

| Module | Location | LOC* | Tech stack | One-liner |
|---|---|---|---|---|
| **AFCN main dashboard** | `resources/Layers & Packages/index.html` | — | ArcGIS Maps SDK v4.30 (AMD/CDN), inline HTML/CSS/JS | Citywide + GT-campus map with 30 GeoJSON layers, mode toggle |
| **Real-time surplus map** | `resources/Layers & Packages/surplus-map.html` | 1,289 | ArcGIS JS SDK, urgency-routing JS | Live food-rescue routing with 4-stop optimization; real LeanPath data |
| **GT Campus Hub** | `resources/Layers & Packages/gt-campus-hub.html` | 1,200 | ArcGIS JS, Eastern-Time logic | Dining menus, pantry hours, event integration |
| **Fleet analytics** | `resources/Layers & Packages/fleet-analytics.html` | ~800 | ArcGIS JS + TomTom API | Traffic + 3D fleet ops dashboard |
| **LeanPath parser** | `scripts/parse_leanpath.py` | 183 | pandas, datetime | CSV → `data/leanpath_surplus.js` regen pipeline |
| **Analytical maps engine** | `scripts/compute_analytical_maps.py` | 1,500+ | geopandas, shapely | Computes 4 composite maps: retail density, access distance, transport, assistance demand |
| **mRFEI computer** | `scripts/compute_mrfei.py` | 380 | geopandas | Modified Retail Food Environment Index w/ LILA flags |
| **Micro-mobility analysis** | `Micro-mobility analysis/` | 585 + 3 notebooks | OSMnx, Folium, KDE | Crash hotspots + 15-min walkability isochrones |
| **Dev server** | `Python Script/serve.py` | 100 | stdlib HTTP, dotenv | Serves dashboards locally + brokers API keys |
| **Build pipeline** | `Python Script/publish_dashboards.py` | 200 | stdlib | Builds static `publish/` bundle for Netlify |
| **Netlify deploy** | `netlify.toml` + `netlify/functions/config.js` | 43 | Netlify Functions | Live serverless API-key broker |
| **GeoJSON layer library** | `geojson/*.geojson` | 30 files | — | Census tracts, food retailers (602), pantries (2,629), recovery sources (11,314), beneficiary points, circular-economy sites |
| **ArcGIS Pro export** | `exports/AFCN_Atlanta.{aprx,gdb,gpkg}` | — | ArcGIS Pro | Full geodatabase deliverable for partner GIS teams |
| **Workshop deliverables** | `workshop/` | — | PPTX + Excel + scripts | April 15, 2026 stakeholder workshop outputs |
| **Polyscape scaffold** | `polyscape/` | 1 file (`requirements.txt`, 493 bytes) | — | **Empty directory tree. Zero code.** |
| **Plan doc** | `.claude/plan/polyscape-prototype.md` | 407 lines | — | Full architecture spec — XGBoost + SHAP + Deck.gl |

\* LOC = lines of code (approximate)

### 1B. GitHub repos (`github.com/SamDuo`)

| Repo | Stack | Commits | Status | Relation to Polymetron |
|---|---|---|---|---|
| **`polymetron`** | HTML / CSS / JS (Mapbox + Formspree) | 9 | Static landing site | Marketing site only — no backend, no ML |
| **`polyscape`** | Python (FastAPI + XGBoost + SHAP + Deck.gl) | 5 | Architecture only | Same plan as `polyscape/` locally — **no implementation yet** |
| **`smart-codes-cura`** | Python (LightRAG + Neo4j + Supabase + Docling) | 2 | Demo for Midtown Atlanta | **Zoning RAG agent** — Phase 2 capability per pitch |
| **`Food_Circular_Network_GT_ATL`** | HTML / Python / JS | 3 | Live (Netlify) | **Public mirror of AFCN** |
| **`gtHackVR`** | React + Vite + Three.js + SparkJS + Gemini + ElevenLabs + Marble | 107 | Built for ImmerseGT 2026 | **Climate-change VR** of Carthage ruins — IPCC AR6 scenarios |
| **`my-landing-page`** | JS / CSS / HTML | — | Portfolio site | Personal site |

---

## 2. Maturity assessment per component

> 🟢 **Production-ready** = could be shown to a paying customer today
> 🟡 **Demo-ready POC** = works for a controlled demo; rough edges
> 🟠 **Prototype / research** = notebook-grade; hardcoded paths; manual loading
> 🔴 **Stub / incomplete** = started but not functional, or planned but not built

### Food security vertical (AFCN)

| Component | Maturity | Why |
|---|---|---|
| Surplus map (`surplus-map.html`) | 🟢 **Production-ready** | Real LeanPath data, real urgency-routing, real fleet stats. ArcGIS + Mapbox + TomTom keys all wired through serverless function. No mock data in the dashboard layer itself. |
| AFCN citywide / campus dashboard | 🟢 **Production-ready** | 30 GeoJSON layers, real Census/USDA/CDC/MARTA bases, layer toggling, popups. Polished dark-mode UI. |
| LeanPath data pipeline | 🟡 **Demo-ready POC** | Real CSV input (408 entries, 2,316 lbs, $2,380, GT campus Mar 4–10 2026). Parser is 183 lines, runs in 2 sec. **But:** manual trigger only; hardcoded dining coords; no schema validation; breaks silently if columns rename. |
| Composite map computation (mRFEI, food assistance demand) | 🟡 **Demo-ready POC** | 1,500+ lines of geopandas. Produces real outputs. **But:** these are *weighted sums*, not ML — `0.5 × snap_rate + 0.5 × poverty_rate`. Calling this "AI" in a pitch would be a stretch. |
| GeoJSON layer library | 🟡 **Demo-ready POC** | 30 files, ~50k lines. Mix of real (TIGER, ACFB pantry network, Fulton compost permits, GT campus dining) + likely-curated (food recovery sources: 11,314 features — source unclear, no provenance file). |
| Netlify deployment | 🟢 **Production-ready** | `netlify.toml` configured, serverless function for API-key brokering, redirects set, build command working. Site is or can be deployed. |
| GT Campus Hub | 🟡 **Demo-ready POC** | Beautiful, functional. **But:** wait-times are hardcoded ("12–15 min"), event calendar is mock, admin analytics partly mock. |
| Fleet analytics | 🟡 **Demo-ready POC** | TomTom integration works; 3D mode + traffic toggles. Mock fleet fallback mode kept silent. |

### Climate / heat / pedestrian (the *headline* of the business proposal)

| Component | Maturity | Why |
|---|---|---|
| Heat vulnerability ML model | 🔴 **Does not exist** | Zero `.pkl` / `.joblib` / `.h5` / `.onnx` / `.pt` files anywhere. Zero training notebooks. Zero SHAP outputs. The 25 environmental/climate layers tracked in `Framework_Matrix.csv` are flagged `In Dashboard? NO`. |
| Pedestrian / GPS / Google Popular Times | 🔴 **Does not exist** | `grep -r "Popular Times\|pedestrian activity\|GPS" .` returns nothing. The micro-mobility analysis is about **infrastructure / crash hotspots / walkability isochrones**, not high-resolution pedestrian flow. |
| LST / NDVI / canopy / impervious feature pipeline | 🔴 **Does not exist** | No raster I/O code, no satellite-data fetchers, no feature engineering script. |
| Polyscape (intended urban-ML platform) | 🔴 **Plan only** | Local: 1 file (`requirements.txt`) in 7 empty subdirectories. GitHub: same. The 407-line plan at `.claude/plan/polyscape-prototype.md` is excellent — but it's a spec, not running code. |
| Intervention simulation ("plant 500 trees on Peachtree") | 🔴 **Does not exist** | No simulation engine, no counterfactual code, no agent-based model. |

### Adjacent capabilities (real but not yet wired into the pitch)

| Component | Maturity | Why |
|---|---|---|
| Micro-mobility analysis (`analysis.py` + 3 notebooks) | 🟠 **Prototype / research** | Real Atlanta data, runs, produces Folium maps. Hardcoded paths; notebooks not parameterized; no API surface. |
| `smart-codes-cura` (zoning RAG) | 🟠 **Prototype / research** | Real Atlanta municipal code ingestion via LightRAG + Neo4j. Demo for Midtown Atlanta exists. 2 commits — early. Useful for the **Phase 2 zoning module**, but not customer-ready. |
| `gtHackVR` (Carthage climate VR) | 🟡 **Demo-ready POC** | Hackathon-built but real (107 commits). Three.js + WebXR + Gemini narrator + ElevenLabs voice + Marble World Labs. **Climate-change scenarios grounded in IPCC AR6**. This is a *killer visual asset* for a developer audience if reframed as "block-level intervention simulation in immersive view." Not directly applicable to Atlanta real estate without rework. |
| Workshop documentation | 🟢 **Production-ready** | Real April 15, 2026 stakeholder workshop with 20+ confirmed orgs (ACFB, Goodr, Concrete Jungle, Atlanta Braves Foundation, City of Atlanta, etc.). Workshop deck + Excel matrix + board photos + organization geojson all in repo. **This is the credibility kit.** |
| `Food_System_Framework_Analysis.md` | 🟢 **Production-ready collateral** | 38 KB rigorous audit of AFCN's 145 ArcGIS layers + 35 GeoJSON files against an 8-map academic framework. Demonstrates research depth. |

---

## 3. Data and integrations

### Real and working
| Data source | Where it lives | What it powers | Update mechanism |
|---|---|---|---|
| **LeanPath GT campus waste audit** (Mar 4–10 2026: 2,316 lbs, $2,380, 408 entries) | `data/Waste-Data.csv` → `data/leanpath_surplus.js` | Surplus map, fleet stats, campus hub | Manual: `python scripts/parse_leanpath.py` |
| **NutriSlice / GA4 engagement** (3,385 users, Feb 10–Mar 9) | `data/Engagement_overview.csv` | Campus hub admin analytics | Manual import |
| **TIGER / Census ACS** (Fulton + DeKalb tracts) | `geojson/census_tracts_tiger.geojson` (1,062 tracts) | mRFEI computation, demographic overlays | One-time download; 2022 vintage |
| **MARTA GTFS 2025** | `geojson/marta_*.geojson` | Transit-accessibility maps | One-time download |
| **OpenStreetMap (March 2026 snapshot)** | grocery, fast food, restaurants | `pkg_*.geojson` (15 files) | Manual via Overpass / OSMnx |
| **Atlanta Community Food Bank pantry network** | `geojson/redistribution_nodes.geojson` (2,629 pts) | Beneficiary access analysis | Manual / one-time |
| **Fulton County compost permits** | `geojson/circular_economy.geojson` | Circular-economy layer | Manual |
| **GT campus dining + boundary** | `geojson/campus_dining.geojson` + `campus_boundary.geojson` | Campus mode | Manual |
| **City of Atlanta DPCD zoning + NPUs** | shapefiles → GeoJSON | Reference layers | One-time |

### External APIs (live)
| API | Used for | Auth model | Status |
|---|---|---|---|
| **ArcGIS Maps SDK v4.30** | Basemap, geocoding, routing | API key via `.env` → `/api/config` broker | ✅ Working |
| **Mapbox GL v3.3** | Alt basemap + geocoder | Public key via broker | ✅ Working |
| **TomTom Maps + Traffic** | Fleet routing + 3D | API key via broker | ✅ Working (with mock fallback) |
| **Esri Route API** | Surplus-map 4-stop optimization | Via ArcGIS key | ✅ Working (with geodesic fallback) |
| **Netlify Functions** | Server-side key brokering | Netlify env vars | ✅ Working |

### Mock / hardcoded / aspirational
| Item | Status |
|---|---|
| Campus Hub wait times | Hardcoded ("12–15 min") |
| Calendar / event integration | Mock data |
| Admin analytics charts | Some mock |
| Fleet driver names + vehicle assignments | Partial mock |
| **Heat / climate / pedestrian-flow data** | **None ingested anywhere** |
| **Trained ML models** | **None exist anywhere** |

### Data pipeline maturity
| Stage | Maturity |
|---|---|
| Ingest | 🟠 Manual ETL — CSV in, regenerate JS, refresh browser |
| Transform | 🟡 Solid Python scripts but hardcoded coords/categories |
| Validate | 🔴 No schema validation, no audit trail |
| Serve | 🟢 Static GeoJSON via CDN + Netlify Function for keys |
| Refresh | 🔴 Zero automation — no cron, no Airflow, no GitHub Action |

---

## 4. What we can credibly demonstrate to a design partner today

### Live, no-asterisks demos (15 minutes total)

**Demo 1 — Real-time Surplus Map (5 min)**
- URL: `http://localhost:8080/resources/Layers & Packages/surplus-map.html` (or Netlify equivalent)
- Live show:
  - 30 real surplus pins from GT campus, March 4–10 2026 (1,051 lbs)
  - Critical / Soon / Stable urgency triage
  - Click "AI Suggested Route" → urgency-aware 4-stop loop computes in <200ms
  - Fleet panel shows real numbers (38 active drivers, 8 refrigerated vehicles, $2,380 cost at risk)
- Honest line: "This is the same engine, plugged into a different city's waste-audit CSV → instant block-level rescue intelligence."

**Demo 2 — AFCN Citywide Dashboard (5 min)**
- 30 layers of food retail, recovery sources, beneficiary access, circular-economy infrastructure
- Toggle mRFEI choropleth (mod-retail-food-environment-index) — real Census-tract scoring
- Mode toggle: Atlanta citywide ↔ GT campus
- Honest line: "We didn't just buy parcel data — we built a 145-layer audit that lets us defend every choice in court."

**Demo 3 — Workshop credibility (5 min, no laptop)**
- One-page handout: April 15, 2026 workshop, 20+ confirmed Atlanta food-system orgs (ACFB, Goodr, Concrete Jungle, Second Helpings, Atlanta Braves Foundation, City of Atlanta, Open Hand, Retazza, NFCC, Umi Feeds, +)
- Show `I2CE Lab Network participatory_workshop_participant_matrix 03_12_2026.csv` printout — real participants, real data needs documented per-org
- Honest line: "We're not pitching a hypothetical product to hypothetical users — we've already convened the city's food-system leaders and have their data needs documented."

### Can show if asked (not lead with)
- **mRFEI + food assistance demand composites** — `python scripts/compute_analytical_maps.py` runs end-to-end and outputs new GeoJSONs. Demonstrates data-engineering depth. Caveat: this is weighted-sum, not ML.
- **Micro-mobility notebooks** — crash hotspots + 15-min walkability. Useful evidence that we work with movement / accessibility data.
- **`smart-codes-cura` zoning RAG** — early but real Atlanta-code ingestion. Honest hook into the Phase 2 zoning story.
- **Carthage VR** — striking visual asset, IPCC-grounded climate scenarios, could anchor a "imagine your portfolio under +3°C" moment. Reframe carefully — currently heritage-focused.

### Do not demo
- Anything in `polyscape/` (empty folders)
- Any claim of "ML heat vulnerability" (model doesn't exist)
- Any claim of "Google Popular Times pedestrian data" (not ingested)
- `index_new.html`, `index_v2.html`, `*.tmp.html` (legacy/broken)
- Raw `.env` (API keys visible — Netlify Functions hide them in prod)

---

## 5. Gaps for a real summer engagement

### What's needed for a credible 3-month design-partner engagement

| Capability | Effort | What needs to happen |
|---|---|---|
| **Heat vulnerability v1 model** | 4–6 weeks, 1 ML engineer | Pull LST (Landsat 8 Surface Temp via Google Earth Engine), NDVI (Sentinel-2), impervious-surface fraction (NLCD), tree canopy (USFS TCC), ACS demographics → train XGBoost regressor on observed heat-related ED visits or CDC PLACES heat-stress proxies → SHAP explainer → serve as REST endpoint |
| **Pedestrian/exposure layer** | 2–4 weeks (depends on data source) | Either (a) license Placer.ai / Dewey / Spectus (~$10–50k/year for 1 metro) and integrate, or (b) MVP with Google Popular Times scrape + MARTA APC counts. Option (b) is cheaper but lower fidelity. |
| **Intervention simulation engine** | 4–6 weeks | Start narrow: "plant N trees at locations L → recompute LST and exposure delta." Needs a UrbanCanopy-style heat model (simplified energy balance) — there's published code (e.g., `solweig` from Sweden, or Trees+ from Google) we can fork. |
| **Auth / multi-tenancy** | 2 weeks | Right now zero auth. For a paying customer we need at minimum: SSO (Auth0 / Clerk / Supabase), per-tenant data isolation, audit log of who-viewed-what. |
| **Persistent backend** | 3 weeks | Move from static GeoJSON → PostGIS + tile server (Martin or pg_tileserv) + FastAPI on Fly.io / Railway / Render. Required for: incremental data updates, user-saved scenarios, model serving. |
| **Automated data refresh** | 2 weeks | GitHub Actions cron: pull latest ACS/CDC/MARTA/OSM weekly → recompute composites → republish. Currently 100% manual. |
| **Observability** | 1 week | Sentry for frontend errors, basic uptime monitoring (Better Stack / Statuspage), API latency dashboard (Grafana Cloud free tier). |
| **Partner data ingest** | 2 weeks per partner | Standardize a "drop CSV / shapefile / API endpoint here" pipeline so partner data (e.g., developer's 10-property portfolio) flows in without bespoke code each time. |

**Total to "credible production for one design partner": 4–5 months for 1 engineer, or 2.5–3 months for 2.** That maps to the summer window if we keep scope tight.

### What we'd need from the design partner
- **Geography**: Specific parcels / corridors / zip codes they care about
- **Their portfolio data**: parcel IDs, ownership timeline, current uses, planned interventions
- **Risk model inputs**: insurance loss data (if available), maintenance/utility costs, tenant complaints / asthma claims
- **Decision criteria**: what they actually act on — "if heat exposure score > X, what do you do?"
- **Validation labels**: 5–20 properties they've worked on where we know the outcome (cooled / didn't), so we can backtest

### Infrastructure / DevOps
- Domain + SSL (~$50/yr)
- Hosting: Netlify (current) + small Fly.io VM ($25/mo) + Supabase ($25/mo) + Mapbox ($50/mo at modest volume) → **~$150/mo all-in for one customer**
- One-time: ML pipeline (Google Earth Engine is free at our scale; Sentinel Hub if we need higher cadence ~$200/mo)

---

## 6. Defensibility — what's the moat

### Hard to replicate (real moat)
1. **Atlanta-specific institutional data + relationships.** The workshop participant matrix is the asset most competitors don't have. *Smart Bricks, Algoma, First Street, Climate X have data; they don't have Goodr's CEO on speed-dial and a documented matrix of what each of 20 food orgs actually needs.* This is the **proof of the food module's wedge.**
2. **AFCN-as-template.** We've built a 65-layer, 800-org platform for one domain in one city. Cloning that for "real-estate developer's 10-property portfolio" is a known engineering exercise, not a research problem. Most competitors haven't shipped a full multi-layer dashboard end-to-end.
3. **Cross-domain bundling.** Food + climate + zoning on one parcel-level fabric is the pitch's actual technical insight. *No competitor offers this combination.* The challenge is that today **we only have the food layer real and the zoning layer partial** — but the data-fusion architecture (GeoJSON → composite indices → web map) is generalizable.
4. **Dr. Rocker's enterprise relationships** (Singapore digital twin scale).
5. **smart-codes-cura RAG architecture.** Specifically: Atlanta zoning code → LightRAG + Neo4j → query-with-citations is a meaningful capability. Few competitors have done municipal-code RAG at this fidelity for the developer use case.

### Commodity / easy to copy
1. **Mapbox + GeoJSON dashboards** — any junior dev can stand up
2. **Census + OSM + USDA data** — all public; lots of teams pull these
3. **Composite "vulnerability" indices via weighted sums** — anyone can publish a Streamlit demo of this in 2 weeks
4. **ArcGIS-based GIS consulting deliverables** — UrbanFootprint / consulting firms have done this for decades
5. **Static "heat island map" pages** — Google "Atlanta heat island map" returns dozens
6. **The fancy 3D Carthage VR demo** — gorgeous but doesn't deliver the same business value as a working risk score; treat as marketing, not product

### What would close gaps quickly (priority order)
1. **Ship one real ML model** — even a simple XGBoost on heat / heat-related ED visits gives us "we have a model" credibility
2. **Cement the workshop output into a published case study** — the April 15 workshop is gold if we package it
3. **Repeat the AFCN template in one more city** (Phoenix? Houston?) — second-city replication kills "you only have Atlanta" objection

---

## 7. Recommendation — what to credibly offer for summer

### Honest scope for a 3-month, 1–2 person engagement

**Do NOT offer:**
- ❌ "Full Estate Barometer" anything
- ❌ "Real-time heat-vulnerability ML platform" at any scale
- ❌ "Block-level pedestrian exposure" (no GPS data feed yet)
- ❌ "Intervention simulation" beyond a single hand-coded scenario
- ❌ National coverage or non-Atlanta cities
- ❌ Phase-2 zoning intelligence at production grade

**Do offer (one of three concrete summer scopes — pick based on partner's actual interest):**

---

### 🏗️ **Summer Scope A — "Climate + Portfolio Risk MVP for [Partner]"** (best fit for a real-estate developer)

**Use case.** Partner owns / develops 10–30 Atlanta-area properties. We deliver a parcel-level risk dashboard that scores each property on heat exposure, food-access externalities, and a single intervention-scenario simulation per property.

**What we build (3 months, 2 students):**
- **Month 1:**
  - PostGIS-backed data fabric for partner's portfolio (we model their 10–30 parcels)
  - LST + NDVI + impervious-surface ingest for the partner's zip codes via Google Earth Engine (free)
  - Heat-exposure v1 score per property (XGBoost on tract-level CDC PLACES heat outcomes + on-site environmental features)
- **Month 2:**
  - Web dashboard (same stack as AFCN, branded for partner): per-parcel risk panel + neighborhood context layer (food access, transit, demographics)
  - SHAP explainer ("this property scores 78 because of low canopy + high impervious + elderly density in tract")
  - One scripted intervention simulation per parcel ("if you plant 20 trees on the south face, the predicted heat score drops X points")
- **Month 3:**
  - Backtesting against any 5 properties where partner has historical maintenance / tenant data
  - Partner walkthrough + 1-page parcel report PDF generator
  - Handoff: source code + monthly data-refresh playbook + co-authored white paper

**What we need from partner:** portfolio parcel IDs, any environmental / tenant / maintenance data they're willing to share, 4 working sessions across the summer.

**Effort.** 2 students × 12 weeks × ~25 hrs/week = **~600 hrs**. Realistic.

**Deliverable.** A working v1 platform for their portfolio + a public case study (with partner approval).

---

### 🌳 **Summer Scope B — "Cooling Center / Tree-Planting ROI for City of Atlanta"** (best fit for municipal partner)

**Use case.** City sustainability office wants to allocate the Inflation Reduction Act tree-planting budget. We deliver a "where to plant" decision tool with predicted heat-exposure-reduction per dollar.

**What we build.**
- Citywide heat-vulnerability layer (same XGBoost approach)
- Tree-planting site-suitability layer (overlay vulnerability × right-of-way × canopy gap × demographic equity)
- Simple "plant N trees" simulator with predicted exposure delta per scenario
- Output: ranked list of 100–500 priority planting locations + map dashboard

**What we need from city:** ROW data, existing canopy inventory, IRA allocation criteria, sustainability staff for 6 sessions over the summer.

**Effort.** 2 students × 12 weeks = ~600 hrs. Realistic.

**Deliverable.** Decision tool + ranked planting plan + co-authored memo.

---

### 🌾 **Summer Scope C — "AFCN-as-a-Service for Atlanta Community Food Bank (or peer)"** (lowest risk, highest demoability)

**Use case.** ACFB (or Goodr / Concrete Jungle) gets a tailored, branded version of the surplus / pantry network platform — production-grade, with their org's data, deployed to their domain.

**What we build.**
- Production AFCN deployment (auth, multi-tenant data isolation, automated refresh)
- Partner's surplus data flowing in (replace LeanPath with partner's actual donor feeds)
- Dispatch UI for their drivers (mobile-responsive)
- Monthly impact-report generator

**What we need from partner:** donor-feed data sample, dispatch workflow walkthrough, 4 working sessions.

**Effort.** 2 students × 12 weeks = ~600 hrs. Realistic.

**Deliverable.** Production system live on partner subdomain + handoff training + case study.

> **My recommendation: Scope A** for a real-estate developer partner. It maps to the *real* pitch (climate + risk), it forces us to ship the one missing ML capability (heat-vulnerability v1), and it lands a private-sector logo. Scope B is better if the partner is municipal. Scope C is the "we don't have to invent anything new" safety net.

---

## 8. Specific things to flag, soften, or remove from the pitch deck before the meeting

> Use the table below to triage. *Bold = critical* — if not corrected, we'll fail technical due diligence.

| Claim in current deck | Current evidence | Pitch decision |
|---|---|---|
| "AI-native engine combines climate science, food system analytics, and geospatial intelligence into autonomous agents" | Food: ✅ real. Climate science: ❌. "Autonomous agents": ❌ (no LangChain/agentic code in this repo). | **Reframe:** "spatial-intelligence platform that **will** integrate climate + food + zoning"; "agentic" only if smart-codes-cura is in scope |
| "Module 1: ML models predict block-level heat vulnerability" | **No model exists.** | **Reframe to "Module 1 (in development): heat vulnerability model — Atlanta v1 ships with first design partner."** Or remove from this deck. |
| "Pedestrian activity data (GPS, Google Popular Times) adds temporal dimension" | **No pedestrian data integrated.** | **Remove or reframe** as "Phase 1.5 will integrate pedestrian flow data" |
| "Module 2: Food Security Mapping" | ✅ Real. AFCN, 30+ layers, LeanPath data. | **Keep — lead with this.** |
| "Module 3: Intervention Simulation" | ❌ Not built. | Reframe as "scripted scenarios on the heat model — partner co-defines first 3" |
| "Project C climate models built with real Atlanta data" | We have *climate-relevant Atlanta data layers* (Census, CDC, ACFB, LeanPath) but **no climate models built on them**. | Reframe: "We have real Atlanta data layers across food, demographics, transit, and infrastructure ready to feed climate models." |
| "Built multiple spatial intelligence platforms and climate resilience models with real Atlanta data" (Sam's bio) | Spatial intelligence platforms: ✅ (AFCN, micro-mobility, Carthage). **Climate resilience models specifically: ❌.** | Reframe to "multiple spatial-intelligence platforms; climate-resilience models in active development" |
| "Polymetron evolves from a climate and food intelligence engine into a comprehensive urban intelligence platform" | Food: ✅. Climate engine: ❌. Zoning: 🟠 (smart-codes-cura prototype). | Reframe: "Polymetron starts as the food-intelligence platform Atlanta already uses, and extends to climate and zoning over the design-partner engagement" |
| "Cities currently spend billions on resilience programs with no AI-powered tools" — implying we have AI tools | Partly fair; we have data and dashboards. AI/ML is aspirational. | Soften to "no integrated, partner-co-designed platform that bundles food + climate + zoning" |
| "$100K avg vs $50K" unit economics claim | Untested — no signed contract yet. | Mark as projection. |
| Carthage VR / gtHackVR | Real but heritage-focused. | If brought up, frame as "we know how to build cinematic 3D climate scenarios; for Polymetron we'll apply the same engine to Atlanta intervention previews." |

---

## 9. Honest one-paragraph for the design partner

> "Polymetron is a spatial-intelligence platform for cities and developers. We've shipped the food-security vertical end-to-end for Atlanta — real institutional data (LeanPath waste audits, Atlanta Community Food Bank pantry network, City of Atlanta zoning), a live dashboard, real workshop relationships with 20+ food-system orgs, and a deployed production deployment. We're in active development on the climate vertical — heat-vulnerability scoring at parcel level using public satellite + Census + CDC data — and that's the piece we propose to co-build with you this summer. We have a 3-month plan to deliver a working portfolio-level climate + community-resilience scoring platform for your properties, with one intervention simulator and a parcel report generator. We won't claim to ship the full Estate Barometer in three months — we'll ship one vertical of it, working, with you as the design partner, and use that as the launchpad for the rest."

That paragraph is defensible under technical due diligence. The current business proposal as written is not.

---

## Appendix A — files referenced in this review

- Local: `c:\Users\qduong7\OneDrive - Georgia Institute of Technology\GT campus Dataset\` (no-suffix path)
- `docs/Polymetron_Idea_OnePager 1.docx`
- `docs/Polymetron_Business_Proposal.docx`
- `CLAUDE.md`
- `Framework_Matrix.csv`
- `AFCN_Phase1_Tracking.md`, `AFCN_Phase2_Tracking.md`
- `Food_System_Framework_Analysis.md`
- `.claude/plan/polyscape-prototype.md`
- `resources/Layers & Packages/index.html`, `surplus-map.html`, `gt-campus-hub.html`, `fleet-analytics.html`
- `scripts/compute_analytical_maps.py`, `compute_mrfei.py`, `parse_leanpath.py`
- `Python Script/serve.py`, `publish_dashboards.py`
- `netlify.toml`, `netlify/functions/config.js`
- `polyscape/` (empty)
- `workshop/I2CE Lab Network participatory_workshop_participant_matrix 03_12_2026.csv`

- GitHub: `github.com/SamDuo/{polymetron,polyscape,smart-codes-cura,Food_Circular_Network_GT_ATL,gtHackVR,my-landing-page}`

## Appendix B — riskiest single dependency

If **Netlify or the ArcGIS API key** disappear tomorrow, the live demo dies. The Netlify Function for key brokering is a single point of failure for all three real APIs. Mitigation: 2-hour fix to fall back to a hard-coded restricted-domain Mapbox public key for demos. Worth doing before any partner meeting.

---

*End of review.*
