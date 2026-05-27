"""Build the four presentation plots.

Plot files are numbered by the slide they appear on, matching script.txt.
Each plot is intentionally UNTITLED — titles live on the pptx slides.

Outputs to presentation/plots/:
  06_all_stations.png            (slide 6)  All AU gas stations
  08_costcos_rings_donors.png    (slide 8)  Costcos + 5/20 km rings + donors
  09_perth_airport_trajectories.png (slide 9)  Treated vs synthetic + 95% CI
  10_forest_plot.png             (slide 10) Per-Costco effects + 95% CIs

Data sources:
  data/stations/station_coords.csv
  data/catalogs/costco_locations.csv
  data/sc_inputs/treated_metadata.csv
  data/sc_inputs/donor_metadata.csv
  presentation/data/au_states.geojson      (downloaded)
  presentation/data/perth_airport_trajectory.csv  (R extract)
  presentation/data/effect_summary.csv             (R extract)
"""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

# ---- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PRES = ROOT / "presentation"
OUT  = PRES / "plots"
OUT.mkdir(parents=True, exist_ok=True)

# ---- Palette -----------------------------------------------------------------
# Picked to read as "data + regulator": dark navy primary, warm coral accent
# for the treated rings, mossy green for donor pool, charcoal text.
COL_STATION  = "#2F3C7E"   # dark navy
COL_COSTCO   = "#065A82"   # deep blue
COL_RING     = "#F96167"   # coral (5km ring fill, slightly translucent)
COL_DONOR    = "#5B8C5A"   # moss green
COL_LAND     = "#F2F1ED"   # warm off-white land
COL_BORDER   = "#7A7A7A"   # muted gray border
COL_TEXT     = "#212121"

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
    "axes.edgecolor": COL_TEXT,
    "axes.labelcolor": COL_TEXT,
    "xtick.color": COL_TEXT,
    "ytick.color": COL_TEXT,
})

# ---- Load data ---------------------------------------------------------------
print("Loading data...")
stations = pd.read_csv(DATA / "stations" / "station_coords.csv")
treated_meta = pd.read_csv(DATA / "sc_inputs" / "treated_metadata.csv")
donor_meta = pd.read_csv(DATA / "sc_inputs" / "donor_metadata.csv")
au_states = gpd.read_file(PRES / "data" / "au_states.geojson")

# Donor postcode centroids: mean lat/lng of stations in each donor postcode.
# station_coords postcode column is int-ish; cast both sides to int.
stations_clean = stations.dropna(subset=["lat", "lng"]).copy()
stations_clean["postcode"] = stations_clean["postcode"].astype(int)
donor_meta["postcode"] = donor_meta["postcode"].astype(int)

donor_centroids = (
    stations_clean.merge(
        donor_meta[["postcode", "state"]],
        on=["postcode", "state"],
        how="inner",
    )
    .groupby(["state", "postcode"], as_index=False)
    .agg(lat=("lat", "mean"), lng=("lng", "mean"))
)
print(f"  {len(stations_clean)} stations, "
      f"{len(treated_meta)} Costcos, "
      f"{len(donor_centroids)}/{len(donor_meta)} donor centroids resolved")

# Subset states to the three we use
AU_STATES_KEEP = ["New South Wales", "Queensland", "Western Australia"]
au_focus = au_states[au_states["STATE_NAME"].isin(AU_STATES_KEEP)].copy()


# ---- Shared map helpers ------------------------------------------------------
def km_to_deg_lat(km: float) -> float:
    """1 deg latitude ~= 111.32 km globally."""
    return km / 111.32


def km_to_deg_lng(km: float, lat: float) -> float:
    """Longitude degrees per km depends on latitude."""
    return km / (111.32 * math.cos(math.radians(lat)))


def draw_basemap(ax, bounds=None, show_state_labels=True):
    """Render Australia (faded), highlight NSW/QLD/WA, optionally label."""
    au_states.plot(
        ax=ax, color="#E8E6E0", edgecolor=COL_BORDER, linewidth=0.5
    )
    au_focus.plot(
        ax=ax, color=COL_LAND, edgecolor=COL_BORDER, linewidth=0.7
    )
    if bounds is not None:
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
    ax.set_aspect("equal")
    ax.set_axis_off()


