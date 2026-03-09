# AFCN Presentation Script
## Atlanta Food Circular Network — Georgia Tech Circular Economy Lab [I2CE]

---

## SLIDE 1 — Opening & Background (1 minute)

> Good [morning/afternoon], my name is [Name] from the Georgia Tech Circular Economy Lab, I2CE.
>
> My background sits at the intersection of **urban planning analytics** and **computer science** — I'm interested in how computational tools can be integrated into the design process, particularly through augmented and spatial intelligence. But today's project is specifically about **spatial analytics and cartography** — and more precisely, about what cartography *chooses* to make visible, and what it leaves out.
>
> I'm presenting the **Atlanta Food Circular Network** — a citywide food system mapping platform built on the principles of **critical cartography**.

---

## SLIDE 2 — Critical Cartography & Problem Statement (2 minutes)

> Let me start with a question: **Who decides what gets mapped?**
>
> Traditional cartography has always been an act of power. Maps of Atlanta will show you highways, commercial districts, property boundaries, and transit lines — the infrastructure of commerce and movement. But they won't show you where 1,500 pounds of prepared meals were thrown away last Tuesday. They won't show you the food bank three miles away that ran out of inventory that same day. They won't show you the volunteer driver who could have connected the two in 24 minutes.
>
> This is where **critical cartography** comes in. Critical cartography asks us to interrogate what maps render invisible — and to build counter-maps that center the lived experiences and material flows that conventional mapping ignores. In the context of food systems, **the flows of surplus, waste, need, and recovery are almost entirely unmapped**. They exist in spreadsheets, phone calls, and institutional memory — but not in spatial form.
>
> **Atlanta has a food waste crisis hiding in plain sight.**
>
> - Roughly **40% of food produced in the United States goes to waste** — 80 million tons per year
> - The Atlanta metro area generates **over 1.7 million tons of food waste** annually
> - Meanwhile, **1 in 7 Atlantans faces food insecurity** — they don't know where their next meal is coming from
> - On the Georgia Tech campus alone, dining halls waste an estimated **420 pounds of edible food per day** — enough to feed 350 students
>
> So we have food being thrown away on one side of the city, and families going hungry on the other. The problem isn't supply — **the problem is visibility and logistics**. The food recovery ecosystem in Atlanta is fragmented. Donors don't know who to call. Food banks can't see what's available in real time. Volunteer drivers waste hours on inefficient routes. And critical perishable items expire unclaimed because no one knew they existed.
>
> From a critical cartography perspective, this is a **spatial justice issue**. The infrastructure of food waste is invisible precisely because no one has chosen to map it. **AFCN is a counter-map** — it makes the circular food economy spatially legible for the first time.

---

## SLIDE 3 — Solution Overview (1.5 minutes)

> **The Atlanta Food Circular Network is a counter-cartography platform that makes the invisible visible.**
>
> As someone working across urban planning analytics and computer science, I approached this as a design problem: how do you take an entire material flow system — food moving from production through surplus, rescue, redistribution, consumption, and composting — and render it as an **interactive spatial narrative**?
>
> The answer is 30 geospatial layers, over **14,000 data points**, organized into four categories that trace the full lifecycle of food:
>
> 1. **Food Recovery Sources** — 11,314 restaurants, institutions, and donors across the metro area. These are the points conventional maps never show — the places where surplus food originates.
> 2. **Redistribution Nodes** — 2,629 food banks, pantries, shelters, and community fridges. The connective tissue of the food rescue network.
> 3. **Beneficiary Access Points** — community centers and SNAP offices where families access support. Overlaid with CDC food insecurity data to reveal spatial inequity.
> 4. **Circular Economy Endpoints** — 127 compost sites, urban farms, and recycling facilities. Where food that can't be rescued returns to the soil — closing the loop.
>
> Each layer is a cartographic argument: **these flows exist, they are spatial, and they can be optimized.** The platform is built on four dashboards, each designed for a specific audience and use case. Let me walk you through them.

---

## SLIDE 4 — AFCN Dashboard Demo (2 minutes)

> *[Open the AFCN Dashboard]*
>
> This is the **main AFCN Dashboard** — the command center for Atlanta's food circular network.
>
> It operates in two modes:
>
> - **Atlanta mode** gives you the full citywide picture — you can toggle layers for food recovery sources, redistribution nodes, beneficiary access points, and the circular economy network. The layer panel on the left lets you drill down into specific categories like grocery stores, farmers markets, hospitals, and religious institutions.
>
> - **GT Campus mode** zooms into Georgia Tech specifically — showing campus dining halls, compost locations, vending machines, and building infrastructure.
>
> Notice the **stats rail** at the bottom — it shows live feature counts as you toggle layers on and off. And when you click any point, you get a floating popup with detailed information about that location.
>
> This is where the critical cartography lens becomes powerful. We've overlaid **CDC food insecurity data** — those shaded census tracts in Fulton and DeKalb counties. When you see a cluster of food recovery sources sitting directly adjacent to a high-insecurity census tract with no redistribution node between them — that's the spatial injustice rendered visible. **The map becomes an argument for intervention.**

