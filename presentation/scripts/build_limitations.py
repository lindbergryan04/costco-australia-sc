"""Slide 13: limitations our robustness checks did not resolve.

Magazine-style stacked list. Each limitation has:
  - A thin colored accent bar on the left (the "tag color"
    cues the kind of concern at a glance)
  - A numbered kicker with the concern-type label
  - A bold headline
  - A short, italic-leaning body

No heavy badges, no horizontal rules between rows — whitespace
carries the rhythm. Same typography family as the BLUF and
recommendation slides.

Output: presentation/plots/13_limitations.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

COL_TEXT  = "#212121"
COL_ANNOT = "#555555"
COL_MUTED = "#7A7A7A"

# Each limitation gets a distinct accent color that cues the kind of
# concern. Distinct hues so the four rows are scannable at slide pace.
COL_WARN  = "#D97706"   # amber  — generalizability caution
COL_GEO   = "#0E7AB6"   # blue   — geometry / spatial
COL_QUEST = "#7C3AED"   # purple — open question / mechanism
COL_TIME  = "#6B7280"   # slate  — time / data window

limitations = [
    {
        "color":   COL_WARN,
        "kicker":  "GENERALIZABILITY",
        "head":    "Only one clean case",
        "body":    "Perth Airport is the single Costco with a confidence "
                   "interval that excludes zero. We can’t claim Costco "
                   "always disciplines prices everywhere.",
    },
    {
        "color":   COL_GEO,
        "kicker":  "GEOMETRY",
        "head":    "The 5 km ring is a researcher choice",
        "body":    "Results shift at 3 km and 8 km. The headline magnitude "
                   "depends on exactly how we draw the local market.",
    },
    {
        "color":   COL_QUEST,
        "kicker":  "MECHANISM",
        "head":    "We identify the effect, not the mechanism",
        "body":    "Whether competitors respond via price-matching, volume "
                   "advantages, or consumer perception, our data cannot tell.",
    },
    {
        "color":   COL_TIME,
        "kicker":  "DATA WINDOW",
        "head":    "QLD and NSW Costcos need more time",
        "body":    "Coomera and Lake Macquarie have only 1–3 years of "
                   "post-opening data. A clean read needs longer follow-up.",
    },
]

# ---- Figure ---------------------------------------------------------
# Aspect ratio (2.08) matches the slide host's image area (12.49 / 6.0)
# so the PNG fills the slot without letterbox whitespace top or bottom.
FIG_W, FIG_H = 13.0, 6.25
fig = plt.figure(figsize=(FIG_W, FIG_H))
ax  = fig.add_axes([0, 0, 1, 1])    # axes fills entire figure
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Row layout: four rows, generously spaced.
# Margins kept small so the slide host (PowerPoint) doesn't add visible
# whitespace at the top / bottom of the embedded PNG.
n           = len(limitations)
TOP_MARGIN  = 0.025
BOT_MARGIN  = 0.025
ROW_BAND_H  = (1 - TOP_MARGIN - BOT_MARGIN) / n
# Row band centers
row_centers = [
    1 - TOP_MARGIN - ROW_BAND_H * (i + 0.5)
    for i in range(n)
]

# Geometry within each row band
BAR_X       = 0.045    # left edge of the accent bar
BAR_WIDTH   = 0.006    # bar thickness (axes units)
BAR_HEIGHT  = 0.105    # bar height — matches content-block height
TEXT_X      = 0.072    # text content starts here

# Within-row vertical anchors (relative to row band center).
# Content block stacks tightly: kicker, then headline right below it,
# then body right below the headline. Tight enough that the three
# lines read as a single labeled paragraph, not as separated text.
KICKER_DY   =  0.026   # kicker bottom (va="bottom")
HEAD_DY     = -0.018   # head bottom (va="bottom")
BODY_DY     = -0.024   # body top (va="top")

for y, lim in zip(row_centers, limitations):
    # Thin colored accent bar — height matches the content block so the
    # bar visually frames the kicker + headline + body together.
    ax.add_patch(Rectangle(
        (BAR_X, y - BAR_HEIGHT / 2), BAR_WIDTH, BAR_HEIGHT,
        facecolor=lim["color"], edgecolor="none",
    ))

    # Numbered kicker:  "01  ·  GENERALIZABILITY"
    idx = limitations.index(lim) + 1
    ax.text(
        TEXT_X, y + KICKER_DY,
        f"0{idx}  ·  {lim['kicker']}",
        ha="left", va="bottom",
        fontsize=10.5, fontweight="bold", color=lim["color"],
    )

    # Headline (bold, dark)
    ax.text(
        TEXT_X, y + HEAD_DY, lim["head"],
        ha="left", va="bottom",
        fontsize=17, fontweight="bold", color=COL_TEXT,
    )

    # Body (gray, normal weight, wrapped to roughly 95 chars per line)
    ax.text(
        TEXT_X, y + BODY_DY, lim["body"],
        ha="left", va="top",
        fontsize=11.3, color=COL_ANNOT,
    )

# Save at exact figsize (no bbox_inches="tight") so the PNG aspect stays
# locked to FIG_W/FIG_H and lines up with the slide's image area.
plt.savefig(OUT / "13_limitations.png", dpi=150, facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '13_limitations.png'}")
