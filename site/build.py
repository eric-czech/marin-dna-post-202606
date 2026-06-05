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
  * each figure ``<img>`` is then replaced by its SVG *inlined* into the page
    and scrubbed (``inline_figure_svgs`` / ``scrub_svg``) so the charts render
    in the page font, follow the page ink via ``currentColor``, and scale
    responsively — i.e. look drawn directly on the page rather than embedded as
    pictures. This pairs with the web-native rcParams in ``utils.figure_theme``;
  * root-absolute asset URLs (``/css/...``, ``/assets/...``) are rewritten to
    relative so the page works without a server. Navigation/footer links stay
    absolute — they target the live site.

Run with: ``uv run site/build.py``
"""

from __future__ import annotations

import html as html_lib
import re
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


# The page ink the figures are drawn in (utils.figure_theme.INK). Mapped to
# currentColor so axis text/ticks/spines follow the page's text color (and flip
# automatically under a dark theme) instead of being a baked-in near-black.
FIGURE_INK = "#1f1e1b"


def scrub_svg(svg: str, alt: str, prefix: str) -> str:
    """Turn a matplotlib SVG file into an inline-ready, page-native fragment.

    The figures are authored with ``svg.fonttype='none'`` and page-ink colors
    (see ``utils.figure_theme``); this strips the standalone-document cruft and
    rewires the SVG so, once dropped into the page DOM, it renders like a chart
    drawn directly on the page:

      * drop the XML prolog / DOCTYPE / ``<metadata>`` (illegal/needless inline);
      * drop the fixed ``pt`` width/height so the ``viewBox`` drives responsive
        sizing (the CSS sets ``width:100%``);
      * map the page-ink color to ``currentColor`` so axes/text follow the
        page's text color;
      * drop matplotlib's bundled font-family so labels inherit the page font;
      * namespace every id/reference with a per-figure prefix so inlining many
        SVGs into one document can't collide on ids (which would break clips);
      * add ``role="img"`` + a ``<title>`` from the alt text for accessibility.
    """
    svg = svg[svg.index("<svg"):]  # drop <?xml ...?> + <!DOCTYPE ...>
    svg = re.sub(r"<metadata>.*?</metadata>\s*", "", svg, flags=re.DOTALL)
    # viewBox carries the aspect ratio; remove the absolute pt dimensions.
    svg = re.sub(r'\swidth="[\d.]+pt"\sheight="[\d.]+pt"', "", svg, count=1)
    # Theme-reactive ink + page font.
    svg = svg.replace(FIGURE_INK, "currentColor")
    svg = re.sub(r'font-family: [^;"]*', "font-family: inherit", svg)
    # Namespace ids and their references (id=, href="#", url(#...)).
    svg = re.sub(r'id="([^"]+)"', rf'id="{prefix}\1"', svg)
    svg = re.sub(r'href="#([^"]+)"', rf'href="#{prefix}\1"', svg)
    svg = re.sub(r"url\(#([^)]+)\)", rf"url(#{prefix}\1)", svg)
    # Accessible name + a hook for the figure-background CSS.
    svg = svg.replace("<svg ", '<svg role="img" class="figure-svg" ', 1)
    close = svg.index(">") + 1
    return svg[:close] + f"<title>{html_lib.escape(alt)}</title>" + svg[close:]


_FIG_IMG = re.compile(
    r'<img\s+src="(assets/images/blog/[^"]+\.svg)"\s+alt="([^"]*)"\s*/>'
)


def inline_figure_svgs(html: str, out_root: Path) -> str:
    """Replace each figure ``<img src=...svg>`` with the inlined, scrubbed SVG.

    Reads from the already-copied files under ``out_root`` so the page is a
    single self-contained document whose charts inherit the page font/theme. A
    missing file leaves the ``<img>`` in place as a graceful fallback.
    """

    def repl(m: re.Match) -> str:
        src, alt = m.group(1), m.group(2)
        svg_path = out_root / src
        if not svg_path.exists():
            return m.group(0)
        prefix = re.sub(r"[^A-Za-z0-9]+", "-", Path(src).stem) + "-"
        return scrub_svg(svg_path.read_text(), html_lib.unescape(alt), prefix)

    return _FIG_IMG.sub(repl, html)


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

    html = rewrite_html_paths(html)
    html = inline_figure_svgs(html, OUT)
    (OUT / "index.html").write_text(html)
    print(f"Built {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
