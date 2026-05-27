"""Slide 2: AU fuel-retail market concentration chart.

Three horizontal bars, one per ACCC retail category, showing the
2023-24 national retail petrol sales volume split. Brand names are
listed inside each category band rather than broken out individually
because the ACCC does NOT publish per-brand shares (commercially
confidential) — only aggregate category figures.

Title is intentionally omitted — slide title lives in the pptx.

Source: ACCC, "Market composition through Australia's evolving
petroleum industry" (November 2025), Figure 3.2. Data: 2023-24.
Available at:
https://www.accc.gov.au/about-us/publications/serial-publications/petrol-industry-reports/market-composition-through-australias-evolving-petroleum-industry

Output: presentation/plots/02_market_concentration.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

# ---- Category data (from ACCC Nov-2025 report, 2023-24 data) ----------
categories = [
    {
        "label":   "Major company brands  (top 4)",
        "share":   40,
        "brands":  ("Ampol", "bp", "Viva Energy / Shell",
                    "Coles / Reddy Express"),
        "color":   "#B85042",   # muted red — most concentrated
    },
    {
        "label":   "Other large retail brands  (next 5)",
        "share":   34,
        "brands":  ("7-Eleven", "EG Group", "Chevron / Caltex",
                    "United Petroleum", "On The Run"),
        "color":   "#D8853A",   # muted amber
    },
    {
        "label":   "Smaller independents  (30+ brands)",
        "share":   26,
        "brands":  ("Liberty", "Metro Petroleum", "Speedway",
                    "X-Convenience", "Puma", "Costco",
                    "and ~25 more"),
        "color":   "#6FA483",   # muted green — fragmented competition
        "highlight_costco": True,
    },
]

COL_TEXT      = "#212121"
COL_ANNOT     = "#444444"
COL_HIGHLIGHT = "#005DAA"   # Costco blue, used for the callout
COL_BG_BOX    = "#FAFAF7"

# ---- Layout ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 6.2))
ax.set_xlim(-1.5, 60)
ax.set_ylim(7.5, -0.85)   # inverted: top category at top
ax.axis("off")

BAR_HEIGHT = 0.72
BAR_X      = 0.0
Y_STEP     = 2.0

for i, cat in enumerate(categories):
    y_bar    = i * Y_STEP
    y_label  = y_bar - 0.65
    y_brands = y_bar + 0.62

    # Category label above the bar
    ax.text(
        BAR_X, y_label, cat["label"],
        ha="left", va="bottom",
        fontsize=13.5, fontweight="bold", color=COL_TEXT,
    )

    # The bar itself
    ax.barh(
        y_bar, cat["share"], left=BAR_X, height=BAR_HEIGHT,
        color=cat["color"], alpha=0.90, edgecolor="white", linewidth=0.5,
    )

    # Percentage label at the end of the bar
    ax.text(
        cat["share"] + 1.0, y_bar, f"{cat['share']}%",
        ha="left", va="center",
        fontsize=18, fontweight="bold", color=COL_TEXT,
    )

    # Brand list below the bar — render Costco specially when present so
    # the audience sees where Costco fits in the long tail.
    brand_x = BAR_X
    for j, brand in enumerate(cat["brands"]):
        is_costco = (cat.get("highlight_costco") and brand == "Costco")
        text_color = COL_HIGHLIGHT if is_costco else COL_ANNOT
        weight = "bold" if is_costco else "normal"
        style = "normal" if is_costco else "italic"
        t = ax.text(
            brand_x, y_brands, brand,
            ha="left", va="top",
            fontsize=10.8, color=text_color,
            fontweight=weight, style=style,
        )
        # Get rendered width so we can place a separator after it
        fig.canvas.draw()
        bb = t.get_window_extent().transformed(ax.transData.inverted())
        brand_x = bb.x1 + 0.25

        if j < len(cat["brands"]) - 1:
            sep = ax.text(
                brand_x, y_brands, "·",
                ha="left", va="top",
                fontsize=10.8, color="#999999",
            )
            fig.canvas.draw()
            sb = sep.get_window_extent().transformed(ax.transData.inverted())
            brand_x = sb.x1 + 0.25

# ---- Top concentration callout (below all bars) -----------------------
callout_y = (len(categories) - 1) * Y_STEP + 2.70
ax.text(
    BAR_X, callout_y,
    "Top 9 ACCC-monitored brands account for 74% of retail volume.\n"
    "This is the market the ACCC is asked to keep competitive, and "
    "where new entrants like Costco can move the needle.",
    ha="left", va="center",
    fontsize=12.5, fontweight="bold", color=COL_HIGHLIGHT,
    bbox=dict(
        boxstyle="round,pad=0.7",
        facecolor=COL_BG_BOX,
        edgecolor=COL_HIGHLIGHT,
        linewidth=1.5,
    ),
)

# ---- X-axis baseline + ticks (faint, just for scale reference) --------
baseline_y = (len(categories) - 1) * Y_STEP + 1.35
ax.plot([BAR_X, 50], [baseline_y, baseline_y],
        color="#BBBBBB", lw=0.6, zorder=0)
for x_tick in (0, 10, 20, 30, 40, 50):
    ax.plot([x_tick, x_tick],
            [baseline_y - 0.06, baseline_y + 0.06],
            color="#BBBBBB", lw=0.6)
    ax.text(x_tick, baseline_y + 0.25, f"{x_tick}%",
            ha="center", va="top", fontsize=9, color="#888888")

# ---- Source citation ---------------------------------------------------
fig.text(
    0.02, 0.025,
    "Source: ACCC, Market composition through Australia's evolving "
    "petroleum industry, November 2025 (data for 2023–24). The ACCC "
    "publishes category aggregates only, not per-brand shares.",
    fontsize=9, color="#888888", style="italic",
)

# 150 dpi keeps the saved image under 2000 px wide while still looking
# crisp at PowerPoint slide size.
plt.savefig(OUT / "02_market_concentration.png", dpi=150,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '02_market_concentration.png'}")
