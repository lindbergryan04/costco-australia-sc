"""Build illustrative figures for Section 3 of the Plan of Attack.

The Section 3 plan-of-attack PDF describes the analysis we *will* run; it
does not run synthetic-control fits. Following the example solution's
convention, the figures here are hypothetical sketches showing what we
expect each figure to look like once the actual analysis happens. This
keeps Section 3 a true plan (no pre-committed result) while giving the
reader a concrete preview of the canonical synthetic-control output.

Outputs:
    section_3/plots/01_sc_trajectories_illustrative.png
    section_3/plots/02_donor_weights_illustrative.png
    section_3/plots/03_event_study_aggregate_illustrative.png
"""

import datetime as dt
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


REPO = Path(__file__).resolve().parents[1]
PLOTS = REPO / "section_3" / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

# Reproducible mock data
RNG = np.random.default_rng(20260509)


_REGISTRY_END = {
    "QLD": dt.date(2025, 12, 1),
    "NSW": dt.date(2026, 1, 1),
    "WA":  dt.date(2026, 4, 1),
}

COSTCOS = [
    {"key": "Coomera",        "state": "QLD",
     "treat": dt.date(2023, 5, 23),
     "pre_start": dt.date(2019, 1, 1),
     "panel_end": _REGISTRY_END["QLD"], "color": "#1F77B4"},
    {"key": "Casuarina",      "state": "WA",
     "treat": dt.date(2022, 11, 11),
     "pre_start": dt.date(2018, 1, 1),
     "panel_end": _REGISTRY_END["WA"], "color": "#FF7F0E"},
    {"key": "Perth Airport",  "state": "WA",
     "treat": dt.date(2020, 2, 19),
     "pre_start": dt.date(2018, 1, 1),
     "panel_end": _REGISTRY_END["WA"], "color": "#2CA02C"},
    {"key": "Lake Macquarie", "state": "NSW",
     "treat": dt.date(2022, 5, 2),
     "pre_start": dt.date(2018, 1, 1),
     "panel_end": _REGISTRY_END["NSW"], "color": "#D62728"},
]


def month_range(start, end):
    """Inclusive monthly date list, first-of-month."""
    out = []
    y, m = start.year, start.month
    while dt.date(y, m, 1) <= end:
        out.append(dt.date(y, m, 1))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def base_au_price(date):
    """Realistic-looking Australian unleaded price level by month.

    Captures the headline regimes: pre-COVID stable, 2020 pandemic dip,
    2021 recovery, 2022 Russia/Ukraine spike with the Mar-Sep excise cut,
    elevated post-2022 plateau. Used to give both treated and synthetic
    illustrative lines a plausible common backbone.
    """
    if date < dt.date(2020, 3, 1):
        return 142.0
    if date < dt.date(2020, 11, 1):
        # COVID demand collapse and partial recovery
        months_in = (date.year - 2020) * 12 + (date.month - 3)
        return 142.0 - 35.0 * np.exp(-0.4 * months_in) + 0.5 * months_in
    if date < dt.date(2022, 2, 1):
        return 148.0 + 1.2 * ((date.year - 2020) * 12 + date.month - 11)
    if date < dt.date(2022, 4, 1):
        return 200.0
    if date < dt.date(2022, 10, 1):
        # Federal excise cut Mar-Sep 2022
        return 175.0
    if date < dt.date(2024, 1, 1):
        return 188.0
    return 180.0


def make_costco_series(costco, gap_size=4.0):
    """Hypothetical treated and synthetic series for one Costco panel.

    Pre-period: synthetic ≈ treated + small noise (illustrating tight
    pre-fit). Post-period: synthetic continues the no-treatment
    counterfactual and treated drops below by ``gap_size`` ¢/L (smooth
    onset, then persistent).
    """
    months = month_range(costco["pre_start"], costco["panel_end"])
    base = np.array([base_au_price(m) for m in months])

    # Common monthly noise that both lines share (so they co-move on
    # macro shocks, like donors and treated should).
    common_noise = RNG.normal(0, 1.5, len(months)).cumsum() * 0.2
    base = base + common_noise

    # Independent fitting noise (synthetic does not perfectly equal treated)
    treated  = base + RNG.normal(0, 1.5, len(months))
    synthetic = base + RNG.normal(0, 1.5, len(months))

    # Apply the illustrative treatment effect: treated drops below
    # synthetic post-treatment, with a smooth onset over ~4 months.
    treat_idx = next(i for i, m in enumerate(months) if m >= costco["treat"])
    months_post = np.arange(len(months)) - treat_idx
    onset = np.where(months_post < 0, 0.0,
                     gap_size * (1 - np.exp(-months_post / 4.0)))
    treated = treated - onset

    # Donor-permutation 95% CI band on the synthetic.
    ci_halfwidth = 2.5 + 0.05 * np.maximum(months_post, 0)
    ci_halfwidth = np.minimum(ci_halfwidth, 6.0)

    return months, treated, synthetic, ci_halfwidth


# ----------------------------------------------------------------------
# Figure 1: SC trajectories per treated Costco (illustrative)
# ----------------------------------------------------------------------

