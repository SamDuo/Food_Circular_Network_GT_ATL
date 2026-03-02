"""
Export all AFCN GeoJSON layers into a single GeoPackage (.gpkg).

Usage:
    python export_geopackage.py
    python export_geopackage.py --output ../exports/AFCN_Atlanta.gpkg

Output: A single .gpkg file with all layers, ready for ArcGIS Pro / QGIS.
"""

import os
import sys
import glob
import geopandas as gpd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GEOJSON_DIR = os.path.join(BASE_DIR, "geojson")

# Default output location
DEFAULT_OUTPUT = os.path.join(BASE_DIR, "exports", "AFCN_Atlanta.gpkg")

# Layer ordering and grouping (prefix helps ArcGIS Pro organize)
LAYER_CONFIG = {
    # AFCN Network layers
    "food_recovery_sources.geojson":       "AFCN_Food_Recovery_Sources",
    "redistribution_nodes.geojson":        "AFCN_Redistribution_Nodes",
    "beneficiary_access_points.geojson":   "AFCN_Beneficiary_Access_Points",
    "circular_economy.geojson":            "AFCN_Circular_Economy",
    "network_flows.geojson":               "AFCN_Network_Flows",
    "food_deserts_atlanta.geojson":        "AFCN_Food_Deserts_Atlanta",

    # GT Campus layers
    "campus_boundary.geojson":             "GT_Campus_Boundary",
    "buildings.geojson":                   "GT_Buildings",
    "sidewalks.geojson":                   "GT_Sidewalks",
    "street_centerlines.geojson":          "GT_Street_Centerlines",
    "compost_locations.geojson":           "GT_Compost_Locations",
    "vending_machines.geojson":            "GT_Vending_Machines",
    "recycling_trash_cans.geojson":        "GT_Recycling_Trash_Cans",
    "trash_recycling_indoor.geojson":      "GT_Trash_Recycling_Indoor",
    "campus_dining.geojson":               "GT_Campus_Dining",

    # Package-sourced layers (metro Atlanta context data)
    "pkg_all_fast_food_locations_in_metro_atlanta.geojson":  "PKG_Fast_Food_Metro_Atlanta",
    "pkg_atlanta_fast_food_restaurants.geojson":              "PKG_Fast_Food_Atlanta",
    "pkg_atlanta_grocery_stores.geojson":                     "PKG_Grocery_Stores_Atlanta",
    "pkg_atlanta_metro_area_farmers_markets.geojson":         "PKG_Farmers_Markets",
    "pkg_community_based_organizations_atlanta.geojson":      "PKG_Community_Orgs_Atlanta",
    "pkg_fast_food_on_gt_campus.geojson":                     "PKG_Fast_Food_GT_Campus",
    "pkg_food_processing_facilities_in_the_southeast.geojson":"PKG_Food_Processing_SE",
    "pkg_gardens_farms_and_orchards_atlanta.geojson":         "PKG_Gardens_Farms_Atlanta",
    "pkg_hospitals_and_health_clinics_atlanta.geojson":       "PKG_Hospitals_Clinics_Atlanta",
    "pkg_religious_institutions_metro_atlanta.geojson":       "PKG_Religious_Institutions",
    "pkg_restaurant_chains_ga.geojson":                       "PKG_Restaurant_Chains_GA",
    "pkg_restaurants_and_cafes_atlanta.geojson":              "PKG_Restaurants_Cafes_Atlanta",
    "pkg_us_kroger_network_v_household_income.geojson":       "PKG_Kroger_Network_Income",
    "pkg_supermarkets_metroatl.geojson":                      "PKG_Supermarkets_Metro_ATL",
}


def export_geopackage(output_path):
    """Read all GeoJSON files and write to a single GeoPackage."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Remove existing file (GeoPackage appends by default)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"  Removed existing: {os.path.basename(output_path)}")

    geojson_files = glob.glob(os.path.join(GEOJSON_DIR, "*.geojson"))
    print(f"\nFound {len(geojson_files)} GeoJSON files in {GEOJSON_DIR}")
    print(f"Output: {output_path}\n")

    success = 0
    skipped = 0
    errors = []

    for filepath in sorted(geojson_files):
        filename = os.path.basename(filepath)
        layer_name = LAYER_CONFIG.get(filename)

        if not layer_name:
            # Auto-generate name for unmapped files
            layer_name = os.path.splitext(filename)[0].replace("-", "_")
            print(f"  [?] {filename} -> {layer_name} (auto-named)")

        try:
            gdf = gpd.read_file(filepath)

            if gdf.empty:
                print(f"  [SKIP] {layer_name} — empty dataset")
                skipped += 1
                continue

            # Ensure WGS84
            if gdf.crs is None:
                gdf = gdf.set_crs(epsg=4326)
            elif gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            # GeoPackage layer names cannot have spaces or special chars
            safe_name = layer_name.replace(" ", "_").replace("-", "_")

            gdf.to_file(output_path, layer=safe_name, driver="GPKG")
            geom_type = gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else "?"
            print(f"  [OK] {safe_name:<45} {len(gdf):>5} features  ({geom_type})")
            success += 1

        except Exception as e:
            print(f"  [ERR] {filename}: {e}")
            errors.append((filename, str(e)))

    # Summary
    print(f"\n{'='*60}")
    print(f"GeoPackage Export Complete")
    print(f"  Layers exported: {success}")
    print(f"  Skipped (empty): {skipped}")
    print(f"  Errors:          {len(errors)}")
    print(f"  Output file:     {output_path}")
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  File size:       {size_mb:.1f} MB")
    print(f"{'='*60}")

    if errors:
        print("\nErrors:")
        for fn, err in errors:
            print(f"  - {fn}: {err}")

    return output_path


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT
    if not os.path.isabs(output):
        output = os.path.join(BASE_DIR, output)
    export_geopackage(output)
