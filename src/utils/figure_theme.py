"""Web-native rcParams for the figure set.

Importing this module applies a small set of matplotlib rcParams (a side
effect, on purpose) that make the saved SVGs look like they were drawn
directly on the blog page rather than dropped in as screenshots:

  * ``svg.fonttype = 'none'`` keeps text as real ``<text>`` elements instead of
    vector outlines, so once the SVG is inlined into the page the labels render
    in the page's webfont and stay selectable. (The site build rewrites the
    emitted ``font-family`` to the page stack and maps black to ``currentColor``
    so axes/text follow the page theme — see ``site/build.py``.)
  * top/right spines off — an open, D3/Observable-Plot-style frame.
  * text, axis, and tick colors set to the page's near-black ink so the mapped
    ``currentColor`` matches the body text exactly.

Metrics still come from matplotlib's bundled DejaVu Sans (always present at
build time), so layout is deterministic regardless of which fonts the machine
has; only the *rendered* font is swapped to the page stack in the browser.

Imported for its side effect by ``utils.savefig`` (which every figure imports),
so the theme applies to all figures without each script opting in.
"""

from __future__ import annotations

import matplotlib as mpl

# The page's body ink (--text in the Open Athena stylesheet). Emitted as
# #1f1e1b, which the site build maps to currentColor for theme-reactivity.
INK = "#1f1e1b"

# The figures are authored wide (~12in) but displayed at the ~720px blog column,
# so their point-sized text scales down to roughly half the body text — it reads
# as oddly tiny on the page. Shrinking each figure uniformly at save time raises
# the font-size-to-figure ratio (text/lines/markers all grow together relative
# to the canvas) so the labels render at a size comparable to the body copy,
# while every figure's aspect ratio and tuned layout are preserved. Applied in
# utils.savefig. 1.0 = no change; smaller = larger on-page text.
WEB_SCALE = 0.74

mpl.rcParams.update(
    {
        # Keep text as <text> (font-independent layout via DejaVu metrics, but
        # restyleable/selectable once inlined).
        "svg.fonttype": "none",
        # Open frame: drop the top/right spines like a native web chart.
        "axes.spines.top": False,
        "axes.spines.right": False,
        # Page ink for every line of text and the axis furniture, so the
        # build's black -> currentColor mapping lands on the page text color.
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.titlecolor": INK,
    }
)
