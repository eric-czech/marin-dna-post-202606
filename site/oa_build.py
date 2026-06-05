#!/usr/bin/env python3
"""Static site generator for openathena.ai"""

import re
import shutil
from pathlib import Path

import frontmatter
import mistune
import yaml
from jinja2 import Environment, FileSystemLoader


def wrap_figures(html: str) -> str:
    """Convert <p><img ...></p> followed by <p><strong>Figure ...</p> into <figure>."""
    return re.sub(
        r"<p>(<img\s[^>]+>)</p>\s*<p>(<strong>Figure\s.+?)</p>",
        r"<figure>\1<figcaption>\2</figcaption></figure>",
        html,
        flags=re.DOTALL,
    )


def add_footnote_commas(html: str) -> str:
    """Insert comma separators between consecutive footnote-ref sups."""
    return re.sub(
        r"(</sup>)(<sup class=\"footnote-ref\")",
        r'\1<span class="fn-comma">,</span>\2',
        html,
    )


def protect_math(text: str) -> tuple[str, list[str]]:
    """Replace $...$ and $$...$$ with placeholders to protect from markdown processing."""
    store: list[str] = []

    def _sub(m: re.Match) -> str:
        math = m.group(0)
        # Unescape markdown escapes that appear inside math (e.g. \* → *)
        math = math.replace("\\*", "*")
        store.append(math)
        return f"MATHPH{len(store) - 1}ENDMATHPH"

    # Display math first, then inline
    text = re.sub(r"\$\$(.+?)\$\$", _sub, text, flags=re.DOTALL)
    text = re.sub(r"(?<!\$)\$(?!\$)([^\n$]+?)\$(?!\$)", _sub, text)
    return text, store


def restore_math(html: str, store: list[str]) -> str:
    """Restore LaTeX expressions from placeholders."""
    for i, original in enumerate(store):
        html = html.replace(f"MATHPH{i}ENDMATHPH", original)
    return html


def expand_plotly_shortcodes(text: str, slug: str) -> tuple[str, bool]:
    """Replace `{{plotly: file.json | title=... | caption=...}}` shortcodes.

    Path resolution: `file.json` is resolved against
    `/assets/images/blog/<slug>/`. A leading `/` gives an absolute path.

    Optional attributes (pipe-separated, double-quoted values):
      - `title="..."`   rendered inside the outer Taupe frame, above the plot
      - `caption="..."` rendered outside both frames, below the plot
      - `height="560"`  min-height (px) for the plotly container, overrides
                        the template CSS default; use for multi-subplot
                        figures that need extra vertical room

    Layout: the figure sits in a box-in-box frame — an outer Taupe (#BDB1A5)
    card with optional title, containing an inner #C4B9AE card with the
    plotly hydration div. The caption renders below both frames as plain
    body copy.

    Returns (text, found). `found` tells the caller whether to load
    plotly.js on the page.
    """
    found = False

    # Frame colors are hard-coded brand hexes. Font/ink for the title pull
    # from the site's CSS variables so any future font or text-color change
    # in style.css propagates here automatically. The caption is rendered
    # as a plain <figcaption> and intentionally carries no inline style,
    # so the site's existing `.blog-post-content figcaption` rule owns it.
    outer_style = "background-color:#d0c1b3;padding: 1rem;border-radius:14px;"
    inner_style = (
        "background-color:#f1e8df;padding: 0;border-radius:10px;"
    )
    title_style = (
        "font-family:var(--font-heading);color:var(--text);"
        "font-size:1.05rem;font-weight:600;letter-spacing:0.01em;"
        "text-align:center;"
    )
    block_style = "margin:1.75rem 0;"

    def _parse_attrs(segments: list[str]) -> dict:
        attrs: dict = {}
        for seg in segments:
            for k, v in re.findall(r'([\w-]+)\s*=\s*"([^"]*)"', seg):
                attrs[k] = v
        return attrs

    def _sub(m: re.Match) -> str:
        nonlocal found
        found = True
        body = m.group(1).strip()
        parts = [p.strip() for p in body.split("|")]
        path = parts[0]
        if not path.startswith("/"):
            path = f"/assets/images/blog/{slug}/{path}"

        attrs = _parse_attrs(parts[1:])
        title = attrs.get("title", "").strip()
        caption = attrs.get("caption", "").strip()
        height = attrs.get("height", "").strip()
        mobile = attrs.get("mobile", "").strip()

        # Optional per-figure min-height override. The template CSS sets
        # `.plotly-figure { min-height: 420px }`; multi-subplot figures
        # need more vertical room and pass their desired size here.
        fig_style = f"min-height:{int(height)}px;" if height.isdigit() else ""
        # Optional mobile-specific JSON variant. Same path resolution as the
        # main `path` (relative → /assets/images/blog/<slug>/).
        if mobile and not mobile.startswith("/"):
            mobile = f"/assets/images/blog/{slug}/{mobile}"
        mobile_attr = f' data-plotly-src-mobile="{mobile}"' if mobile else ""
        figure_div = (
            f'<div class="plotly-figure" data-plotly-src="{path}"'
            + mobile_attr
            + (f' style="{fig_style}"' if fig_style else "")
            + "></div>"
        )
        title_html = (
            f'<div class="plotly-frame-title" style="{title_style}">{title}</div>'
            if title
            else ""
        )
        caption_html = f"<figcaption>{caption}</figcaption>" if caption else ""

        return (
            f'<figure class="plotly-figure-block" style="{block_style}">'
            f'<div class="plotly-frame-outer" style="{outer_style}">'
            f"{title_html}"
            f'<div class="plotly-frame-inner" style="{inner_style}">'
            f"{figure_div}"
            f"</div></div>"
            f"{caption_html}"
            f"</figure>"
        )

    text = re.sub(r"\{\{\s*plotly:\s*([^}]+?)\s*\}\}", _sub, text)
    return text, found


