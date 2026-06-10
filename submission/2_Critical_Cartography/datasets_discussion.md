# Datasets — Relevance to Spatial Analysis & Critical Cartography of Atlanta
**ARCH 4017 · AFCN · Quan Duong · Georgia Tech I2CE Lab · April 2026**

> This document inventories the datasets assembled for the AFCN project, discusses
> what each is good for, what each is silent about, and how the combination enables
> a Spatial Analysis and Critical Cartography reading of Atlanta's food system.
> It is the *evidence base* underneath the 5 maps in `1_Spatial_Analytics/` and the
> critical review in `critical_review.md`.

---

## 1. Dataset inventory (10 source families · 65 GeoJSON layers · ~800 mapped orgs)

| Family | Source | Vintage | Geographic scope | Role in AFCN |
|---|---|---|---|---|
| **A. Census ACS** | US Census Bureau 5-Year ACS | 2018–2022 | Tract (Fulton + DeKalb + GA state) | Demographic denominator: poverty, income, vehicle access, SNAP, household structure |
| **B. CDC PLACES** | CDC Local Data for Better Health | 2024 release | Tract | Modeled health outcomes — obesity, diabetes, food insecurity small-area estimates |
| **C. USDA SNAP retailers + LILA** | USDA Food Access Research Atlas | 2019 | Tract | Low-income / low-access (LILA) classification; SNAP retailer locations |
| **D. CDC mRFEI** | CDC Modified Retail Food Environment Index | 2023 | Tract | Per-tract ratio of healthy to less-healthy retailers |
| **E. MARTA GTFS** | MARTA Open Data | 2025 | Atlanta region | Rail + bus stops, routes, official line colors |
| **F. OpenStreetMap** | OSM contributors (ODbL) | March 2026 snapshot | Atlanta region | Roads, sidewalks, fast food, restaurants, convenience stores, buildings |
| **G. City of Atlanta DPCD** | Department of City Planning | 2024 | City of Atlanta | Zoning, NPUs, neighborhood plans, BeltLine, historic districts |
| **H. ACFB pantry network** | Atlanta Community Food Bank | 2025 | Metro Atlanta | Pantry locations, distribution sites |
| **I. LeanPath audit** | GT Dining via LeanPath platform | Mar 4–10 2026 | GT campus | Real surplus weights, food cost wasted, donate vs compost rates, loss reasons |
| **J. Workshop-curated** | I2CE Lab + 14 partner orgs | April 15 2026 | Atlanta + GT | Beneficiary access, redistribution nodes, network flows, circular-economy points |

Plus derived layers: healthy-food 1-mile coverage (pgRouting network buffer), grocery access distance (per-tract nearest grocery in miles), 5/10/15-min walksheds from MARTA (OSRM isochrone), and the M8 food-insecurity composite risk score.

---

## 2. Per-family discussion

### A. Census ACS 5-Year (2018–2022)
**Relevance.** Without ACS, the food map is just dots — no population denominator. Every choropleth in AFCN normalizes against ACS tract counts. Vehicle availability (B08201) is essential for arguing that food access is a *mobility* problem, not just a distance problem.

**What it enables.** Spatial joins between food-retailer points and household demographics; computing access *rates* instead of raw counts.

**Critical-cartography caveat.** ACS is a *survey* with margins of error that grow at small geographies. A tract-level median income of $42,000 may carry a ±$8,000 confidence interval that no choropleth color band reveals. The map asserts certainty the data does not have.

### B. CDC PLACES (2024)
**Relevance.** Health outcomes (obesity, diabetes, food insecurity perception) at tract granularity. Connects food environment → health, the SDOH argument that justifies the project's framing.

**What it enables.** Map 4 / M8 composite uses PLACES obesity + diabetes as 2 of 7 indicators; the bivariate prototype (M4 × M7) is built on PLACES.

**Critical-cartography caveat.** PLACES is **modeled, not measured**. The agency runs multilevel regression with poststratification (MRP) using BRFSS state-level survey results, smoothing each tract toward its demographic neighbors. **A tract's PLACES obesity rate is partly a prediction**. This is rarely shown in public uses of PLACES.

### C. USDA SNAP retailers + LILA tracts
**Relevance.** LILA is the federal definition of food deserts and the entry point for most policy conversations. Including it lets AFCN dialog with USDA / HUD / Treasury programs.

**What it enables.** Map 2 overlays USDA Food Desert tracts on our own network-distance computation; the comparison reveals where federal definition agrees with on-the-ground access and where it misses.

**Critical-cartography caveat.** USDA LILA uses **1-mile urban threshold + 20% low-income threshold**. These cutoffs are administrative conventions, not behavioral truths. A household 0.9 miles from a Kroger in 95°F humidity walking with children faces fundamentally different access than the threshold suggests. LILA also has not been updated since 2019; recent closures are not reflected.

