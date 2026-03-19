# -*- coding: utf-8 -*-
"""
Download ArcGIS Online hosted layers as GeoJSON via REST API.

Queries FeatureServer endpoints with spatial filters (Atlanta bbox),
handles pagination for large datasets, and saves to geojson/ folder.

Requirements:
    pip install requests geopandas shapely

Usage:
    python fetch_arcgis_layers.py              # download all layers
    python fetch_arcgis_layers.py vehicle      # download just vehicle availability
"""

import os
import sys
import json
import time
import requests
import geopandas as gpd
from shapely.geometry import shape, box

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GEOJSON_DIR = os.path.join(BASE_DIR, "geojson")

# Atlanta metro bounding box (Fulton + DeKalb counties, generous)
ATL_BBOX = {
    "xmin": -84.65,
    "ymin": 33.55,
    "xmax": -84.15,
    "ymax": 33.95,
}

# Layer definitions: key -> (service_url, layer_id, output_filename, where_clause, description)
LAYERS = {
    "vehicle": {
        "url": "https://services1.arcgis.com/Ug5xGQbHsD8zuZzM/arcgis/rest/services/ACS%202022%20Housing%20Vehicles%20GeoSplitJoined/FeatureServer",
        "layer_id": 19,  # Tract level
        "output": "census_vehicle_availability_ga.geojson",
        "where": "1=1",
        "description": "ACS 2022 Vehicle Availability by Census Tract",
        "use_bbox": True,
    },
    "transit": {
        "url": "https://services2.arcgis.com/I9cUOJUZvdGAJncI/arcgis/rest/services/Transit_Routes_in_Atlanta/FeatureServer",
        "layer_id": 0,
        "output": "transit_routes_atl.geojson",
        "where": "1=1",
        "description": "Transit Routes in Atlanta",
        "use_bbox": True,
    },
    "places": {
        "url": "https://services3.arcgis.com/ZvidGQkLaDJxRSJ2/arcgis/rest/services/PLACES_LocalData_for_BetterHealth/FeatureServer",
        "layer_id": 3,  # Tract level
        "output": "places_food_insecurity.geojson",
        "where": "StateAbbr='GA' AND (CountyName='Fulton' OR CountyName='DeKalb')",
        "description": "CDC PLACES Health Data (Fulton + DeKalb tracts)",
        "use_bbox": False,  # Use where clause instead
    },
}


def query_feature_layer(base_url, layer_id, where="1=1", bbox=None,
                        out_fields="*", max_per_request=2000):
    """
    Query an ArcGIS FeatureServer layer with pagination.
    Returns a list of GeoJSON features.
    """
    query_url = f"{base_url}/{layer_id}/query"
    all_features = []
    offset = 0

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "geojson",
            "returnGeometry": "true",
            "resultOffset": offset,
            "resultRecordCount": max_per_request,
            "outSR": "4326",
        }

        if bbox:
            params["geometry"] = json.dumps({
                "xmin": bbox["xmin"],
                "ymin": bbox["ymin"],
                "xmax": bbox["xmax"],
                "ymax": bbox["ymax"],
                "spatialReference": {"wkid": 4326},
            })
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        print(f"    Fetching offset {offset}...", end=" ", flush=True)
        resp = requests.get(query_url, params=params, timeout=120)

        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}")
            print(f"    Response: {resp.text[:500]}")
            break

        data = resp.json()

        if "error" in data:
            print(f"API Error: {data['error'].get('message', data['error'])}")
            break

        features = data.get("features", [])
        print(f"{len(features)} features")
        all_features.extend(features)

        # Check if there are more results
        if len(features) < max_per_request:
            break

        offset += max_per_request
        time.sleep(0.5)  # Be polite to the API

    return all_features


def download_layer(key, layer_cfg, skip_existing=True):
    """Download a single layer and save as GeoJSON."""
    output_path = os.path.join(GEOJSON_DIR, layer_cfg["output"])

    if skip_existing and os.path.exists(output_path):
        print(f"  [SKIP] {layer_cfg['output']} already exists")
        return True

    print(f"\n  [{key.upper()}] {layer_cfg['description']}")
    print(f"  Service: {layer_cfg['url']}/{layer_cfg['layer_id']}")

    bbox = ATL_BBOX if layer_cfg.get("use_bbox") else None
    features = query_feature_layer(
        layer_cfg["url"],
        layer_cfg["layer_id"],
        where=layer_cfg["where"],
        bbox=bbox,
    )

    if not features:
        print(f"  [ERR] No features returned")
        return False

    # Build GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Write raw first, then validate with geopandas
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    try:
        gdf = gpd.read_file(tmp_path)

        # Drop null geometries
        gdf = gdf[gdf.geometry.notna()]

        if gdf.empty:
            print(f"  [ERR] All features had null geometry")
            os.remove(tmp_path)
            return False

        # Ensure WGS84
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Save final GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")
        os.remove(tmp_path)

        geom_type = gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else "?"
        fields = [c for c in gdf.columns if c != "geometry"]
        print(f"  [OK]  {layer_cfg['output']:<50} {len(gdf):>5} features ({geom_type})")
        print(f"        Fields: {fields[:8]}{'...' if len(fields) > 8 else ''}")
        return True

    except Exception as e:
        print(f"  [ERR] Failed to process: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def main():
    os.makedirs(GEOJSON_DIR, exist_ok=True)

    # Determine which layers to download
    if len(sys.argv) > 1:
        keys = [k for k in sys.argv[1:] if k in LAYERS]
        if not keys:
            print(f"Unknown layer(s). Available: {', '.join(LAYERS.keys())}")
            return
    else:
        keys = list(LAYERS.keys())

    print(f"Downloading {len(keys)} layer(s) from ArcGIS Online")
    print(f"Output directory: {GEOJSON_DIR}")
    print(f"Atlanta bbox: {ATL_BBOX}")

    success = 0
    errors = 0

    for key in keys:
        result = download_layer(key, LAYERS[key], skip_existing=False)
        if result:
            success += 1
        else:
            errors += 1

    print(f"\n{'=' * 60}")
    print(f"Download Complete")
    print(f"  Success: {success}")
    print(f"  Errors:  {errors}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