def figure1():
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0), sharey=False)
    axes_flat = axes.flatten()

    for ax, costco in zip(axes_flat, COSTCOS):
        months, treated, synthetic, ci = make_costco_series(costco)

        ax.fill_between(months, synthetic - ci, synthetic + ci,
                        color="#888888", alpha=0.18,
                        label="95% CI (donor permutation)")
        ax.plot(months, treated, color=costco["color"], linewidth=1.6,
                label="Treated 5 km ring (actual)")
        ax.plot(months, synthetic, color="black", linestyle="--",
                linewidth=1.4, label="Synthetic counterfactual")
        ax.axvline(costco["treat"], color="red", linestyle=":",
                   linewidth=1.2,
                   label=f"opens {costco['treat'].strftime('%b %Y')}")

        ax.set_title(f"{costco['key']} ({costco['state']})", fontsize=11,
                     fontweight="bold")
        ax.set_ylabel("Mean unleaded price (¢/L)", fontsize=9)
        ax.grid(alpha=0.3)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.legend(loc="upper left", fontsize=7.5, framealpha=0.85)

    fig.suptitle("Figure 1 (illustrative): synthetic-control trajectories, "
                 "per treated Costco", fontsize=12, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = PLOTS / "01_sc_trajectories_illustrative.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ----------------------------------------------------------------------
# Figure 2: Donor weights per treated Costco (illustrative)
# ----------------------------------------------------------------------

ILLUSTRATIVE_WEIGHTS = {
    "Coomera": [
        ("4209 Coomera-Helensvale", 0.32),
        ("4214 Southport",          0.21),
        ("4215 Labrador",           0.16),
        ("4220 Burleigh Heads",     0.12),
        ("4216 Runaway Bay",        0.10),
        ("4218 Mermaid Beach",      0.06),
        ("4226 Robina",             0.03),
    ],
    "Casuarina": [
        ("6168 Rockingham",   0.38),
        ("6169 Safety Bay",   0.24),
        ("6210 Mandurah",     0.18),
        ("6164 Cockburn",     0.11),
        ("6163 Bibra Lake",   0.06),
        ("6173 Warnbro",      0.03),
    ],
    "Perth Airport": [
        ("6105 Belmont",       0.28),
        ("6107 Cannington",    0.22),
        ("6109 Maddington",    0.17),
        ("6062 Morley",        0.13),
        ("6056 Midland",       0.10),
        ("6065 Wanneroo",      0.06),
        ("6017 Karrinyup",     0.04),
    ],
    "Lake Macquarie": [
        ("2287 Wallsend",        0.34),
        ("2299 Cardiff",         0.23),
        ("2261 Toukley",         0.15),
        ("2284 Edgeworth",       0.12),
        ("2298 Mayfield",        0.08),
        ("2259 Wyong",           0.05),
        ("2285 West Wallsend",   0.03),
    ],
}


def figure2():
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.5))
    axes_flat = axes.flatten()

    for ax, costco in zip(axes_flat, COSTCOS):
        weights = ILLUSTRATIVE_WEIGHTS[costco["key"]]
        labels = [w[0] for w in weights][::-1]
        values = [w[1] for w in weights][::-1]
        ypos = np.arange(len(values))
        ax.barh(ypos, values, color=costco["color"], alpha=0.85)
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlim(0, 0.5)
        ax.set_xlabel("Synthetic-control weight", fontsize=9)
        ax.set_title(f"{costco['key']} ({costco['state']})", fontsize=11,
                     fontweight="bold")
        ax.grid(axis="x", alpha=0.3)
        for y, v in zip(ypos, values):
            ax.text(v + 0.005, y, f"{v:.2f}", va="center", fontsize=8)

    fig.suptitle("Figure 2 (illustrative): donor-postcode weights, per "
                 "treated Costco", fontsize=12, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = PLOTS / "02_donor_weights_illustrative.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ----------------------------------------------------------------------
# Figure 3: Aggregate event study (illustrative)
# ----------------------------------------------------------------------

def figure3():
    rel_months = np.arange(-24, 25)

    # Pre-period: gap fluctuates around zero
    pre_mask = rel_months < 0
    pre_gap = RNG.normal(0, 0.8, pre_mask.sum())

    # Post-period: gap drops to ~-4 ¢/L with smooth onset
    post_months = rel_months[~pre_mask]
    post_gap = -4.2 * (1 - np.exp(-post_months / 4.0)) \
        + RNG.normal(0, 0.6, len(post_months))

    gap = np.concatenate([pre_gap, post_gap])

    # Cross-Costco SE band: tighter pre, wider in early post (response
    # heterogeneity), narrowing again as effect stabilises.
    se = np.where(rel_months < 0, 0.9,
                  1.6 - 0.5 * np.exp(-rel_months / 6.0))

    fig, ax = plt.subplots(figsize=(10, 5.0))
    ax.fill_between(rel_months, gap - 1.96 * se, gap + 1.96 * se,
                    color="#888888", alpha=0.22, label="95% CI (cross-Costco SE)")
    ax.plot(rel_months, gap, color="#1F77B4", linewidth=1.8,
            marker="o", markersize=3.5, label="Mean gap (actual − synthetic)")
    ax.axvline(0, color="red", linestyle=":", linewidth=1.2,
               label="Costco opens (month 0)")
    ax.axhline(0, color="black", linestyle="-", linewidth=0.6)
    ax.set_xlabel("Months relative to Costco opening", fontsize=10)
    ax.set_ylabel("Mean gap (¢/L), averaged across 4 Costcos",
                  fontsize=10)
    ax.set_title("Figure 3 (illustrative): aggregate event study — "
                 "treatment effect by month-since-opening",
                 fontsize=11, fontweight="bold")
    ax.set_xlim(-24, 24)
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left", fontsize=9)

    fig.tight_layout()
    out = PLOTS / "03_event_study_aggregate_illustrative.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


def main():
    figure1()
    figure2()
    figure3()


if __name__ == "__main__":
    main()