# Manually-tuned label positions for the three focal states. The geometric
# centroid for NSW lands on an outline, and QLD's centroid sits awkwardly
# close to where the Coomera label lives. These coordinates put each label
# in empty interior space.
STATE_LABEL_POS = {
    "WA":  (122.0, -25.5),
    "QLD": (141.5, -25.5),   # south of the inset bounds so the label isn't covered
    "NSW": (146.5, -32.5),
}


def draw_state_labels(ax, fontsize=18):
    """Place faint state labels (WA / QLD / NSW) inside each polygon."""
    for state, (lng, lat) in STATE_LABEL_POS.items():
        ax.text(
            lng, lat, state,
            fontsize=fontsize, fontweight="bold",
            color="#8A8A8A", alpha=0.85,
            ha="center", va="center", zorder=1.5,
        )


# ====================================================================
# Plot 1: All-stations map of Australia
# ====================================================================
print("Plot 1: all-stations map...")
fig, ax = plt.subplots(figsize=(11, 8.5))
draw_basemap(ax, bounds=(112, -44, 154, -10))
draw_state_labels(ax)

ax.scatter(
    stations_clean["lng"], stations_clean["lat"],
    s=2.2, c=COL_STATION, alpha=0.55, linewidths=0,
)

# Per-state counts as a small stat strip at the bottom of the figure.
# Kept because it's data context, not a title; the slide title can still
# say "6,084 stations across NSW/QLD/WA" and this complements it.
state_counts = (
    stations_clean.groupby("state").size().reindex(["NSW", "QLD", "WA"])
)
labels = [f"{s}: {n:,}" for s, n in state_counts.items()]
fig.text(
    0.02, 0.04, "    ".join(labels),
    fontsize=12, color="#555555",
)

