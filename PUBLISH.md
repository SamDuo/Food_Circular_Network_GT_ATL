# Publish AFCN Dashboards

## 1) Build a deploy bundle

From project root:

```powershell
python "Python Script\publish_dashboards.py"
```

This creates a `publish/` folder containing:

- `resources/` dashboards
- `geojson/` data
- `api/config` and `api/config.json` for ArcGIS key config
- `index.html` landing page that links all dashboard/map HTML files

To force a full clean rebuild:

```powershell
python "Python Script\publish_dashboards.py" --clean
```

## 2) Publish on a static host (fastest options)

### Option A: Cloudflare Pages (recommended)

1. Open Cloudflare Pages.
2. Create a new project.
3. Upload the full `publish/` folder as static assets.
4. Deploy.

### Option B: Netlify Drop

1. Open Netlify Drop.
2. Drag the `publish/` folder into the upload area.
3. Netlify gives you a public URL immediately.

## 3) Dashboard URLs after publish

- Landing page with all map links: `/`
- Main dashboard: `/resources/Layers%20%26%20Packages/index.html`
- Surplus map: `/resources/Layers%20%26%20Packages/surplus-map.html`
- Fleet analytics: `/resources/Layers%20%26%20Packages/fleet-analytics.html`
- Campus hub: `/resources/Layers%20%26%20Packages/gt-campus-hub.html`
- GT-FCH preview map: `/resources/Layers%20%26%20Packages/gt_fch_preview.html`
- GT-FCH feature map: `/resources/Layers%20%26%20Packages/gt_fch_map.html`

## 4) Notes

- `gt_fch_preview.html` now uses dynamic host origin (no localhost lock-in).
- `publish_dashboards.py` reads `ARCGIS_API_KEY` from `.env` by default.
- Override key at build time:

```powershell
python "Python Script\publish_dashboards.py" --api-key "YOUR_KEY"
```
