"""Slide 12: ACCC recommendation + back-of-envelope.

Two concrete recommendations (left column) and the BotE math
chain ending in the A$9M / year aggregate-savings hero (right
column). Layout uses the same magazine-style typography
language as the BLUF slide: kicker labels, a single vertical
rule separator, dominant green hero number.

Numbers from qmd §5.3, Scenario A (Costco-specific). We anchor
on Scenario A rather than the 4-Costco mean because the mean is
dragged toward zero by Lake Macquarie and Coomera, which are
the fragile cases.

Output: presentation/plots/12_recommendation.png
"""

from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

COL_HERO  = "#1E5F2A"   # deep green — savings
COL_BLUE  = "#065A82"   # Costco blue — recommendations
COL_GRAY  = "#7A7A7A"
COL_TEXT  = "#212121"
COL_ANNOT = "#444444"
COL_RULE  = "#D8D8D8"

FIG_W, FIG_H = 13.0, 5.6
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Vertical rule between recommendations (left) and BotE (right)
RULE_X = 0.485
ax.plot([RULE_X, RULE_X], [0.08, 0.92],
        color=COL_RULE, lw=1.0, transform=ax.transAxes)

# =====================================================================
# LEFT COLUMN: two recommendations
# =====================================================================
LEFT_X = 0.04

# Kicker label
ax.text(
    LEFT_X, 0.90, "RECOMMENDATIONS FOR THE ACCC",
    ha="left", va="top",
    fontsize=13, fontweight="bold", color=COL_BLUE,
)

# Recommendation 1
ax.text(
    LEFT_X, 0.76, "1.  Lower fuel-retail entry barriers",
    ha="left", va="top",
    fontsize=15.5, fontweight="bold", color=COL_TEXT,
)
ax.text(
    LEFT_X + 0.025, 0.68,
    "Use ACCC advocacy and merger-review powers to ease\n"
    "zoning, lease, and approval constraints that delay\n"
    "big-box fuel entry into concentrated metro markets.",
    ha="left", va="top",
    fontsize=11.3, color=COL_ANNOT,
)

# Recommendation 2
ax.text(
    LEFT_X, 0.45, "2.  Factor into merger reviews",
    ha="left", va="top",
    fontsize=15.5, fontweight="bold", color=COL_TEXT,
)
ax.text(
    LEFT_X + 0.025, 0.37,
    "Treat the documented Costco price-discipline effect\n"
    "as a substantive consideration in any future\n"
    "fuel-retail merger review.",
    ha="left", va="top",
    fontsize=11.3, color=COL_ANNOT,
)

# =====================================================================
# RIGHT COLUMN: BotE math chain ending in the hero number
# =====================================================================
RIGHT_X = 0.515
COL_MID = 0.755   # horizontal center of the right column

# Kicker label (AUD established here so dollar figures don't repeat it)
ax.text(
    RIGHT_X, 0.90, "BACK-OF-ENVELOPE IMPACT  (AUD)",
    ha="left", va="top",
    fontsize=13, fontweight="bold", color=COL_HERO,
)

# Sub-label: per ring
ax.text(
    COL_MID, 0.825, "Per 5 km urban ring, per year:",
    ha="center", va="top",
    fontsize=10.5, color=COL_ANNOT, style="italic",
)

# Math row 1: 63 ML  ×  1.4 ¢/L  =  A$0.9 M
ML_X    = 0.585
CENTS_X = 0.755
RES_X   = 0.925
MATH_Y  = 0.73

# 63 ML/yr
ax.text(ML_X, MATH_Y, "63 ML",
        ha="center", va="center",
        fontsize=26, fontweight="bold", color=COL_TEXT)
ax.text(ML_X, MATH_Y - 0.07, "competitor\nfuel volume",
        ha="center", va="top",
        fontsize=9.5, color=COL_ANNOT, style="italic")

# ×
ax.text((ML_X + CENTS_X) / 2, MATH_Y, "×",
        ha="center", va="center",
        fontsize=20, color=COL_GRAY)

# 1.4 ¢/L
ax.text(CENTS_X, MATH_Y, "1.4 ¢/L",
        ha="center", va="center",
        fontsize=26, fontweight="bold", color=COL_BLUE)
ax.text(CENTS_X, MATH_Y - 0.07, "Costco-specific\nprice reduction",
        ha="center", va="top",
        fontsize=9.5, color=COL_ANNOT, style="italic")

# =
ax.text((CENTS_X + RES_X) / 2, MATH_Y, "=",
        ha="center", va="center",
        fontsize=20, color=COL_GRAY)

# $0.9 M (AUD established in the column kicker)
ax.text(RES_X, MATH_Y, "$0.9 M",
        ha="center", va="center",
        fontsize=26, fontweight="bold", color=COL_HERO)
ax.text(RES_X, MATH_Y - 0.07, "saved per ring\nper year",
        ha="center", va="top",
        fontsize=9.5, color=COL_ANNOT, style="italic")

# Horizontal rule separating per-ring math from the scale-up
ax.plot([RIGHT_X, 0.98], [0.475, 0.475],
        color=COL_RULE, lw=0.8, transform=ax.transAxes)

# Scale-up label
ax.text(
    COL_MID, 0.43,
    "Scaled to ~10 plausible new rings nationwide if barriers fall:",
    ha="center", va="top",
    fontsize=10.5, color=COL_ANNOT, style="italic",
)

# Hero impact number
ax.text(
    COL_MID, 0.27, "≈  $9 M / year",
    ha="center", va="center",
    fontsize=44, fontweight="bold", color=COL_HERO,
)
ax.text(
    COL_MID, 0.11,
    "aggregate annual consumer savings",
    ha="center", va="center",
    fontsize=12, color=COL_TEXT,
)

plt.savefig(OUT / "12_recommendation.png", dpi=150,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '12_recommendation.png'}")
