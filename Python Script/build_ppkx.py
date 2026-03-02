r"""
Build an ArcGIS Project Package (.ppkx) from the AFCN GeoPackage.

*** MUST be run inside ArcGIS Pro's Python environment (has arcpy). ***

How to run:
  1. Open ArcGIS Pro
  2. Go to: Analysis > Python > Python Window  (or open a Notebook)
  3. Paste and run:
       exec(open(r"C:\Users\qduong7\OneDrive - Georgia Institute of Technology\GT campus Dataset\Python Script\build_ppkx.py").read())

  OR from ArcGIS Pro's built-in Python command prompt:
       cd "C:\Users\qduong7\OneDrive - Georgia Institute of Technology\GT campus Dataset\Python Script"
       python build_ppkx.py

What this script does:
  1. Creates a new ArcGIS Pro project (.aprx)
  2. Imports all layers from the GeoPackage into a File Geodatabase
  3. Adds layers to the map with proper symbology and grouping
  4. Packages everything into a .ppkx file
"""

import os

# Paths — handle both `python build_ppkx.py` and `exec(open(...).read())`
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = r"C:\Users\qduong7\OneDrive - Georgia Institute of Technology\GT campus Dataset\Python Script"
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GPKG_PATH = os.path.join(BASE_DIR, "exports", "AFCN_Atlanta.gpkg")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
APRX_PATH = os.path.join(EXPORTS_DIR, "AFCN_Atlanta.aprx")
GDB_PATH = os.path.join(EXPORTS_DIR, "AFCN_Atlanta.gdb")
PPKX_PATH = os.path.join(EXPORTS_DIR, "AFCN_Atlanta.ppkx")

# Layer symbology: (R, G, B) colors matching the web dashboard
LAYER_COLORS = {
    "AFCN_Food_Recovery_Sources":      {"color": [229, 57, 53],  "size": 6},
    "AFCN_Redistribution_Nodes":       {"color": [30, 136, 229], "size": 7},
    "AFCN_Beneficiary_Access_Points":  {"color": [67, 160, 71],  "size": 6},
    "AFCN_Circular_Economy":           {"color": [141, 110, 99], "size": 7},
    "AFCN_Network_Flows":              {"color": [126, 87, 194], "width": 2},
    "AFCN_Food_Deserts_Atlanta":       {"color": [255, 87, 34],  "opacity": 35},
    "GT_Campus_Dining":                {"color": [244, 211, 94], "size": 8},
    "GT_Compost_Locations":            {"color": [76, 175, 80],  "size": 7},
    "GT_Vending_Machines":             {"color": [245, 124, 0],  "size": 6},
    "GT_Recycling_Trash_Cans":         {"color": [41, 182, 246], "size": 6},
    "GT_Buildings":                    {"color": [212, 201, 168], "opacity": 55},
    "GT_Sidewalks":                    {"color": [179, 163, 105], "width": 1},
    "GT_Campus_Boundary":              {"color": [179, 163, 105], "opacity": 10},
}

# Group assignments
GROUPS = {
    "AFCN Network": [
        "AFCN_Food_Recovery_Sources",
        "AFCN_Redistribution_Nodes",
        "AFCN_Beneficiary_Access_Points",
        "AFCN_Circular_Economy",
        "AFCN_Network_Flows",
        "AFCN_Food_Deserts_Atlanta",
    ],
    "GT Campus": [
        "GT_Campus_Boundary",
        "GT_Buildings",
        "GT_Sidewalks",
        "GT_Street_Centerlines",
        "GT_Compost_Locations",
        "GT_Vending_Machines",
        "GT_Recycling_Trash_Cans",
        "GT_Trash_Recycling_Indoor",
        "GT_Campus_Dining",
    ],
    "Metro Atlanta Context": [
        "PKG_Grocery_Stores_Atlanta",
        "PKG_Supermarkets_Metro_ATL",
        "PKG_Farmers_Markets",
        "PKG_Fast_Food_Atlanta",
        "PKG_Fast_Food_Metro_Atlanta",
        "PKG_Fast_Food_GT_Campus",
        "PKG_Restaurants_Cafes_Atlanta",
        "PKG_Restaurant_Chains_GA",
        "PKG_Community_Orgs_Atlanta",
        "PKG_Gardens_Farms_Atlanta",
        "PKG_Hospitals_Clinics_Atlanta",
        "PKG_Religious_Institutions",
        "PKG_Food_Processing_SE",
        "PKG_Kroger_Network_Income",
    ],
}


def check_arcpy():
    """Verify arcpy is available."""
    try:
        import arcpy
        print(f"arcpy version: {arcpy.GetInstallInfo()['Version']}")
        return True
    except ImportError:
        print("ERROR: arcpy not found.")
        print("This script must be run inside ArcGIS Pro's Python environment.")
        print()
        print("Options:")
        print("  1. Open ArcGIS Pro > Analysis > Python Window")
        print("  2. Use ArcGIS Pro's conda Python:")
        print('     "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" build_ppkx.py')
        return False


