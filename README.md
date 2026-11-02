# History of Art
A static website tracing art history from the Stone Age to today. Live site: https://prashant-mehra.github.io/history-of-art/

## About this repo
Static site (HTML/CSS/JS, no build step needed to view) tracing art history from the Stone Age to today.

- View locally: `python3 -m http.server 8000`
- Content lives in `tools/data_*.py`; regenerate pages with `python3 tools/build.py`.
- Hand-written pages: `eras/prehistoric/**`, `about/`. Everything else is generated.
- Deploy: `.github/workflows/pages.yml` publishes to GitHub Pages on push to `main` (enable Pages → Source: GitHub Actions in repo settings). The expected URL is https://prashant-mehra.github.io/history-of-art/ (sitemap base set in `tools/build.py`).

Images are from Wikimedia Commons (public domain or open licenses); credits are in `tools/images.json` and on the site at `/about/credits/`.
