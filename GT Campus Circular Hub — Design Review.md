# PART II — Georgia Tech Campus Circular Hub — Design Review

## Problem Statement

Students at Georgia Tech lack visibility into what food is available across campus — from dining hall surplus and daily menus to student org events, campus vendor availability, and community resources like the campus pantry and mutual aid fridges. There is no centralized, real-time view connecting food sources, distribution points, and circular economy infrastructure at the campus level. Students don't know how much food is wasted daily or how many peers face food insecurity.

## Solution

A standalone Campus Circular Hub dashboard that provides:
1. **Live campus food map** — pins for every food source, distribution point, and circular economy node on campus
2. **Daily menu visibility** — what each dining hall is serving today, with portions remaining, pickup windows, and healthy food badges
3. **Real contact info** — hours, phone, address, website for every dining hall and campus vendor (from dining.gatech.edu)
4. **GT Engage integration** — quick link to free food events calendar + mock event pins on the map
5. **Student actions** — report surplus, find the pantry, join a pickup team, schedule food at events (all functional with localStorage)
6. **Impact awareness** — daily campus food waste stats and hunger impact metrics
7. **Campus route optimizer** — walking/biking directions between food sources, distribution, and compost
8. **Administrator analytics** — surplus trends, waste patterns, pantry usage, event waste (hidden by default)

**Target Users:** Students (primary), dining administrators (secondary)

---

## Page Architecture

| Aspect | Decision |
|--------|----------|
| **File** | New standalone `gt-campus-hub.html` in `resources/Layers & Packages/` |
| **Style** | Inline CSS/HTML/JS (no build step), dark theme matching surplus-map.html |
| **Basemap** | `dark-gray-vector`, centered on GT campus `[-84.3963, 33.7756]`, zoom 15 |
| **Nav** | 3-page header nav: AFCN Dashboard | **Campus Hub** | Surplus Map |
| **Default view** | Student View (map + panels) |
| **Admin view** | Hidden, toggled via "For administrator, click here" link |
| **Libraries** | ArcGIS JS SDK 4.30 (AMD/CDN) + Chart.js 4.x (CDN, admin view only) |

### Relationship to Existing Pages

| Page | After Implementation |
|------|---------------------|
| `index.html` (AFCN Dashboard) | Unchanged. Header nav adds link to Campus Hub. |
| `surplus-map.html` (Surplus Map) | Remove 12 GT campus entries from MOCK_SURPLUS. Becomes Atlanta-only. Header nav adds link to Campus Hub. |
| `gt-campus-hub.html` (**NEW**) | New standalone page. Links to AFCN Dashboard and Surplus Map. |
| `gt_fch_map.html` (old GT FCH) | Superseded by the new Campus Hub. |

---

## Two Views

| View | Audience | Default? | Content |
|------|----------|----------|---------|
| **Student View** | Students finding food | Yes | Map with pins, home panel, filters, daily menus, route optimizer |
| **Admin Coordination View** | Dining administrators | No (link toggle) | Chart.js dashboards with mock trend data |

---

## Student View — Components

### 1. Campus Home Panel (left sidebar)

```
──────────────────────────────────────
Georgia Tech Food Circular Hub
──────────────────────────────────────
Today's Surplus:
• 1,320 lbs available
• 4 dining halls reporting
• 3 pickup windows closing soon

Impact:
• 420 lbs wasted/day on campus
• Could feed 350 students
──────────────────────────────────────
Quick Buttons:
[Report Surplus]        → form modal, saves to localStorage, creates pin
[Find Campus Pantry]    → zooms to pantry, opens popup
[Join Pickup Team]      → registration form, saves to localStorage
[Food Event Scheduler]  → event form, saves to localStorage, creates pin
[Free Food Events ↗]    → opens GT Engage calendar in new tab
──────────────────────────────────────
For administrator, click here
──────────────────────────────────────
```

**Summary Stats** — computed from mock data:
- `X lbs available` (sum of all current surplus)
- `Y dining halls reporting` (count with active surplus)
- `Z pickup windows closing soon` (count with urgency = Critical or Soon)

**Impact Metrics** — in the summary section:
- `420 lbs wasted/day` (mock campus food waste figure)
- `Could feed 350 students` (mock calculation: waste_lbs / 1.2 lbs per meal)

**Quick Action Buttons — 5 buttons, all functional with localStorage:**

