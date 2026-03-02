# Design Research Notes — Real-Time Surplus Map + Logistics Optimizer

**Research Date:** 2026-02-28
**Purpose:** Inform UX/UI design for AFCN Intelligence Layer (Phase 4)
**Method:** Parallel analysis of 4 platform categories via dedicated research agents

---

## 1. Food Rescue Platforms

### Platforms Studied
- **MealConnect** (Feeding America) — largest US food rescue matching platform
- **Too Good To Go** — surplus food marketplace (Europe/US)
- **Food Rescue US** — volunteer-driver food rescue coordination
- **Food Rescue Hero** (412 Food Rescue) — gamified volunteer dispatch
- **OLIO** — peer-to-peer food sharing app

### Key Design Patterns

**Map & Pin Design:**
- Minimum **24px pin size** — Too Good To Go's tiny dots are a documented UX failure; users can't tap them on mobile
- Pair color with **icons + text labels** — never rely on color alone (WCAG accessibility)
- Use **category-specific icons** inside pins (fork for prepared meals, leaf for produce, box for packaged)
- **Cluster pins at low zoom** with count badges; expand to individual pins on zoom

**Information Architecture:**
- **Map + List split view** — let users browse as list OR on map (Food Rescue US pattern)
- **"Available Rescues" tab** — task-focused naming, not data-focused ("Items" or "Locations")
- **Card-based listing** beside map with: photo, name, quantity, distance, urgency badge
- Sort by: urgency (default), distance, quantity, time posted

**Popup/Detail Design:**
- Include **photos** of available food in popups (builds volunteer trust — "I know what I'm picking up")
- Show **pickup window** not just expiration ("Available 2-4 PM" vs "Expires 4 PM")
- **One-tap claim** button prominently placed — reduce friction to zero
- Show **donor reliability score** (MealConnect pattern: verified donors get badges)

**Urgency Communication:**
- **Color + text + icon** triple-encoding: red circle + "URGENT" text + clock icon
- **Countdown timer** in real-time: "1h 23m remaining" not just "Expires 2 PM"
- **Push notification** trigger at urgency threshold transitions (Stable → Soon → Critical)

