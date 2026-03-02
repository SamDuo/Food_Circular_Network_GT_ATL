# -*- coding: utf-8 -*-
"""
GT Campus Food Circular Hub (GT-FCH) - Shapefile to GeoJSON Converter
Converts all campus shapefiles to WGS84 GeoJSON for use in the web map.

Requirements:
    pip install geopandas
"""

import os
import sys
import json
import geopandas as gpd

# Force UTF-8 output so arrow/check characters don't crash on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "geojson")

# Shapefile name → output GeoJSON filename
SHAPEFILES = {
    "campus_boundary":       "CampusBoundary_generalized_20260220",
    "buildings":             "GTBuildings_20260220",
    "street_centerlines":    "CampusStreetCenterlines",
    "sidewalks":             "GTSidewalks_20260220",
    "compost_locations":     "CompostLocations",
    "vending_machines":      "GTVendingMachineLocations",
    "recycling_trash_cans":  "RecyclingTrashCans_asof2021",
    "trash_recycling_indoor":"TrashRecycling_mostlyindoors",
}


def convert_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}\n")

    results = {}
    for key, shp_name in SHAPEFILES.items():
        shp_path = os.path.join(BASE_DIR, f"{shp_name}.shp")

        if not os.path.exists(shp_path):
            print(f"  [SKIP] Not found: {shp_name}.shp")
            continue

        print(f"[...] Converting: {shp_name}")
        try:
            gdf = gpd.read_file(shp_path)

            # Reproject everything to WGS84 (EPSG:4326) for web mapping
            if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                print(f"       Reprojecting from {gdf.crs.to_string()} → EPSG:4326")
                gdf = gdf.to_crs(epsg=4326)

            # Drop rows with null geometry
            gdf = gdf[gdf.geometry.notna()]

            out_path = os.path.join(OUTPUT_DIR, f"{key}.geojson")
            gdf.to_file(out_path, driver="GeoJSON")

            fields = [c for c in gdf.columns if c != "geometry"]
            print(f"  [OK]  {len(gdf)} features | Fields: {fields}")
            print(f"        Saved → geojson/{key}.geojson\n")

            results[key] = {"file": f"{key}.geojson", "count": len(gdf), "fields": fields}

        except Exception as e:
            print(f"  [ERR] {shp_name}: {e}\n")

    # Write a manifest so the web app knows what's available
    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Manifest written → geojson/manifest.json")
    print("\nAll done! Run  python serve.py  to start the local server.")


if __name__ == "__main__":
    convert_all()
