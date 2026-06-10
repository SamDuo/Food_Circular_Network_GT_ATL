# City of South Fulton — GIS Exports
_Generated 2026-05-03_
**Source:** City of South Fulton ArcGIS Online → `South_Fulton_City_Limits_And_Districts_WFL1` FeatureServer
All layers are in WGS 84 / EPSG:4326.

## Layers exported

| Layer | Features | Geometry |
|---|---:|---|
| streets | 6,232 | LineString |
| city_limits | 3 | MultiPolygon |
| council_districts | 8 | MultiPolygon |

## Files

Each layer ships in four formats:

- `*.shp.zip` — Zipped ESRI Shapefile bundle. Unzip, then drag the `.shp` into ArcGIS Pro. Field names are truncated to 10 characters per the Shapefile spec.
- `*.gpkg` — GeoPackage. Single-file format, ArcGIS Pro 2.5+ reads it natively (Catalog → drag in). Preserves full column names.
- `*.kmz` — Google Earth + ArcGIS Pro. Display-only.
- `geojson/southfulton_*.geojson` — Web (Mapbox / Leaflet) and also readable directly by ArcGIS Pro via 'Add Data'.

## Live REST endpoints

If you would rather pull live data, add these as services in ArcGIS Pro (Catalog → Servers → Add ArcGIS Server):

```
https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/services/South_Fulton_City_Limits_And_Districts_WFL1/FeatureServer/0   (street centerlines)
https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/services/South_Fulton_City_Limits_And_Districts_WFL1/FeatureServer/1   (city limits)
https://services3.arcgis.com/y2BJK2GUfoTwH7py/arcgis/rest/services/South_Fulton_City_Limits_And_Districts_WFL1/FeatureServer/2   (council districts)
```
