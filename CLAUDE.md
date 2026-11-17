# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Alyssa's Cookie Codex: a static Astro site listing every Cookie Run: Kingdom cookie by rarity and personality, with each cookie's backstory. There are two halves: Python scrapers in `scripts/` that produce the data, and the Astro site in `site/` that renders it. There are no tests and no linter.

## Commands

Site (run from `site/`; `node_modules` is not committed):

```bash
npm install
npm run dev       # dev server
npm run build     # static build to site/dist/
npm run preview
```

Data refresh (from the repo root; needs `requests`, and `.venv/` is gitignored, so use uv or pip):

```bash
python scripts/crk_images.py         # portraits -> downloads/crk_cookies/ + manifest.csv
python scripts/build_cookie_data.py  # -> site/src/data/cookies.json, copies images to site/public/cookies/
```

Run them in that order. `build_cookie_data.py` reads `downloads/crk_cookies/manifest.csv` to match images. Both scripts hit live sites (noff.gg, and the cookierunkingdom.fandom.com MediaWiki API) with a 0.5 s delay per cookie. At the end, `build_cookie_data.py` prints coverage stats (missing image, backstory, personality or wiki page, and tag counts), so check that output after a refresh.

## Architecture

- **Single data file.** `site/src/data/cookies.json` (committed) is `{rarityOrder, tags, cookies[]}`, and it is the only data source the site uses. `site/src/lib/data.ts` types it (`Cookie`) and derives everything the pages use: `byRarity`, `rarityOrder` and `tags`, each filtered to values that actually occur, plus `rarityLabel` and `tagSlug`. Edit the generator, not the JSON, unless you are making a deliberate one-off fix that a regeneration would overwrite.
- **Rarity** comes from noff.gg's list page, and `rarityOrder` is sorted rarest first. Each rarity needs a matching `--r-<rarity>` colour variable in `site/src/styles/global.css`. A new rarity without one falls back to `--r-common`.
- **Personality tags** are a fixed vocabulary in `TAGS` in `scripts/build_cookie_data.py`. A tag applies only if one of its keywords appears in the cookie's wiki Personality text. To change tags, edit `TAGS` and rerun the script. Pages are generated per tag at `/personality/<lowercased tag>`.
- **Pages:** `index.astro` is the full shelf grouped by rarity, with a client-side `<script>` that filters by name, rarity and tag without reloading. `cookie/[slug].astro` is the detail page. `personality/[tag].astro` lists the cookies with one tag. `CookieCard.astro` is the card shared by these pages, and `Base.astro` is the layout.
- **Images:** `downloads/` holds the raw scrape and is gitignored. `site/public/cookies/` is the committed copy the site serves, referenced as `/cookies/<file>.webp`.
- Static output only (`output: 'static'` in `astro.config.mjs`); there is no server runtime.
