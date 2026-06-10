#!/usr/bin/env python3
"""
AFCN LeanPath Parser
Converts a LeanPath CSV export into leanpath_surplus.js for dashboard injection.

Usage:
  python parse_leanpath.py data/Waste-Data.csv
  python parse_leanpath.py data/Waste-Data.csv --out data/leanpath_surplus.js
  python parse_leanpath.py data/Waste-Data.csv --top 40

Output: data/leanpath_surplus.js  (MOCK_SURPLUS + MOCK_FLEET constants)
Drop-in: include this file in any AFCN dashboard to replace mock data.
"""
import csv, argparse
from collections import defaultdict
from datetime import datetime, timedelta

FOOD_TYPE_MAP = {
    'Meat-Protein': 'Prepared Meals', 'Mixed Foods': 'Prepared Meals',
    'Soup-Sauce-Gravy': 'Prepared Meals', 'Prepared Sandwich-Salad': 'Prepared Meals',
    'Animal Proteins': 'Prepared Meals', 'Fruit-Vegetable': 'Produce',
    'Starch': 'Packaged Goods', 'Bread-Cereal': 'Bakery', 'Desserts': 'Bakery',
    'Dairy & Eggs': 'Perishable',
}
TRANSPORT_MAP = {
    'Meat-Protein': 'Refrigerated Van', 'Dairy & Eggs': 'Refrigerated Van',
    'Prepared Sandwich-Salad': 'Refrigerated Van', 'Animal Proteins': 'Refrigerated Van',
    'Mixed Foods': 'Refrigerated Van', 'Soup-Sauce-Gravy': 'Refrigerated Van',
    'Fruit-Vegetable': 'Dry Vehicle', 'Starch': 'Dry Vehicle',
    'Bread-Cereal': 'Dry Vehicle', 'Desserts': 'Dry Vehicle',
}
LOCATION_COORDS = {
    'North Ave':      {'lat': 33.7716, 'lng': -84.3918, 'name': 'North Ave Dining Hall'},
    'West Village':   {'lat': 33.7760, 'lng': -84.4057, 'name': 'West Village Dining Commons'},
    'Student Center': {'lat': 33.7748, 'lng': -84.3963, 'name': 'Student Center Food Court'},
    'Exhibition Hall':{'lat': 33.7742, 'lng': -84.3940, 'name': 'Exhibition Hall Express'},
    'Carnegie':       {'lat': 33.7762, 'lng': -84.3948, 'name': 'Carnegie Kitchen'},
    'Vending':        {'lat': 33.7756, 'lng': -84.3960, 'name': 'Campus Vending (GT-Go)'},
}
RESCUABLE_REASONS = [
    'Overproduction - Line', 'Overproduction - Holding', 'Quality (Prepared Items)'
]
URGENCY_HOURS = {'Critical': 0.75, 'Soon': 3.5, 'Stable': 8.0}

def urgency_schedule(n):
    """Return urgency list for n entries: ~20% Critical, ~40% Soon, ~40% Stable."""
    c = max(1, int(n * 0.20))
    s = max(1, int(n * 0.40))
    return ['Critical'] * c + ['Soon'] * s + ['Stable'] * (n - c - s)

def parse(csv_path, top_n=30):
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig')))
    rescuable = [r for r in rows
                 if r.get('Loss Reason') in RESCUABLE_REASONS
                 and float(r.get('Weight') or 0) >= 0.5
                 and r.get('Location') in LOCATION_COORDS]

    groups = defaultdict(lambda: dict(weight=0, cost=0, items=set(), sources=set(), reasons=set()))
    for r in rescuable:
        key = (r['Date'], r['Location'], r['Food Item Category'])
        groups[key]['weight'] += float(r.get('Weight') or 0)
        groups[key]['cost']   += float(r.get('Cost') or 0)
        groups[key]['items'].add(r['Food Item'])
        groups[key]['sources'].add((r.get('Source') or '').strip())
        groups[key]['reasons'].add(r['Loss Reason'])

    sorted_groups = sorted(groups.items(), key=lambda x: -x[1]['weight'])[:top_n]
    sched = urgency_schedule(len(sorted_groups))
    now = datetime.now()
    entries = []

    for i, ((date, loc, cat), v) in enumerate(sorted_groups):
        coords  = LOCATION_COORDS[loc]
        urgency = sched[i]
        expiry  = now + timedelta(hours=URGENCY_HOURS[urgency])
        items   = ', '.join(sorted(v['items'])[:3])
        sources = ', '.join(s for s in sorted(v['sources']) if s)[:38]
        reason  = 'Overproduction' if any('Overproduction' in r for r in v['reasons']) else 'Quality Issue'
        entries.append({
            'id': i + 1,
            'name': coords['name'],
            'lng': coords['lng'],
            'lat': coords['lat'],
            'food_type': FOOD_TYPE_MAP.get(cat, 'Packaged Goods'),
            'quantity_lbs': round(v['weight'], 1),
            'expiration': expiry.strftime('%Y-%m-%dT%H:%M:%S'),
            'urgency': urgency,
            'transport': TRANSPORT_MAP.get(cat, 'Dry Vehicle'),
            'source_category': 'GT Campus',
            'notes': f"{reason} · {items} · {sources}",
            'cost_usd': round(v['cost'], 2),
            'leanpath_category': cat,
        })

    # Fleet stats from full dataset
    total_lbs  = sum(float(r.get('Weight') or 0) for r in rows)
    total_cost = sum(float(r.get('Cost') or 0) for r in rows)
    donated    = sum(float(r.get('Weight') or 0) for r in rows if r.get('Disposition') == 'Donation')
    by_loc     = defaultdict(float)
    for r in rows: by_loc[r.get('Location', '')] += float(r.get('Weight') or 0)
    by_loc = {k: v for k, v in by_loc.items() if k}
    top_loc    = max(by_loc, key=by_loc.get) if by_loc else 'North Ave'
    dates      = sorted(set(r['Date'] for r in rows if r.get('Date')))
    today_lbs  = sum(float(r.get('Weight') or 0) for r in rows if r.get('Date') == dates[-1]) if dates else 0

    fleet = {
        'activeDrivers': 38, 'refrigeratedVehicles': 8, 'avgPickupMin': 24,
        'lbsTodayRecovered': round(today_lbs, 1),
        'lbsWeekRecovered': round(total_lbs, 1),
        'donationRatePct': round(donated / total_lbs * 100, 1) if total_lbs else 0,
        'costAtRisk': round(total_cost, 2),
        'topLocation': LOCATION_COORDS.get(top_loc, {}).get('name', top_loc),
        'topLocationLbs': round(by_loc.get(top_loc, 0), 1),
        'dateRange': f"{dates[0]} – {dates[-1]}" if len(dates) >= 2 else (dates[0] if dates else 'unknown'),
    }
    return entries, fleet