| Button | Action |
|--------|--------|
| **Report Surplus** | Modal form: location (dropdown), food type, quantity, expiration, transport, notes → localStorage → new pin |
| **Find Campus Pantry** | Zooms map to pantry pin(s), opens popup with hours/details |
| **Join Pickup Team** | Modal form: name, availability, transport method → localStorage → volunteer pin |
| **Food Event Scheduler** | Modal form: event name, date/time, location, food type, quantity → localStorage → event pin |
| **Free Food Events** | Opens `https://gatech.campuslabs.com/engage/events?perks=FreeFood` in a new tab |

**Admin Toggle** — "For administrator, click here" text link at bottom of home panel

### 2. Campus Micro-Map (center)

Pin categories with colors:

| Pin | Category | Color | Data Source |
|-----|----------|-------|-------------|
| 🍽 | Dining Hall Surplus | `#f4d35e` (gold) | `campus_dining.geojson` + mock surplus/menus |
| 🍔 | Campus Vendors | `#f57c00` (orange) | `pkg_fast_food_on_gt_campus.geojson` + real hours |
| 🎉 | Events | `#e040fb` (purple) | Mock: student org, Greek, research, athletics |
| 🥫 | Campus Pantry | `#29b6f6` (blue) | Mock (1-2 locations) |
| 🚲 | Student Pickup Volunteers | `#26a69a` (teal) | Mock (5-8) + localStorage additions |
| 🌱 | Compost Drop | `#4caf50` (green) | `compost_locations.geojson` (11 existing points) |
| 🏠 | Mutual Aid / Residence Fridges | `#78909c` (gray-blue) | Mock (3-4) |
| 🔬 | Urban Ag / Sustainability | `#8d6e63` (brown) | Mock (2-3) |

Base layers (always visible): `buildings.geojson`, `sidewalks.geojson`, `campus_boundary.geojson`

### 3. Filter Panel (left sidebar, below home panel)

**Category toggles** — checkbox per pin category with live count badges

**Dropdown filters:**
- **Time remaining**: All / Closing Soon (<2h) / Available Soon (<6h) / Available Later
- **Refrigeration**: Any / Refrigeration Required / No Refrigeration Needed
- **Portion size**: All Sizes / Small (<50 lbs) / Medium (50-200 lbs) / Large (200+ lbs)

### 4. Daily Menu Display + Contact Info (popup)

When clicking a **dining hall** pin, popup shows real contact info + mock menu with healthy badges:

```
North Ave Dining Hall
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 North Ave, Atlanta GA 30332
📞 404-894-2000
🕐 Mon-Thu 7a-2a | Fri 7a-10p | Sat-Sun 9a-9p
🔗 dining.gatech.edu

Today's Menu:
• Grilled Chicken Breast      🥗 Healthy
• Caesar Salad Bar             🥗 Healthy
• Pasta Primavera
• Fresh Fruit Station          🥗 Healthy
• Chocolate Chip Cookies

Available: 85 portions remaining
Pickup Window: 2:00 PM - 4:00 PM
Urgency: ● Soon (closing in 1h 30m)
```

**Healthy badges**: Items tagged as healthy in mock menu data get a `🥗 Healthy` badge. Healthy items include: salads, fruits, grilled proteins, whole grains, vegetables, smoothies.

When clicking a **campus vendor** pin, popup shows real hours:
```
Chick-fil-A
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 John Lewis Student Center
🕐 Mon-Thu 7a-9p | Fri 7a-7p | Sat 9a-5p | Closed Sun
```

When clicking an **event** pin, popup includes GT Engage link:
```
SGA Town Hall — Free Pizza
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Student Government Association
📍 Student Center Theater
🕐 Today 6:00 PM - 8:00 PM
🍕 Prepared Meals (~50 lbs)

View all free food events on GT Engage ↗
```

### 5. GT Engage Free Food Events Integration

- **Quick button**: "Free Food Events" opens `https://gatech.campuslabs.com/engage/events?perks=FreeFood` in a new tab
- **Event pins on map**: Mock event pins (🎉 purple) for upcoming free food events, each popup includes a note: "View all campus free food events on GT Engage" with a clickable link to the real calendar

### 6. Full Route Optimizer (right panel)

Campus-scale walking/biking route optimizer (adapted from surplus-map.html):