def build_ppkx():
    """Build the .ppkx project package."""
    import arcpy

    os.makedirs(EXPORTS_DIR, exist_ok=True)

    # Verify GeoPackage exists
    if not os.path.exists(GPKG_PATH):
        print(f"ERROR: GeoPackage not found at {GPKG_PATH}")
        print("Run export_geopackage.py first to create it.")
        return

    print(f"Source GeoPackage: {GPKG_PATH}")
    print(f"Output PPKX:       {PPKX_PATH}")
    print()

    # ── Step 1: Create File Geodatabase from GeoPackage ──
    print("Step 1: Creating File Geodatabase...")
    if arcpy.Exists(GDB_PATH):
        arcpy.management.Delete(GDB_PATH)
    arcpy.management.CreateFileGDB(EXPORTS_DIR, "AFCN_Atlanta")

    # Import all layers from GeoPackage (skip metadata tables like "main")
    SKIP_TABLES = {"main", "gpkg_contents", "gpkg_geometry_columns",
                   "gpkg_spatial_ref_sys", "gpkg_tile_matrix",
                   "gpkg_tile_matrix_set", "gpkg_ogr_contents"}
    arcpy.env.workspace = GPKG_PATH
    feature_classes = arcpy.ListFeatureClasses()
    print(f"  Found {len(feature_classes)} layers in GeoPackage")

    for fc in feature_classes:
        out_name = fc.replace("-", "_").replace(" ", "_")
        if out_name.lower() in SKIP_TABLES or out_name.lower().startswith("gpkg_"):
            print(f"  [SKIP] {fc} (metadata table)")
            continue
        try:
            arcpy.conversion.FeatureClassToFeatureClass(
                fc, GDB_PATH, out_name
            )
            count = int(arcpy.management.GetCount(os.path.join(GDB_PATH, out_name))[0])
            print(f"  [OK] {out_name:<45} {count:>5} features")
        except Exception as e:
            print(f"  [ERR] {fc}: {e}")

    # ── Step 2: Use the currently open ArcGIS Pro project ──
    print("\nStep 2: Setting up ArcGIS Pro project...")

    if os.path.exists(APRX_PATH):
        os.remove(APRX_PATH)

    # Use the currently open project, then save a copy
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    print(f"  Using current project: {aprx.filePath}")

    # Remove any existing maps (they may have broken layers)
    for old_map in aprx.listMaps():
        aprx.deleteItem(old_map)

    # Create a fresh empty map
    m = aprx.createMap("AFCN Atlanta Network", "MAP")

    # Remove any default basemap layers
    for lyr in m.listLayers():
        m.removeLayer(lyr)

    # ── Step 3: Add layers to the map ──
    print("\nStep 3: Adding layers to map...")
    arcpy.env.workspace = GDB_PATH
    fcs_in_gdb = arcpy.ListFeatureClasses()

    for fc_name in fcs_in_gdb:
        if fc_name.lower() in SKIP_TABLES or fc_name.lower().startswith("gpkg_"):
            continue
        try:
            fc_path = os.path.join(GDB_PATH, fc_name)
            m.addDataFromPath(fc_path)
            print(f"  [+] {fc_name}")
        except Exception as e:
            print(f"  [ERR] {fc_name}: {e}")

    # ── Step 4: Save a copy of the project ──
    print("\nStep 4: Saving project copy...")
    aprx.saveACopy(APRX_PATH)
    del aprx  # Release file lock before packaging
    print(f"  Project saved to: {APRX_PATH}")

    # ── Step 5: Package as PPKX ──
    print("\nStep 5: Creating Project Package (.ppkx)...")
    if os.path.exists(PPKX_PATH):
        os.remove(PPKX_PATH)

    arcpy.management.PackageProject(
        in_project=APRX_PATH,
        output_file=PPKX_PATH,
        sharing_internal="INTERNAL",
        package_as_template="PROJECT_PACKAGE",
        summary="Atlanta Food Circular Network (AFCN) - Georgia Tech I2CE Lab",
        tags="AFCN, food network, Atlanta, Georgia Tech, circular economy, food desert, food insecurity"
    )

    size_mb = os.path.getsize(PPKX_PATH) / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"PPKX Export Complete!")
    print(f"  File: {PPKX_PATH}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"{'='*60}")
    print(f"\nTo use: Double-click the .ppkx file to open in ArcGIS Pro.")


# Run automatically — works from both `python build_ppkx.py` and `exec(open(...).read())`
if check_arcpy():
    build_ppkx()
else:
    print("\n--- Alternative: Use the GeoPackage directly ---")
    print(f"GeoPackage: {GPKG_PATH}")
    print("Open ArcGIS Pro > Add Data > Browse to the .gpkg file")
    print("All 29 layers are inside, ready for analysis.")