plt.savefig(OUT / "06_all_stations.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print(f"  -> {OUT / '06_all_stations.png'}")


# ====================================================================
# Plot 2: Costcos + 5km rings + donor pool, with Coomera inset
# ====================================================================
print("Plot 2: Costcos + rings + donor pool...")
fig, ax = plt.subplots(figsize=(11, 8.5))
draw_basemap(ax, bounds=(112, -44, 154, -10))
draw_state_labels(ax)

# Donor postcodes (green)
ax.scatter(
    donor_centroids["lng"], donor_centroids["lat"],
    s=18, c=COL_DONOR, alpha=0.7, linewidths=0,
    label=f"Donor postcodes (n={len(donor_meta)})",
)

# 20 km exclusion ring around each Costco — visible at country scale as
# a small gray dashed outline. Anything inside is excluded from being a
# donor (the 5 km ring is treated; the 5-20 km annulus is the buffer).
COL_EXCLUDE = "#888888"
for _, row in treated_meta.iterrows():
    ex_lng = km_to_deg_lng(20, row["lat"])
    ex_lat = km_to_deg_lat(20)
    ax.add_patch(mpatches.Ellipse(
        (row["lng"], row["lat"]),
        width=2 * ex_lng, height=2 * ex_lat,
        facecolor="none", edgecolor=COL_EXCLUDE,
        linewidth=1.2, linestyle="--", zorder=4,
    ))

# Costcos (blue) — the actual 5 km rings would be sub-pixel at country
# scale, so we show only the marker here and the real rings in the inset.
ax.scatter(
    treated_meta["lng"], treated_meta["lat"],
    s=160, c=COL_COSTCO, edgecolor="white", linewidths=2.0, zorder=5,
    label="Treated Costcos (n=4)",
)

# Costco labels (offset so they don't sit on the dot)
label_offsets = {
    "Coomera":        (1.5, -0.5),
    "Casuarina":      (-9.5, -0.2),
    "Perth Airport":  (-9.5,  1.5),
    "Lake Macquarie": (1.5,  0.5),
}
for _, row in treated_meta.iterrows():
    dx, dy = label_offsets.get(row["costco_key"], (1.0, 0.5))
    ax.annotate(
        row["costco_key"],
        xy=(row["lng"], row["lat"]),
        xytext=(row["lng"] + dx, row["lat"] + dy),
        fontsize=11, fontweight="bold", color=COL_COSTCO,
        arrowprops=dict(arrowstyle="-", color=COL_COSTCO, lw=0.8),
    )

# Legend
legend_handles = [
    mpatches.Patch(color=COL_COSTCO, label="Treated Costco (4)"),
    mpatches.Patch(color=COL_RING, alpha=0.45,
                   label="5 km treated ring (see inset)"),
    Line2D([0], [0], color=COL_EXCLUDE, lw=1.2, linestyle="--",
           label="20 km exclusion ring (no donors allowed)"),
    mpatches.Patch(color=COL_DONOR, label="Donor postcode (196)"),
]
ax.legend(
    handles=legend_handles, loc="lower left", frameon=True,
    facecolor="white", edgecolor=COL_BORDER, fontsize=11,
    bbox_to_anchor=(0.02, 0.02),
)

# ---- Inset: zoom on Coomera (densest 5km ring, 19.63 stations) -----------
coomera = treated_meta[treated_meta["costco_key"] == "Coomera"].iloc[0]
clat, clng = coomera["lat"], coomera["lng"]

# Bounding box ~32km half-width around Coomera so the 20 km exclusion
# ring fits with a touch of breathing room
half_lat = km_to_deg_lat(32)
half_lng = km_to_deg_lng(32, clat)
inset_bounds = (clng - half_lng, clat - half_lat,
                clng + half_lng, clat + half_lat)

# Inset axis, anchored top-right
ax_in = inset_axes(
    ax, width="32%", height="32%", loc="upper right",
    bbox_to_anchor=(0.0, 0.0, 0.98, 0.93),
    bbox_transform=ax.transAxes,
    borderpad=0,
)

# Light gray fill so the inset doesn't bleed into the map
ax_in.set_facecolor("#FAFAF7")
au_focus.plot(ax=ax_in, color=COL_LAND, edgecolor=COL_BORDER, linewidth=0.5)

# Stations near Coomera (within ~25 km of the dot, for context)
nearby_mask = (
    (stations_clean["lat"].between(inset_bounds[1], inset_bounds[3])) &
    (stations_clean["lng"].between(inset_bounds[0], inset_bounds[2]))
)
nearby = stations_clean[nearby_mask]
ax_in.scatter(
    nearby["lng"], nearby["lat"],
    s=14, c=COL_STATION, alpha=0.7, linewidths=0, zorder=3,
)

# 20 km exclusion ring (dashed gray outline, no fill) — annulus between
# the 5 km treated ring and this is the buffer zone where postcodes are
# excluded from being donors
ex_lng = km_to_deg_lng(20, clat)
ex_lat = km_to_deg_lat(20)
ax_in.add_patch(mpatches.Ellipse(
    (clng, clat), width=2 * ex_lng, height=2 * ex_lat,
    facecolor="none", edgecolor=COL_EXCLUDE,
    linewidth=1.6, linestyle="--", zorder=4,
))

# Real 5 km ring around Coomera (ellipse in lat/lng to account for cos(lat))
ring_lng = km_to_deg_lng(5, clat)
ring_lat = km_to_deg_lat(5)
ring = mpatches.Ellipse(
    (clng, clat), width=2 * ring_lng, height=2 * ring_lat,
    facecolor=COL_RING, edgecolor=COL_RING, alpha=0.30, linewidth=1.5, zorder=4,
)
ax_in.add_patch(ring)
ring_outline = mpatches.Ellipse(
    (clng, clat), width=2 * ring_lng, height=2 * ring_lat,
    facecolor="none", edgecolor=COL_RING, linewidth=1.8, zorder=5,
)
ax_in.add_patch(ring_outline)

# Costco dot
ax_in.scatter(
    [clng], [clat], s=90, c=COL_COSTCO,
    edgecolor="white", linewidths=1.6, zorder=6,
)

ax_in.set_xlim(inset_bounds[0], inset_bounds[2])
ax_in.set_ylim(inset_bounds[1], inset_bounds[3])
ax_in.set_aspect("equal")
ax_in.set_xticks([])
ax_in.set_yticks([])
for spine in ax_in.spines.values():
    spine.set_color(COL_BORDER)
    spine.set_linewidth(1.0)

# Inset caption (above the inset axes)
ax_in.set_title(
    "Coomera, QLD  ·  5 km treated, 20 km excluded",
    fontsize=10.5, fontweight="bold", color=COL_TEXT, pad=4, loc="left",
)

# Connect inset to its target on the main map with a faint box
mark_inset(ax, ax_in, loc1=2, loc2=3, fc="none",
           ec=COL_BORDER, lw=0.7, linestyle="--")

plt.savefig(OUT / "08_costcos_rings_donors.png", dpi=200,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"  -> {OUT / '08_costcos_rings_donors.png'}")


# ====================================================================
# Plot 3: Perth Airport trajectories
# ====================================================================
print("Plot 3: Perth Airport trajectories...")
pa = pd.read_csv(PRES / "data" / "perth_airport_trajectory.csv",
                 parse_dates=["time_unit", "treatment_date"])
pa = pa.sort_values("time_unit").reset_index(drop=True)
treatment_date = pa["treatment_date"].iloc[0]

# Explicit axes positioning. No figure-level title — the slide title
# will handle that — so the plot area fills the figure vertically.
fig = plt.figure(figsize=(12, 6.0))
ax = fig.add_axes([0.085, 0.13, 0.88, 0.82])

# CI band (donor-permutation, pointwise gap CI added back to synthetic)
ax.fill_between(
    pa["time_unit"], pa["synth_ci_lo"], pa["synth_ci_hi"],
    color=COL_RING, alpha=0.18, linewidth=0,
    label="95% donor-permutation CI on synthetic",
)

# Synthetic line
ax.plot(
    pa["time_unit"], pa["synth_y"],
    color=COL_STATION, lw=2.2, ls="--",
    label="Synthetic Perth Airport (counterfactual)",
)

# Treated line
ax.plot(
    pa["time_unit"], pa["real_y"],
    color=COL_COSTCO, lw=2.6,
    label="Actual Perth Airport competitor prices",
)

# Treatment-date vertical line + label (place mid-height so it doesn't
# collide with the legend at top)
ax.axvline(treatment_date, color=COL_TEXT, lw=1.0, ls=":")
ax.annotate(
    "Costco opens\nFeb 2020",
    xy=(treatment_date, 0.55), xycoords=("data", "axes fraction"),
    xytext=(8, 0), textcoords="offset points",
    fontsize=10.5, color=COL_TEXT, ha="left", va="center",
    fontweight="bold",
)

# Mean post-treatment gap callout
post = pa[pa["time_unit"] >= treatment_date]
mean_gap = (post["real_y"] - post["synth_y"]).mean()
ax.text(
    0.985, 0.05,
    f"Mean post-treatment gap: {mean_gap:+.2f} ¢/L\n"
    f"95% CI excludes zero  ·  MSPE ratio = 4.31",
    transform=ax.transAxes, ha="right", va="bottom",
    fontsize=11, color=COL_TEXT,
    bbox=dict(boxstyle="round,pad=0.45", facecolor="#FAFAF7",
              edgecolor=COL_BORDER, linewidth=0.8),
)

ax.set_ylabel("Mean unleaded price (¢/L), 5 km ring", fontsize=12)
ax.set_xlabel("")
# Explicit y-range with padding so the 2026 CI spike isn't clipped
ymin = min(pa["real_y"].min(), pa["synth_ci_lo"].min()) - 5
ymax = max(pa["real_y"].max(), pa["synth_ci_hi"].max()) + 5
ax.set_ylim(ymin, ymax)
ax.grid(True, axis="y", linestyle="-", linewidth=0.4, color="#DDDDDD")
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)

