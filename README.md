# Choke Slam Wrestling

**Live:** [cptspaulding1980.github.io/choke-slam-wrestling](https://cptspaulding1980.github.io/choke-slam-wrestling/)

Static site for the Choke Slam Wrestling league in Fire Pro Wrestling World (MotW mod).

## Build

```bash
npm install
npm run build
```

Generates the site into `docs/`. The build pipeline:
- **Eleventy** (11ty) — static site generator
- **SASS** — CSS preprocessing (→ `docs/styles/`)
- **Markdown-it** — Markdown rendering with plugins (anchors, footnotes, math, wikilinks)

## Deploy

Push to `main` branch. GitHub Pages serves from `/docs`. No special configuration needed.

## Structure

```
.
├── .eleventy.js              # Eleventy config (path prefix, image transforms, plugins)
├── package.json              # Dependencies & build scripts
├── build:eleventy            # Production build (ELEVENTY_ENV=prod)
├── build:sass                # SCSS → compressed CSS
├── obsidian-wikilink-image-plugin.js  # Obsidian wikilink image handling
├── src/
│   ├── site/                 # Eleventy source (layouts, includes, styles, content)
│   └── helpers/              # Utility modules
└── docs/                     # Generated static site (committed, served by GitHub Pages)
    ├── home/                 # Home page
    ├── events/               # Event pages (ChokeSlamMania etc.)
    ├── wrestler/             # Wrestler profiles (~500+)
    ├── championships/        # Title histories
    ├── teams/                # Tag teams & stables
    ├── manager/              # Manager profiles
    ├── referees/             # Referee profiles
    ├── statistiken/          # Statistics
    ├── audio/                # Entrance themes
    ├── img/                  # Images (optimized WebP/JPEG)
    ├── styles/               # Compiled CSS
    ├── feed.xml              # RSS feed
    └── sitemap.xml           # Sitemap
```
