# Map 5 — Campus-to-Community Surplus Flow

## Sources
| Layer | File | Source | Date | License |
|---|---|---|---|---|
| GT campus dining surplus | `data/leanpath_surplus.js` (from `Waste-Data.csv`) | LeanPath audit, GT Campus | Mar 4–10, 2026 | I2CE Lab (used with permission) |
| Campus dining locations | `geojson/campus_dining.geojson` | GT Dining Services | 2026 | GT |
| Redistribution nodes | `geojson/redistribution_nodes.geojson` | Curated from ACFB + faith network | March 2026 | I2CE Lab |
| Beneficiary access points | `geojson/beneficiary_access_points.geojson` | Workshop participants | April 2026 | I2CE Lab |
| Compost sites | `fulton_permitted_compost_sites (2).csv` + `geojson/compost_locations.geojson` | Fulton County Permits | 2024 | Public |
| Network flows | `geojson/network_flows.geojson` | Origin-destination pairs (synthesized) | March 2026 | I2CE Lab |

## Methodology
- 30 grouped surplus pins (1,051 lbs total, 408 raw entries) from 6 GT dining locations
- Urgency classification per item: Critical / Soon / Stable based on freshness curves
- Flow lines drawn from origin (dining hall) to nearest matching redistribution node (capacity-aware)
- Urgency-aware scoring: `priority = 0.50 × urgency_decay + 0.30 × volume_score + 0.20 × proximity_score`
- Transport hierarchy: Refrigerated Van (4) > Dry Vehicle (3) > Bike Courier (2) > Walk-in (1)

## LeanPath summary (Mar 4–10, 2026)
| Metric | Value |
|---|---|
| Total entries | 408 |
| Total wasted | **2,316 lbs** ($2,380) |
| Donated (rescue-ready) | **80 lbs (3.5%)** |
| Composted | **2,236 lbs (96.5%)** |
| Preventable (overproduction) | **1,392 lbs (60%)** |
| Mapped to flow lines | **1,051 lbs** in 30 grouped pins |

## Caveats
- One-week snapshot; not representative of annual flows or semester variation
- LeanPath data is self-reported by dining staff — under-reporting likely
- Flow lines are *modeled* optimal pairings, not observed deliveries
- "Beneficiary" nodes are public-facing addresses; many community recipients (informal networks, neighbors) invisible
- The 96.5% composted figure conceals upstream questions: was overproduction avoidable in the first place?