# Legend upper-left — open space above ~160 c/L in 2018-2020. Anchor it
# slightly below the plot top so it doesn't touch the upper border.
ax.legend(loc="upper left", frameon=False, fontsize=10.5,
          bbox_to_anchor=(0.0, 0.97))

plt.savefig(OUT / "09_perth_airport_trajectories.png", dpi=200,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"  -> {OUT / '09_perth_airport_trajectories.png'}")


# ====================================================================
# Plot 4: Forest plot of 4-Costco effects
# ====================================================================
print("Plot 4: forest plot...")
fx = pd.read_csv(PRES / "data" / "effect_summary.csv")

# Order rows for visual hierarchy: strongest negative at top
fx = fx.sort_values("mean_post_gap_cents").reset_index(drop=True)

# No figure-level title — the slide handles that. The legend lives at
# the bottom of the figure, so axes claim the upper ~75% of the canvas.
fig = plt.figure(figsize=(12, 5.5))
ax = fig.add_axes([0.20, 0.20, 0.55, 0.75])  # [left, bottom, width, height]

ys = np.arange(len(fx))[::-1]  # so top row is at top of plot

# Color by signal class
def row_color(row):
    if row["ci_hi"] < 0 and row["post_pre_ratio"] >= 3.0:
        return COL_COSTCO       # clean negative effect
    if row["ci_lo"] > 0:
        return "#B85042"        # wrong-sign concern
    return "#9A9A9A"            # inconclusive

