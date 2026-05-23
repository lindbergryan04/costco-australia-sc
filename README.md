# Costco Australia / Synthetic Control

Causal study of whether Costco gas-station entry into an Australian local
market lowers nearby competitor fuel prices, using state fuel-price
registry data from NSW, QLD, and WA combined with hand-collected Costco
opening dates. Identification strategy: **synthetic control**, fit
separately for each treated Costco using same-state donor postcodes.

The full analysis lives in [`analysis/costco_australia_sc.qmd`](analysis/costco_australia_sc.qmd)
and renders to [`analysis/costco_australia_sc.pdf`](analysis/costco_australia_sc.pdf).

## Reproducing the analysis

### Recommended: ask Claude

The fastest path is to clone the repo, open Claude Code at the root, and
ask Claude to render the analysis. Claude reads
[`CLAUDE.md`](CLAUDE.md) — which documents the tool prerequisites, the
`renv` workflow, knit timing, and the gotchas — and drives the steps
itself. This is the recommended method because Claude handles
environment setup, watches for the known LaTeX/Quarto pitfalls, and can
explain the analysis section-by-section as it goes.

### Manual

Prerequisites: R 4.5+, Quarto 1.4+, and a LaTeX engine (TinyTeX is fine:
`quarto install tinytex`).

```bash
cd analysis
Rscript -e 'renv::restore()'           # one-time; seconds if the renv cache is warm, ~5-10 min cold
quarto render costco_australia_sc.qmd  # ~20 min cold; <1 min once chunks are cached
```

Output: `analysis/costco_australia_sc.pdf`. The committed PDF is the same
artifact; rendering only matters if you change the `.qmd` or the inputs.

The `.qmd` reads its five input CSVs from a public Dropbox folder at knit
time, so you don't need the 2.2 GB raw cache to reproduce.

## Treated units

Four Costco fuel stations meet the pre/post coverage requirements:

| Costco | State | Treatment date | Pre months | Post months |
|---|---|---|---:|---:|
| Coomera | QLD | May 2023 | 51 | 31 |
| Casuarina | WA | November 2022 | 58 | 42 |
| Perth Airport | WA | February 2020 | 26 | 74 |
| Lake Macquarie | NSW | May 2022 | 58 | 35 |

Six additional Costcos (Marsden Park, Auburn, Canberra Airport, Casula,
North Lakes, Ipswich) are excluded for insufficient pre- or
post-treatment data; they appear as descriptive context in the
deliverables. The donor pool is 196 Australian postcodes more than 20 km
from any Costco — see [`data/sc_inputs/README.md`](data/sc_inputs/README.md).

## Repo layout

