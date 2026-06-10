# Assignment 1c — Spatial Analytics & Critical Cartography
## Definitions and Relevance to AFCN
**ARCH 4017 · Quan Duong · Georgia Tech I2CE Lab · April 2026**

---

## Spatial Analytics — definition

**Spatial Analytics** is the family of computational methods that use the *geographic location* of phenomena as a first-class analytical variable. Where ordinary statistics asks "what is the relationship between X and Y?", spatial analytics asks **"what is the relationship between X and Y given where each occurs, and how does that relationship change across space?"** It combines:

1. **Geometry operations** — points, lines, polygons; intersections, buffers, unions
2. **Spatial joins** — attaching attributes from one layer to another by location
3. **Network analysis** — shortest paths, isochrones, accessibility along road / transit graphs
4. **Spatial statistics** — autocorrelation (Moran's I), hot-spot detection (Getis-Ord), classification (quantile, Jenks, equal-interval)
5. **Composite indexing** — weighted synthesis of multiple indicators into a single per-place score (e.g. the M8 composite vulnerability index)
6. **Cartographic communication** — choropleth, dot density, bivariate, flow, heatmap — translating quantitative results into legible visual claims

Spatial analytics treats *place* as both **subject and method**: a tract's score on poverty matters not in isolation but in relation to its neighbors, its transit access, its retail environment, and its position in the broader regional system.

## Critical Cartography — definition

**Critical Cartography** is a reflexive, political reading of maps and mapping practice. It rejects the modernist assumption that maps are neutral representations of reality. Drawing on Harley (1989), Wood (2010), Crampton (2010), and the participatory-GIS tradition, critical cartography insists that **every map is an argument** about:

- **Who counts** as data (the included)
- **What is silenced** by being unmapped or aggregated away (the excluded)
- **Whose categories** organize the legend (administrative vs. lived)
- **Whose authority** the map performs (state, university, community)
- **What political work** the visual choices do (which colors signal "alarm" vs. "normal," which boundaries are rendered, which scales privilege which actors)

Critical cartography is not opposed to making maps. It is opposed to making maps *uncritically*. A critical cartographer maps as carefully and rigorously as a spatial analyst, but also documents the choices, exposes the silences, and **invites contestation** rather than asserting closure.

---

## Why both matter together — and to AFCN specifically

The AFCN project cannot be done with only one of these. Spatial analytics without critical cartography produces **technically impressive but politically naive** maps — the kind that confidently render a "food desert" without examining the colonial origins of that term, the federal threshold that defined it, or the informal economies the term erases. Critical cartography without spatial analytics produces **politically sharp but operationally useless** critique — eloquent essays about whose data is silenced, with no tools that a food-rescue dispatcher can actually use on Monday morning.

**AFCN holds the two in productive tension:**

| AFCN component | Spatial-analytics contribution | Critical-cartography contribution |
|---|---|---|
| **5 maps (Map 1–5 / M1, M2, M3, M5, M8)** | Quantile choropleths, network distance, walkshed isochrones, bivariate composite | `critical_review.md` interrogates each classification choice; exposes that the bivariate hides outliers and that the composite weights are political |
| **Real-Time Surplus Map** | Urgency-weighted routing, 4-stop optimization, transport-hierarchy scoring | The 96.5% / 3.5% compost-vs-donate ratio is foregrounded as a *provocation*, not a metric to optimize away |
| **AFCN Atlas + Network views** | 65 layers across 9 categories, 802 organizations rendered in a radial topology | The Network view's gaps are themselves a claim about who is unseen — three orgs at the April 15 workshop declined to publish beneficiary detail |
| **Workshop documentation** | Quantified gap matrix (14 orgs × 11 stages), composite scoring of org capabilities | Per-org "Cannot Share" quadrant explicitly records what each org refused to map; the workshop method *requires* declared silence |
| **M8 Composite Vulnerability Index** | 7-indicator weighted z-score synthesis, 5-quintile classification, tornado-chart sensitivity | The composite is presented with a printed disclaimer that "composite indices are interpretive tools, not ground truth" — the most technically powerful map carries the most explicit critique |

---

## Why this matters for *my* research topic

My research focuses on **the campus-to-community surplus pipeline** at Georgia Tech. The honest framing requires both methods.

**Spatial analytics tells me:** GT campus generates 2,316 lbs of measurable food waste per week (LeanPath, March 4–10, 2026), 1,392 lbs of which is overproduction-preventable. There are 233 ACFB-affiliated pantries within 25 mi of campus. The urgency-aware routing problem has a tractable solution: a 4-stop refrigerated-van loop covering high-priority pantries can be optimized in under 200ms via the ArcGIS Route API.

**Critical cartography tells me:** That answer is incomplete and risks doing harm. It assumes:
- the *formal* pantry network is what GT surplus should serve (ACFB-affiliated, public-facing addresses) — silencing front-porch fridges, mutual-aid networks, and faith-based distribution that operate without public visibility
- "rescue" is a virtue undifferentiated from its alternatives (composting locally, redesigning campus production to avoid overproduction in the first place)
- the campus is donor and the community is recipient (a power asymmetry that I, as a GT graduate researcher, embody and risk reproducing)
- one week of LeanPath data is a seasonal pattern (it is not)
- "Beneficiaries" prefer rescued food over funds, agency, or structural change (they may not)

The two methods are not in conflict. The spatial-analytics work makes specific, testable, operationally useful claims; the critical-cartography work makes those claims **contestable, situated, and accountable**. **A map that can be argued with is more honest than a map that cannot.** AFCN is built on the wager that partner orgs will actually *use* the dashboard precisely because the limits are visible — that legibility about what is uncertain is the prerequisite for trust.

---

## Sources

- Harley, J.B. (1989). "Deconstructing the Map." *Cartographica* 26(2): 1–20.
- Wood, D. (2010). *Rethinking the Power of Maps.* Guilford.
- Crampton, J. (2010). *Mapping: A Critical Introduction to Cartography and GIS.* Wiley.
- O'Sullivan, D. & Unwin, D. (2010). *Geographic Information Analysis.* 2nd ed. Wiley.
- Goodchild, M. (1992). "Geographical information science." *International Journal of GIS* 6(1).
- Kwan, M.-P. (2002). "Feminist visualization: Re-envisioning GIS as a method in feminist geographic research." *Annals of the AAG* 92(4).
- Bunge, W. (1971). *Fitzgerald: Geography of a Revolution.* Schenkman.

*One page · approx. 700 words.*
