# AFCN Phase 1 — Data Collection Tracking Sheet

**Project:** Atlanta Food Circular Network Map (AFCN)
**Phase:** 1 — Data Collection & Acquisition
**Status:** ⏳ Not Started
**Last Updated:** 2026-02-26

---

## Subagent Assignment Summary

| Subagent | Stakeholder Category | Target Count | Status | Locations Found | Data Quality | Review |
|----------|---------------------|-------------|--------|-----------------|--------------|--------|
| **SA-1** | 🔴 Food Recovery Sources | 20–25 | ⏳ Pending | — | — | — |
| **SA-2** | 🔵 Redistribution Nodes | 20–25 | ⏳ Pending | — | — | — |
| **SA-3** | 🟢 Beneficiary Access Points | 20–25 | ⏳ Pending | — | — | — |
| **SA-4** | 🟤 Circular Economy Extensions | 12–18 | ⏳ Pending | — | — | — |

**Status Key:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Needs Review | ❌ Failed

---

## Data Quality Scoring Rubric

Each location entry is scored across 7 fields. Total score = quality grade.

| Field | Points | Description |
|-------|--------|-------------|
| `location_name` | 1 | Official, verified name |
| `address` | 1 | Full street address with ZIP |
| `latitude / longitude` | 2 | Accurate coordinates (verified via map) |
| `category / type` | 1 | Correctly classified |
| `capacity / served` | 1 | Has a real or estimated volume figure |
| `hours / contact` | 1 | At least one contact method or hours |
| `status` | 1 | Operational status confirmed |

**Grade Scale:**
| Score | Grade | Meaning |
|-------|-------|---------|
| 7–8 pts | ⭐⭐⭐ High | GeoJSON-ready, no follow-up needed |
| 5–6 pts | ⭐⭐ Medium | Usable, minor gaps to fill |
| 3–4 pts | ⭐ Low | Needs follow-up before GeoJSON build |
| 0–2 pts | ❌ Unusable | Drop or replace |

---

---

## SA-1: Food Recovery Sources 🔴

**Category:** Restaurants · Stadiums · Grocery · Farmers Markets · Corporate Cafeterias · Event Venues · Film Catering
**Status:** ⏳ Pending
**Subagent Output File:** _(to be attached after run)_

### Field Completion Checklist
- [ ] `location_name` — all entries have verified names
- [ ] `address` — all entries have full address + ZIP
- [ ] `latitude` / `longitude` — all entries have verified coordinates
- [ ] `category` — correctly assigned to one of: Restaurant | Stadium | Grocery | FarmersMarket | Corporate | EventVenue | FilmCatering
- [ ] `est_lbs_week` — estimated lbs/week present for ≥ 70% of entries
- [ ] `hours` / `contact` — at least one field populated per entry
- [ ] `status` — Active | Pilot | Inactive | Unknown assigned to all
- [ ] `food_types` — food types noted for ≥ 50% of entries
- [ ] `existing_partner` — partnership status noted

### Sub-Category Targets
| Sub-Category | Target | Found | Gap |
|-------------|--------|-------|-----|
| Restaurants (Midtown/Downtown/Buckhead) | 5–7 | — | — |
| Stadium Vendors | 3–4 | — | — |
| Grocery Chains | 4–5 | — | — |
| Farmers Markets | 3–4 | — | — |
| Corporate Cafeterias | 3–4 | — | — |
| Film/TV Catering | 1–2 | — | — |
| Event Venues | 2–3 | — | — |
| **TOTAL** | **20–25** | **—** | **—** |

### Data Quality Evaluation (fill in after review)
| # | Location Name | Address ✓ | Coords ✓ | Category ✓ | Capacity ✓ | Contact ✓ | Status ✓ | Score | Grade |
|---|--------------|-----------|----------|------------|-----------|----------|----------|-------|-------|
| 1 | | | | | | | | /8 | |
| 2 | | | | | | | | /8 | |
| 3 | | | | | | | | /8 | |
| 4 | | | | | | | | /8 | |
| 5 | | | | | | | | /8 | |
| _..._ | | | | | | | | | |

### Reviewer Notes (SA-1)
```
Overall quality:
Gaps identified:
Recommended follow-up:
GeoJSON-ready: Yes / No / Partial
```

---

---

