#!/usr/bin/env python3
"""Render the Bolinas DNA post to ``post/index.html`` using vendored Open Athena
site templates and styles.

This mirrors the static-site generator at
github.com/Open-Athena/open-athena.github.io: the post is a Markdown file with
frontmatter (``site/content/blog/<slug>.md``) rendered through the same
``blog_post.html`` / ``base.html`` templates and ``style.css``. Keeping the
markdown + conventions identical means the post drops straight into that repo's
``content/blog/`` later.

Differences from the upstream build, all to keep this a single self-contained
page that previews locally (``file://`` or any static server):

  * only the one post is rendered, into ``post/`` as its own web root;
  * figure SVGs are copied from this repo's ``figures/`` into
    ``assets/images/blog/<slug>/`` (preserving the ``appendix/`` subpath);
  * root-absolute asset URLs (``/css/...``, ``/assets/...``) are rewritten to
    relative so the page works without a server. Navigation/footer links stay
    absolute — they target the live site.

Run with: ``uv run site/build.py``
"""

from __future__ import annotations

import shutil
from pathlib import Path

import frontmatter
import mistune
import yaml
from jinja2 import Environment, FileSystemLoader

# Reuse the upstream rendering helpers verbatim (vendored as oa_build.py) so the
# HTML matches what the live site would produce.
from oa_build import (
    add_footnote_commas,
    expand_plotly_shortcodes,
    generate_bibtex,
    protect_math,
    restore_math,
    wrap_display_math,
    wrap_figures,
)

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
TEMPLATES = SITE / "templates"
STATIC = SITE / "static"
CONTENT = SITE / "content"
FIGURES = REPO / "figures"
OUT = REPO / "post"

POST_FILE = CONTENT / "blog" / "genomic-lm-optimization.md"


def render_markdown(text: str, slug: str) -> tuple[str, bool]:
    """Markdown -> post body HTML, applying the same passes as the live build."""
    text, has_plotly = expand_plotly_shortcodes(text, slug)
    protected, math_store = protect_math(text)
    md = mistune.create_markdown(escape=False, plugins=["footnotes", "table"])
    raw_html = restore_math(md(protected), math_store)
    body = add_footnote_commas(wrap_figures(wrap_display_math(raw_html)))
    return body, has_plotly


def rewrite_html_paths(html: str) -> str:
    """Make root-absolute asset references relative to post/index.html."""
    return (
        html.replace('href="/css/', 'href="css/')
        .replace('href="/assets/', 'href="assets/')
        .replace('src="/assets/', 'src="assets/')
    )


def main() -> None:
    config = yaml.safe_load((CONTENT / "config.yaml").read_text())
    post = frontmatter.load(POST_FILE)
    meta = dict(post.metadata)
    slug = meta.get("slug", POST_FILE.stem)

    body, has_plotly = render_markdown(post.content, slug)
    meta["body"] = body
    if has_plotly:
        meta["plotly"] = True
    meta["bibtex"] = generate_bibtex(meta, config.get("url", ""))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=False)
    tmpl = env.get_template("blog_post.html")
    # Truthy blog_posts so the nav renders the Blog link.
    html = tmpl.render(config=config, post=meta, blog_posts=[meta])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # CSS lives in post/css/, so its own /assets/... urls become ../assets/...
    (OUT / "css").mkdir()
    css = (STATIC / "css" / "style.css").read_text()
    css = css.replace("url('/assets/", "url('../assets/").replace(
        'url("/assets/', 'url("../assets/'
    )
    (OUT / "css" / "style.css").write_text(css)

    shutil.copytree(STATIC / "assets", OUT / "assets")

    # Figure SVGs -> assets/images/blog/<slug>/ (mirrors the live image dir
    # convention; appendix/ subpath preserved).
    fig_dir = OUT / "assets" / "images" / "blog" / slug
    fig_dir.mkdir(parents=True, exist_ok=True)
    for svg in sorted(FIGURES.rglob("*.svg")):
        dest = fig_dir / svg.relative_to(FIGURES)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg, dest)

    (OUT / "index.html").write_text(rewrite_html_paths(html))
    print(f"Built {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
