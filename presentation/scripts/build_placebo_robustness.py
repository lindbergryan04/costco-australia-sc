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
fig = plt.figure(figsize=(13, 8.0))
ax_main  = fig.add_axes([0.07, 0.36, 0.88, 0.60])
ax_strip = fig.add_axes([0.03, 0.03, 0.94, 0.28])
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

# ---- Bottom strip: three most intuitive supplementary checks --------
# Q/A layout, one row per check. Per assignment PDF §3.7: show the
# MOST IMPORTANT checks, do not let this section drag, lead with the
# checks that most strengthen credibility. We picked the three that
# address distinct concerns and read fastest at slide pace.
checks = [
    {
        "rc":      "RC4",
        "concern": "“Isn’t this just a COVID artifact?”",
        "finding": "Dropped Mar–Dec 2020 from both panels; "
                   "the gap barely moved.",
    },
    {
        "rc":      "RC2",
        "concern": "“Did you get lucky with the 5 km choice?”",
        "finding": "Re-ran at 3 km and 8 km treated rings; "
                   "sign and magnitude survive.",
    },
    {
        "rc":      "RC7",
        "concern": "“Maybe Costco affects far-away stations too, "
                   "contaminating the donors?”",
        "finding": "Tested stations 5–20 km out; "
                   "no comparable price drop.",
    },
]

# Strip header
ax_strip.text(
    0.04, 0.95,
    "Three more checks worth highlighting "
    "(we ran seven total; details in the analysis):",
    ha="left", va="top",
    fontsize=12, fontweight="bold", color=COL_TEXT,
)

# Row geometry: three evenly spaced rows below the header
n = len(checks)
top_y    = 0.74
bot_y    = 0.18
row_step = (top_y - bot_y) / (n - 1) if n > 1 else 0
row_ys   = [top_y - i * row_step for i in range(n)]

# Column anchors
X_CONCERN = 0.04   # left edge of italic question
X_CHECK   = 0.42   # checkmark glyph
X_RC      = 0.455  # RC label
X_FIND    = 0.505  # finding text

# Faint vertical separator between concern column and answer column
ax_strip.plot(
    [0.39, 0.39], [bot_y - 0.05, top_y + 0.05],
    color="#E0E0E0", lw=0.8,
)

for y, check in zip(row_ys, checks):
    # Concern (italic gray, the question someone might ask)
    ax_strip.text(
        X_CONCERN, y, check["concern"],
        ha="left", va="center",
        fontsize=10.8, color=COL_ANNOT, style="italic",
    )
    # Green check
    ax_strip.text(
        X_CHECK, y, r"$\checkmark$",
        ha="left", va="center",
        fontsize=13, fontweight="bold", color=COL_PASS,
    )
    # RC label (green, bold)
    ax_strip.text(
        X_RC, y, check["rc"],
        ha="left", va="center",
        fontsize=11.5, fontweight="bold", color=COL_PASS,
    )
    # Finding (dark, normal weight)
    ax_strip.text(
        X_FIND, y, check["finding"],
        ha="left", va="center",
        fontsize=10.8, color=COL_TEXT,
    )


plt.savefig(OUT / "11_placebo_robustness.png", dpi=150,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '11_placebo_robustness.png'}")
