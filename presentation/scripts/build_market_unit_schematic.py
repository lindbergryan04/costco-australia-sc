"""Slide 3: market-unit schematic.

A minimal conceptual diagram showing "one local market" as defined in
our analysis: a Costco station at the center, surrounded by ~10 nearby
competitor stations, all inside a 5 km ring. No map background, no
axes, no labels beyond the bare minimum. Meant to sit next to the
research question in big text on slide 3 and answer "what is the unit
of analysis?" without restating the question.

Output: presentation/plots/03_market_unit.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

# Palette (consistent with the rest of the deck)
COL_COSTCO     = "#065A82"   # deep blue
COL_COMPETITOR = "#2F3C7E"   # dark navy
COL_FAR        = "#C9C9C9"   # faint gray for stations outside the ring
COL_RING       = "#F96167"   # coral 5 km ring
COL_TEXT       = "#212121"

RNG = np.random.default_rng(7)  # fixed seed -> reproducible layout
RADIUS = 5.0   # the "5 km" ring

fig, ax = plt.subplots(figsize=(7, 7))
ax.set_aspect("equal")
ax.axis("off")

# Plot extent: a bit beyond the ring so a few "outside" stations fit
LIM = 7.5
ax.set_xlim(-LIM, LIM)
ax.set_ylim(-LIM, LIM)

# ---- 5 km ring (coral, translucent) ----------------------------------
ring_fill = Circle((0, 0), RADIUS,
                   facecolor=COL_RING, alpha=0.12,
                   edgecolor="none", zorder=1)
ring_outline = Circle((0, 0), RADIUS,
                      facecolor="none", edgecolor=COL_RING,
                      linewidth=2.2, zorder=2)
ax.add_patch(ring_fill)
ax.add_patch(ring_outline)

# ---- Competitor stations inside the ring (uniform in disk) -----------
N_INSIDE = 10
# Reject-sample uniformly inside a disk of radius 0.85*RADIUS so dots
# stay clear of the ring edge and the central Costco
inside = []
while len(inside) < N_INSIDE:
    x, y = RNG.uniform(-RADIUS, RADIUS, size=2)
    r = np.hypot(x, y)
    if 1.2 <= r <= 0.85 * RADIUS:
        inside.append((x, y))
inside = np.array(inside)
ax.scatter(inside[:, 0], inside[:, 1],
           s=120, c=COL_COMPETITOR, alpha=0.85,
           edgecolor="white", linewidths=1.5, zorder=4)

# ---- A few stations outside the ring (faint, "not in this market") ---
N_OUTSIDE = 6
outside = []
while len(outside) < N_OUTSIDE:
    x, y = RNG.uniform(-LIM, LIM, size=2)
    r = np.hypot(x, y)
    if RADIUS + 0.6 <= r <= LIM - 0.4:
        outside.append((x, y))
outside = np.array(outside)
ax.scatter(outside[:, 0], outside[:, 1],
           s=70, c=COL_FAR, alpha=0.7,
           edgecolor="white", linewidths=1.0, zorder=3)

# ---- Costco at the center (larger, brand color) ----------------------
ax.scatter([0], [0],
           s=420, c=COL_COSTCO, edgecolor="white", linewidths=2.5,
           zorder=5)
ax.text(0, -0.85, "Costco",
        ha="center", va="top",
        fontsize=12.5, fontweight="bold", color=COL_COSTCO)

# ---- "5 km" label on the ring (top-right of ring) --------------------
# Draw a small radial tick at 45 deg with a "5 km" label
ang = np.deg2rad(55)
rx0, ry0 = 0, 0
rx1, ry1 = RADIUS * np.cos(ang), RADIUS * np.sin(ang)
ax.plot([rx0, rx1], [ry0, ry1],
        color=COL_RING, lw=1.0, alpha=0.55, zorder=2)
ax.text(rx1 / 2 + 0.15, ry1 / 2 + 0.25, "5 km",
        ha="left", va="bottom",
        fontsize=11.5, color=COL_RING, fontweight="bold",
        rotation=np.degrees(ang),
        rotation_mode="anchor")

# ---- Tiny legend at the bottom ---------------------------------------
legend_y = -LIM + 0.55
ax.scatter([-3.5], [legend_y], s=180, c=COL_COSTCO, zorder=6,
           edgecolor="white", linewidths=1.5)
ax.text(-3.1, legend_y, "Costco",
        ha="left", va="center", fontsize=10.5, color=COL_TEXT)

ax.scatter([0.0], [legend_y], s=80, c=COL_COMPETITOR, zorder=6,
           edgecolor="white", linewidths=1.0)
ax.text(0.4, legend_y, "Competitor in the local market (within 5 km)",
        ha="left", va="center", fontsize=10.5, color=COL_TEXT)

# Second legend row, slightly lower
legend_y2 = legend_y - 0.85
ax.scatter([-3.5], [legend_y2], s=60, c=COL_FAR, zorder=6,
           edgecolor="white", linewidths=1.0)
ax.text(-3.1, legend_y2, "Station outside this local market",
        ha="left", va="center", fontsize=10.5, color=COL_TEXT)

plt.savefig(OUT / "03_market_unit.png", dpi=200,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '03_market_unit.png'}")
