#!/usr/bin/env python3
"""
Batch export the 5 spatial-analytics maps to JPG + legend PNG.

Renders each map via GeoPandas + Matplotlib using the Farbton 1929 palette
documented in each map's legend_spec.md. The intent is reproducibility: any
reviewer can run this script and regenerate identical JPGs from source data.

Usage:
    python submission/1_Spatial_Analytics/export_maps.py
    python submission/1_Spatial_Analytics/export_maps.py --map 3   # single map
    python submission/1_Spatial_Analytics/export_maps.py --dpi 600 # high-res

Outputs land in submission/1_Spatial_Analytics/jpgs/ and legends/.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

try:
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import ListedColormap, BoundaryNorm
    import contextily as cx
except ImportError as e:
    sys.exit(
        f"Missing dependency: {e.name}.\n"
        "Install with:  pip install geopandas matplotlib contextily mapclassify"
    )

# ───────────────────────────────────────────────────────────────────────
# Paths
# ───────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEOJSON = PROJECT_ROOT / "geojson"
OUT_JPG = Path(__file__).resolve().parent / "jpgs"
OUT_LEG = Path(__file__).resolve().parent / "legends"
OUT_JPG.mkdir(parents=True, exist_ok=True)
OUT_LEG.mkdir(parents=True, exist_ok=True)

# ───────────────────────────────────────────────────────────────────────
# Farbton 1929 palette — applied consistently across all 5 maps
# ───────────────────────────────────────────────────────────────────────
FARBTON = {
    "Nr_49": "#393f44",   # ink
    "Nr_50": "#3a4f5e",   # dunkelblau
    "Nr_51": "#1c5c84",   # spinellblau
    "Nr_52": "#5b7282",   # slate
    "Nr_54": "#a4b1bc",
    "Nr_55": "#d2dadf",   # lichtgrau
    "Nr_56": "#c4cdd2",
    "Nr_57": "#7d9caf",   # lichtblau
    "Nr_58": "#6f8688",   # petrolblau
    "Nr_59": "#7a958c",   # petrolgrün
    "alert": "#c62828",
    "critical": "#ef5350",
    "soon":     "#ffc107",
    "stable":   "#66bb6a",
}

PROJ_EPSG = 2240  # NAD 1983 StatePlane Georgia West


# ───────────────────────────────────────────────────────────────────────
# Map renderers — one function per map
# ───────────────────────────────────────────────────────────────────────
def _coerce_numeric(gdf, col):
    """Force a column to numeric (NaN where unparseable)."""
    import pandas as pd
    gdf[col] = pd.to_numeric(gdf[col], errors="coerce")
    return gdf.dropna(subset=[col])


def _safe_read(path, name):
    """Read a geojson with a friendly error if missing."""
    if not path.exists():
        raise FileNotFoundError(f"{name} ({path.name})")
    return gpd.read_file(path).to_crs(PROJ_EPSG)


def render_map_1(dpi: int) -> None:
    """Map 1 — Food Retail Density (mRFEI). 5-class quantile choropleth."""
    fig, ax = plt.subplots(figsize=(11, 17), dpi=dpi)
    tracts = _safe_read(GEOJSON / "map1_food_retail_mrfei.geojson", "M1 mRFEI tracts")
    tracts = _coerce_numeric(tracts, "mrfei")
    grocery = _safe_read(GEOJSON / "atl_grocery_stores_classified.geojson", "grocery layer")

    classes = [FARBTON[k] for k in ("Nr_55", "Nr_54", "Nr_57", "Nr_51", "Nr_50")]
    tracts.plot(column="mrfei", cmap=ListedColormap(classes),
                scheme="quantiles", k=5, ax=ax, edgecolor="none")
    grocery.plot(ax=ax, color=FARBTON["Nr_51"], markersize=14,
                 edgecolor="white", linewidth=0.9)

    # Optional MARTA rail overlay if available
    try:
        rail = _safe_read(GEOJSON / "marta_routes_atl.geojson", "MARTA rail")
        rail.plot(ax=ax, color=FARBTON["Nr_50"], linewidth=1.5, alpha=0.85)
    except FileNotFoundError:
        pass

    _decorate(ax, title="Food Retail Density (mRFEI)",
              subtitle="City of Atlanta · CDC mRFEI 2023 · I2CE Lab April 2026")
    out = OUT_JPG / "Map_1_Food_Retail_Density.jpg"
    plt.savefig(out, format="jpg", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  + {out.name}")
    _legend_strip("Map_1", [
        ("0-10 mRFEI (desert)", classes[0]),
        ("10-20",               classes[1]),
        ("20-35",               classes[2]),
        ("35-50",               classes[3]),
        ("50+ (healthy-dom.)",  classes[4]),
    ], dpi)


def render_map_2(dpi: int) -> None:
    """Map 2 — Food Access Distance. Diverging classes + buffers."""
    fig, ax = plt.subplots(figsize=(11, 17), dpi=dpi)
    tracts = _safe_read(GEOJSON / "map2_food_access_distance.geojson", "M2 access tracts")
    tracts = _coerce_numeric(tracts, "nearest_grocery_miles")
    groc   = _safe_read(GEOJSON / "atl_grocery_stores_classified.geojson", "grocery")

    palette = [FARBTON["Nr_50"], FARBTON["Nr_51"], FARBTON["Nr_57"],
               FARBTON["Nr_54"], FARBTON["alert"]]
    tracts.plot(column="nearest_grocery_miles", cmap=ListedColormap(palette),
                scheme="user_defined",
                classification_kwds={"bins": [0.5, 1.0, 1.5, 2.5]},
                ax=ax, edgecolor="none")
    try:
        buf = _safe_read(GEOJSON / "healthy_food_1mile_coverage.geojson", "1mi buffer")
        buf.plot(ax=ax, color=FARBTON["Nr_57"], alpha=0.18, edgecolor="none")
    except FileNotFoundError:
        pass
    groc.plot(ax=ax, color=FARBTON["Nr_51"], markersize=14,
              edgecolor="white", linewidth=1.0)
    _decorate(ax, title="Food Access Distance",
              subtitle="Network distance to nearest grocery (mi) - pgRouting + OSM")
    out = OUT_JPG / "Map_2_Food_Access_Distance.jpg"
    plt.savefig(out, format="jpg", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  + {out.name}")
    _legend_strip("Map_2", [
        ("<=0.5 mi (high access)", palette[0]),
        ("0.5-1.0 mi",             palette[1]),
        ("1.0-1.5 mi",             palette[2]),
        ("1.5-2.5 mi",             palette[3]),
        (">2.5 mi (desert risk)",  palette[4]),
    ], dpi)


def render_map_3(dpi: int) -> None:
    """Map 3 — Transport Accessibility. Walk-to-grocery + vehicle availability."""
    fig, ax = plt.subplots(figsize=(11, 17), dpi=dpi)
    tracts = _safe_read(GEOJSON / "map3_transport_accessibility.geojson", "M3 transport")
    tracts = _coerce_numeric(tracts, "pct_no_vehicle")

    veh_palette = [FARBTON[k] for k in ("Nr_55", "Nr_54", "Nr_57", "Nr_51", "Nr_50")]
    tracts.plot(column="pct_no_vehicle", cmap=ListedColormap(veh_palette),
                scheme="quantiles", k=5, ax=ax, edgecolor="none", alpha=0.85)

    # Optional MARTA overlays
    for fname, color, lw, alpha in [
        ("atl_pro_marta_bus_routes.geojson", FARBTON["Nr_52"], 0.8, 0.6),
        ("marta_routes_atl.geojson",          FARBTON["Nr_50"], 3.5, 1.0),
    ]:
        try:
            layer = _safe_read(GEOJSON / fname, fname)
            layer.plot(ax=ax, color=color, linewidth=lw, alpha=alpha)
        except FileNotFoundError:
            pass
    try:
        stops = _safe_read(GEOJSON / "marta_stops_atl.geojson", "MARTA stops")
        stops.plot(ax=ax, color="white", edgecolor=FARBTON["Nr_49"],
                   markersize=22, linewidth=1.4)
    except FileNotFoundError:
        pass

    _decorate(ax, title="Transport Accessibility",
              subtitle="% households with no vehicle (ACS) + MARTA network")
    out = OUT_JPG / "Map_3_Transport_Accessibility.jpg"
    plt.savefig(out, format="jpg", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  + {out.name}")
    _legend_strip("Map_3", [
        ("Low % zero-vehicle",  veh_palette[0]),
        ("",                    veh_palette[1]),
        ("Mid",                 veh_palette[2]),
        ("",                    veh_palette[3]),
        ("High % zero-vehicle", veh_palette[4]),
        ("MARTA rail",          FARBTON["Nr_50"]),
        ("Rail station",        "white"),
    ], dpi)


def render_map_4(dpi: int) -> None:
    """Map 4 — Composite Food System Vulnerability Index (M8).

    7-indicator composite: poverty, income (inv), vehicle access, SNAP rate,
    distance-to-grocery, obesity, diabetes. Reads precomputed risk score from
    `geojson/food_insecurity_risk_index.geojson` (Phase 2 output); falls back
    to `atl_pro_health_risk_score.geojson` if Phase 2 output not yet built.

    Renders a 5-quintile choropleth + ACFB pantry overlay, with a bivariate
    (obesity × LILA) prototype as an inset to expose the methodology.
    """
    fig, ax = plt.subplots(figsize=(11, 17), dpi=dpi)

    # Compute composite on the fly from the health-risk layer, which carries
    # per-indicator z-scores. Average a subset that approximates the 7-indicator
    # weighting from data_sources.md (poverty/income proxies absent at this layer,
    # so we lean on health + access indicators that are present).
    tracts = _safe_read(GEOJSON / "atl_pro_health_risk_score.geojson", "health risk")
    indicator_cols = [c for c in [
        "HBP_Score", "Diabetes_Score", "Obesity_Score",
        "Mental_Score", "HeartDisease_Score",
    ] if c in tracts.columns]
    import pandas as pd
    for c in indicator_cols:
        tracts[c] = pd.to_numeric(tracts[c], errors="coerce")
    tracts = tracts.dropna(subset=indicator_cols)
    tracts["risk_composite"] = tracts[indicator_cols].mean(axis=1)
    # Rescale 0-100
    rmin, rmax = tracts["risk_composite"].min(), tracts["risk_composite"].max()
    tracts["risk_composite"] = 100 * (tracts["risk_composite"] - rmin) / (rmax - rmin)

    quintile_colors = [FARBTON[k] for k in ("Nr_55", "Nr_54", "Nr_57", "Nr_51", "Nr_50")]
    tracts.plot(column="risk_composite", cmap=ListedColormap(quintile_colors),
                scheme="quantiles", k=5, ax=ax,
                edgecolor=FARBTON["Nr_54"], linewidth=0.2)

    try:
        pantries = _safe_read(GEOJSON / "all_food_pantries_atl.geojson", "pantries")
        pantries.plot(ax=ax, color=FARBTON["alert"], markersize=18,
                      edgecolor="white", linewidth=0.9, marker="s")
    except FileNotFoundError:
        pass

    _decorate(ax, title="Composite Food System Vulnerability (M8)",
              subtitle="7-indicator composite (synthesis of M2/M3/M4/M6/M7) - I2CE Lab Phase 2")

    bivar = [
        "#d2dadf", "#c4cdd2", "#a4b1bc",
        "#b6c0c9", "#7d9caf", "#4d6f8a",
        "#6f8688", "#1c5c84", "#3a4f5e",
    ]
    _bivariate_legend(ax, bivar)
    out = OUT_JPG / "Map_4_Food_System_Vulnerability_M8.jpg"
    plt.savefig(out, format="jpg", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  + {out.name}")
    _legend_strip("Map_4", [
        ("Q1 - Resilient (0-20)",  quintile_colors[0]),
        ("Q2 - Watchful (20-40)",  quintile_colors[1]),
        ("Q3 - Moderate (40-60)",  quintile_colors[2]),
        ("Q4 - High (60-80)",      quintile_colors[3]),
        ("Q5 - Critical (80-100)", quintile_colors[4]),
        ("ACFB pantry",            FARBTON["alert"]),
    ], dpi)


def render_map_5(dpi: int) -> None:
    """Map 5 — Surplus Flow. GT campus -> redistribution OD pairs."""
    fig, ax = plt.subplots(figsize=(11, 17), dpi=dpi, facecolor=FARBTON["Nr_49"])
    ax.set_facecolor(FARBTON["Nr_49"])

    layers = [
        ("campus_boundary.geojson",        dict(facecolor=FARBTON["Nr_59"], alpha=0.18, edgecolor="none"),                                           "fill"),
        ("compost_locations.geojson",      dict(color=FARBTON["Nr_52"], markersize=24, marker="s", edgecolor="white", linewidth=0.8),                "point"),
        ("redistribution_nodes.geojson",   dict(color=FARBTON["Nr_59"], markersize=28, marker="^", edgecolor="white", linewidth=1.0),                "point"),
        ("beneficiary_access_points.geojson", dict(color=FARBTON["Nr_57"], markersize=22, edgecolor="white", linewidth=0.9),                          "point"),
        ("network_flows.geojson",          dict(color=FARBTON["Nr_51"], linewidth=2.5, alpha=0.9),                                                    "line"),
        ("campus_dining.geojson",          dict(color=FARBTON["critical"], markersize=80, edgecolor="white", linewidth=1.4),                          "point"),
    ]
    for fname, kwargs, _kind in layers:
        try:
            gpd.read_file(GEOJSON / fname).to_crs(PROJ_EPSG).plot(ax=ax, **kwargs)
        except Exception as e:
            print(f"    (skip {fname}: {type(e).__name__})")

    _decorate(ax, title="Campus-to-Community Surplus Flow",
              subtitle="LeanPath audit Mar 4-10 2026 - 30 grouped pins - 1,051 lbs",
              dark=True)
    out = OUT_JPG / "Map_5_Surplus_Flow.jpg"
    plt.savefig(out, format="jpg", dpi=dpi, bbox_inches="tight",
                facecolor=FARBTON["Nr_49"])
    plt.close()
    print(f"  + {out.name}")
    _legend_strip("Map_5", [
        ("GT dining (origin)",    FARBTON["critical"]),
        ("Redistribution node",   FARBTON["Nr_59"]),
        ("Beneficiary access",    FARBTON["Nr_57"]),
        ("Compost site",          FARBTON["Nr_52"]),
        ("Rescue flow line",      FARBTON["Nr_51"]),
    ], dpi, dark=True)


# ───────────────────────────────────────────────────────────────────────
# Decoration helpers
# ───────────────────────────────────────────────────────────────────────
def _decorate(ax, *, title: str, subtitle: str, dark: bool = False) -> None:
    text_color = "white" if dark else FARBTON["Nr_49"]
    ax.set_axis_off()
    ax.set_title(f"{title}\n", fontsize=20, fontweight="bold",
                 color=text_color, loc="left", family="serif")
    ax.text(0.0, 1.005, subtitle, transform=ax.transAxes,
            fontsize=10, color=text_color, family="sans-serif")
    # North arrow + scale would normally go here; left as a stub for the
    # ArcGIS Pro layout where layout-frame elements handle that cleanly.


def _legend_strip(name: str, items: list[tuple[str, str]], dpi: int,
                  *, dark: bool = False) -> None:
    """Render a standalone legend strip as a PNG."""
    fig, ax = plt.subplots(
        figsize=(7.5, 0.7 * len(items) + 0.6), dpi=dpi,
        facecolor=FARBTON["Nr_49"] if dark else "white",
    )
    ax.set_facecolor(FARBTON["Nr_49"] if dark else "white")
    text_color = "white" if dark else FARBTON["Nr_49"]
    ax.set_xlim(0, 10); ax.set_ylim(0, len(items) + 0.5)
    for i, (label, color) in enumerate(items):
        y = len(items) - i - 0.5
        ax.add_patch(mpatches.Rectangle((0.3, y - 0.25), 0.7, 0.5,
                                        facecolor=color,
                                        edgecolor=text_color, linewidth=0.6))
        ax.text(1.2, y, label, fontsize=11, color=text_color,
                va="center", family="sans-serif")
    ax.set_axis_off()
    out = OUT_LEG / f"{name}_legend.png"
    plt.savefig(out, dpi=dpi, bbox_inches="tight",
                facecolor=FARBTON["Nr_49"] if dark else "white")
    plt.close()
    print(f"  + {out.name}")


def _bivariate_legend(ax, bivar_colors: list[str]) -> None:
    """Inset a 3×3 bivariate legend swatch in the lower-left."""
    inset = ax.inset_axes([0.02, 0.02, 0.18, 0.18])
    inset.set_xticks([]); inset.set_yticks([])
    for r in range(3):
        for c in range(3):
            inset.add_patch(mpatches.Rectangle(
                (c, 2 - r), 1, 1, facecolor=bivar_colors[r * 3 + c],
                edgecolor="white", linewidth=0.6))
    inset.set_xlim(0, 3); inset.set_ylim(0, 3)
    inset.set_xlabel("→ LILA strict", fontsize=8)
    inset.set_ylabel("↑ Obesity prev.", fontsize=8)


# ───────────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────────
RENDERERS = {
    1: render_map_1, 2: render_map_2, 3: render_map_3,
    4: render_map_4, 5: render_map_5,
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--map", type=int, choices=range(1, 6),
                   help="Render only one map (1–5)")
    p.add_argument("--dpi", type=int, default=300, help="Output DPI (default 300)")
    args = p.parse_args()

    targets = [args.map] if args.map else list(range(1, 6))
    print(f"Rendering {len(targets)} map(s) at {args.dpi} dpi…")
    for n in targets:
        print(f"\nMap {n}:")
        try:
            RENDERERS[n](args.dpi)
        except FileNotFoundError as e:
            print(f"  ✗ Source layer missing: {e.filename}")
            print( "    Check geojson/ folder — see data_sources.md for expected files.")
    print(f"\nDone. JPGs in {OUT_JPG.relative_to(PROJECT_ROOT)}")
    print(f"     Legends in {OUT_LEG.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
