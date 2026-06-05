# Post build

Renders the blog post to [`../post/index.html`](../post/) using templates and
styles vendored from the Open Athena site
([Open-Athena/open-athena.github.io](https://github.com/Open-Athena/open-athena.github.io)),
so the local preview matches the live blog and the markdown ports over cleanly.

## Build

```
uv run site/build.py
```

Outputs a self-contained `post/` web root (`index.html`, `css/`, `assets/`).
Open `post/index.html` directly (`file://`) or serve it:

```
cd post && python3 -m http.server 8765   # http://localhost:8765
```

## Layout

- `content/blog/genomic-lm-optimization.md` — the post (frontmatter + body).
  Tracks `docs/outline.md`; figures embedded as `![...]()` + `**Figure N:** ...`.
- `templates/`, `static/css/style.css`, `static/assets/` — vendored OA chrome
  (templates, stylesheet, Herbik font, logo/footer images).
- `oa_build.py` — verbatim copy of the upstream `build.py`; `build.py` imports its
  markdown-rendering helpers for parity.
- `build.py` — renders the one post, copies `../figures/*.svg` into
  `assets/images/blog/<slug>/`, rewrites root-absolute asset URLs to relative,
  and **inlines + scrubs** each figure SVG into the page (see below).

Figures use the `.svg` variants only.

## Web-native figures

The figures are authored to look drawn directly on the page rather than dropped
in as pictures, via two cooperating pieces:

- `../src/utils/figure_theme.py` — matplotlib rcParams applied to every figure
  (imported for its side effect by `utils.savefig`): `svg.fonttype='none'` (text
  stays as real `<text>`), top/right spines off, and page-ink colors.
- `build.py` (`scrub_svg` / `inline_figure_svgs`) — replaces each figure
  `<img src=...svg>` with the SVG inlined into the page DOM, then: drops the XML
  prolog/`<metadata>` and the fixed `pt` size (so the `viewBox` drives
  responsive width), maps the page ink to `currentColor`, drops the bundled
  font-family so labels inherit the page font, and namespaces every id so
  inlining ten SVGs into one document can't collide.

Inlining (not `<img>`) is what lets the page font and theme reach inside the
SVG; an `<img>`-embedded SVG renders in an isolated document that can't see
either. Regenerate figures (`uv run python -m figures`, plus the two wandb-fed
appendix scripts) after any theme change.

## Migrating to the live site

Copy `content/blog/genomic-lm-optimization.md` into the OA repo's
`content/blog/`, and the referenced SVGs into
`static/assets/images/blog/genomic-lm-optimization/`. The image paths and figure
conventions already match; set a real `author` first.

Note: the on-disk SVGs are raw matplotlib output (page-ink hex, bundled font,
`pt` dimensions) — the page-native treatment happens at build time in
`scrub_svg`/`inline_figure_svgs`. To get the same look on the live site, port
that inline+scrub step into the upstream generator; otherwise the figures fall
back to `<img>` rendering (still fine, just not font/theme-reactive).
