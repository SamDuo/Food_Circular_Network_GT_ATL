# Map 5 — Legend Specification

## Title
**Campus-to-Community Surplus Flow** — Real-time food rescue routing from GT dining surplus to redistribution network
Source: LeanPath audit Mar 4–10 2026 · I2CE Lab April 2026

## Pin classification — urgency
| Urgency class | Color | Size rule | Animation |
|---|---|---|---|
| Critical (≤4 hrs remaining) | `#ef5350` red | 18 px if 200+ lbs / 14 px 50–200 / 10 px <50 | Pulse |
| Soon (4–24 hrs) | `#ffc107` amber | 18 / 14 / 10 px | static |
| Stable (>24 hrs) | `#66bb6a` green | 18 / 14 / 10 px | static |

## Flow line — directional
- **Route line:** solid Nr. 51 spinellblau `#1c5c84` 4px
- **Glow underlay:** Nr. 51 8px 30% opacity
- **Arrowhead:** Nr. 59 petrolgrün `#7a958c` triangle at destination
- **Route chain numbers:** Nr. 52 gray with white circle background

## Destination classes
| Node type | Color | Shape |
|---|---|---|
| Redistribution (food bank / shelter) | `#7a958c` (Nr. 59 petrolgrün) | Triangle, 12px, white halo |
| Beneficiary access (pantry / community fridge) | `#7d9caf` (Nr. 57 lichtblau) | Circle 12px, white halo |
| Compost site (Fulton permitted) | `#5b7282` (Nr. 52) | Square 10px |

## Symbology layers (draw order, bottom to top)
1. Base: dark-gray vector basemap (`dark-gray-vector` ArcGIS)
2. GT campus boundary — `#7a958c` 0.25 opacity polygon
3. Redistribution nodes (background pool)
4. Compost site dots
5. Flow lines (with glow underlay)
6. Surplus pins (origin) sized + colored by urgency, pulse animation on Critical
7. Route chain numbers
8. Destination pins (highlighted)

## Auxiliary elements
- **Fleet panel inset:** "1,051 lbs in 30 grouped pins · 6 Critical · 12 Soon · 12 Stable"
- **Scoring formula** rendered in legend footer: `priority = 0.50·urgency + 0.30·volume + 0.20·proximity`
- **Transport hierarchy** mini-legend (van → dry → bike → walk-in)
- **Source line:** "LeanPath audit Mar 4–10 2026 · 408 entries · 2,316 lbs total. Routing via ArcGIS Route API."