| Feature | Detail |
|---------|--------|
| **Origin** | Dropdown of all campus dining/vendor locations (default: North Ave Dining Hall) |
| **Transport mode** | Walking (~3 mph) or Biking (~10 mph) toggle |
| **Route chain** | Food Source → Distribution (pantry/fridge) → Compost Drop |
| **Auto-select** | Greedy nearest-neighbor with Haversine (reused from surplus-map.html) |
| **Real routing** | ArcGIS Route Service with API key, fallback to geodesic lines |
| **Stats** | Distance, walking/biking time, food volume |
| **Google Maps** | "Open in Google Maps" button for turn-by-turn directions |

---

## Admin Coordination View

Triggered by clicking **"For administrator, click here"** link in the Home Panel. Hides student panels (home, filter, route), shows full-width chart dashboard.

**"Back to Student View"** link returns to the default student view.

### Charts (Chart.js 4.x via CDN, mock data)

| Chart | Type | Mock Data |
|-------|------|-----------|
| Surplus Trends by Dining Hall | Line chart | 14 days × 4 dining halls, daily lbs |
| Waste Patterns by Weekday | Bar chart | Mon-Sun average waste lbs |
| Student Pantry Usage Rates | Bar chart | 6 months, visits + items distributed |
| Event Catering Waste Index | Horizontal bar | 4 event types, avg waste lbs |

### Helps Optimize
- Purchasing volumes
- Event planning
- Dining contracts

---

## Campus Stakeholders

### Food Sources
- Dining halls (existing `campus_dining.geojson` + real contact data + mock surplus/menus)
- Student org events (mock + GT Engage link)
- Greek life catering (mock)
- Campus cafes/vendors (existing `pkg_fast_food_on_gt_campus.geojson` + real hours)
- Research events (mock)
- Athletics (mock)

### Distribution
- Campus pantry (mock)
- Mutual aid networks (mock)
- Residence hall fridges (mock)
- Student emergency funds (mock — metadata only)

### Circular Economy
- Campus compost facility (existing `compost_locations.geojson`)
- Urban agriculture labs (mock)
- Sustainability research centers (mock)

---

## Data Model

### GeoJSON Enrichment (real data from dining.gatech.edu)

#### `campus_dining.geojson` — New fields to add

| Restaurant | hours | phone | url | address |
|-----------|-------|-------|-----|---------|
| North Ave Dining Hall | Sun 9a-9p, Mon-Thu 7a-2a, Fri 7a-10p, Sat 9a-9p | 404-894-2000 | dining.gatech.edu | North Ave, Atlanta GA 30332 |
| West Village Dining Commons | Sun-Sat 9a-9p (Mon-Fri extends to 11p) | 404-894-2000 | dining.gatech.edu | Hemphill Ave, Atlanta GA 30332 |
| Brittain Dining Hall | (to be confirmed) | 404-894-2000 | dining.gatech.edu | Techwood Dr, Atlanta GA 30332 |
| John Lewis Student Center Food Court | Mon-Fri varies by vendor | 404-894-2000 | dining.gatech.edu | 351 Ferst Dr NW |
| Nave Dining Concepts | Mon-Fri varies | 404-894-2000 | dining.gatech.edu | North Ave |
| Tech Square Dining Hub | Varies by vendor | 404-894-2000 | dining.gatech.edu | Tech Square |
| Clough Commons Cafe | Mon-Fri 7a-10p, Sat 9a-5p, Sun 9a-9p | 404-894-2000 | dining.gatech.edu | Clough Commons |
| Ferst District Cafe | — | 404-894-2000 | dining.gatech.edu | Ferst Dr |
| Klaus Bistro | — | 404-894-2000 | dining.gatech.edu | Klaus Advanced Computing Bldg |
| Exhibition Hall Express | — | 404-894-2000 | dining.gatech.edu | Exhibition Hall |
| Crosland Tower Coffee Bar | — | 404-894-2000 | dining.gatech.edu | Crosland Tower |
| CRC Fuel Zone | — | 404-894-2000 | dining.gatech.edu | Campus Recreation Center |

#### `pkg_fast_food_on_gt_campus.geojson` — New fields to add

