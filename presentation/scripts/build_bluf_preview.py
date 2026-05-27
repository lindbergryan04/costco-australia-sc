"""Slide 4: BLUF preview.

Magazine-style composition with a hero finding (the −3.4 ¢/L Perth
Airport effect) as the dominant visual on the left and two supporting
blocks (the "3 of 4 inconclusive" honest caveat + the regulatory
recommendation) stacked on the right. No card chrome — typography +
a single thin vertical rule carries the structure.

Per script.txt: no chart on this slide; figure reveal lives on slides
9 and 10. Pure typography.

Output: presentation/plots/04_bluf_preview.png
"""

from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

# Palette
COL_HERO   = "#1E5F2A"   # deep green — savings to consumers
COL_GRAY   = "#7A7A7A"
COL_BLUE   = "#065A82"   # Costco blue, used for the recommendation
COL_TEXT   = "#212121"
COL_ANNOT  = "#444444"
COL_RULE   = "#D8D8D8"

# ---- Figure ----------------------------------------------------------
FIG_W, FIG_H = 13.0, 5.0
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Layout anchors
LEFT_X  = 0.04
LEFT_W  = 0.54
RIGHT_X = 0.63
RIGHT_W = 0.33
RULE_X  = 0.60

# Thin vertical rule separating hero from supporting column
ax.plot([RULE_X, RULE_X], [0.08, 0.92],
        color=COL_RULE, lw=1.0, transform=ax.transAxes)

# ===== LEFT: hero finding =============================================
# Kicker label (small caps, accent)
ax.text(
    LEFT_X, 0.90, "THE CLEAN FINDING",
    ha="left", va="top",
    fontsize=13, fontweight="bold", color=COL_HERO,
)

# Hero number — dominates the page
ax.text(
    LEFT_X, 0.60, "−3.4 ¢/L",
    ha="left", va="center",
    fontsize=88, fontweight="bold", color=COL_HERO,
)

# Bold sub-headline
ax.text(
    LEFT_X, 0.34, "Perth Airport (WA): the one clean case",
    ha="left", va="top",
    fontsize=15.5, fontweight="bold", color=COL_TEXT,
)

# Body detail
ax.text(
    LEFT_X, 0.265,
    "Mean competitor-price gap vs the synthetic\n"
    "counterfactual, sustained for 6 years.\n"
    "95% CI excludes zero; MSPE ratio 4.31.",
    ha="left", va="top",
    fontsize=11.5, color=COL_ANNOT,
)

# ===== RIGHT TOP: 3 of 4 inconclusive =================================
ax.text(
    RIGHT_X, 0.90, "3 OF 4 INCONCLUSIVE",
    ha="left", va="top",
    fontsize=13, fontweight="bold", color=COL_GRAY,
)
ax.text(
    RIGHT_X, 0.83,
    "Lake Macquarie  ·  Casuarina  ·  Coomera",
    ha="left", va="top",
    fontsize=12, fontweight="bold", color=COL_TEXT,
)
ax.text(
    RIGHT_X, 0.75,
    "Short post-windows or 5 km geometry\n"
    "artifacts (see §4 robustness).",
    ha="left", va="top",
    fontsize=10.8, color=COL_ANNOT,
)

# Horizontal divider in the right column
ax.plot([RIGHT_X, RIGHT_X + RIGHT_W], [0.55, 0.55],
        color=COL_RULE, lw=0.8, transform=ax.transAxes)

# ===== RIGHT BOTTOM: recommendation ===================================
# Arrow rendered via mathtext so it works regardless of system fonts
ax.text(
    RIGHT_X, 0.47, r"RECOMMENDATION  $\rightarrow$",
    ha="left", va="top",
    fontsize=13, fontweight="bold", color=COL_BLUE,
)
ax.text(
    RIGHT_X, 0.40, "Lower fuel-retail entry barriers",
    ha="left", va="top",
    fontsize=12, fontweight="bold", color=COL_TEXT,
)
ax.text(
    RIGHT_X, 0.32,
    "ACCC advocacy + merger-review weight\n"
    "on zoning and lease constraints.",
    ha="left", va="top",
    fontsize=10.8, color=COL_ANNOT,
)

plt.savefig(OUT / "04_bluf_preview.png", dpi=150,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '04_bluf_preview.png'}")