colors = [row_color(r) for _, r in fx.iterrows()]

# CI bars + endpoint ticks
for y, (_, r), c in zip(ys, fx.iterrows(), colors):
    ax.hlines(y, r["ci_lo"], r["ci_hi"], color=c, lw=3.0, alpha=0.55)
    ax.plot([r["ci_lo"], r["ci_hi"]], [y, y], "|",
            color=c, ms=12, mew=2.2)

# Point estimates
ax.scatter(
    fx["mean_post_gap_cents"], ys,
    s=180, c=colors, edgecolor="white", linewidths=2.0, zorder=5,
)

# Zero line
ax.axvline(0, color=COL_TEXT, lw=1.0, ls="--", alpha=0.6)

# Row labels (Costco + state) on the left and numeric annotation on the right
for y, (_, r) in zip(ys, fx.iterrows()):
    ax.text(
        -0.025, y, f"{r['costco']}  ·  {r['state']}",
        transform=ax.get_yaxis_transform(),
        ha="right", va="center", fontsize=13, fontweight="bold",
        color=COL_TEXT,
    )
    ax.text(
        1.025, y,
        f"{r['mean_post_gap_cents']:+.2f}   "
        f"[{r['ci_lo']:+.2f}, {r['ci_hi']:+.2f}]",
        transform=ax.get_yaxis_transform(),
        ha="left", va="center", fontsize=11, color="#444444",
        family="monospace",
    )

# X-axis range gives a touch of padding around the data
xmin = min(fx["ci_lo"].min(), fx["mean_post_gap_cents"].min()) - 0.8
xmax = max(fx["ci_hi"].max(), fx["mean_post_gap_cents"].max()) + 0.8
ax.set_xlim(xmin, xmax)
ax.set_ylim(-0.6, len(fx) - 0.4)

ax.set_yticks([])
ax.set_xlabel("Mean post-treatment gap vs synthetic (¢/L)", fontsize=12)
ax.grid(True, axis="x", linestyle="-", linewidth=0.4, color="#DDDDDD")
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)

# Color legend below the plot
legend_handles = [
    mpatches.Patch(color=COL_COSTCO,
                   label="Clean negative effect (CI < 0, MSPE ratio ≥ 3)"),
    mpatches.Patch(color="#9A9A9A",
                   label="Inconclusive (CI straddles or near zero)"),
    mpatches.Patch(color="#B85042",
                   label="Wrong-sign concern (5 km artifact, see §4)"),
]
fig.legend(
    handles=legend_handles, loc="lower center", ncol=3,
    frameon=False, fontsize=10.5,
    bbox_to_anchor=(0.5, 0.02),
)

plt.savefig(OUT / "10_forest_plot.png", dpi=200,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"  -> {OUT / '10_forest_plot.png'}")

print("\nDone. All four PNGs in", OUT)