### Lessons for AFCN
- Our 10-18px pin range is too small — use 14-22px minimum
- Add pulse animation ONLY for Critical urgency pins (not all)
- Popup should lead with quantity + urgency, not location name
- "Route From Here" button should be primary action color (#00bfa5), not secondary

---

## 2. Logistics & Route Optimization Dashboards

### Platforms Studied
- **Onfleet** — last-mile delivery management
- **Circuit** — route optimization for drivers
- **Route4Me** — multi-stop route planning
- **Routific** — fleet routing with time windows
- **OptimoRoute** — delivery scheduling + route optimization
- **Google Maps Platform** — Directions API integration patterns

### Key Design Patterns

**Stop List Design:**
- **Drag-reorderable stop list** with numbered sequence and six-dot drag handles
- **Color-coded stop numbers** matching map markers (1=blue, 2=green, 3=orange, 4=red)
- **Two-way binding** — click list item = zoom to marker on map; click marker = highlight in list
- **Compact stop cards**: Number + Name + ETA + Distance from previous (one line each)

**Stats Dashboard:**
- **4-metric stats grid** (2x2): Distance, Duration, Stops, Savings %
- Large numbers with small labels below
- **Before/after comparison**: "Optimized: 24 min" vs "Unoptimized: 38 min (37% saved)"
- Use **progress bar** for savings visualization

**Route Polyline:**
- **3-5px solid line** — too thin is invisible, too thick obscures streets
- **Traffic-aware coloring**: green (free flow) → yellow (moderate) → red (congested) segments
- **Faint underlay shadow** (8px, 20% opacity) to make route pop against busy basemap
- **Animated dashes** for estimated/fallback routes (not solid)
- **Direction arrows** along polyline at intervals

**Panel Layout:**
- **Collapsible right panel** (300-400px wide) — standard placement for route details
- **Progressive disclosure**: Basic controls visible, advanced settings behind expandable sections
- **Loading state**: skeleton cards + pulsing progress bar during route calculation
- **Clear visual hierarchy**: Origin (green) → Stops (numbered) → Destination (red flag)

**Interaction Patterns:**
- **Click-to-add stops** on map (bypasses dropdown selection)
- **Estimated arrival time** at each stop, not just total duration
- **"Optimize Sequence"** button separate from "Calculate Route" — user can choose fixed vs optimized order
- **Export to Google Maps / Apple Maps** — "Navigate" button opens turn-by-turn in phone app

### Lessons for AFCN
- Our 360px panel width is appropriate (Onfleet uses 340px, Circuit uses 380px)
- Stats grid should show 4 metrics max — don't overload
- Route line at 4px width with 8px underlay is correct
- Add leg-by-leg ETA, not just total time
- Loading spinner should be inside the panel, not a modal overlay

---

## 3. Real-Time Map Dashboards

### Platforms Studied
- **ArcGIS Operations Dashboard** — Esri's real-time monitoring solution
- **Kepler.gl** — Uber's open-source geospatial visualization
- **PulsePoint** — real-time emergency response visualization
- **Waze Live Map** — crowd-sourced traffic incidents
- **Mapbox Studio** — custom map design patterns
- **CARTO** — spatial analytics dashboards

### Key Design Patterns

**Dark Theme Best Practices:**
- Base color: `#1a1a1a` to `#1e1e2e` — NOT pure black `#000` (causes eye strain / halation on OLED)
- **Text contrast**: `#e0e0e0` for primary, `#9e9e9e` for secondary (meets WCAG AA)
- **Card backgrounds**: `#252530` to `#2a2a3a` — slightly lighter than map background
- **Border color**: `rgba(255,255,255,0.08)` — subtle separation without harsh lines
- **Accent colors** need higher saturation on dark backgrounds to remain visible

**Real-Time Indicators:**
- **Pulse animation only for critical/active** items — animating everything creates visual noise
- `@keyframes pulse { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(2.5); opacity: 0; } }`
- **Glow/halo effect** via `filter: drop-shadow(0 0 6px rgba(color, 0.6))` for real-time overlay pop
- **"Live" indicator**: pulsing green dot + "Updated 2s ago" ticker in header/footer
- **Stale data warning**: yellow badge when data is >5 min old, red when >15 min

**Overlay Techniques:**
- ArcGIS **blend mode `lighten`** for overlay data against dark basemap — makes bright data pop
- **Opacity by confidence/freshness**: newer data = more opaque, older = more transparent
- **Z-ordering**: critical items always on top (`zIndex` by urgency)
- **Declutter at scale**: auto-hide labels below certain zoom, show on hover

**Performance Patterns:**
- **WebGL rendering** for 1000+ points (ArcGIS FeatureLayer with WebGL)
- **Viewport culling** — only render features in current extent
- **Debounce filter changes** — don't re-render on every checkbox click (wait 150ms)
- **Level-of-detail**: simplified symbols at low zoom, detailed at high zoom

### Lessons for AFCN
- Our existing `--bg-dark: #07090f` is quite dark — works since we use basemap, not flat background
- Add pulse animation ONLY to Critical surplus pins
- Use `drop-shadow` glow on surplus pins for real-time "alive" feel
- Add "Last updated" ticker somewhere visible
- Use blend mode `lighten` on the surplus GraphicsLayer

---

## 4. Surplus Inventory & Food Waste UIs

### Platforms Studied
- **Leanpath** — commercial kitchen food waste tracking
- **Winnow** — AI-powered food waste monitoring
- **Wasteless** — dynamic pricing for expiring food
- **Flashfood** — discounted near-expiry grocery marketplace
- **OLIO** — peer-to-peer food sharing (also in Category 1)
- **Spoiler Alert** — surplus food B2B marketplace

### Key Design Patterns

**Card Hierarchy:**
1. **Urgency badge** (top-left corner) — most important signal
2. **Name + Quantity** in large text
3. **Location** in muted smaller text
4. **Action button** at bottom (full-width, high contrast)

**Quantity Display:**
- **Dual units**: "25 lbs (~15 servings)" — weight alone is meaningless to volunteers
- **Visual quantity indicator**: small/medium/large icons or filled bar (like battery level)
- **Conversion reference**: 1 lb ≈ 0.6 meals (EPA estimate for mixed food)

**Expiration & Urgency:**
- **Color progression**: green (#66bb6a) → yellow (#ffc107) → orange (#ff9800) → red (#ef5350)
- **Countdown format**: "2h 15m" for <6 hours, "Tomorrow 2 PM" for >6 hours
- **Progress bar** showing time remaining as percentage of original window
- **Threshold alerts**: visual change when crossing 6hr → 2hr → 30min boundaries

**Transport Requirements:**
- **Icon row** with tooltips: refrigerated truck icon / fragile-handle icon / pickup-only icon
- **Color coding**: blue = refrigerated, orange = ambient/dry, green = walkable
- **Capacity indicator**: "Fits in sedan" / "Needs van" / "Needs truck"

**Impact Metrics:**
- **Gamification dashboard**: lbs diverted, CO2 avoided, meals served, $ value saved
- **Running totals** with animated counters
- **Personal + community stats** ("You rescued 45 lbs this week; Atlanta rescued 12,400 lbs")
- **Equivalency translations**: "120 lbs = 72 meals = 180 lbs CO2 avoided"

**Inventory List Patterns:**
- **Sortable columns**: Name, Type, Quantity, Expires, Urgency, Distance
- **Batch actions**: "Claim All Critical" button for dispatchers
- **Quick filters**: pill/chip buttons along top (All | Critical | Prepared | Produce)
- **Empty state**: encouraging message + illustration when no items match filter

### Lessons for AFCN
- Add serving estimate alongside lbs: "120 lbs (~72 meals)"
- Use color progression in countdown timer text, not just pin color
- Transport field should use icon + text, not just text
- Summary should show impact metrics: total lbs, meals equivalent, critical count
- Consider adding a "Claim All Critical" batch action in future iterations

---

## Cross-Cutting Design Principles (Synthesized)

### 1. Visual Hierarchy
Pin urgency must be readable at a glance: **size + color + animation** triple-encoding
- Critical: 18-22px, red, pulsing
- Soon: 14-18px, yellow, static with glow
- Stable: 12-14px, green, static

### 2. Accessibility
- Never use color as sole differentiator — always pair with text/icon/shape
- Minimum touch target: 44x44px on mobile (even if pin is smaller, tap area must be 44px)
- Sufficient contrast ratios on dark theme (WCAG AA minimum)

### 3. Information Density
- **Popups**: 6-8 fields maximum, prioritize actionable info
- **Stats grid**: 4 primary metrics (more behind expansion)
- **Stop list**: name + ETA + distance per line (3 data points max)

### 4. Progressive Disclosure
- Show essential controls first, advanced behind "More Options"
- Route panel: origin + optimize button visible; chain stops expandable
- Filter panel: checkboxes visible; summary stats below

### 5. Real-Time Feel
- Pulse animation for critical items only
- "Updated Xs ago" indicator
- Smooth transitions on filter/route changes (200-300ms)
- Avoid jarring redraws — animate opacity changes

### 6. Mobile-First Considerations
- Route panel → bottom sheet on mobile (<760px)
- Surplus filters → collapsible section
- Touch-friendly button sizes (min 44px height)
- Swipe-to-dismiss for panels

---

## Color Palette Reference

| Purpose | Color | Hex |
|---------|-------|-----|
| Critical urgency | Red | #ef5350 |
| Soon urgency | Amber | #ffc107 |
| Stable urgency | Green | #66bb6a |
| Route line | Teal | #00bfa5 |
| Prepared Meals | Red | #ef5350 |
| Packaged Goods | Blue | #42a5f5 |
| Produce | Green | #66bb6a |
| Bakery | Orange | #ffa726 |
| Perishable | Pink | #ec407a |
| Panel background | Dark | #141924 |
| Card background | Dark elevated | #1e2433 |
| Muted text | Gray | #9ca6b8 |

---

*These notes synthesize research from 20+ platforms across 4 categories. Applied findings are reflected in the implementation plan at `Real-time Surplus Map.md`.*
