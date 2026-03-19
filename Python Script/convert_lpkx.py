# -*- coding: utf-8 -*-
"""
Convert ArcGIS Layer Packages (.lpkx) to GeoJSON.

.lpkx files are 7-zip archives containing a file geodatabase (.gdb).
This script extracts each .lpkx, reads the geodatabase with geopandas/fiona,
reprojects to WGS84, and saves as GeoJSON in the geojson/ folder.

Requirements:
    pip install geopandas fiona py7zr

Usage:
    python convert_lpkx.py                          # convert all .lpkx in Layers & Packages
    python convert_lpkx.py MARTA_Routes_-_ATL.lpkx  # convert a single file
"""

import os
import sys
import glob
import zipfile
import tempfile
import shutil
import re
import geopandas as gpd
import py7zr

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LPKX_DIR = os.path.join(BASE_DIR, "resources", "Layers & Packages")
GEOJSON_DIR = os.path.join(BASE_DIR, "geojson")

# Atlanta metro bounding box (generous) for clipping national/state datasets
# Covers roughly: Marietta to McDonough (N-S), Douglasville to Stone Mountain (E-W)
ATL_BBOX = (-84.65, 33.55, -84.15, 33.95)  # (minx, miny, maxx, maxy)

# Map .lpkx filenames to desired output GeoJSON names
# If not listed here, a name is auto-generated from the .lpkx filename
FILENAME_MAP = {
    "Midtown_Convenience_Stores.lpkx":                              "midtown_convenience_stores.geojson",
    "MARTA_Routes_-_ATL.lpkx":                                      "marta_routes_atl.geojson",
    "MARTA_Stops_-_ATL.lpkx":                                       "marta_stops_atl.geojson",
    "Vehicle_Availability_2022_(all_geographies__statewide).lpkx":   "census_vehicle_availability_ga.geojson",
    "10_Minute_Walk_Access_to_Grocery_Stores_-_USA.lpkx":            "walk_access_grocery_2024.geojson",
    "10_Minute_Drive_Access_to_Grocery_Stores_-_USA.lpkx":           "drive_access_grocery_2024.geojson",
    "Transit_Routes_-_Atlanta.lpkx":                                 "transit_routes_atl.geojson",
    "Places_with_food_insecurity.lpkx":                              "places_food_insecurity.geojson",
    "Food_Deserts_-_Atlanta.lpkx":                                   "food_deserts_atlanta_pkg.geojson",
    # Already-converted packages (skip if GeoJSON exists)
    "All_Fast_Food_Locations_in_Metro_Atlanta.lpkx":                 "pkg_all_fast_food_locations_in_metro_atlanta.geojson",
    "Atlanta_Fast_Food_Restaurants.lpkx":                            "pkg_atlanta_fast_food_restaurants.geojson",
    "Atlanta_Grocery_Stores.lpkx":                                   "pkg_atlanta_grocery_stores.geojson",
    "Atlanta_Metro_Area_Farmers_Markets.lpkx":                       "pkg_atlanta_metro_area_farmers_markets.geojson",
    "Campus_Dining.lpkx":                                            "pkg_campus_dining.geojson",
    "Community_Based_Organizations_-_Atlanta.lpkx":                  "pkg_community_based_organizations_atlanta.geojson",
    "Fast_Food_on_GT_Campus.lpkx":                                   "pkg_fast_food_on_gt_campus.geojson",
    "Food_Processing_Facilities_in_the_Southeast.lpkx":              "pkg_food_processing_facilities_in_the_southeast.geojson",
    "Gardens_Farms_and_Orchards_-_Atlanta.lpkx":                     "pkg_gardens_farms_and_orchards_atlanta.geojson",
    "Hospitals_and_Health_Clinics_Atlanta.lpkx":                     "pkg_hospitals_and_health_clinics_atlanta.geojson",
    "Religious_Institutions_-_Metro_Atlanta.lpkx":                   "pkg_religious_institutions_metro_atlanta.geojson",
    "Restaurant_Chains_-_GA.lpkx":                                   "pkg_restaurant_chains_ga.geojson",
    "Restaurants_and_Cafes_-_Atlanta.lpkx":                          "pkg_restaurants_and_cafes_atlanta.geojson",
    "Supermarkets_-_MetroATL.lpkx":                                  "pkg_supermarkets_metroatl.geojson",
    "US_Kroger_Network_v_Household_Income.mpkx":                     "pkg_us_kroger_network_v_household_income.geojson",
}