## SA-2: Redistribution Nodes 🔵

**Category:** Food Banks · Community Fridges · Church Pantries · Mutual Aid · Shelters · Senior Centers
**Status:** ⏳ Pending
**Subagent Output File:** _(to be attached after run)_

### Field Completion Checklist
- [ ] `location_name` — all entries have verified names
- [ ] `address` — all entries have full address + ZIP
- [ ] `latitude` / `longitude` — all entries have verified coordinates
- [ ] `node_type` — correctly assigned to one of: FoodBank | CommunityFridge | ChurchPantry | MutualAid | Shelter | SeniorCenter
- [ ] `capacity_lbs_week` — estimated capacity for ≥ 60% of entries
- [ ] `hours` — distribution schedule populated for ≥ 70%
- [ ] `status` — Active | At Capacity | Seasonal | Unknown assigned to all
- [ ] `populations_served` — noted for ≥ 50% of entries
- [ ] `neighborhood` — Atlanta neighborhood name included

### Sub-Category Targets
| Sub-Category | Target | Found | Gap |
|-------------|--------|-------|-----|
| Food Banks / Pantries | 3–4 | — | — |
| Community Fridges | 5–7 | — | — |
| Church Pantries | 4–5 | — | — |
| Mutual Aid Groups | 2–3 | — | — |
| Housing Shelters | 3–4 | — | — |
| Senior Centers | 2–3 | — | — |
| **TOTAL** | **20–25** | **—** | **—** |

### Data Quality Evaluation (fill in after review)
| # | Location Name | Address ✓ | Coords ✓ | Type ✓ | Capacity ✓ | Hours ✓ | Status ✓ | Score | Grade |
|---|--------------|-----------|----------|--------|-----------|---------|----------|-------|-------|
| 1 | | | | | | | | /8 | |
| 2 | | | | | | | | /8 | |
| 3 | | | | | | | | /8 | |
| _..._ | | | | | | | | | |

### Reviewer Notes (SA-2)
```
Overall quality:
Gaps identified:
Recommended follow-up:
GeoJSON-ready: Yes / No / Partial
```

---

---

## SA-3: Beneficiary Access Points 🟢

**Category:** SNAP Offices · Mobile Trucks · College Pantries · Public Schools · Healthcare Clinics
**Status:** ⏳ Pending
**Subagent Output File:** _(to be attached after run)_

### Field Completion Checklist
- [ ] `location_name` — all entries have verified names
- [ ] `address` — all entries have full address + ZIP
- [ ] `latitude` / `longitude` — all entries have verified coordinates
- [ ] `access_type` — correctly assigned to one of: SNAP | MobileTruck | CollegePantry | School | Clinic
- [ ] `served_per_week` — estimate present for ≥ 60% of entries
- [ ] `hours` — service hours populated for ≥ 70%
- [ ] `eligibility` — who can access documented for ≥ 60%
- [ ] `status` — Active | Scheduled | Inactive | Unknown assigned to all
- [ ] `neighborhood` — Atlanta neighborhood name included

### Sub-Category Targets
| Sub-Category | Target | Found | Gap |
|-------------|--------|-------|-----|
| SNAP Enrollment Offices | 3–4 | — | — |
| Mobile Distribution Trucks | 2–3 | — | — |
| College Pantries | 6–8 | — | — |
| Public Schools (with programs) | 4–5 | — | — |
| Healthcare Clinics / Food Pharmacies | 3–4 | — | — |
| **TOTAL** | **20–25** | **—** | **—** |

### Data Quality Evaluation (fill in after review)
| # | Location Name | Address ✓ | Coords ✓ | Type ✓ | Served/wk ✓ | Hours ✓ | Status ✓ | Score | Grade |
|---|--------------|-----------|----------|--------|------------|---------|----------|-------|-------|
| 1 | | | | | | | | /8 | |
| 2 | | | | | | | | /8 | |
| 3 | | | | | | | | /8 | |
| _..._ | | | | | | | | | |

### Reviewer Notes (SA-3)
```
Overall quality:
Gaps identified:
Recommended follow-up:
GeoJSON-ready: Yes / No / Partial
```

---

---

## SA-4: Circular Economy Extensions 🟤

**Category:** Compost Facilities · Urban Farms · (Animal Feed · Anaerobic Digestion — if found)
**Status:** ⏳ Pending
**Subagent Output File:** _(to be attached after run)_