def generate_bibtex(meta: dict, site_url: str) -> str:
    """Build a BibTeX @misc entry for a blog post from its frontmatter."""
    author = str(meta.get("author", "")).strip()
    parts = author.split()
    last = parts[-1] if parts else "anon"
    first = " ".join(parts[:-1])
    author_fmt = f"{last}, {first}" if first else last
    date = meta["date"]
    year = date.year
    month = date.strftime("%b").lower()
    slug = meta.get("slug", "")
    title = meta.get("title", "")
    key = f"{last.lower()}{year}_{slug.replace('-', '_')}"
    url = f"{site_url.rstrip('/')}/blog/{slug}/"
    return (
        f"@misc{{{key},\n"
        f"  author = {{{author_fmt}}},\n"
        f"  title = {{{title}}},\n"
        f"  year = {{{year}}},\n"
        f"  month = {{{month}}},\n"
        f"  howpublished = {{\\url{{{url}}}}},\n"
        f"  note = {{Open Athena Blog}}\n"
        f"}}"
    )


def wrap_display_math(html: str) -> str:
    """Wrap consecutive <p>$$...$$</p> blocks in <div class="math-block">."""
    html = re.sub(
        r"<p>\$\$.*?\$\$</p>",
        lambda m: m.group(0).replace("\n", " "),
        html,
        flags=re.DOTALL,
    )
    lines = html.split("\n")
    out = []
    in_block = False
    for line in lines:
        is_math = line.strip().startswith("<p>$$") and line.strip().endswith("$$</p>")
        if is_math and not in_block:
            out.append('<div class="math-block">')
            in_block = True
        elif not is_math and in_block:
            out.append("</div>")
            in_block = False
        out.append(line)
    if in_block:
        out.append("</div>")
    return "\n".join(out)


ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_blog_posts() -> list[dict]:
    blog_dir = CONTENT / "blog"
    if not blog_dir.exists():
        return []
    posts = []
    for md_file in blog_dir.glob("*.md"):
        post = frontmatter.load(md_file)
        meta = dict(post.metadata)
        if not meta.get("published", False):
            continue
        content, has_plotly = expand_plotly_shortcodes(
            post.content, meta.get("slug", md_file.stem)
        )
        if has_plotly:
            meta["plotly"] = True
        protected, math_store = protect_math(content)
        md = mistune.create_markdown(escape=False, plugins=["footnotes", "table"])
        raw_html = restore_math(md(protected), math_store)
        meta["body"] = add_footnote_commas(wrap_figures(wrap_display_math(raw_html)))
        posts.append(meta)
    posts.sort(key=lambda p: p.get("date"), reverse=True)
    return posts


def load_projects() -> list[dict]:
    projects_dir = CONTENT / "projects"
    projects = []
    for md_file in sorted(projects_dir.glob("*.md")):
        post = frontmatter.load(md_file)
        project = dict(post.metadata)
        project["body"] = mistune.html(post.content)
        projects.append(project)
    projects.sort(key=lambda p: p.get("order", 999))
    return projects