---

## SLIDE 5 — Real-Time Surplus Map Demo (2.5 minutes)

> *[Switch to the Surplus Map]*
>
> This is where the platform moves from **mapping to action**.
>
> The Real-Time Surplus Map is a dispatch-grade logistics tool for food rescue operations. Each pin represents a live food surplus report — color-coded by urgency:
>
> - **Red** means critical — this food expires within 2 hours
> - **Yellow** means soon — 2 to 6 hours remaining
> - **Green** means stable — more than 6 hours
>
> On the left, you can filter by food type — prepared meals, produce, bakery items, packaged goods, or perishables requiring refrigeration.
>
> But the real innovation is the **Route Optimizer** on the right. Watch what happens when I select a vehicle type — say, a Refrigerated Van — and click Auto-Select.
>
> *[Click Auto-Select]*
>
> The system just built an optimized **4-stop chain**: Food Recovery pickup, Redistribution drop-off, Beneficiary delivery, and Compost endpoint. It uses a **weighted scoring algorithm** that prioritizes:
>
> - **Urgency at 50%** — items expiring within the hour get an exponential priority boost
> - **Volume at 30%** — larger quantities are prioritized to maximize impact per trip
> - **Proximity at 20%** — distance matters, but it doesn't dominate
>
> This means a 500-pound load expiring in 45 minutes will always get rescued before a 50-pound load 2 miles closer — which is exactly the right decision.
>
> The system also checks **transport compatibility** — a Bike Courier physically can't carry a 500-pound refrigerated load, so those pickups only show for Refrigerated Vans. And it checks **destination capacity** — if a food bank's cold storage is 95% full, it gets deprioritized but not excluded.
>
> When we have a valid ArcGIS API key, these routes use **real-time traffic data** from the ArcGIS Route Service. Without it, we fall back to geodesic estimates.
>
> The **Fleet Intelligence panel** at the top shows live fleet status — active drivers, refrigerated vehicles available, average pickup time, and total pounds moved today. The AI Suggestion auto-generates the highest-priority route chain on page load.

---

## SLIDE 6 — Fleet Analytics Demo (1.5 minutes)

> *[Switch to Fleet Analytics]*
>
> The Fleet Analytics dashboard takes the operational view one step deeper — into **real-time fleet management**.
>
> On the left, you see the **fleet roster** — 8 vehicles with their drivers, vehicle type, status, and utilization percentage. This is a dispatcher's view.
>
> The bottom strip is the **4-step assignment funnel**:
>
> 1. **Select a driver** from the fleet table
> 2. The system **AI-ranks food donors** by distance, vehicle compatibility, and urgency
> 3. Based on the selected donor, it **ranks redistribution destinations**
> 4. You review the **Guided Assignment Builder** — which validates that the driver is active, the vehicle is compatible, and the route is calculated — then queue it for approval
>
> Approved routes move through a lifecycle: **Pending, Approved, In-Progress, Completed** — tracked in the dock on the right.
>
> This dashboard bridges the gap between the strategic map view and the operational reality of coordinating volunteers and vehicles on the ground.

---

## SLIDE 7 — GT Campus Hub Demo (1.5 minutes)

> *[Switch to GT Campus Hub]*
>
> Finally, the GT Campus Circular Hub brings the entire system down to the **student scale**.
>
> This is designed for two audiences:
>
> **For students**, the left panel shows today's surplus stats — how many pounds are available, how many dining halls are reporting, and how many pickup windows are closing soon. There are quick actions: report surplus food you see on campus, find the nearest pantry, sign up as a volunteer pickup courier, or check for free food events.
>
> The micro-map shows 8 pin categories specific to campus life — dining hall surplus, campus vendors, free food events, the campus pantry, volunteer pickup points, compost drop-offs, community fridges, and urban agriculture sites.
>
> Students can even plan **walking or biking routes** between food sources, pantries, and compost sites — optimized for campus distances.
>
> **For administrators**, there's a hidden analytics view with Chart.js dashboards showing surplus trends by dining hall over 14 days, waste patterns by day of the week, student pantry usage rates, and event catering waste indexes. This data helps dining services make better procurement decisions.

---

## SLIDE 8 — Spatial Intelligence & Technical Architecture (1.5 minutes)