### Field Completion Checklist
- [ ] `location_name` — all entries have verified names
- [ ] `address` — all entries have full address + ZIP
- [ ] `latitude` / `longitude` — all entries have verified coordinates
- [ ] `process_type` — correctly assigned to: Compost | AnimalFeed | AnaerobicDigestion | UrbanFarm
- [ ] `capacity_tons_month` — estimated capacity for ≥ 50% of entries
- [ ] `accepts_from` — source types listed for ≥ 60%
- [ ] `outputs` — what it produces listed for ≥ 60%
- [ ] `status` — Operational | In Development | Seasonal | Research Needed assigned to all
- [ ] `certifications` — organic/permit status noted where applicable

### Sub-Category Targets
| Sub-Category | Target | Found | Gap |
|-------------|--------|-------|-----|
| Compost Facilities | 4–6 | — | — |
| Urban Farms | 6–8 | — | — |
| Animal Feed Processors | 1–2 | — | — |
| Anaerobic Digestion Plants | 1–2 | — | — |
| **TOTAL** | **12–18** | **—** | **—** |

### Data Quality Evaluation (fill in after review)
| # | Location Name | Address ✓ | Coords ✓ | Type ✓ | Capacity ✓ | Accepts ✓ | Status ✓ | Score | Grade |
|---|--------------|-----------|----------|--------|-----------|----------|----------|-------|-------|
| 1 | | | | | | | | /8 | |
| 2 | | | | | | | | /8 | |
| 3 | | | | | | | | /8 | |
| _..._ | | | | | | | | | |

### Reviewer Notes (SA-4)
```
Overall quality:
Gaps identified:
Recommended follow-up:
GeoJSON-ready: Yes / No / Partial
```

---

---

## Phase 1 — Completion Criteria

Phase 1 is complete when ALL of the following are true:

| Criterion | SA-1 | SA-2 | SA-3 | SA-4 |
|-----------|------|------|------|------|
| Minimum location count met | ⬜ | ⬜ | ⬜ | ⬜ |
| ≥ 80% of entries have verified coordinates | ⬜ | ⬜ | ⬜ | ⬜ |
| ≥ 80% of entries have full addresses | ⬜ | ⬜ | ⬜ | ⬜ |
| All entries have a status field | ⬜ | ⬜ | ⬜ | ⬜ |
| No duplicate locations across subagents | ⬜ | ⬜ | ⬜ | ⬜ |
| Data sources documented | ⬜ | ⬜ | ⬜ | ⬜ |
| Reviewer approved | ⬜ | ⬜ | ⬜ | ⬜ |

**→ When all boxes checked: proceed to Phase 2 (GeoJSON Build)**

---

## Phase 1 — Aggregate Summary (fill in after all subagents complete)

| Metric | Count |
|--------|-------|
| Total locations collected | — |
| High quality (⭐⭐⭐) | — |
| Medium quality (⭐⭐) | — |
| Low quality (⭐) | — |
| Unusable / dropped | — |
| GeoJSON-ready entries | — |
| Entries needing follow-up | — |
| Unique neighborhoods covered | — |
| Atlanta counties covered | — |

---

## Data Sources Reference (for all subagents)

| Source | URL / Method | Best For |
|--------|-------------|---------|
| Atlanta Community Food Bank | acfb.org partner directory | Redistribution nodes |
| Georgia 211 Database | ga.211.org | All categories |
| Feeding America Network | feedingamerica.org | Food banks |
| findhelp.org (Aunt Bertha) | findhelp.org → Atlanta GA | All categories |
| OpenStreetMap Overpass | overpass-turbo.eu | Coordinates, farms |
| USDA Food Access Atlas | ers.usda.gov | Food desert data |
| Georgia Organics | georgiaorganics.org | Urban farms |
| Atlanta Open Data Portal | atlantaga.gov/opendata | General Atlanta data |
| Georgia DFCS office locator | dfcs.georgia.gov | SNAP offices |
| CompostNow | compostnowinc.com | Compost facilities |
| Atlanta Community Fridges | @atlantacommunityfridge | Community fridges |
| Google Maps Places API | (manual search) | Addresses + hours |
| Georgia Department of Ag | agr.georgia.gov | Farm registry |