def slugify(name):
    """Convert a filename to a clean geojson name."""
    name = os.path.splitext(name)[0]
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return name + ".geojson"


def extract_archive(archive_path, tmp_dir):
    """Extract a .lpkx/.mpkx archive (7z or ZIP)."""
    # Try 7z first (ArcGIS Pro uses 7-zip format for .lpkx)
    try:
        with py7zr.SevenZipFile(archive_path, "r") as sz:
            sz.extractall(tmp_dir)
            return
    except Exception:
        pass
    # Fall back to standard ZIP
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(tmp_dir)
            return
    except Exception as e:
        raise ValueError(f"Cannot extract: not a valid 7z or ZIP archive ({e})")


def find_data_source(tmp_dir):
    """Find the best data source (.gdb or .shp) in extracted archive.
    Returns (path, type) where type is 'gdb' or 'shp'."""
    # Priority 1: .gdb directory
    for root, dirs, files in os.walk(tmp_dir):
        for d in dirs:
            if d.endswith(".gdb"):
                return os.path.join(root, d), "gdb"

    # Priority 2: .gdbtable files (gdb without folder extension)
    for root, dirs, files in os.walk(tmp_dir):
        for f in files:
            if f.endswith(".gdbtable"):
                return root, "gdb"

    # Priority 3: Shapefile (.shp)
    shp_files = []
    for root, dirs, files in os.walk(tmp_dir):
        for f in files:
            if f.endswith(".shp"):
                shp_files.append(os.path.join(root, f))
    if shp_files:
        # Return the largest .shp file (most likely the main data)
        shp_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
        return shp_files[0], "shp"

    return None, None


