# Map 3 — Legend Specification

## Title
**Transport Accessibility** — Walking access to MARTA rail + bus
Source: MARTA GTFS · OSRM isochrones · I2CE Lab April 2026

## Classification — sequential walkshed
| Band | Walk time to MARTA | Color (hex) |
|---|---|---|
| Excellent | ≤5 min | `#1c5c84` (Nr. 51) — 60% fill |
| Good | 5–10 min | `#7d9caf` (Nr. 57) — 50% fill |
| Moderate | 10–15 min | `#a4b1bc` (Nr. 54) — 40% fill |
| Outside walkshed | >15 min | no fill |

## Vehicle-availability overlay
| % zero-vehicle HH | Hatch pattern |
|---|---|
| <10% | no hatch |
| 10–20% | sparse diagonal Nr. 52 |
| >20% | dense diagonal `#c62828` (alert) — transit-dependent + low access = priority zones |

## Symbology layers (draw order, bottom to top)
1. Tracts colored by % zero-vehicle households (light Nr. 55 → Nr. 50)
2. 15/10/5 min walkshed buffers — stacked translucent fills
3. MARTA bus routes — `#5b7282` (Nr. 52) 1px solid
4. MARTA rail — official line colors (Red `#E51937`, Gold `#FFC72C`, Blue `#0072CE`, Green `#00A551`) at 4.5px
5. MARTA rail stations — white `#fff` 8px dot + 2px dark outline

## Auxiliary elements
- **Annotation:** Label all 38 rail stations; major bus hubs (Five Points, H.E. Holmes, Lindbergh)
- **Source line:** "MARTA GTFS 2025. OSRM 3 mph isochrones. ACS B08201 2022."
