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
  `assets/images/blog/<slug>/`, and rewrites root-absolute asset URLs to
  relative so the page works without a server.

Figures use the `.svg` variants only.

## Migrating to the live site

Copy `content/blog/genomic-lm-optimization.md` into the OA repo's
`content/blog/`, and the referenced SVGs into
`static/assets/images/blog/genomic-lm-optimization/`. The image paths and figure
conventions already match; set a real `author` first.
