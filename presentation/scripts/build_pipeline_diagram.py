"""Slide 5 data pipeline diagram.

4-stage horizontal flow showing how raw state fuel registries become per-
Costco synthetic-control effect estimates. Designed for a 30-second slide
read from the back of a classroom: big boxes, big text, clear arrows.

Output: presentation/plots/05_data_pipeline.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

# Palette (matches build_plots.py)
COL_PRIMARY   = "#065A82"   # deep blue
COL_OUTPUT    = "#2F3C7E"   # dark navy (filled, white text)
COL_BG_BOX    = "#F2F1ED"   # warm off-white
COL_DARK      = "#212121"
COL_ANNOT     = "#555555"
COL_ARROW     = "#7A7A7A"

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

fig, ax = plt.subplots(figsize=(16, 5.8))
ax.set_xlim(0, 16)
ax.set_ylim(0, 5.8)
ax.set_aspect("equal")
ax.axis("off")


def add_box(x, y, w, h, fill, edge, lw=1.8, alpha=1.0):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.15",
        facecolor=fill, edgecolor=edge, linewidth=lw, alpha=alpha,
    )
    ax.add_patch(box)
    return box


def add_arrow(x0, y0, x1, y1, rad=0.0):
    arrow = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle="-|>", color=COL_ARROW, lw=2.0,
        mutation_scale=22,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)


def stage_label(x_center, y, text, color=COL_PRIMARY):
    ax.text(
        x_center, y, text,
        ha="center", va="bottom",
        fontsize=10, fontweight="bold",
        color=color,
    )


# ------------------------------------------------------------------
# Stage 1: three state registries (stacked column on the left)
# ------------------------------------------------------------------
s1_x = 0.3
s1_w = 3.1
src_h = 0.95
src_gap = 0.20
src_total_h = 3 * src_h + 2 * src_gap
src_y_start = (5.8 - src_total_h) / 2 + src_total_h - src_h  # top box

sources = [
    ("NSW FuelCheck",        "Dec 2016 – Jan 2026"),
    ("QLD Fuel Price Reporting", "Dec 2018 – Dec 2025"),
    ("WA FuelWatch",         "Jan 2018 – Apr 2026"),
]
src_centers_y = []
for i, (name, dates) in enumerate(sources):
    y = src_y_start - i * (src_h + src_gap)
    add_box(s1_x, y, s1_w, src_h, "white", COL_PRIMARY, lw=1.4)
    ax.text(s1_x + s1_w / 2, y + src_h * 0.62, name,
            ha="center", va="center", fontsize=11.5,
            fontweight="bold", color=COL_DARK)
    ax.text(s1_x + s1_w / 2, y + src_h * 0.27, dates,
            ha="center", va="center", fontsize=9.5, color=COL_ANNOT)
    src_centers_y.append(y + src_h / 2)

stage_label(s1_x + s1_w / 2, src_y_start + src_h + 0.35,
            "STATE FUEL REGISTRIES")

# ------------------------------------------------------------------
# Stage 2: monthly station-level panel
# ------------------------------------------------------------------
s2_x = s1_x + s1_w + 1.4
s2_w = 2.55
s2_h = 1.95
s2_y = (5.8 - s2_h) / 2

add_box(s2_x, s2_y, s2_w, s2_h, COL_BG_BOX, COL_PRIMARY, lw=1.8)
ax.text(s2_x + s2_w / 2, s2_y + s2_h * 0.70,
        "Monthly\nstation-level\nprice panel",
        ha="center", va="center", fontsize=12.5,
        fontweight="bold", color=COL_DARK)
ax.text(s2_x + s2_w / 2, s2_y + s2_h * 0.22,
        "6,084 stations\n× ~96 months",
        ha="center", va="center", fontsize=10.5, color=COL_ANNOT,
        style="italic")
stage_label(s2_x + s2_w / 2, s2_y + s2_h + 0.25,
            "CLEAN & AGGREGATE")

# ------------------------------------------------------------------
# Stage 3: variables we actually use (raw fields + the constructed
# monthly mean). Slide 7 owns the treated/donor split, so this stage
# answers "what data goes into the analysis?" instead of duplicating
# the funnel counts.
# ------------------------------------------------------------------
s3_x = s2_x + s2_w + 1.2
s3_w = 2.85
s3_h = 1.95
s3_y = s2_y

add_box(s3_x, s3_y, s3_w, s3_h, COL_BG_BOX, COL_PRIMARY, lw=1.8)
ax.text(s3_x + s3_w / 2, s3_y + s3_h * 0.83,
        "Analysis variables",
        ha="center", va="center", fontsize=12.5,
        fontweight="bold", color=COL_DARK)
ax.text(s3_x + s3_w / 2, s3_y + s3_h * 0.52,
        "Raw fields:\nstation_id, postcode,\nlat, lng, date,\nunleaded_price",
        ha="center", va="center", fontsize=9.3, color=COL_ANNOT,
        style="italic")
ax.text(s3_x + s3_w / 2, s3_y + s3_h * 0.13,
        "Constructed:\nmean_price_cents (monthly)",
        ha="center", va="center", fontsize=9.3, color=COL_ANNOT,
        style="italic")
stage_label(s3_x + s3_w / 2, s3_y + s3_h + 0.25,
            "KEY VARIABLES")

# ------------------------------------------------------------------
# Stage 4: synthetic control fits
# ------------------------------------------------------------------
s4_x = s3_x + s3_w + 1.2
s4_w = 2.55
s4_h = 1.95
s4_y = s2_y

add_box(s4_x, s4_y, s4_w, s4_h, COL_OUTPUT, COL_OUTPUT, lw=1.8)
ax.text(s4_x + s4_w / 2, s4_y + s4_h * 0.72,
        "Synthetic\ncontrol fits",
        ha="center", va="center", fontsize=12.5,
        fontweight="bold", color="white")
ax.text(s4_x + s4_w / 2, s4_y + s4_h * 0.26,
        "Per-Costco effect\n+ 95% CI",
        ha="center", va="center", fontsize=10.5, color="white",
        style="italic")
stage_label(s4_x + s4_w / 2, s4_y + s4_h + 0.25,
            "ESTIMATE", color=COL_OUTPUT)

# ------------------------------------------------------------------
# Arrows
# ------------------------------------------------------------------
# Sources -> Stage 2 (3 converging arrows)
for cy in src_centers_y:
    add_arrow(s1_x + s1_w + 0.10, cy,
              s2_x - 0.10, s2_y + s2_h / 2)

# Stage 2 -> Stage 3
add_arrow(s2_x + s2_w + 0.10, s2_y + s2_h / 2,
          s3_x - 0.10, s3_y + s3_h / 2)

# Stage 3 -> Stage 4
add_arrow(s3_x + s3_w + 0.10, s3_y + s3_h / 2,
          s4_x - 0.10, s4_y + s4_h / 2)

# No figure-level title — the slide title handles that. bbox_inches="tight"
# trims the blank band at the top.

plt.savefig(OUT / "05_data_pipeline.png", dpi=200,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '05_data_pipeline.png'}")