### D. CDC mRFEI (2023)
**Relevance.** Single number per tract summarizing the ratio of healthy to less-healthy food retailers. Useful as a *headline* metric; powerful in policy briefings.

**What it enables.** Map 1 — the most immediately legible AFCN map. Quintile choropleth that reads as the "food landscape" at a glance.

**Critical-cartography caveat.** mRFEI **does not weight by store size, hours, or product mix**. A 5,000 sqft Save-A-Lot counts identically with a 50,000 sqft Kroger; a Whole Foods open 14 hrs/day counts identically with a corner grocer open 6 hrs.

### E. MARTA GTFS (2025)
**Relevance.** Atlanta is unusually transit-segmented; food access *outside* the rail walkshed differs dramatically from inside.

**What it enables.** Map 3 builds 5/10/15-min walksheds via OSRM around every MARTA stop. Surplus map routing uses MARTA proximity as a tie-breaker when sending rescue runs.

**Critical-cartography caveat.** GTFS schedules are *plans*, not *observed performance*. A bus stop with hourly service is functionally different from a rail station with 10-min headways — the feed treats both as binary "present/not present" in our isochrone analysis.

### F. OpenStreetMap (March 2026 snapshot)
**Relevance.** Free, volunteer-edited, comprehensive. The only feasible source for fast-food, restaurant, convenience-store, and sidewalk geometry at city scale.

**What it enables.** mRFEI denominator (Map 1), walkshed routing (Map 3), street centerlines for visual context.

**Critical-cartography caveat.** **Coverage is uneven and correlated with editor demographics.** Buckhead is more densely mapped than southwest Atlanta — not because it has more amenities, but because more OSM editors live there. A "low density" reading in a low-edited area might be *under-mapping*, not under-supply. This is the single biggest invisible bias in AFCN's spatial layer stack.

### G. City of Atlanta DPCD layers (2024)
**Relevance.** Zoning, NPUs, BeltLine, historic districts — the *regulatory* context in which the food system operates.

**What it enables.** Showcase scenes that explain *why* a grocery cannot open in a given tract (zoning), why beltline-adjacent neighborhoods are gentrifying faster, and which NPUs have organized food-policy positions.

**Critical-cartography caveat.** Zoning maps make exclusion *legible* but also *natural-looking*. Rendering a `C-1` zone one shade and `R-3` another presents the divide as administrative when it is in fact the product of decades of land-use politics, redlining legacies, and continued exclusionary zoning.

### H. ACFB pantry network
**Relevance.** ACFB is the regional anchor. Without their roster, the demand-supply pantry layer in Map 4 / M8 does not exist.

**What it enables.** Pantry overlay on M8 composite; flow-routing in the Surplus map; partner-network analysis in Network view.

**Critical-cartography caveat.** ACFB lists **public-facing distribution addresses**. Many community pantries (front-porch fridges, faith-based informal networks, mutual-aid pickup points) operate without ACFB visibility. The map renders the *formal* food-rescue economy and *erases* the informal one. Three orgs at the April 15 workshop explicitly noted their beneficiary-side data is not for public release.

### I. LeanPath audit (Mar 4–10, 2026)
**Relevance.** The only **measured, weight-based** surplus dataset in the project. Every other surplus layer is modeled or self-reported.

**What it enables.** Map 5 surplus flow (real source quantities); Surplus map ops dashboard (1,051 lbs across 30 grouped pins); fleet KPIs.

**Critical-cartography caveat.** **One week is not a season**, and **GT dining is not Atlanta retail**. The aggregate finding that **96.5% of GT waste composts while only 3.5% is donated** describes campus dining, not Atlanta. It is the project's central provocation but cannot be generalized without separate audits.

### J. Workshop-curated layers (April 2026)
**Relevance.** Reflect *what the 14 partner orgs themselves said about their work* — ground-truth that no top-down dataset captures.

**What it enables.** Beneficiary access points (17 features), redistribution nodes (2,629 features, ACFB + curated), network flows (12 modeled OD pairs), circular-economy points (127 — compost, recycling, gardens).

**Critical-cartography caveat.** Workshop-curated data inherits the *organizations who showed up*. Orgs that declined or were not invited are absent. This produces a "**RSVP-shaped map**" — accurate for who is engaged, blind to who is excluded.

---

## 3. How the datasets combine — a Spatial-Analysis reading

The power of the AFCN dataset stack is not any single layer but the **systematic overlay of supply (D, F, H), access (C, E, derived isochrones), demand (A, B), and operational reality (I, J)** at the same geographic unit (tract).

