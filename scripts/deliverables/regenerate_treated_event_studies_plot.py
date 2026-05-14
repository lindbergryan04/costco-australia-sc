"""Regenerate Section 1 plot 05 (treated event studies) with the validated
treatment dates from data/sc_inputs/treated_metadata.csv.

This is a worktree-local helper; section_1/describe_data.py uses
australia/-prefixed paths and depends on the registry cache, neither of
which is available here. This script reads only the already-built treated
panel and metadata, so it has no cache dependency. Re-run after any
change to treatment dates.

State-median overlay: this script reads section_1/state_median_monthly.csv
(written as a side-artifact by describe_data.py). If that file is not
present, the state-median reference line is skipped and a warning is
printed; everything else still renders.
"""

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter


REPO = Path(__file__).resolve().parents[2]
TREATED_UNITS = REPO / "data" / "sc_inputs" / "treated_units.csv"
TREATED_META = REPO / "data" / "sc_inputs" / "treated_metadata.csv"
STATE_MEDIAN = REPO / "section_1" / "state_median_monthly.csv"
OUT = REPO / "section_1" / "plots" / "05_treated_event_studies.png"


PALETTE = {"Coomera": "#1F77B4", "Casuarina": "#FF7F0E",
           "Perth Airport": "#2CA02C", "Lake Macquarie": "#D62728"}
ORDER = ["Perth Airport", "Casuarina", "Lake Macquarie", "Coomera"]
COSTCO_STATE = {"Perth Airport": "WA", "Casuarina": "WA",
                "Lake Macquarie": "NSW", "Coomera": "QLD"}

# Shock windows (Australian context)
COVID_START  = dt.date(2020, 3, 1)
COVID_END    = dt.date(2020, 9, 1)
EXCISE_START = dt.date(2022, 3, 30)
EXCISE_END   = dt.date(2022, 9, 28)
UKRAINE_DATE = dt.date(2022, 2, 24)


def load_state_median():
    if not STATE_MEDIAN.exists():
        print(f"  warning: {STATE_MEDIAN.relative_to(REPO)} not found; "
              "rendering without state-median overlay. Run "
              "section_1/describe_data.py to generate it.")
        return {}
    series = defaultdict(list)
    with open(STATE_MEDIAN) as f:
        for r in csv.DictReader(f):
            d = dt.date.fromisoformat(r["date"])
            series[r["state"]].append((d, float(r["median_price_cents"])))
    for state in series:
        series[state].sort(key=lambda x: x[0])
    return series


def main():
    openings = {}
    with open(TREATED_META) as f:
        for r in csv.DictReader(f):
            openings[r["costco_key"]] = dt.date.fromisoformat(r["treatment_date"])

    treated = []
    with open(TREATED_UNITS) as f:
        for r in csv.DictReader(f):
            treated.append({
                "costco_key": r["costco_key"],
                "date": dt.date.fromisoformat(r["date"]),
                "mean_price_cents": float(r["mean_price_cents"]),
            })

    state_median = load_state_median()

    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    for ax, ckey in zip(axes, ORDER):
        rs = sorted([r for r in treated if r["costco_key"] == ckey],
                    key=lambda r: r["date"])
        if not rs:
            ax.set_title(f"{ckey}: no data")
            continue

        # NBER-style grey for COVID demand collapse; pale blue for the
        # policy-intervention window (AU fuel-excise cut).
        ax.axvspan(COVID_START, COVID_END, color="#BBBBBB", alpha=0.30,
                   label="COVID demand collapse")
        ax.axvspan(EXCISE_START, EXCISE_END, color="#9ECAE1", alpha=0.40,
                   label="AU fuel-excise cut")
        ax.axvline(UKRAINE_DATE, color="#444444", linestyle=":",
                   linewidth=1.1, label="Russia/Ukraine (24 Feb 2022)")

        state = COSTCO_STATE[ckey]
        s_points = state_median.get(state, [])
        if s_points:
            s_ds, s_ys = zip(*s_points)
            ax.plot(s_ds, s_ys, color="#444444", linestyle="--",
                    linewidth=1.1, alpha=0.75,
                    label=f"{state} state median (all postcodes)")

        ds = [r["date"] for r in rs]
        ys = [r["mean_price_cents"] for r in rs]
        ax.plot(ds, ys, color=PALETTE[ckey], marker="o", markersize=3,
                linewidth=1.4, label="Treated mean (5 km)", zorder=3)
        ax.axvline(openings[ckey], color="red", linestyle="--",
                   label=f"opens {openings[ckey]}", linewidth=1.2,
                   zorder=4)
        ax.set_ylabel("¢/L")
        ax.set_title(f"{ckey}: treated 5 km ring vs. {state} state median")
        ax.legend(loc="upper left", fontsize=7.5, ncol=2, framealpha=0.9)
        ax.grid(alpha=0.3)
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    axes[-1].set_xlabel("Date")
    fig.suptitle("Treated-market unleaded price vs. state median, per treated Costco",
                 fontsize=12, y=1.00)
    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
