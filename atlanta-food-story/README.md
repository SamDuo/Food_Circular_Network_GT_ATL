# Atlanta Food Story — Static Deploy Bundle

This directory is a self-contained static website. Drop it into any of the
following hosts and you have a public URL the story can be QR-coded to.

## One-line deploy options

### Netlify Drop (zero signup, instant)
1. Go to https://app.netlify.com/drop
2. Drag the entire `dist/` folder onto the page.
3. You get a URL like `https://lucent-bunny-7f3a92.netlify.app` immediately.
4. (Optional) Sign in to claim it and rename it.

### Cloudflare Pages (free, custom subdomain on `*.pages.dev`)
1. Install Wrangler once: `npm install -g wrangler` then `wrangler login`.
2. From the project root: `wrangler pages deploy dist --project-name atl-food-story`
3. URL: `https://atl-food-story.pages.dev`

### GitHub Pages (free if the repo is public)
1. Commit `dist/` to a branch.
2. In repo Settings → Pages, set source to that branch / `dist` folder.
3. URL: `https://<user>.github.io/<repo>/`

## After deploy

The Mapbox public token is in `config.json`. Mapbox public tokens (`pk.…`)
are designed to be exposed in client-side code — restrict the token by URL
on https://account.mapbox.com/access-tokens/ to your deployed domain so it
can't be lifted and reused.

## Updating the data

1. Re-run `python scripts/spatial_analysis.py` in the project root to refresh
   `data/analysis_findings.json`.
2. Re-run `python scripts/build_dist.py` to rebuild this folder.
3. Re-deploy.
