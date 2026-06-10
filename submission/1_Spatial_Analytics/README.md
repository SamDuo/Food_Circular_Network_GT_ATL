# 1 · Spatial Analytics — 5 Maps
**Quan Duong · AFCN · April 2026**

---

## Overview

Five maps that together tell the story of Atlanta's food environment from individual indicator layers (M1, M2, M3) → core operation (M5 surplus rescue) → integrated risk synthesis (**M8 composite vulnerability**). Each map uses the **same study area** (City of Atlanta + 5-county metro for context), the **same projection** (NAD 1983 StatePlane Georgia West, EPSG: 2240), and a **consistent editorial palette** (Farbton 1929 standardfarbtonkarte — blue-grey family) so they read as a series.

These 5 maps cover **5 of the 8 framework maps** described in `Food_System_Framework_Analysis.md`. The remaining (M4 Food Assistance Demand stand-alone, M6 Socioeconomic stand-alone, M7 Health Outcomes stand-alone) are inputs that get absorbed into Map 4 (M8 composite).

| # | Framework | Map title | Data source | Classification | Lens |
|---|---|---|---|---|---|
| 1 | **M1** | Food Retail Density (mRFEI) | CDC mRFEI 2023 + USDA SNAP retailers | 5-class quantile | Sequential (Nr. 55 → Nr. 50) |
| 2 | **M2** | Food Access Distance | OpenStreetMap network + USDA grocery layer | 1 mi / 0.5 mi buffer + tract overlay | Diverging (gap zones in red) |
| 3 | **M3** | Transport Accessibility | MARTA GTFS + walkshed isochrone | 5 / 10 / 15 min walk bands | Sequential blue |
| 4 | **M8** | **Composite Food System Vulnerability** | 7-indicator stack (ACS + CDC PLACES + pgRouting) — synthesizes M2/M3/M4/M6/M7 | 5-quintile composite + tornado sensitivity | Sequential blue + bivariate inset |
| 5 | **M5** | Campus-to-Community Surplus Flow | LeanPath GT data + 30 grouped surplus pins + rescue OD pairs | Flow lines + urgency-weighted pin sizes | Flow (directional) |

**Why this cut?**
- M1, M2, M3 are *foundational layers* — the basemap that any food-system claim relies on
- **M5 (surplus recovery) is Quan's core project strength** — the AFCN dashboard was built around this
- **M8 (composite vulnerability) is the Phase 2 capstone** — the synthesis the framework analysis flagged as "not implemented" until now
- The bivariate (obesity × LILA) technique that Map 4 previously highlighted is now an *inset on M8*, kept as a methodological stepping-stone

---

## Per-map deliverable structure

For each of the 5 maps, the `maps/` folder contains:

```
maps/
├── Map_1_Food_Retail_Density/             ← M1
├── Map_2_Food_Access_Distance/            ← M2
├── Map_3_Transport_Accessibility/         ← M3
├── Map_4_Food_System_Vulnerability_M8/    ← M8 composite (CAPSTONE)
└── Map_5_Surplus_Flow/                    ← M5 (CORE)

Each contains:
├── *.aprx                                  ← ArcGIS Pro project file (original)
├── *.qgz                                   ← QGIS project (cross-platform alt)
├── data_sources.md                         ← Provenance + dates + license
└── legend_spec.md                          ← Classification breaks + colors
```

Rendered outputs:

```
jpgs/
├── Map_1_Food_Retail_Density.jpg              ← 300 dpi, 11×17 letter
├── Map_2_Food_Access_Distance.jpg
├── Map_3_Transport_Accessibility.jpg
├── Map_4_Food_System_Vulnerability_M8.jpg
└── Map_5_Surplus_Flow.jpg

legends/
├── Map_1_legend.png                            ← Standalone legend strip
├── Map_2_legend.png
└── … (legends 3–5)
```

---

## How to regenerate the JPGs

Run from project root:

```powershell
python submission/1_Spatial_Analytics/export_maps.py
```

The script reads `geojson/` source layers, applies the renderer specs in `legend_spec.md`, and renders each map at 300 dpi. Outputs land in `jpgs/` and `legends/`.

For the .aprx originals, open `exports/AFCN_Atlanta.aprx` in ArcGIS Pro — each of the 5 maps exists as a separate layout. Use **Share → Export Layout → PNG/JPG** at 300 dpi.

---

## Cartographic standards applied

- **Projection:** EPSG:2240 (NAD 1983 StatePlane Georgia West, US Feet) — preserves shape for Atlanta-scale comparisons
- **Color palette:** Farbton 1929 standardfarbtonkarte — Nr. 51 spinellblau primary, Nr. 57 lichtblau secondary
- **Sequential ramps:** Nr. 55 → Nr. 54 → Nr. 57 → Nr. 51 → Nr. 50 (light to dark)
- **Composite ramp (Map 4 / M8):** 5-quintile sequential Nr. 55 → Nr. 50, with a Stevens 2015 bivariate (3×3) **inset** illustrating the methodology's first step
- **Type:** Inter (sans, labels) + Source Serif 4 (titles)
- **Scale bar:** miles primary, km secondary
- **North arrow:** simple chevron, lower-right
- **Inset:** 5-county metro context, top-right corner

---

## Notes on data lineage

See `2_Critical_Cartography/critical_review.md` for a critical discussion of:
- Why mRFEI was chosen over the simpler USDA Food Access Research Atlas
- Limitations of network-distance buffers (no transit time, no real-world barriers)
- How the bivariate classification quietly conceals tract-level outliers