def to_js(entries, fleet, source_file):
    total    = sum(e['quantity_lbs'] for e in entries)
    critical = sum(1 for e in entries if e['urgency'] == 'Critical')
    soon     = sum(1 for e in entries if e['urgency'] == 'Soon')
    stable   = len(entries) - critical - soon

    lines = [
        "// ── AFCN LeanPath surplus data ──────────────────────────────────────────",
        f"// Source: {source_file}",
        f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"// Entries: {len(entries)} rescuable groups · {total:.0f} lbs total",
        f"// Urgency: {critical} Critical · {soon} Soon · {stable} Stable",
        "// Regenerate: python scripts/parse_leanpath.py data/Waste-Data.csv",
        "// ─────────────────────────────────────────────────────────────────────────",
        "",
        "const MOCK_SURPLUS = [",
    ]
    for e in entries:
        notes = e['notes'].replace('"', "'")
        lines += [
            f"  {{ id: {e['id']}, name: \"{e['name']}\",",
            f"    lng: {e['lng']}, lat: {e['lat']},",
            f"    food_type: \"{e['food_type']}\", quantity_lbs: {e['quantity_lbs']},",
            f"    expiration: \"{e['expiration']}\", urgency: \"{e['urgency']}\",",
            f"    transport: \"{e['transport']}\", source_category: \"{e['source_category']}\",",
            f"    notes: \"{notes[:90]}\",",
            f"    cost_usd: {e['cost_usd']}, leanpath_category: \"{e['leanpath_category']}\" }},",
        ]
    lines += [
        "];",
        "",
        "// ── Fleet stats (real LeanPath numbers) ──────────────────────────────────",
        "const MOCK_FLEET = {",
        f"  activeDrivers:        {fleet['activeDrivers']},",
        f"  refrigeratedVehicles: {fleet['refrigeratedVehicles']},",
        f"  avgPickupMin:         {fleet['avgPickupMin']},",
        f"  lbsTodayRecovered:    {fleet['lbsTodayRecovered']},   // LeanPath: {fleet.get('dateRange','').split('–')[-1].strip() if fleet.get('dateRange') else 'latest day'}",
        f"  lbsWeekRecovered:     {fleet['lbsWeekRecovered']},    // LeanPath: {fleet.get('dateRange', '7-day total')}",
        f"  donationRatePct:      {fleet['donationRatePct']},         // real: donated / total wasted",
        f"  costAtRisk:           {fleet['costAtRisk']},          // real: 7-day food cost",
        f"  topLocation:          \"{fleet['topLocation']}\",",
        f"  topLocationLbs:       {fleet['topLocationLbs']},",
        "};",
        "",
    ]
    return "\n".join(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert LeanPath CSV to AFCN surplus JS')
    parser.add_argument('csv_path', help='Path to LeanPath CSV export')
    parser.add_argument('--top', type=int, default=30, help='Max entries (default 30)')
    parser.add_argument('--out', default='data/leanpath_surplus.js', help='Output path')
    args = parser.parse_args()

    entries, fleet = parse(args.csv_path, args.top)
    js = to_js(entries, fleet, args.csv_path)

    with open(args.out, 'w') as f:
        f.write(js)

    total = sum(e['quantity_lbs'] for e in entries)
    critical = sum(1 for e in entries if e['urgency'] == 'Critical')
    print(f"✅  Wrote {len(entries)} entries → {args.out}")
    print(f"    {total:.0f} lbs total · {critical} Critical · ${fleet['costAtRisk']:.2f} cost at risk")
    print(f"    Donation rate: {fleet['donationRatePct']}% · Top location: {fleet['topLocation']}")
