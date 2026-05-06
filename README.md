# Costco Australia / Synthetic Control

Causal study of whether Costco gas station entry into an Australian local
market lowers nearby competitor fuel prices, using state fuel-price
registry data from NSW, QLD, and WA combined with hand-collected Costco
opening dates. Identification strategy: **synthetic control**.

## Repo layout

```
.
├── README.md                           ← this file
├── references.md                       external sources used in §1 and §2
│
├── deliverables/                       handed-in PDFs
│   ├── question_and_dataset.pdf
│   ├── plan_of_attack_section_1.pdf
│   └── plan_of_attack_section_2.pdf
│
├── scripts/
│   ├── _nsw_reader.py                  shared utility (robust NSW XLSX iterator)
│   ├── data_acquisition/                         data acquisition
│   │   ├── pull_au_data.py             pulls historical state-registry data
│   │   ├── pull_nsw_stations.py        pulls live NSW FuelCheck station list
│   │   └── build_station_coords.py     builds unified station-coord lookup
│   ├── synthetic_control_input/                         synthetic-control inputs
│   │   ├── build_sc_inputs.py          builds the four SC input CSVs
│   │   └── verify_sc_inputs.py         filter checks on the donor pool
│   └── deliverables/
│       ├── build_question_and_dataset_pdf.py
│       ├── build_plan_of_attack_section_1_pdf.py
│       ├── build_plan_of_attack_section_2_pdf.py
│       └── regenerate_treated_event_studies_plot.py
│
├── data/                               (small, committable)
│   ├── stations/
│   │   ├── nsw_stations.json           live NSW FuelCheck snapshot
│   │   ├── wa_stations.json            live WA FuelWatch snapshot
│   │   └── station_coords.csv          unified coord lookup, all 6,084 stations
│   ├── catalogs/
│   │   ├── costco_locations.csv        every Costco fuel station
│   │   ├── costco_observed.csv         first-appearance dates
│   │   ├── data_availability.csv       per-state registry endpoints
│   │   └── usable_costcos.csv          treated/excluded with reasons
│   └── sc_inputs/                      ★ inputs to the synthetic control ★
│       ├── README.md
│       ├── treated_units.csv           4 treated Costcos × month panel
│       ├── donor_pool.csv              196 donor postcodes × month panel
│       ├── treated_metadata.csv        per-Costco metadata
│       └── donor_metadata.csv          per-postcode metadata
│
├── section_1/                          Section 1 of the plan-of-attack
│   ├── describe_data.py                produces every Section 1 artifact
│   ├── raw_counts.csv                  observation/variable counts per registry
│   ├── time_periods.csv                date ranges per registry
│   ├── unit_of_observation.md          composite unique key per registry
│   ├── summary_statistics.csv          stats on key analysis variables
│   ├── data_quality.md                 by-variable issues + resolutions
│   └── plots/
│       ├── 01_price_histogram.png
│       ├── 02_unleaded_median_over_time.png
│       ├── 03_distance_to_costco_hist.png
│       └── 05_treated_event_studies.png
│
└── _local/                             ★ DO NOT COMMIT, local-only ★
    ├── .nsw_credentials.json           NSW FuelCheck API key (sensitive)
    ├── cache/                          1.86 GB of raw API snapshots
    │   ├── nsw/                        93 monthly XLSX files
    │   ├── qld/                        85 monthly CSV files
    │   └── wa/                         100 monthly CSV files
```

The `_local/` folder is a **do-not-commit zone** that holds the cache (too
big for Git), credentials (sensitive), and historical exploratory work.
Everything outside `_local/` is intended for the shared repo.

## Raw data archive (for reproducibility)

The 1.86 GB of raw API snapshots used to build the SC inputs are too
large for this repository. They are mirrored on Dropbox under each
state's open-data license:

**[Download all three state archives (Dropbox)](https://www.dropbox.com/scl/fo/chbey2wl68rmfpr7pyebu/AAv432hXHk078lsbcMFmrN4?rlkey=153uqubvpf9xq4u1su1molnie&st=x1w4jzva&dl=0)**

Contains:
- NSW FuelCheck: Aug 2016 to Apr 2026 (originally published at data.nsw.gov.au)
- QLD Fuel Price Reporting Scheme: Dec 2018 to Dec 2025 (originally published at data.qld.gov.au)
- WA FuelWatch: Jan 2018 to Apr 2026 (originally published at data.wa.gov.au)

To reproduce the SC inputs from raw data, download the archives, extract
each into `_local/cache/{nsw,qld,wa}/`, then run
`python scripts/synthetic_control_input/build_sc_inputs.py`. See the next section
for the full pipeline.

## Running the pipeline from scratch

If you have just cloned the repo you will not have `_local/` (the
cache and credentials are not committed). To rebuild the synthetic control inputs:

1. **Populate the cache.** Either download the Dropbox archives above and
   extract them into `_local/cache/{nsw,qld,wa}/`, or pull
   directly from the source APIs:
   ```bash
   python scripts/data_acquisition/pull_au_data.py
   ```
   The pull-from-API path takes ~15 minutes on a fresh run; cached files
   skip re-download. The Dropbox path is faster and gives you a frozen
   snapshot identical to the one used in the deliverables.

2. **Get an NSW FuelCheck API key** (only needed if you want to refresh
   the live NSW station-coordinate snapshot). Register at
   <https://api.nsw.gov.au/Account/Register>, subscribe to the free Fuel
   API, and save your key + secret into
   `_local/.nsw_credentials.json`:
   ```json
   {
     "api_key": "<your-api-key>",
     "api_secret": "<your-api-secret>",
     "auth_header": "Basic <base64-of-key:secret>"
   }
   ```

3. **Pull the live station-coordinate snapshots** (only if you want to
   refresh; the committed `data/stations/` is already current):
   ```bash
   python scripts/data_acquisition/pull_nsw_stations.py
   python scripts/data_acquisition/build_station_coords.py
   ```

4. **Build the synthetic-control inputs**:
   ```bash
   python scripts/synthetic_control_input/build_sc_inputs.py
   ```
   Reads from `_local/cache/`, writes to `data/sc_inputs/`. Takes ~10
   minutes (NSW XLSX parse dominates).

5. **Verify the donor pool**:
   ```bash
   python scripts/synthetic_control_input/verify_sc_inputs.py
   ```

6. **(Optional) Rebuild Section 1 artifacts**:
   ```bash
   python section_1/describe_data.py
   ```

## Treated units

Four Costco fuel stations meet the pre/post coverage requirements:

| Costco | State | Treatment date | Pre months | Post months |
|---|---|---|---:|---:|
| Coomera | QLD | May 2023 | 51 | 31 |
| Casuarina | WA | November 2022 | 58 | 42 |
| Perth Airport | WA | February 2020 | 26 | 74 |
| Lake Macquarie | NSW | May 2022 | 58 | 35 |

Six additional Costcos (Marsden Park, Auburn, Canberra Airport, Casula,
North Lakes, Ipswich) are excluded from formal estimation because of
insufficient pre- or post-treatment data; they appear as descriptive
context in the deliverables.

## Donor pool

196 Australian postcodes (NSW: 104, QLD: 56, WA: 36) located more than
20 km from any Costco fuel station, with at least 3 stations on average
per month and at least 24 months of observed coverage. Total donor panel
size: 17,578 (postcode × month) observations.

## Method

The synthetic-control method. For each treated Costco we construct a synthetic
counterfactual as a weighted combination of donor postcodes whose
pre-treatment price trajectory matches the treated market's; the
post-treatment gap between the actual treated market and the synthetic
counterfactual is the estimated treatment effect.