| Spatial-analysis question | Required dataset overlay |
|---|---|
| Where are the food deserts in Atlanta? | C (LILA) ∩ D (mRFEI) ∩ derived network distance |
| Where do demand and supply diverge? | A (poverty/income) × H (pantries) over tract polygons |
| Where does transit fail food access? | E (MARTA walksheds) ∩ A (no-vehicle %) ∩ D (mRFEI) |
| Which tracts are simultaneously high-need on multiple axes? | A + B + C + D → M8 composite (Map 4) |
| Where does GT campus surplus go, and where could it go? | I (LeanPath) × H (pantries) + derived routing |
| Who is doing what in the network? | J (workshop-curated org roster) + spatial join |

This combinatorial power is the central argument for spatial analysis: **no single source answers any of these questions; the intersection does**.

---

## 4. How the same datasets enable a Critical Cartography reading

A Critical Cartography reading does the opposite — it interrogates the same overlays for what they conceal. Each dataset's caveat becomes a *line of critique*:

| Critical-cartography question | Which dataset is being interrogated |
|---|---|
| Whose hunger is rendered visible? | C (USDA LILA) — formally measured low-income only |
| Whose food provisioning is rendered invisible? | F, H, J — informal vendors, mutual aid, faith-based, undocumented fridges |
| What administrative threshold becomes a "natural" boundary on the map? | C (1-mile LILA), E (15-min walkshed) |
| What modeled estimate is being presented as ground truth? | B (CDC PLACES MRP), composite indices built on B |
| What demographic of map-editor is shaping coverage? | F (OSM) editor geography |
| Whose data won the right to publication, and whose did not? | J (workshop orgs declined to publish beneficiary detail) |
| What week-long snapshot is being read as a yearly pattern? | I (LeanPath Mar 4–10 2026) |

The critical-cartography stance does not reject the maps — it insists that **the maps' authority depends on the reader knowing what they exclude**.

---

## 5. Provenance & licensing summary

| License | Covered datasets |
|---|---|
| **Public domain** | A (Census ACS), B (CDC PLACES), C (USDA), D (CDC mRFEI), E (MARTA GTFS), G (City of Atlanta DPCD) |
| **Open data (ODbL)** | F (OpenStreetMap — attribution required) |
| **Used with permission** | H (ACFB pantry network), I (LeanPath audit) |
| **I2CE Lab / personal-academic use only** | J (workshop-curated), derived composite scores |

Reproducibility: every layer is named in `data_sources.md` of the relevant map folder. Every derived layer is rebuilt from raw sources via scripts in `scripts/` and `submission/1_Spatial_Analytics/export_maps.py`.

---

## 6. What is still missing — the dataset roadmap

| Gap | Why it matters | Acquisition path |
|---|---|---|
| **Real-time demand signals** (pantry visit counts, waitlist sizes) | All current demand layers are *modeled* (PLACES) or *static* (ACS). The April 15 workshop's #1 wish was real-time demand. | ACFB MoU + pantry partner POS integration |
| **Cold-chain capacity** by vehicle / facility | Surplus map routes flow lines without knowing which lines are physically feasible | Workshop partners (Second Helpings, Goodr) |
| **Mutual-aid + faith-based community fridges** | Currently invisible | Field survey (sensitive, deferred) |
| **Historical SNAP retailer churn** | Closures since 2019 erased from current data | USDA SNAP archive scrape |
| **Suburban inner-ring tracts** (Cobb, Clayton, Gwinnett) | M8 scopes only to Fulton + DeKalb | API extension — straightforward |
| **MARTA frequency, not just presence** | Walkshed bands treat all stops equally | Already in GTFS; just not modeled yet |
| **Heat / climate-exposure layer** | Food-access difficulty rises in summer heat | NWS / Urban Heat Island datasets |

---

## 7. References

1. CDC (2024). *PLACES: Local Data for Better Health.* Methodology v.2024.
2. USDA ERS (2019). *Food Access Research Atlas Documentation.*
3. CDC (2023). *Modified Retail Food Environment Index (mRFEI).*
4. US Census Bureau (2022). *American Community Survey 5-Year Estimates.*
5. MARTA (2025). *General Transit Feed Specification — Atlanta.*
6. Coleman-Jensen et al. (2019). *Household Food Security in the United States.* USDA ERS.
7. Walker et al. (2010). "Food deserts: a systematic review." *Health & Place*.
8. Berkowitz et al. (2018). "Food insecurity and healthcare utilization." *Health Affairs*.
9. Harley, J.B. (1989). "Deconstructing the Map." *Cartographica* 26(2): 1–20.
10. Crampton, J. (2010). *Mapping: A Critical Introduction to Cartography and GIS.* Wiley.
