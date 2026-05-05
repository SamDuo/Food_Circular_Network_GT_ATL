"""
Fetch authoritative GIS layers for the City of South Fulton, Georgia,
and export to every format ArcGIS Pro / ArcGIS Online ingests cleanly.

Source: City of South Fulton's own ArcGIS Online organization, exposed via
the "South_Fulton_City_Limits_And_Districts_WFL1" FeatureServer:

    https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/services/
        South_Fulton_City_Limits_And_Districts_WFL1/FeatureServer/

  /0  Street Centerlines      6,232 polylines
  /1  City Limits                 3 polygons (main + detached areas)
  /2  City Council Districts      8 polygons

Outputs (in `geojson/` and `gis_exports/southfulton/`):

  geojson/southfulton_*.geojson         (Mapbox / Leaflet / web)
  gis_exports/southfulton/*.shp.zip     (ArcGIS Pro 'Add Data')
  gis_exports/southfulton/*.gpkg        (modern single-file format,
                                          works in ArcGIS Pro 2.5+, QGIS,
                                          and the ArcGIS Online uploader)
  gis_exports/southfulton/*.kmz         (Google Earth + ArcGIS Pro)
  gis_exports/southfulton/README.md     (how to use the exports)

USAGE
─────
    python scripts/fetch_south_fulton.py

Optional dependencies for the ArcGIS-native exports:
    pip install geopandas pyogrio
If those are missing, the script still produces the GeoJSON outputs
(which ArcGIS Pro can also read directly via 'Add Data')."""

import json, os, shutil, time, urllib.parse, urllib.request, zipfile
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
OUT_GJ    = ROOT / "geojson"
OUT_GIS   = ROOT / "gis_exports" / "southfulton"
OUT_GJ.mkdir(exist_ok=True)
OUT_GIS.mkdir(parents=True, exist_ok=True)

# Try to import optional GIS export stack (geopandas + pyogrio backend)
try:
    import geopandas as gpd
    HAS_GPD = True
except ImportError:
    gpd = None
    HAS_GPD = False

BASE = ("https://services3.arcgis.com/y2BJK2GUfoTwH7py/"
        "arcgis/rest/services/"
        "South_Fulton_City_Limits_And_Districts_WFL1/FeatureServer")

LAYERS = [
    {"id": 0, "name": "streets",            "out": "southfulton_streets.geojson"},
    {"id": 1, "name": "city_limits",        "out": "southfulton_city_limits.geojson"},
    {"id": 2, "name": "council_districts",  "out": "southfulton_council_districts.geojson"},
]

PAGE = 2000  # service maxRecordCount is 2000


def query(layer_id: int, offset: int) -> dict:
    """Single paginated query against an ArcGIS FeatureServer layer."""
    params = {
        "where":               "1=1",
        "outFields":           "*",
        "outSR":               "4326",                # WGS84 lon/lat
        "f":                   "geojson",
        "returnGeometry":      "true",
        "resultRecordCount":   PAGE,
        "resultOffset":        offset,
    }
    url = f"{BASE}/{layer_id}/query?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "AFCN/fetch_south_fulton 1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_layer(layer: dict) -> dict:
    """Page through a layer until exhausted; merge into one FeatureCollection."""
    print(f"\n→ {layer['name']:18s}  /{layer['id']}")
    offset, all_features = 0, []
    while True:
        chunk = query(layer["id"], offset)
        feats = chunk.get("features", [])
        if not feats:
            break
        all_features.extend(feats)
        print(f"    page offset={offset:>5d}  +{len(feats):>4d}  total={len(all_features):>5d}")
        if len(feats) < PAGE:
            break
        offset += PAGE
        time.sleep(0.15)   # gentle pacing
    return {
        "type": "FeatureCollection",
        "features": all_features,
        "_source": (
            f"{BASE}/{layer['id']}  · fetched "
            f"{time.strftime('%Y-%m-%d')} from City of South Fulton ArcGIS Online"
        ),
    }


