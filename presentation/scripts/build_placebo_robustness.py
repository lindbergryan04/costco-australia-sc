"""Slide 11: placebo-in-time + 6-check robustness strip.

Top panel: Perth Airport placebo trajectory. We refit the synthetic
as if Costco arrived 12 months early (Feb 2019). Honest read (per qmd
line 1837): the placebo gap is ~-1.96 c/L with CI excluding zero,
indicating some pre-period downward drift in WA prices. But the real
post-Costco gap (-3.4 c/L) is meaningfully larger, so the
Costco-incremental effect is on the order of -1.4 c/L.

Bottom strip: a quick name-check of the other six robustness checks
documented in qmd §4, each marked with a check. Visual is the
credibility statement: "we tried to break our own finding seven
different ways; the headline survives with honest caveats."

Input:  presentation/data/perth_airport_placebo_trajectory.csv
        presentation/data/perth_airport_placebo_summary.csv
        presentation/data/effect_summary.csv
Output: presentation/plots/11_placebo_robustness.png
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "presentation" / "plots"
DATA = ROOT / "presentation" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# Palette (matches slide 9)
COL_STATION = "#2F3C7E"   # dark navy — synthetic
COL_COSTCO  = "#065A82"   # deep blue — actual
COL_RING    = "#F96167"   # coral — CI band
COL_TEXT    = "#212121"
COL_ANNOT   = "#444444"
COL_BORDER  = "#7A7A7A"
COL_PASS    = "#2E7D32"   # deep green — passed check
COL_CARD_BG = "#FAFAF7"

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

# ---- Load placebo data -----------------------------------------------
pl = pd.read_csv(
    DATA / "perth_airport_placebo_trajectory.csv",
    parse_dates=["time_unit", "real_treatment_date",
                 "placebo_treatment_date"],
).sort_values("time_unit").reset_index(drop=True)

placebo_date = pl["placebo_treatment_date"].iloc[0]
real_date    = pl["real_treatment_date"].iloc[0]

# Pull the rigorous numbers from the R extraction (mean gap + 95% CI
# from donor-permutation inference, matching the qmd tbl-rc1 row).
ps = pd.read_csv(DATA / "perth_airport_placebo_summary.csv").iloc[0]
mean_placebo_gap = float(ps["mean_placebo_gap_cents"])
placebo_ci_lo    = float(ps["ci_lo"])
placebo_ci_hi    = float(ps["ci_hi"])

# Headline post-Costco gap for the side-by-side comparison
effects   = pd.read_csv(DATA / "effect_summary.csv").set_index("costco")
real_gap  = float(effects.loc["Perth Airport", "mean_post_gap_cents"])
costco_incremental = real_gap - mean_placebo_gap

# ---- Figure layout ---------------------------------------------------
fig = plt.figure(figsize=(13, 7.5))
ax_main  = fig.add_axes([0.07, 0.30, 0.88, 0.65])
ax_strip = fig.add_axes([0.03, 0.04, 0.94, 0.18])
ax_strip.set_xlim(0, 1)
ax_strip.set_ylim(0, 1)
ax_strip.axis("off")

# ---- Main panel: placebo trajectory ---------------------------------
ax_main.fill_between(
    pl["time_unit"], pl["synth_ci_lo"], pl["synth_ci_hi"],
    color=COL_RING, alpha=0.18, linewidth=0,
    label="95% donor-permutation CI",
)
ax_main.plot(
    pl["time_unit"], pl["synth_y"],
    color=COL_STATION, lw=2.2, ls="--",
    label="Synthetic (counterfactual)",
)
ax_main.plot(
    pl["time_unit"], pl["real_y"],
    color=COL_COSTCO, lw=2.6,
    label="Actual competitor prices",
)

# Vertical lines: solid-ish for placebo, faint for real (the truncation
# boundary; no data beyond it in this fit)
ax_main.axvline(placebo_date, color=COL_TEXT, lw=1.2, ls=":")
ax_main.axvline(real_date,    color=COL_BORDER, lw=0.8, ls=":", alpha=0.5)

# Annotations
ax_main.annotate(
    f"Placebo 'opening'\n{placebo_date.strftime('%b %Y')}\n"
    f"(12 months early)",
    xy=(placebo_date, 0.20), xycoords=("data", "axes fraction"),
    xytext=(10, 0), textcoords="offset points",
    fontsize=10.5, color=COL_TEXT, ha="left", va="center",
    fontweight="bold",
)
ax_main.annotate(
    f"Real Costco opens\n{real_date.strftime('%b %Y')}\n"
    "(panel ends here)",
    xy=(real_date, 0.82), xycoords=("data", "axes fraction"),
    xytext=(-10, 0), textcoords="offset points",
    fontsize=9.5, color=COL_BORDER, ha="right", va="center",
    style="italic",
)

# Honest read: placebo + real + incremental, side by side.
ax_main.text(
    0.985, 0.05,
    f"Placebo gap   {mean_placebo_gap:+.2f} ¢/L   "
    f"[{placebo_ci_lo:+.2f}, {placebo_ci_hi:+.2f}]\n"
    f"Real gap         {real_gap:+.2f} ¢/L\n"
    f"Costco-incremental  ≈  {costco_incremental:+.2f} ¢/L",
    transform=ax_main.transAxes, ha="right", va="bottom",
    fontsize=10.5, color=COL_TEXT, family="monospace",
    bbox=dict(boxstyle="round,pad=0.45", facecolor="#FAFAF7",
              edgecolor=COL_BORDER, linewidth=0.8),
)

# Axes
ax_main.set_ylabel("Mean unleaded price (¢/L), 5 km ring", fontsize=12)
ymin = min(pl["real_y"].min(), pl["synth_ci_lo"].min()) - 4
ymax = max(pl["real_y"].max(), pl["synth_ci_hi"].max()) + 6
ax_main.set_ylim(ymin, ymax)
ax_main.grid(True, axis="y", linestyle="-", linewidth=0.4, color="#DDDDDD")
ax_main.set_axisbelow(True)
for sp in ("top", "right"):
    ax_main.spines[sp].set_visible(False)

ax_main.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
ax_main.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))

ax_main.legend(loc="upper left", frameon=False, fontsize=10.5,
               bbox_to_anchor=(0.0, 0.97))

# ---- Bottom strip: 6 other robustness checks (passed) ---------------
checks = [
    ("RC2", "Alt radii\n3 km / 15 km, 8 km / 30 km"),
    ("RC3", "Alt Casuarina geometry\n10 km treated ring"),
    ("RC4", "Drop COVID window\nMar–Dec 2020 excluded"),
    ("RC5", "12-month holdout\non Perth Airport pre-period"),
    ("RC6", "Donor-permutation CIs\n(powers the band above)"),
    ("RC7", "Spatial placebo\non the 5–20 km donut"),
]

# Strip title
ax_strip.text(
    0.5, 0.95, "Six other robustness checks (all support the headline):",
    ha="center", va="top",
    fontsize=11.5, fontweight="bold", color=COL_TEXT,
)

n = len(checks)
card_w = 0.14
card_h = 0.75
margin = (1 - n * card_w) / (n + 1)
card_y = 0.04

for i, (rc, label) in enumerate(checks):
    x = margin + i * (card_w + margin)
    # Mini card
    bg = FancyBboxPatch(
        (x, card_y), card_w, card_h,
        boxstyle="round,pad=0.005,rounding_size=0.015",
        facecolor=COL_CARD_BG,
        edgecolor=COL_PASS, linewidth=1.4,
    )
    ax_strip.add_patch(bg)

    # RC label + check (mathtext checkmark for font compatibility)
    ax_strip.text(
        x + card_w / 2, card_y + card_h - 0.10,
        rf"$\checkmark$  {rc}",
        ha="center", va="top",
        fontsize=12, fontweight="bold", color=COL_PASS,
    )
    # Description
    ax_strip.text(
        x + card_w / 2, card_y + card_h - 0.34, label,
        ha="center", va="top",
        fontsize=9.0, color=COL_ANNOT,
    )

plt.savefig(OUT / "11_placebo_robustness.png", dpi=150,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '11_placebo_robustness.png'}")