```
.
├── README.md                                ← this file
├── CLAUDE.md                                ← project guide for Claude / agents
├── references.md                            ← external sources cited in §1-§3
│
├── analysis/                                ← ★ the analysis ★
│   ├── README.md                            reproduction details
│   ├── costco_australia_sc.qmd              main Quarto document
│   ├── costco_australia_sc.pdf              rendered output (committed)
│   ├── _sc_helpers.R                        tidysynth wrappers
│   ├── renv.lock                            110 pinned R packages
│   └── renv/                                renv bootstrap (library/ gitignored)
│
├── deliverables/                            handed-in PDFs
│   ├── question_and_dataset.pdf
│   ├── plan_of_attack_section_1.pdf
│   ├── plan_of_attack_section_2.pdf
│   ├── plan_of_attack_section_3.pdf
│   └── plan_of_attack_combined.pdf
│
├── scripts/
│   ├── _nsw_reader.py                       shared NSW XLSX iterator
│   ├── data_acquisition/                    pull raw data from state APIs
│   │   ├── pull_au_data.py                  monthly NSW/QLD/WA registry archives
│   │   ├── pull_nsw_stations.py             live NSW FuelCheck station snapshot
│   │   └── build_station_coords.py          unified station-coord lookup
│   ├── synthetic_control_input/             build SC input panels
│   │   ├── build_sc_inputs.py               headline 5 km / 20 km panel
│   │   ├── build_sc_inputs_alt_radii.py     §4 alt-radius variants
│   │   └── verify_sc_inputs.py              donor-pool checks
│   └── deliverables/
│       ├── build_question_and_dataset_pdf.py
│       ├── build_plan_of_attack_section_1_pdf.py
│       ├── build_plan_of_attack_section_2_pdf.py
│       ├── build_plan_of_attack_section_3_pdf.py
│       ├── build_combined_plan_of_attack.py
│       └── regenerate_treated_event_studies_plot.py
│
├── data/                                    (small, committable)
│   ├── stations/                            station coordinates
│   │   ├── nsw_stations.json                live NSW FuelCheck snapshot
│   │   ├── wa_stations.json                 live WA FuelWatch snapshot
│   │   └── station_coords.csv               unified lookup, 6,084 stations
│   ├── catalogs/                            Costco metadata
│   │   ├── costco_locations.csv             every Australian Costco fuel station
│   │   ├── costco_observed.csv              first-appearance dates
│   │   ├── data_availability.csv            per-state registry endpoints
│   │   └── usable_costcos.csv               treated / excluded with reasons
│   ├── sc_inputs/                           ★ headline 5/20 km SC inputs ★
│   │   ├── README.md
│   │   ├── treated_units.csv                4 treated Costcos × month
│   │   ├── donor_pool.csv                   196 donor postcodes × month
│   │   ├── treated_metadata.csv             per-Costco metadata
│   │   └── donor_metadata.csv               per-postcode metadata
│   └── sc_inputs_alt/                       §4 robustness-check variants
│       ├── 3km_15km/                        RC2 narrow geometry
│       ├── 8km_30km/                        RC2 wide geometry
│       ├── casuarina_10km/                  RC3 Casuarina-specific
│       └── donut_5_20km/                    RC7 spatial placebo
│
├── section_1/                               Section 1 artifacts
│   ├── describe_data.py                     produces every Section 1 artifact
│   ├── raw_counts.csv                       rows / vars / unique units per registry
│   ├── time_periods.csv                     date ranges per registry
│   ├── unit_of_observation.md               composite unique key per registry
│   ├── summary_statistics.csv               stats on key analysis variables
│   ├── data_quality.md                      by-variable issues + resolutions
│   ├── state_median_monthly.csv             per-state monthly medians (used by §1)
│   └── plots/                               §1 figures
│
├── section_3/                               §3 illustrative-only plots (plan-of-attack)
│   ├── build_section_3_plots.py
│   └── plots/
│
└── _local/                                  ★ gitignored, do not commit ★
    ├── .nsw_credentials.json                NSW FuelCheck API key
    └── cache/                               2.2 GB raw API snapshots
        ├── nsw/                             93 monthly XLSX files
        ├── qld/                             85 monthly CSV files
        └── wa/                              100 monthly CSV files
```

`_local/` holds the raw cache (too big for git) and credentials (sensitive).
Everything outside `_local/` is intended for the shared repo.

## Optional: rebuild SC inputs from raw archives

The `.qmd` reads its inputs from Dropbox, so rebuilding the SC input
panels is only needed if you want to verify the upstream pipeline or
build a new geometry.

1. **Get the raw archive** (~2.2 GB):

   **[Download all three state archives (Dropbox)](https://www.dropbox.com/scl/fo/chbey2wl68rmfpr7pyebu/AAv432hXHk078lsbcMFmrN4?rlkey=153uqubvpf9xq4u1su1molnie&st=x1w4jzva&dl=0)**

   Contains NSW FuelCheck (Dec 2016 - Jan 2026), QLD Fuel Price Reporting
   Scheme (Dec 2018 - Dec 2025), and WA FuelWatch (Jan 2018 - Apr 2026).
   Extract into `_local/cache/{nsw,qld,wa}/`.

   Alternatively, pull live from the source APIs (~15 min):
   ```bash
   python3 scripts/data_acquisition/pull_au_data.py
   ```

2. **Build the SC input panels** (run from repo root):
   ```bash
   python3 scripts/synthetic_control_input/build_sc_inputs.py            # headline 5/20 km, ~10 min
   python3 scripts/synthetic_control_input/build_sc_inputs_alt_radii.py  # §4 variants, ~16 min
   ```
   Outputs land in `data/sc_inputs/` and `data/sc_inputs_alt/`.

3. **Verify the donor pool**:
   ```bash
   python3 scripts/synthetic_control_input/verify_sc_inputs.py
   ```

4. **Refresh the live station-coord snapshots** (optional; the committed
   `data/stations/` is already current). Requires an NSW FuelCheck API
   key — register at <https://api.nsw.gov.au/Account/Register>, subscribe
   to the free Fuel API, and save the credentials to
   `_local/.nsw_credentials.json`:
   ```json
   {
     "api_key": "<your-api-key>",
     "api_secret": "<your-api-secret>",
     "auth_header": "Basic <base64-of-key:secret>"
   }
   ```
   Then:
   ```bash
   python3 scripts/data_acquisition/pull_nsw_stations.py
   python3 scripts/data_acquisition/build_station_coords.py
   ```

5. **Regenerate Section 1 artifacts** (optional):
   ```bash
   python3 section_1/describe_data.py
   ```

After rebuilding the SC inputs, upload the new CSVs to the Dropbox
folder so the `.qmd` can find them (the URL is hardcoded near the top of
the `.qmd`'s setup chunk).