| Name | hours | building |
|------|-------|----------|
| Chick-fil-A | Mon-Thu 7a-9p, Fri 7a-7p, Sat 9a-5p, Closed Sun | John Lewis Student Center |
| Panda Express | Mon-Fri 10a-9p (Fri 7p), Sat 11a-4p, Sun 11a-5p | John Lewis Student Center |
| Dancing Goats | Sun 9a-5p, Mon-Thu 8a-7p, Fri 8a-4p | John Lewis Student Center |
| Jimmy John's | Mon-Fri 10a-8p, Sat-Sun 10a-5p | Campus Retail |
| Dunkin Donuts | Mon-Fri 7a-8p, Sat 9a-5p, Sun 8a-5p | Campus Retail |
| Kaldi's Coffee | Mon-Thu 8a-6p, Fri 8a-5p | Campus Retail / Tech Square |
| Blue Donkey Coffee | Mon-Fri 7a-10p, Sat 9a-5p, Sun 9a-9p | Clough Commons |
| Twisted Taco | Mon-Thu 11a-7p, Fri 11a-3p | John Lewis Student Center |
| Noodle Theory | Mon-Fri 11a-3p | John Lewis Student Center |
| Marrakech Express | Mon-Fri 11a-7p, Sun 11a-5p | John Lewis Student Center |
| Brain Freeze | Mon-Fri 11a-3p | John Lewis Student Center |
| Campus Crust | Mon-Fri 11a-3p | John Lewis Student Center |
| Test Kitchen | Mon-Thu 11a-6p, Fri 11a-3p | John Lewis Student Center |
| The Pop Up | Mon-Fri 11a-2p | John Lewis Student Center |
| Tech it to Go | Mon-Thu 9a-6p, Fri 9a-3p | John Lewis Student Center |
| Carnegie Kitchen | Mon-Fri 8a-3p | Carnegie Building |
| Gold & Bold Coffee | Mon-Fri 8a-4p | IBB |

### Mock Data to Create (inline JS)

| Category | Entries | Key Fields |
|----------|---------|------------|
| **Campus menus** | 12 halls × ~5 items | item, healthy (boolean), portions_remaining, pickup_window |
| **Dining surplus** | 12 dining locations | quantity_lbs, hours_left, food_type, transport, urgency |
| **Campus events** | ~12 total (student org, Greek, research, athletics) | event_name, org_name, location, date, food_type, est_quantity, source_category |
| **Campus pantry** | 1-2 | name, location, hours, items_available, capacity |
| **Mutual aid / residence fridges** | ~3-4 | name, building, floor, items_available, last_stocked |
| **Pickup volunteers** | ~5-8 | name, availability, transport_method, location, status |
| **Urban ag / sustainability** | ~2-3 | name, location, type, description, accepts_compost |
| **Campus impact** | Static object | daily_waste_lbs, daily_diverted_lbs, students_could_feed, co2_saved_kg |
| **Admin chart data** | Time-series arrays | daily_surplus_lbs[], weekday_waste[], pantry_visits[], event_waste[] |

---

## Design Notes

- **Walking/biking speeds** for route optimizer: walking ~3 mph, biking ~10 mph (not driving 25 mph)
- **Campus boundary**: Add `campus_boundary.geojson` for visual context
- **Clustering**: Enable for point layers below zoom 15 (reuse pattern from index.html)
- **Popup style**: Undocked/floating (consistent with AFCN dashboard and surplus map)
- **Healthy food**: Use `🥗 Healthy` badge on mock menu items tagged `healthy: true`
- **GT Engage URL**: `https://gatech.campuslabs.com/engage/events?perks=FreeFood`
- **Page size estimate**: ~1,200-1,400 lines

---

## Reusable Patterns from Existing Code

| Pattern | Source | Reuse |
|---------|--------|-------|
| Dark theme CSS variables | surplus-map.html | `--bg-dark`, `--text`, `--muted`, `--gold` |
| Topbar with GT logo SVG + nav links | surplus-map.html | Extend to 3-page nav |
| Left panel toggle + filter checkboxes | surplus-map.html | Category filters |
| Right panel route optimizer | surplus-map.html | Adapt for walking/biking |
| GraphicsLayer for dynamic pins | surplus-map.html | Surplus/event/volunteer pins |
| GeoJSONLayer for static data | index.html | Dining, compost, vending layers |
| Custom HTML popup content | surplus-map.html | Menu + contact popups |
| Haversine + greedy nearest-neighbor | surplus-map.html | Route auto-select |
| Campus color tokens | index.html | `--gt-dining`, `--gt-compost`, etc. |
| API key fetch from `/api/config` | surplus-map.html | Same pattern |
| `CAMPUS_VIEW` constant | index.html | `[-84.3963, 33.7756], zoom: 15` |
