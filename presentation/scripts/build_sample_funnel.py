"""Slide 7: sample-construction funnel.

Two side-by-side funnels showing how we get from the universe to the
analysis sample:
  - Costcos: 10 AU Costco fuel stations -> 4 treated units
  - Postcodes: 1,004 NSW+QLD+WA postcodes -> 196 donor postcodes

Each funnel has three horizontal bars (top = universe, middle = after
the first big filter, bottom = final sample). Bar width is proportional
to count within the funnel. The two filter steps per funnel are the
ones the slide actually calls out; the granular cell-count steps in
the qmd appendix table are deliberately omitted.

Source counts: scripts/synthetic_control_input/build_sc_inputs.py,
captured in analysis/costco_australia_sc.qmd at tbl-funnel.

Output: presentation/plots/07_sample_funnel.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

# ---- Palette (kept consistent with other slide plots) -----------------
COL_TEXT      = "#212121"
COL_ANNOT     = "#555555"
COL_MUTED     = "#9A9A9A"
COL_UNIVERSE  = "#CFCFCF"   # neutral gray for the "everything" top bar
COL_INTERIM   = "#9DB7C8"   # pale blue for mid-step (Costco side)
COL_INTERIM_G = "#A8C2A0"   # pale green for mid-step (donor side)
COL_COSTCO    = "#065A82"   # final treated panel
COL_DONOR     = "#5B8C5A"   # final donor pool

# ---- Funnel data ------------------------------------------------------
# Each list of 3 dicts: top = universe, mid = after filter 1, bot = final.
costco_levels = [
    {"count": 10,  "label": "Costcos",
     "sub":   "All AU Costco fuel stations",
     "fill":  COL_UNIVERSE, "text": COL_TEXT},
    {"count": 5,   "label": "Costcos",
     "sub":   "have enough pre-Costco price history",
     "fill":  COL_INTERIM,  "text": COL_TEXT},
    {"count": 4,   "label": "Costcos",
     "sub":   "TREATED PANEL",
     "fill":  COL_COSTCO,   "text": "white"},
]
costco_filters = [
    ("− 5", "fewer than 24 months of pre-opening price data"),
    ("− 1", "fewer than 12 months of post-opening price data"),
]

postcode_levels = [
    {"count": 1004, "label": "postcodes",
     "sub":   "NSW + QLD + WA reporting unleaded prices",
     "fill":  COL_UNIVERSE,  "text": COL_TEXT},
    {"count": 642,  "label": "postcodes",
     "sub":   "are outside every Costco's 20 km footprint",
     "fill":  COL_INTERIM_G, "text": COL_TEXT},
    {"count": 196,  "label": "postcodes",
     "sub":   "DONOR POOL",
     "fill":  COL_DONOR,     "text": "white"},
]
postcode_filters = [
    ("− 362", "within 20 km of a Costco (already exposed)"),
    ("− 446", "fewer than 3 stations / month (too noisy)"),
]

# State breakdown for the final donor count
DONOR_STATE_BREAKDOWN = "NSW 104  ·  QLD 56  ·  WA 36"
TREATED_STATE_BREAKDOWN = (
    "Coomera (QLD)  ·  Casuarina (WA)  ·  "
    "Perth Airport (WA)  ·  Lake Macquarie (NSW)"
)

# ---- Layout helpers ---------------------------------------------------
def draw_funnel(ax, levels, filters, title, footer):
    """Render one funnel (universe -> filter -> filter -> final)."""
    ax.set_xlim(-1.10, 1.10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    max_count = max(L["count"] for L in levels)

    # Three bar y-positions (top is at large y because axis isn't inverted)
    bar_y = [8.1, 5.05, 2.0]
    bar_h = 1.15

    # Title
    ax.text(0, 9.55, title,
            ha="center", va="bottom",
            fontsize=14.5, fontweight="bold", color=COL_TEXT)

    # Draw bars
    for y, level in zip(bar_y, levels):
        # Linear width scaling, with a floor so the final bar can fit text
        w = max(0.40, 2.0 * level["count"] / max_count)
        rect = Rectangle(
            (-w / 2, y), w, bar_h,
            facecolor=level["fill"], edgecolor="white", linewidth=1.0,
        )
        ax.add_patch(rect)

        # Count + unit (e.g. "10 Costcos") centered in bar
        ax.text(
            0, y + bar_h * 0.62,
            f"{level['count']:,}",
            ha="center", va="center",
            fontsize=26, fontweight="bold", color=level["text"],
        )
        ax.text(
            0, y + bar_h * 0.22,
            level["label"],
            ha="center", va="center",
            fontsize=11.5, color=level["text"],
        )

        # Sub-label below the bar (small caption)
        sub_color = COL_TEXT if level["sub"].isupper() else COL_ANNOT
        sub_weight = "bold" if level["sub"].isupper() else "normal"
        ax.text(
            0, y - 0.22,
            level["sub"],
            ha="center", va="top",
            fontsize=10.5, color=sub_color, fontweight=sub_weight,
            style="normal" if level["sub"].isupper() else "italic",
        )

    # Draw filter transitions: centered down-arrow with drop count + reason
    # to the right. Anchoring at x=0 keeps the arrow visually attached to
    # the funnel regardless of how narrow the next bar gets.
    filter_y = [(bar_y[0] - 0.55, bar_y[1] + bar_h + 0.05),
                (bar_y[1] - 0.55, bar_y[2] + bar_h + 0.05)]
    for (y_from, y_to), (drop_count, reason) in zip(filter_y, filters):
        arrow = FancyArrowPatch(
            (0, y_from), (0, y_to),
            arrowstyle="-|>", mutation_scale=22,
            color=COL_MUTED, lw=1.8,
        )
        ax.add_patch(arrow)
        y_mid = (y_from + y_to) / 2
        ax.text(
            0.10, y_mid, drop_count,
            ha="left", va="center",
            fontsize=13, fontweight="bold", color=COL_TEXT,
        )
        ax.text(
            0.32, y_mid, reason,
            ha="left", va="center",
            fontsize=10.5, color=COL_ANNOT, style="italic",
        )

    # Footer (state breakdown or treated names)
    ax.text(
        0, 0.85, footer,
        ha="center", va="top",
        fontsize=10.0, color=COL_ANNOT,
    )


# ---- Figure -----------------------------------------------------------
fig = plt.figure(figsize=(13, 7.0))
ax_left  = fig.add_axes([0.025, 0.055, 0.46, 0.92])
ax_right = fig.add_axes([0.515, 0.055, 0.46, 0.92])

draw_funnel(
    ax_left, costco_levels, costco_filters,
    title="Treated Costcos",
    footer=TREATED_STATE_BREAKDOWN,
)
draw_funnel(
    ax_right, postcode_levels, postcode_filters,
    title="Donor postcodes",
    footer=DONOR_STATE_BREAKDOWN,
)

# Source line
fig.text(
    0.025, 0.012,
    "Source: scripts/synthetic_control_input/build_sc_inputs.py  "
    "(exact cell counts in analysis qmd, Table 'sample-construction funnel').",
    fontsize=9, color="#888888", style="italic",
)

plt.savefig(OUT / "07_sample_funnel.png", dpi=150,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '07_sample_funnel.png'}")