def build():
    # Clean dist
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # Copy static files
    if STATIC.exists():
        shutil.copytree(STATIC / "css", DIST / "css", dirs_exist_ok=True)
        if (STATIC / "js").exists():
            shutil.copytree(STATIC / "js", DIST / "js", dirs_exist_ok=True)
        shutil.copytree(STATIC / "assets", DIST / "assets", dirs_exist_ok=True)
        if (STATIC / "CNAME").exists():
            shutil.copy2(STATIC / "CNAME", DIST / "CNAME")
        if (STATIC / "admin").exists():
            shutil.copytree(STATIC / "admin", DIST / "admin", dirs_exist_ok=True)

    # Load content
    config = load_yaml(CONTENT / "config.yaml")
    homepage = load_yaml(CONTENT / "homepage.yaml")
    team = load_yaml(CONTENT / "about" / "team.yaml")
    faq = load_yaml(CONTENT / "about" / "faq.yaml")
    for item in faq["faqs"]:
        item["answer_html"] = mistune.html(item["answer"])
    projects = load_projects()
    blog_posts = load_blog_posts()
    site_url = config.get("url", "")
    for post in blog_posts:
        post["bibtex"] = generate_bibtex(post, site_url)
    # Collect testimonials from project collaborators, ordered by homepage.yaml
    all_quoted = {}
    for p in projects:
        for c in p.get("collaborators", []):
            if c.get("quote"):
                all_quoted[c["name"]] = {
                    "name": c["name"],
                    "title": c.get("title", ""),
                    "photo": c.get("photo", ""),
                    "quote": c["quote"],
                    "institution": c.get("institution", ""),
                }
    testimonial_names = homepage.get("testimonials", [])
    testimonials = [
        all_quoted[name] for name in testimonial_names if name in all_quoted
    ]

    # Setup Jinja
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=False)

    # Build homepage
    featured_slugs = homepage.get("featured_projects", [])
    featured = [p for p in projects if p["slug"] in featured_slugs]
    featured.sort(key=lambda p: featured_slugs.index(p["slug"]))

    tmpl = env.get_template("homepage.html")
    html = tmpl.render(
        config=config,
        homepage=homepage,
        featured_projects=featured,
        projects=projects,
        blog_posts=blog_posts,
        testimonials=testimonials,
    )
    (DIST / "index.html").write_text(html)

    # Build projects index
    tmpl = env.get_template("projects.html")
    html = tmpl.render(config=config, projects=projects, blog_posts=blog_posts)
    projects_dir = DIST / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    (projects_dir / "index.html").write_text(html)

    # Build each project detail page
    tmpl = env.get_template("project_detail.html")
    for project in projects:
        project_dir = projects_dir / project["slug"]
        project_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl.render(config=config, project=project, blog_posts=blog_posts)
        (project_dir / "index.html").write_text(html)

    # Build blog index
    tmpl = env.get_template("blog.html")
    html = tmpl.render(config=config, posts=blog_posts, blog_posts=blog_posts)
    blog_dir = DIST / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)
    (blog_dir / "index.html").write_text(html)

    # Build each blog post page
    tmpl = env.get_template("blog_post.html")
    for post in blog_posts:
        post_dir = blog_dir / post["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)
        html = tmpl.render(config=config, post=post, blog_posts=blog_posts)
        (post_dir / "index.html").write_text(html)

    # Build legal pages (privacy policy, terms of use)
    legal_tmpl = env.get_template("legal.html")
    for md_file in ["privacy-policy.md", "terms.md"]:
        post = frontmatter.load(CONTENT / md_file)
        page = dict(post.metadata)
        page["body"] = mistune.html(post.content)
        page_dir = DIST / page["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        html = legal_tmpl.render(config=config, page=page, blog_posts=blog_posts)
        (page_dir / "index.html").write_text(html)

    # Build about page
    tmpl = env.get_template("about.html")
    html = tmpl.render(config=config, team=team, faq=faq, blog_posts=blog_posts)
    about_dir = DIST / "about"
    about_dir.mkdir(parents=True, exist_ok=True)
    (about_dir / "index.html").write_text(html)

    print(f"Built site to {DIST}")


def main():
    build()


if __name__ == "__main__":
    main()
