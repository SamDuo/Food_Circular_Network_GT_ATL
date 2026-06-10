# Map 3 — Transport Accessibility

## Sources
| Layer | File | Source | Date | License |
|---|---|---|---|---|
| MARTA stops | `geojson/marta_stops_atl.geojson` | MARTA GTFS (rail stations only via def. expression) | 2025 | Public (MARTA) |
| MARTA bus routes | `geojson/atl_pro_marta_bus_routes.geojson` | MARTA GTFS (routes 1/3) | 2025 | Public |
| MARTA rail | `geojson/marta_routes_atl.geojson` | MARTA GTFS rail with route_color | 2025 | Public |
| Walksheds | `geojson/map3_transport_accessibility.geojson` | Computed isochrones (OSRM) | March 2026 | Derived |
| Street centerlines | `geojson/street_centerlines.geojson` | City of Atlanta DPCD | 2024 | Public |
| Vehicle availability | `geojson/census_vehicle_availability_ga.geojson` | ACS 5-year B08201 | 2022 | Public |

## Methodology
- 5-min / 10-min / 15-min walking isochrones from every MARTA rail station and major bus stop
- Routed on OSM pedestrian network via OSRM
- Tract-level vehicle availability overlay (% households with zero vehicles) to flag transit-dependent areas

## Caveats
- Isochrones assume 3 mph constant walking speed (no slope, no waiting time, no transfer)
- Bus frequency is not represented — a 5-min walk to a once-an-hour bus is functionally different from a 5-min walk to a 5-min-frequency train
- Wheelchair / mobility accessibility not modeled
