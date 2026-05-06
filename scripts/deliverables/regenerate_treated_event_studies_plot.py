"""Regenerate Section 1 plot 05 (treated event studies) with the validated
treatment dates from data/sc_inputs/treated_metadata.csv.

This is a worktree-local helper; section_1/describe_data.py uses
australia/-prefixed paths and depends on the registry cache, neither of
which is available here. This script reads only the already-built treated
panel and metadata, so it has no cache dependency. Re-run after any
change to treatment dates.
"""

import csv
import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter


REPO = Path(__file__).resolve().parents[2]
TREATED_UNITS = REPO / "data" / "sc_inputs" / "treated_units.csv"
TREATED_META = REPO / "data" / "sc_inputs" / "treated_metadata.csv"
OUT = REPO / "section_1" / "plots" / "05_treated_event_studies.png"


PALETTE = {"Coomera": "#1F77B4", "Casuarina": "#FF7F0E",
           "Perth Airport": "#2CA02C", "Lake Macquarie": "#D62728"}
ORDER = ["Perth Airport", "Casuarina", "Lake Macquarie", "Coomera"]


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

    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    for ax, ckey in zip(axes, ORDER):
        rs = sorted([r for r in treated if r["costco_key"] == ckey],
                    key=lambda r: r["date"])
        if not rs:
            ax.set_title(f"{ckey}: no data")
            continue
        ds = [r["date"] for r in rs]
        ys = [r["mean_price_cents"] for r in rs]
        ax.plot(ds, ys, color=PALETTE[ckey], marker="o", markersize=3,
                linewidth=1.3, label="Treated mean (5 km)")
        ax.axvline(openings[ckey], color="red", linestyle="--",
                   label=f"opens {openings[ckey]}", linewidth=1)
        ax.set_ylabel("¢/L")
        ax.set_title(f"{ckey}: treated-market mean unleaded price")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(alpha=0.3)
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    axes[-1].set_xlabel("Date")
    fig.suptitle("Treated-market unleaded price over time, per treated Costco",
                 fontsize=12, y=1.00)
    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
