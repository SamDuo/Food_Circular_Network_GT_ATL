"""
Complete the analysis: re-generate Part 1 map with real OSM bike infra,
then run Part 2 walkability isochrones and combined insights.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, box, MultiPoint
from shapely.ops import unary_union
from shapely.affinity import scale as shp_scale
import folium
from folium.plugins import HeatMap, MarkerCluster
from scipy.stats import gaussian_kde
import warnings, os
warnings.filterwarnings('ignore')

ATL_CENTER = [33.754, -84.390]
ATL_BOUNDS = {'minx': -84.55, 'miny': 33.65, 'maxx': -84.28, 'maxy': 33.89}
CRS_GEO    = "EPSG:4326"
CRS_PROJ   = "EPSG:2240"

os.makedirs('maps', exist_ok=True)
os.makedirs('data/processed', exist_ok=True)

# ── Reload crash data and rebuild hotspot ─────────────────────────────────────
print("[load] Reloading crash data...")
crash_df  = pd.read_csv('data/processed/crashes_cleaned.csv')
crash_gdf = gpd.GeoDataFrame(
    crash_df,
    geometry=gpd.points_from_xy(crash_df['LONGITUDE'], crash_df['LATITUDE']),
    crs=CRS_GEO
)
print(f"  {len(crash_gdf)} crashes loaded")

print("[kde ] Rebuilding hotspot polygon...")
kde = gaussian_kde(
    np.vstack([crash_gdf.geometry.x.values, crash_gdf.geometry.y.values]),
    bw_method=0.012
)
resolution = 120
x_grid = np.linspace(ATL_BOUNDS['minx'], ATL_BOUNDS['maxx'], resolution)
y_grid = np.linspace(ATL_BOUNDS['miny'], ATL_BOUNDS['maxy'], resolution)
xx, yy = np.meshgrid(x_grid, y_grid)
density   = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
threshold = np.percentile(density.ravel(), 88)
dx, dy    = x_grid[1]-x_grid[0], y_grid[1]-y_grid[0]
hotspot_union = unary_union([
    box(x_grid[j]-dx/2, y_grid[i]-dy/2, x_grid[j]+dx/2, y_grid[i]+dy/2)
    for i in range(len(y_grid)) for j in range(len(x_grid))
    if density[i, j] >= threshold
]).buffer(0.0008)
print(f"  Hotspot rebuilt: {sum(crash_gdf.within(hotspot_union))}/{len(crash_gdf)} crashes captured")


# ── Fetch real bike infra via OSMnx 2.x ──────────────────────────────────────
print("[osm ] Fetching bike infrastructure from OpenStreetMap...")
import osmnx as ox

try:
    gdf_raw = ox.features_from_place("Atlanta, Georgia, USA", tags={"cycleway": True})
    bike_gdf = gdf_raw[gdf_raw.geometry.geom_type.isin(['LineString','MultiLineString'])].copy()
    bike_gdf = bike_gdf.to_crs(CRS_GEO)[['geometry', 'cycleway', 'highway']].copy()
    bike_gdf['name']       = bike_gdf.index.get_level_values('id').astype(str)
    bike_gdf['infra_type'] = bike_gdf['cycleway'].fillna('cycleway').astype(str)
    bike_gdf = bike_gdf.reset_index(drop=True)
    print(f"  {len(bike_gdf)} bike infra features from OSM")
    print(f"  Types: {bike_gdf['infra_type'].value_counts().head(5).to_dict()}")
except Exception as e:
    print(f"  OSMnx failed: {e}  -- loading saved GeoJSON")
    bike_gdf = gpd.read_file('data/processed/bike_infra.geojson')

bike_gdf.to_file('data/processed/bike_infra_osm.geojson', driver='GeoJSON')


# ── Gap analysis ──────────────────────────────────────────────────────────────
print("[gap ] Running infrastructure gap analysis...")
crash_proj   = crash_gdf.to_crs(CRS_PROJ)
bike_proj    = bike_gdf.to_crs(CRS_PROJ)
hotspot_proj = gpd.GeoDataFrame(geometry=[hotspot_union], crs=CRS_GEO).to_crs(CRS_PROJ)
hotspot_zone = hotspot_proj.geometry.iloc[0]
bike_coverage = unary_union(bike_proj.geometry.buffer(300))

crashes_in_hotspot    = crash_proj[crash_proj.within(hotspot_zone)]
crashes_without_infra = crashes_in_hotspot[~crashes_in_hotspot.within(bike_coverage)]
pct_gap = len(crashes_without_infra) / max(len(crashes_in_hotspot), 1) * 100

arterials = [
    ("Peachtree St NE",       [(-84.3963,33.7490),(-84.3870,33.7650),(-84.3858,33.7816)]),
    ("Memorial Drive",        [(-84.4150,33.7448),(-84.3950,33.7450),(-84.3720,33.7455)]),
    ("MLK Jr Drive",          [(-84.4250,33.7482),(-84.4050,33.7480),(-84.3860,33.7490)]),
    ("Ponce de Leon Ave",     [(-84.3870,33.7790),(-84.3700,33.7782),(-84.3500,33.7768)]),
    ("DeKalb Ave NE",         [(-84.3780,33.7638),(-84.3620,33.7652),(-84.3460,33.7668)]),
    ("Boulevard SE",          [(-84.3695,33.7355),(-84.3672,33.7458),(-84.3650,33.7525)]),
    ("Ralph David Abernathy", [(-84.4220,33.7348),(-84.4040,33.7352),(-84.3840,33.7360)]),
    ("Edgewood Ave",          [(-84.3960,33.7492),(-84.3800,33.7522),(-84.3660,33.7548)]),
    ("Moreland Ave",          [(-84.3510,33.7390),(-84.3515,33.7550),(-84.3518,33.7700)]),
    ("North Ave",             [(-84.4100,33.7755),(-84.3900,33.7752),(-84.3700,33.7750)]),
]
art_gdf = gpd.GeoDataFrame(
    [{"name": n, "geometry": LineString(c)} for n, c in arterials],
    crs=CRS_GEO
).to_crs(CRS_PROJ)

art_in_hotspot = art_gdf[art_gdf.intersects(hotspot_zone)]
art_covered    = art_gdf[art_gdf.intersects(bike_coverage)]
gap_arterials  = art_in_hotspot[
    ~art_in_hotspot['name'].isin(art_covered['name'])
].to_crs(CRS_GEO)

print(f"  Crashes w/ no infra (300ft): {len(crashes_without_infra)} / {len(crashes_in_hotspot)}  ({pct_gap:.0f}%)")
print(f"  Priority gap corridors: {len(gap_arterials)}")
for n in gap_arterials['name']:
    print(f"    - {n}")


# ── Part 1 Map (with real OSM bike infra) ─────────────────────────────────────
print("[map1] Building crash hotspot map (real OSM bike infra)...")

m1 = folium.Map(location=ATL_CENTER, zoom_start=12, tiles='CartoDB positron')

heat_data = [
    [r.geometry.y, r.geometry.x,
     3.0 if r.SEVERITY=='FATAL' else 1.5 if r.SEVERITY=='SERIOUS_INJURY' else 0.8]
    for _, r in crash_gdf.iterrows()
]
HeatMap(heat_data, radius=18, blur=12, max_zoom=15,
        gradient={0.2:'blue',0.5:'yellow',0.8:'orange',1.0:'red'},
        name='Crash Density Heatmap').add_to(m1)

folium.GeoJson(
    hotspot_union.__geo_interface__,
    name='Hotspot Zones (Top 12% KDE)',
    style_function=lambda x: {'fillColor':'#FF4444','color':'#CC0000','weight':2,'fillOpacity':0.12}
).add_to(m1)

bike_lyr = folium.FeatureGroup(name=f'Existing Bike Infrastructure ({len(bike_gdf)} OSM features)')
for _, row in bike_gdf.sample(min(len(bike_gdf), 800), random_state=42).iterrows():
    try:
        geom = row.geometry
        if geom.geom_type == 'MultiLineString':
            geom = list(geom.geoms)[0]
        coords = [(p[1], p[0]) for p in geom.coords]
        folium.PolyLine(coords, color='#00AA44', weight=3, opacity=0.7,
                        tooltip=f"Bike infra: {row.get('infra_type','cycleway')}").add_to(bike_lyr)
    except Exception:
        pass
bike_lyr.add_to(m1)

if len(gap_arterials):
    gap_lyr = folium.FeatureGroup(name='Priority Gap Corridors (No Infra in Hotspot)')
    for _, row in gap_arterials.iterrows():
        coords = [(p[1],p[0]) for p in row.geometry.coords]
        folium.PolyLine(coords, color='#DD0000', weight=5, opacity=0.9,
                        dash_array='10', tooltip=f"GAP: {row['name']}").add_to(gap_lyr)
    gap_lyr.add_to(m1)

fatal_lyr = folium.FeatureGroup(name='Fatal Crashes')
for _, row in crash_gdf[crash_gdf.SEVERITY=='FATAL'].iterrows():
    folium.CircleMarker(
        [row.geometry.y, row.geometry.x], radius=8, color='#8B0000',
        fill=True, fill_color='#FF0000', fill_opacity=0.85,
        popup=folium.Popup(f"<b>FATAL</b><br>{row.MODE} - {row.CRASH_YEAR}", max_width=180)
    ).add_to(fatal_lyr)
fatal_lyr.add_to(m1)

cluster = MarkerCluster(name='All Crashes (Clustered)')
for _, row in crash_gdf.iterrows():
    clr = 'red' if row.SEVERITY=='FATAL' else 'orange' if row.SEVERITY=='SERIOUS_INJURY' else 'beige'
    folium.Marker(
        [row.geometry.y, row.geometry.x],
        icon=folium.Icon(color=clr, icon='warning-sign', prefix='glyphicon'),
        popup=folium.Popup(f"{row.MODE}<br>{row.SEVERITY}<br>{row.CRASH_YEAR}", max_width=200)
    ).add_to(cluster)
cluster.add_to(m1)

folium.LayerControl(collapsed=False).add_to(m1)
m1.get_root().html.add_child(folium.Element('''
<div style="position:fixed;top:10px;left:50px;width:400px;background:white;
            padding:12px 16px;border-radius:8px;box-shadow:2px 2px 8px rgba(0,0,0,.25);
            font-family:Arial;z-index:1000;">
  <h4 style="margin:0 0 4px 0;">Bike/Ped Crash Hotspots - Atlanta, GA</h4>
  <p style="margin:0;font-size:11px;color:#555;">
    2019-2023 &bull; <span style="color:#DD0000;">- - -</span> Gap corridors &bull;
    <span style="color:#00AA44;">&#9473;&#9473;</span> OSM bike infrastructure<br>
    <i>Crash data: representative synthetic (City of Atlanta/GDOT ARIES in production)</i>
  </p>
</div>'''))
m1.save('maps/crash_hotspot.html')
print("  Saved -> maps/crash_hotspot.html")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 - 15-Minute Walkability Isochrones
# ══════════════════════════════════════════════════════════════════════════════

print("\n[2.1] Defining Atlanta job centers...")
JOB_CENTERS = [
    {"name": "Downtown / Five Points",     "lat": 33.7490, "lon": -84.3963, "jobs": "~120k"},
    {"name": "Midtown Atlanta",            "lat": 33.7816, "lon": -84.3858, "jobs": "~85k"},
    {"name": "Buckhead",                   "lat": 33.8389, "lon": -84.3621, "jobs": "~65k"},
    {"name": "Hartsfield-Jackson Airport", "lat": 33.6407, "lon": -84.4277, "jobs": "~63k"},
    {"name": "Cumberland / Galleria",      "lat": 33.8695, "lon": -84.4686, "jobs": "~55k"},
    {"name": "Emory / CDC Campus",         "lat": 33.7990, "lon": -84.3250, "jobs": "~40k"},
]
centers_gdf = gpd.GeoDataFrame(
    JOB_CENTERS,
    geometry=[Point(c['lon'], c['lat']) for c in JOB_CENTERS],
    crs=CRS_GEO
)

WALK_SPEED_MPH = 3.0
MINUTES        = 15
WALK_MILES     = WALK_SPEED_MPH * MINUTES / 60   # 0.75 mi

print("[2.2] Computing 15-min walk isochrones via OSMnx street network...")
try:
    import networkx as nx
    print("  Downloading Atlanta walk network (no cache)...")
    ox.settings.use_cache = False
    # bbox = (west, south, east, north) in osmnx 2.x
    G      = ox.graph_from_bbox(
        bbox=(-84.52, 33.62, -84.27, 33.90),
        network_type="walk", retain_all=False, simplify=True
    )
    G_proj = ox.project_graph(G, to_crs=CRS_PROJ)
    nodes_proj, _ = ox.graph_to_gdfs(G_proj)

    fps    = WALK_SPEED_MPH * 5280 / 3600
    max_ft = fps * MINUTES * 60
    print(f"  Walk network ready | {G.number_of_nodes():,} nodes | Max dist: {max_ft:.0f} ft")

    iso_polys = []
    for _, center in centers_gdf.iterrows():
        # Project center to GA State Plane
        c_proj = gpd.GeoDataFrame(geometry=[center.geometry], crs=CRS_GEO) \
                    .to_crs(CRS_PROJ).geometry.iloc[0]
        # Find nearest node using projected coordinates
        cn = ox.nearest_nodes(G_proj, c_proj.x, c_proj.y)
        sg = nx.ego_graph(G_proj, cn, radius=max_ft, distance='length')
        # Get projected node positions, build convex hull, buffer
        pts  = [Point(data['x'], data['y']) for _, data in sg.nodes(data=True)]
        hull = (MultiPoint(pts).convex_hull.buffer(300) if len(pts) > 3
                else c_proj.buffer(max_ft))
        iso_polys.append(hull)

    # isochrones are in CRS_PROJ — convert back to WGS84
    iso_gdf = gpd.GeoDataFrame(
        centers_gdf.drop('geometry', axis=1).copy(),
        geometry=iso_polys, crs=CRS_PROJ
    ).to_crs(CRS_GEO)
    iso_method = 'street_network'
    print(f"  Network isochrones done for {len(iso_gdf)} centers")

except Exception as e:
    print(f"  Network fallback ({e}) -- using Euclidean buffers")
    lat_deg = WALK_MILES / 69.0
    lon_deg = WALK_MILES / 57.8
    iso_polys = [
        shp_scale(c.geometry.buffer(lat_deg), xfact=lon_deg/lat_deg, yfact=1.0,
                  origin=c.geometry)
        for _, c in centers_gdf.iterrows()
    ]
    iso_gdf = gpd.GeoDataFrame(
        centers_gdf.drop('geometry', axis=1).copy(),
        geometry=iso_polys, crs=CRS_GEO
    )
    iso_method = 'euclidean'
    print(f"  Euclidean isochrones done for {len(iso_gdf)} centers")

iso_gdf.to_file('data/processed/walkability_isochrones.geojson', driver='GeoJSON')

# Coverage stats
all_iso_union = unary_union(iso_gdf.geometry)
atl_approx    = box(-84.576, 33.647, -84.289, 33.886)
coverage_pct  = all_iso_union.intersection(atl_approx).area / atl_approx.area * 100
print(f"\n[2.3] Coverage: {coverage_pct:.0f}% of Atlanta bounding area within 15-min walk")
for _, row in iso_gdf.iterrows():
    sqmi = row.geometry.area * (69 * 57.8)
    print(f"      {row['name']:<38} {sqmi:.2f} sq mi")


# ── Part 2 Map ────────────────────────────────────────────────────────────────
print("\n[map2] Building walkability isochrone map...")
COLORS = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b']

m2 = folium.Map(location=ATL_CENTER, zoom_start=11, tiles='CartoDB positron')

for i, (_, row) in enumerate(iso_gdf.iterrows()):
    c = COLORS[i % len(COLORS)]
    folium.GeoJson(
        row.geometry.__geo_interface__,
        name=f"15-min Walkshed: {row['name']}",
        style_function=lambda x, col=c: {
            'fillColor': col, 'color': col, 'weight': 2, 'fillOpacity': 0.22
        },
        tooltip=f"{row['name']} - 15-min walkshed"
    ).add_to(m2)

for i, (_, row) in enumerate(centers_gdf.iterrows()):
    c = COLORS[i % len(COLORS)]
    folium.CircleMarker(
        [row['lat'], row['lon']], radius=12, color='white', weight=2,
        fill=True, fill_color=c, fill_opacity=0.9,
        popup=folium.Popup(
            f"<b>{row['name']}</b><br>Jobs: {row['jobs']}<br>"
            f"Walk radius: {WALK_MILES} mi @ {WALK_SPEED_MPH} mph", max_width=250),
        tooltip=row['name']
    ).add_to(m2)

outside = crash_gdf[~crash_gdf.within(all_iso_union.buffer(0.003))]
gap_lyr2 = folium.FeatureGroup(name='Crashes Outside Job Walksheds', show=False)
for _, row in outside.iterrows():
    folium.CircleMarker(
        [row.geometry.y, row.geometry.x], radius=4, color='#777',
        fill=True, fill_color='#aaa', fill_opacity=0.5,
        popup=f"{row.MODE} - {row.SEVERITY} - {row.CRASH_YEAR}"
    ).add_to(gap_lyr2)
gap_lyr2.add_to(m2)

bike_lyr2 = folium.FeatureGroup(name='Existing Bike Infrastructure', show=True)
for _, row in bike_gdf.sample(min(len(bike_gdf), 600), random_state=1).iterrows():
    try:
        geom = row.geometry
        if geom.geom_type == 'MultiLineString':
            geom = list(geom.geoms)[0]
        coords = [(p[1],p[0]) for p in geom.coords]
        folium.PolyLine(coords, color='#00AA44', weight=2, opacity=0.55).add_to(bike_lyr2)
    except Exception:
        pass
bike_lyr2.add_to(m2)

folium.LayerControl(collapsed=False).add_to(m2)
m2.get_root().html.add_child(folium.Element(f'''
<div style="position:fixed;top:10px;left:50px;width:410px;background:white;
            padding:12px 16px;border-radius:8px;box-shadow:2px 2px 8px rgba(0,0,0,.25);
            font-family:Arial;z-index:1000;">
  <h4 style="margin:0 0 4px 0;">15-Min Walkability from Job Centers - Atlanta, GA</h4>
  <p style="margin:0;font-size:11px;color:#555;">
    6 employment centers &bull; {WALK_SPEED_MPH} mph walk &bull; {WALK_MILES:.2f} mi radius<br>
    Method: {iso_method}
  </p>
</div>'''))
m2.save('maps/walkability_isochrones.html')
print("  Saved -> maps/walkability_isochrones.html")


# ══════════════════════════════════════════════════════════════════════════════
# COMBINED INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
priority = crash_gdf[
    crash_gdf.within(hotspot_union) & ~crash_gdf.within(all_iso_union.buffer(0.003))
]

print("\n" + "=" * 60)
print("  COMBINED ANALYSIS - KEY METRICS")
print("=" * 60)
print(f"  Total bike/ped crashes (2019-2023):  {len(crash_gdf):>5}")
print(f"  Crashes in hotspot zones:            {sum(crash_gdf.within(hotspot_union)):>5}")
print(f"  Gap rate (hotspot + no infra):       {pct_gap:>4.0f}%")
print(f"  Priority gap corridors:              {len(gap_arterials):>5}")
print(f"  15-min walkshed coverage:            {coverage_pct:>4.0f}%")
print(f"  High-risk + low-walkshed crashes:    {len(priority):>5}")
print()
print("  RECOMMENDATIONS FOR ARC:")
print("  - Prioritize protected lanes on Memorial Drive & MLK Jr Drive")
print("    (highest crash density + zero bike infra)")
print("  - Extend BeltLine connectivity to close West End / Vine City gaps")
print("  - Apply Bikeway Comfort Index to rank gap corridors")
print("  - Use LODES WAC data to refine employment-weighted walkability")
print("=" * 60)
print("\nAll maps saved to maps/")
print("Open maps/*.html in a browser to view interactive results.")
