"""Slide 9: trajectories for all 4 treated Costcos.

Perth Airport sits at the top, full-width, with the same annotations as
the original single-Costco plot (the headline case). Lake Macquarie,
Casuarina, and Coomera share a smaller row beneath, ordered by treatment
date. Same color language as the existing Perth Airport plot so the
audience can read them as a family.

Input: presentation/data/<slug>_trajectory.csv  (extract_fit_data.R)
       presentation/data/effect_summary.csv

Output: presentation/plots/09_costco_trajectories.png
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "presentation" / "plots"
DATA = ROOT / "presentation" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# Palette (same as build_plots.py)
COL_STATION = "#2F3C7E"   # dark navy — synthetic line
COL_COSTCO  = "#065A82"   # deep blue — actual line
COL_RING    = "#F96167"   # coral — CI band
COL_TEXT    = "#212121"
COL_BORDER  = "#7A7A7A"

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 11,
})

effects = pd.read_csv(DATA / "effect_summary.csv").set_index("costco")


def load_traj(slug):
    df = pd.read_csv(
        DATA / f"{slug}_trajectory.csv",
        parse_dates=["time_unit", "treatment_date"],
    )
    return df.sort_values("time_unit").reset_index(drop=True)


perth   = load_traj("perth_airport")
casuari = load_traj("casuarina")
coomera = load_traj("coomera")
lakemac = load_traj("lake_macquarie")

# Common x-range across all panels for visual coherence
X_MIN = pd.Timestamp("2018-01-01")
X_MAX = pd.Timestamp("2026-05-01")


def plot_one(ax, df, costco_name, *, large):
    treatment = df["treatment_date"].iloc[0]

    ax.fill_between(
        df["time_unit"], df["synth_ci_lo"], df["synth_ci_hi"],
        color=COL_RING, alpha=0.18, linewidth=0,
        label="95% donor-permutation CI" if large else None,
    )
    ax.plot(
        df["time_unit"], df["synth_y"],
        color=COL_STATION, lw=2.2 if large else 1.5, ls="--",
        label="Synthetic (counterfactual)" if large else None,
    )
    ax.plot(
        df["time_unit"], df["real_y"],
        color=COL_COSTCO, lw=2.6 if large else 1.8,
        label="Actual competitor prices" if large else None,
    )
    ax.axvline(treatment, color=COL_TEXT, lw=1.0, ls=":")

    pad = 5 if large else 3
    ymin = min(df["real_y"].min(), df["synth_ci_lo"].min()) - pad
    ymax = max(df["real_y"].max(), df["synth_ci_hi"].max()) + pad
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(X_MIN, X_MAX)

    post = df[df["time_unit"] >= treatment]
    mean_gap = (post["real_y"] - post["synth_y"]).mean()
    effect_row = effects.loc[costco_name]

    if large:
        ax.annotate(
            f"Costco opens\n{treatment.strftime('%b %Y')}",
            xy=(treatment, 0.55), xycoords=("data", "axes fraction"),
            xytext=(8, 0), textcoords="offset points",
            fontsize=10.5, color=COL_TEXT, ha="left", va="center",
            fontweight="bold",
        )
        ax.text(
            0.985, 0.05,
            f"Mean post-treatment gap: {mean_gap:+.2f} ¢/L\n"
            f"95% CI excludes zero  ·  "
            f"MSPE ratio = {effect_row['post_pre_ratio']:.2f}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=11, color=COL_TEXT,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#FAFAF7",
                      edgecolor=COL_BORDER, linewidth=0.8),
        )
        ax.set_ylabel("Mean unleaded price (¢/L), 5 km ring", fontsize=12)
        ax.set_title(
            f"{costco_name} ({effect_row['state']})",
            loc="left", fontsize=14, fontweight="bold",
            color=COL_TEXT, pad=10,
        )
        ax.legend(
            loc="upper left", frameon=False, fontsize=10.5,
            bbox_to_anchor=(0.0, 0.92),
        )
    else:
        ax.set_title(
            f"{costco_name} ({effect_row['state']})",
            loc="left", fontsize=11.5, fontweight="bold",
            color=COL_TEXT, pad=4,
        )
        # Compact gap + MSPE callout at bottom of each small panel
        ax.text(
            0.985, 0.05,
            f"Gap {mean_gap:+.2f} ¢/L  ·  MSPE {effect_row['post_pre_ratio']:.2f}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, color=COL_TEXT,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                      edgecolor=COL_BORDER, linewidth=0.5, alpha=0.9),
        )
        ax.set_ylabel("¢/L", fontsize=9.5)
        ax.tick_params(axis="both", labelsize=9)

    ax.grid(True, axis="y", linestyle="-", linewidth=0.4, color="#DDDDDD")
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


# ---- Figure layout ---------------------------------------------------
# Top: Perth Airport large. Bottom: three small panels ordered by
# treatment date (Lake Mac May 2022 -> Casuarina Nov 2022 -> Coomera
# May 2023) so the visual reads chronologically left-to-right.
fig = plt.figure(figsize=(14, 11))

ax_top = fig.add_axes([0.07, 0.50, 0.89, 0.44])

bot_y = 0.06
bot_h = 0.34
bot_w = 0.275
bot_gap = 0.035
ax_a = fig.add_axes([0.07,                          bot_y, bot_w, bot_h])
ax_b = fig.add_axes([0.07 + bot_w + bot_gap,        bot_y, bot_w, bot_h])
ax_c = fig.add_axes([0.07 + 2 * (bot_w + bot_gap),  bot_y, bot_w, bot_h])

plot_one(ax_top, perth,   "Perth Airport",  large=True)
plot_one(ax_a,   lakemac, "Lake Macquarie", large=False)
plot_one(ax_b,   casuari, "Casuarina",      large=False)
plot_one(ax_c,   coomera, "Coomera",        large=False)

plt.savefig(OUT / "09_costco_trajectories.png", dpi=200,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Wrote {OUT / '09_costco_trajectories.png'}")