> This is where my background in both urban planning analytics and computer science comes together. AFCN is not just a map — it's an **integrated application** where spatial analytics drives design decisions.
>
> The cartographic layer provides the **legibility** — making food flows visible. But the computational layer provides the **intelligence** — urgency-aware scoring, transport compatibility filtering, capacity-aware routing. Neither works without the other. A map without analytics is just dots. An algorithm without spatial context can't tell you that the critical pickup is across a highway from the nearest redistribution node.
>
> Technically, the platform is built on:
>
> - **ArcGIS Maps SDK for JavaScript v4.30** — spatial rendering, geocoding, and real-time route solving with live traffic data
> - **30 GeoJSON data layers** — over 14,000 geospatial features sourced from Atlanta city records, GT campus GIS, CDC food insecurity surveys, and Fulton County compost permits
> - **Urgency-aware routing algorithms** — weighted priority scoring that embeds food science constraints (expiration decay, cold chain requirements) into spatial optimization
> - **Pure HTML, CSS, and JavaScript** — no build step, no framework dependency — designed for portability and accessibility
> - **Netlify deployment** with serverless functions for secure API key management
>
> Every algorithm is designed to be **replaceable with live API data** when partners come online. The mock data layer demonstrates the full spatial intelligence while real-time integrations are developed.

---

## SLIDE 9 — Impact & Vision (1.5 minutes)

> To put this in perspective:
>
> - We've mapped **11,314 food recovery sources** — most of which had no digital presence in the food rescue ecosystem before this
> - **2,629 redistribution nodes** are now discoverable and routable in real time
> - The urgency-aware routing ensures that **the most critical food gets rescued first**, not just the closest food
> - On campus, we've quantified that **420 pounds per day** of edible food waste could feed **350 students** — and now there's a tool to actually make that happen
>
> Coming back to **critical cartography** — the argument I'm making with this platform is that food systems are fundamentally spatial systems, and the reason they fail is not scarcity but **spatial illegibility**. The infrastructure of food waste has been invisible because no one chose to map it. AFCN is a deliberate cartographic intervention — it renders the circular food economy legible so that planners, logistics coordinators, students, and community organizations can act on it.
>
> This is what I mean by **integrating computation into design**. The map is the design artifact. The algorithms are the design intelligence. And the spatial analytics are what transform a static picture into a dynamic, actionable system.
>
> The vision for AFCN is to become Atlanta's **shared infrastructure for food circularity** — connecting donors, food banks, volunteers, and compost facilities on a single platform, powered by real-time spatial intelligence.
>
> **No more food wasted because nobody knew it was there. No more families hungry because the logistics didn't connect. The map makes it visible. The algorithm makes it actionable.**
>
> Thank you. I'm happy to take questions.

---

## Q&A PREP — Likely Questions & Answers

**Q: Is the data real or simulated?**
> The geographic data is real — 30 GeoJSON layers sourced from Atlanta city records, GT campus GIS, CDC food insecurity surveys, and Fulton County permits. The surplus pins and fleet data use mock entries with real Atlanta coordinates, designed to be swapped with live feeds.

**Q: How does the urgency scoring work?**
> It's a weighted formula: 50% urgency (exponential decay — items under 1 hour get extreme priority), 30% volume (logarithmic — diminishing returns past 500 lbs), and 20% proximity (inverse distance). This prevents the naive nearest-neighbor approach from ignoring critical large loads.

**Q: What's the deployment plan?**
> The platform is deployed via Netlify with a serverless function handling the ArcGIS API key securely. It's also runnable locally via a Python dev server for campus demos. The architecture is designed for zero infrastructure cost at this stage.

**Q: How would this connect to real food banks?**
> The MOCK_FLEET and MOCK_SURPLUS constants are designed as drop-in API placeholders. A partner food bank could expose a simple JSON API with their current inventory and vehicle status, and the system would consume it without architectural changes.

**Q: How does critical cartography apply here specifically?**
> Traditional maps of Atlanta show the built environment — roads, buildings, zones. They don't show material flows like food waste. Critical cartography argues that what gets mapped is a political choice. AFCN is a counter-map that makes the food recovery ecosystem spatially legible for the first time — revealing gaps between surplus and need that are invisible in conventional GIS. The CDC food insecurity overlay is a direct example: layering census-tract vulnerability data onto food recovery sources exposes spatial inequity that no standard city map would show.

**Q: What about privacy concerns with mapping food-insecure populations?**
> Beneficiary access points show service locations (community centers, SNAP offices), not individual households. CDC food insecurity data is aggregated at the census tract level. No personally identifiable information is stored or displayed.

---

*Estimated total speaking time: ~14 minutes + Q&A*
