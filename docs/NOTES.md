# Notes

- 2026-11-08 Repo policy requires actions pinned to full commit SHAs; tag refs (@v5) make the build job fail at setup. deploy.yml now pins SHAs with the tag as a trailing comment.
- 2026-11-08 On GitHub Pages `pd.read_csv(url)` fails with BadGzipFile: Pages sends Content-Encoding: gzip, the browser already decompresses, and pandas gunzips again. Read URLs via urllib into BytesIO first.
- 2026-11-08 First Pages deploy stayed "in progress" (yellow) for ~8 min in deploy-pages before succeeding; no error, just slow first-time provisioning.
- 2026-11-08 marimo html-wasm only auto-installs Pyodide-bundled packages; others (e.g. folium) must be listed in the notebook's PEP 723 `# /// script` header or the setup cell fails with ModuleNotFoundError.
- 2026-11-08 `import branca` is not resolved in WASM; use `folium.LinearColormap` (re-exported by folium) instead.
- 2026-11-08 html-wasm export does not bundle local modules, so helper functions live in dashboard.py as `@app.function` cells instead of one-function-per-file under src/.
- 2026-11-08 Data must sit in `public/` and be read via `mo.notebook_location() / "public"`; the export copies `public/` into `_site/`.
- 2026-11-08 marimo export ships a CLAUDE.md asset; the deploy workflow deletes it from `_site/` before upload.
- 2026-11-08 CartoDB tiles in folium now require an API key; the map uses OpenStreetMap tiles.
- 2026-11-08 GitHub Pages enabled with build_type=workflow; site URL https://fneira-geo.github.io/sitio/.
- 2026-11-08 Local preview: `uv run marimo edit dashboard.py`; WASM check: export to `_site/` and serve with `python -m http.server --directory _site`.