def export_arcgis_formats(geojson_path: Path, name: str) -> dict:
    """Read the GeoJSON we just wrote and re-emit it as Shapefile (zipped),
    GeoPackage, and KMZ. Returns dict of {format: path|error}.
    Skipped silently if geopandas isn't installed."""
    results = {}
    if not HAS_GPD:
        return {"_skipped": "geopandas not installed (pip install geopandas pyogrio)"}

    gdf = gpd.read_file(geojson_path)
    # Shapefile attribute column names are limited to 10 chars; truncate safely
    shp_dir = OUT_GIS / f"{name}_shp"
    if shp_dir.exists():
        shutil.rmtree(shp_dir, ignore_errors=True)
    shp_dir.mkdir(parents=True, exist_ok=True)
    shp_path = shp_dir / f"{name}.shp"
    try:
        # Shapefile column names are 10-char-max; truncate AND deduplicate
        gdf_shp = gdf.copy()
        truncated, seen = [], {}
        for c in gdf_shp.columns:
            base = c[:10] if len(c) > 10 else c
            if base in seen:
                seen[base] += 1
                # keep within 10 chars by reserving space for the suffix
                suffix = str(seen[base])
                base = (base[:10 - len(suffix)] + suffix)
            else:
                seen[base] = 0
            truncated.append(base)
        gdf_shp.columns = truncated
        gdf_shp.to_file(shp_path, driver="ESRI Shapefile")
        # Bundle into zip (Shapefiles are 4-6 sidecar files; users want one file)
        zip_path = OUT_GIS / f"{name}.shp.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in shp_dir.iterdir():
                zf.write(f, arcname=f.name)
        shutil.rmtree(shp_dir, ignore_errors=True)
        results["Shapefile (.shp.zip)"] = zip_path
    except Exception as e:
        results["Shapefile (.shp.zip)"] = f"failed: {e}"

    # GeoPackage — single file, modern, no column-name truncation
    try:
        gpkg = OUT_GIS / f"{name}.gpkg"
        if gpkg.exists():
            gpkg.unlink()
        gdf.to_file(gpkg, driver="GPKG", layer=name)
        results["GeoPackage (.gpkg)"] = gpkg
    except Exception as e:
        results["GeoPackage (.gpkg)"] = f"failed: {e}"

    # KMZ — pyogrio supports LIBKML driver; KMZ is a zipped KML
    try:
        kml_path = OUT_GIS / f"{name}.kml"
        if kml_path.exists():
            kml_path.unlink()
        gdf.to_file(kml_path, driver="KML")
        kmz_path = OUT_GIS / f"{name}.kmz"
        with zipfile.ZipFile(kmz_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(kml_path, arcname=f"{name}.kml")
        kml_path.unlink()
        results["KMZ"] = kmz_path
    except Exception as e:
        results["KMZ"] = f"failed: {e}"

    return results


def write_readme(layer_summaries: list[dict]) -> None:
    body = ["# City of South Fulton — GIS Exports\n"]
    body.append(f"_Generated {time.strftime('%Y-%m-%d')}_\n")
    body.append("**Source:** City of South Fulton ArcGIS Online → ")
    body.append("`South_Fulton_City_Limits_And_Districts_WFL1` FeatureServer\n")
    body.append("All layers are in WGS 84 / EPSG:4326.\n\n")
    body.append("## Layers exported\n\n")
    body.append("| Layer | Features | Geometry |\n|---|---:|---|\n")
    for s in layer_summaries:
        body.append(f"| {s['name']} | {s['count']:,} | {s['geom']} |\n")
    body.append("\n## Files\n\n")
    body.append("Each layer ships in four formats:\n\n")
    body.append("- `*.shp.zip` — Zipped ESRI Shapefile bundle. Unzip, then "
                "drag the `.shp` into ArcGIS Pro. Field names are truncated "
                "to 10 characters per the Shapefile spec.\n")
    body.append("- `*.gpkg` — GeoPackage. Single-file format, ArcGIS Pro "
                "2.5+ reads it natively (Catalog → drag in). Preserves full "
                "column names.\n")
    body.append("- `*.kmz` — Google Earth + ArcGIS Pro. Display-only.\n")
    body.append("- `geojson/southfulton_*.geojson` — Web (Mapbox / Leaflet) "
                "and also readable directly by ArcGIS Pro via 'Add Data'.\n\n")
    body.append("## Live REST endpoints\n\n")
    body.append("If you would rather pull live data, add these as services "
                "in ArcGIS Pro (Catalog → Servers → Add ArcGIS Server):\n\n")
    body.append("```\n")
    body.append("https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/"
                "services/South_Fulton_City_Limits_And_Districts_WFL1/"
                "FeatureServer/0   (street centerlines)\n")
    body.append("https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/"
                "services/South_Fulton_City_Limits_And_Districts_WFL1/"
                "FeatureServer/1   (city limits)\n")
    body.append("https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/"
                "services/South_Fulton_City_Limits_And_Districts_WFL1/"
                "FeatureServer/2   (council districts)\n")
    body.append("```\n")
    (OUT_GIS / "README.md").write_text("".join(body), encoding="utf-8")


def main():
    print(f"Source: {BASE}\n")
    if not HAS_GPD:
        print("⚠  geopandas not installed — only GeoJSON outputs will be produced.")
        print("    For Shapefile / GeoPackage / KMZ exports, run:")
        print("    pip install geopandas pyogrio\n")

    summaries = []
    for layer in LAYERS:
        gj = fetch_layer(layer)
        gj_path = OUT_GJ / layer["out"]
        gj_path.write_text(json.dumps(gj, separators=(",", ":")), encoding="utf-8")
        n = len(gj["features"])
        geom = (gj["features"][0]["geometry"]["type"]
                if n and gj["features"][0].get("geometry") else "—")
        kb = gj_path.stat().st_size / 1024
        print(f"    ✓ {gj_path.name}  ({n:,} features, {kb:,.0f} KB)")
        summaries.append({"name": layer["name"], "count": n, "geom": geom})

        # Export to ArcGIS-native formats
        name_for_export = layer["out"].replace(".geojson", "")
        results = export_arcgis_formats(gj_path, name_for_export)
        for fmt, val in results.items():
            if isinstance(val, Path):
                kb = val.stat().st_size / 1024
                print(f"    ✓ {fmt:<22s} {val.name}  ({kb:,.0f} KB)")
            else:
                print(f"    · {fmt:<22s} {val}")

    if HAS_GPD:
        write_readme(summaries)
        print(f"\n✓ Wrote {OUT_GIS / 'README.md'}")
    print(f"\nAll exports: {OUT_GIS}")
    print("To preview in ArcGIS Pro, open the .gpkg or unzip the .shp.zip and drag the .shp in.")


if __name__ == "__main__":
    main()
