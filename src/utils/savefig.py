"""Save a figure as PNG + PDF + SVG with transparent backgrounds.

The SVG is the web-facing format: a transparent background lets it sit
seamlessly on an HTML page (the page background shows through instead of an
opaque white rectangle), and ``svg.fonttype="path"`` embeds glyphs as vector
outlines so the figure renders identically regardless of which fonts the
browser has. PNG/PDF are kept for previews and the paper, and are made
transparent too so all three formats stay visually consistent.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

# Embed text as vector outlines so SVGs are self-contained and font-independent.
mpl.rcParams["svg.fonttype"] = "path"


def save_figure(fig, directory: Path, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext, extra in (("png", {"dpi": 300}), ("pdf", {}), ("svg", {})):
        path = directory / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight", transparent=True, **extra)
        paths.append(path)
    print("Wrote " + ", ".join(str(p) for p in paths))