def convert_lpkx(lpkx_path, output_path, skip_existing=True):
    """Convert a single .lpkx file to GeoJSON."""
    filename = os.path.basename(lpkx_path)

    if skip_existing and os.path.exists(output_path):
        print(f"  [SKIP] {os.path.basename(output_path)} already exists")
        return True

    tmp_dir = tempfile.mkdtemp(prefix="lpkx_")
    try:
        print(f"  Extracting {filename}...")
        extract_archive(lpkx_path, tmp_dir)
        data_path, data_type = find_data_source(tmp_dir)

        if not data_path:
            print(f"  [ERR] No .gdb or .shp found in {filename}")
            return False

        if data_type == "shp":
            # Read shapefile directly
            print(f"       Found shapefile: {os.path.basename(data_path)}")
            gdf = gpd.read_file(data_path)
            best_layer = os.path.splitext(os.path.basename(data_path))[0]
        else:
            # Read geodatabase — list layers with pyogrio or fiona
            try:
                import pyogrio
                layers = pyogrio.list_layers(data_path)
                # Returns array of [name, geom_type] — filter to layers with geometry
                layer_names = [l[0] for l in layers if l[1] is not None and l[1] != ""]
                if not layer_names:
                    # Try all layers as fallback
                    layer_names = [l[0] for l in layers]
                print(f"       Found .gdb with layers: {layer_names}")
            except Exception:
                try:
                    import fiona
                    layer_names = fiona.listlayers(data_path)
                except Exception:
                    layer_names = [None]

            if not layer_names:
                print(f"  [ERR] No layers found in {filename}")
                return False

            best_layer = None
            best_count = 0
            for layer_name in layer_names:
                try:
                    kwargs = {"engine": "pyogrio"} if layer_name else {}
                    test_gdf = gpd.read_file(data_path, layer=layer_name, **kwargs)
                    if len(test_gdf) > best_count and test_gdf.geometry is not None:
                        best_layer = layer_name
                        best_count = len(test_gdf)
                except Exception:
                    continue

            if best_layer is None:
                print(f"  [ERR] No valid feature layers in {filename}")
                return False

            gdf = gpd.read_file(data_path, layer=best_layer, engine="pyogrio")

        # Reproject to WGS84
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            print(f"       Reprojecting from {gdf.crs.to_string()} -> EPSG:4326")
            gdf = gdf.to_crs(epsg=4326)
        elif gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)

        # Drop null geometry rows
        gdf = gdf[gdf.geometry.notna()]

        # Clip to Atlanta metro area if dataset is national/state-level
        from shapely.geometry import box
        atl_box = box(*ATL_BBOX)
        total_before = len(gdf)
        gdf_clipped = gdf[gdf.geometry.intersects(atl_box)]
        if len(gdf_clipped) > 0 and len(gdf_clipped) < total_before:
            print(f"       Clipped to Atlanta metro: {total_before} -> {len(gdf_clipped)} features")
            gdf = gdf_clipped
        elif len(gdf_clipped) == 0 and total_before > 0:
            # Bounding box might be too tight — try a wider Georgia extent
            ga_box = box(-85.6, 30.3, -80.8, 35.0)
            gdf_ga = gdf[gdf.geometry.intersects(ga_box)]
            if len(gdf_ga) > 0:
                print(f"       No features in Atlanta bbox; keeping Georgia extent: {len(gdf_ga)} features")
                gdf = gdf_ga
            else:
                print(f"       WARNING: No features in Atlanta or Georgia bbox, keeping all {total_before}")

        # Save
        gdf.to_file(output_path, driver="GeoJSON")
        geom_type = gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else "?"
        fields = [c for c in gdf.columns if c != "geometry"]
        print(f"  [OK]  {os.path.basename(output_path):<50} {len(gdf):>6} features  ({geom_type})")
        print(f"        Layer: {best_layer} | Fields: {fields[:5]}{'...' if len(fields) > 5 else ''}")
        return True

    except ValueError as ve:
        print(f"  [ERR] {filename}: {ve}")
        return False
    except Exception as e:
        print(f"  [ERR] {filename}: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    os.makedirs(GEOJSON_DIR, exist_ok=True)

    # Determine which files to convert
    if len(sys.argv) > 1:
        # Convert specific file(s)
        targets = []
        for arg in sys.argv[1:]:
            path = os.path.join(LPKX_DIR, arg) if not os.path.isabs(arg) else arg
            if os.path.exists(path):
                targets.append(path)
            else:
                print(f"[WARN] File not found: {arg}")
    else:
        # Convert all .lpkx and .mpkx files
        targets = sorted(
            glob.glob(os.path.join(LPKX_DIR, "*.lpkx"))
            + glob.glob(os.path.join(LPKX_DIR, "*.mpkx"))
        )

    print(f"Found {len(targets)} package files to process")
    print(f"Output directory: {GEOJSON_DIR}\n")

    success = 0
    skipped = 0
    errors = 0

    for lpkx_path in targets:
        filename = os.path.basename(lpkx_path)
        out_name = FILENAME_MAP.get(filename)
        if not out_name:
            out_name = slugify(filename)

        out_path = os.path.join(GEOJSON_DIR, out_name)

        if os.path.exists(out_path):
            print(f"  [SKIP] {out_name} already exists")
            skipped += 1
            continue

        result = convert_lpkx(lpkx_path, out_path, skip_existing=False)
        if result:
            success += 1
        else:
            errors += 1

    print(f"\n{'=' * 60}")
    print(f"Conversion Complete")
    print(f"  Converted: {success}")
    print(f"  Skipped:   {skipped} (already exist)")
    print(f"  Errors:    {errors}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
