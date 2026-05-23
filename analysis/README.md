# Analysis: Costco Australia synthetic-control study

This folder contains the Quarto analysis for the MGT159 group project.
[`costco_australia_sc.qmd`](costco_australia_sc.qmd) reads its inputs from a
public Dropbox folder, fits four synthetic-control models (one per treated
Costco) plus the §4 robustness checks, and renders the figures and tables
that support the project's headline causal claim. The analysis follows
the pre-committed plan in [`../deliverables/plan_of_attack_combined.pdf`](../deliverables/plan_of_attack_combined.pdf)
section-by-section.

The recommended way to reproduce this analysis is to ask Claude — see the
top-level [`README.md`](../README.md) and [`CLAUDE.md`](../CLAUDE.md).
This file documents the manual path.

## File layout

```
analysis/
├── README.md                     ← this file
├── costco_australia_sc.qmd       ← main analysis (R-engine Quarto)
├── costco_australia_sc.pdf       ← rendered output (committed)
├── _sc_helpers.R                 ← tidysynth wrappers (fit, gaps, CIs, summaries)
├── renv.lock                     ← 110 pinned R package versions
├── .Rprofile                     ← auto-activates renv on R startup
├── renv/                         ← renv bootstrap (library/ gitignored)
└── costco_australia_sc_cache/    ← knitr chunk cache (gitignored, built on first knit)
```

## Prerequisites

| Tool   | Version         | Install                                            |
|--------|-----------------|----------------------------------------------------|
| R      | 4.5+            | `brew install r` or download from [r-project.org](https://cran.r-project.org/) |
| Quarto | 1.4+            | `brew install --cask quarto`                       |
| LaTeX  | any             | `quarto install tinytex` (recommended)             |
| renv   | bootstrap auto-installs | n/a — `renv/activate.R` handles it          |

Verify: `R --version`, `quarto --version`.

## Restore R packages (one-time)

From the `analysis/` directory:

```r
renv::restore()
```

This installs the 110 pinned packages (`tidyverse`, `tidysynth`, `lubridate`,
`kableExtra`, `patchwork`, `scales`, `glue`, plus transitive deps) into a
project-scoped library at `renv/library/`. Cold restore is ~5-10 min; renv's
global cache (under `~/Library/Caches/org.R-project.R/`) makes subsequent
restores on the same machine finish in seconds.

`.Rprofile` auto-activates the project library when you open R in
`analysis/`, so package loads pick the pinned versions rather than the
global R library.

To add or update a package later:

```r
renv::install("packagename")
renv::snapshot()             # writes the new version into renv.lock
```

Then commit the updated `renv.lock` alongside the code change.

## Knit the .qmd

From the repository root:

```bash
quarto render analysis/costco_australia_sc.qmd
```

Output: [`costco_australia_sc.pdf`](costco_australia_sc.pdf).

Timing:

- **First render on a clean clone: ~20 min.** The setup chunk downloads the
  input data from Dropbox (~3.7 MB ZIP) to a session-local tempdir, and
  every fit chunk runs from scratch. The `sc_fits` chunk (four headline
  Costcos + donor permutations for 95% CIs) is ~10 min on its own; the
  seven §4 robustness fits add another ~10 min.
- **Cached re-render: <1 min.** All fit chunks have `#| cache: true`, so
  prose edits and figure tweaks reuse the cached fits. The cache lives at
  `costco_australia_sc_cache/` (gitignored) and survives `quarto render`
  invocations.

## Where the data comes from

The `.qmd` reads its inputs from a single public Dropbox folder share
(URL hardcoded at the top of the setup chunk). The trailing `dl=1`
returns the folder contents as a ZIP, which the `.qmd` downloads once,
extracts to a session-local tempdir, and reads from there.

| File                       | Source in the main repo  | Purpose in the `.qmd`                                    |
|----------------------------|--------------------------|----------------------------------------------------------|
| `treated_units.csv`        | `data/sc_inputs/`        | 5 km treated rings × month (375 rows; 4 Costcos)         |
| `donor_pool.csv`           | `data/sc_inputs/`        | 196 donor postcodes × month (17,578 rows)                |
| `treated_metadata.csv`     | `data/sc_inputs/`        | Per-Costco lat/lng, validated treatment date, coverage   |
| `donor_metadata.csv`       | `data/sc_inputs/`        | Per-postcode suburb labels (used for Figure 2 in §3.3)   |
| `state_median_monthly.csv` | `section_1/`             | Per-state monthly median unleaded price (Figures 2 & 3)  |

In addition, the Dropbox folder has a top-level `sc_inputs_alt/`
subfolder mirroring `data/sc_inputs_alt/` — the four geometry variants
used by the §4 robustness checks (`3km_15km/`, `8km_30km/`,
`casuarina_10km/`, `donut_5_20km/`), each containing the same four input
CSVs at that geometry.

These CSVs are the analysis-ready outputs of
`scripts/synthetic_control_input/build_sc_inputs.py` (and
`build_sc_inputs_alt_radii.py` for the §4 variants). Re-running those
scripts requires the 2.2 GB raw archive linked from the main repo's
`README.md`; that step is upstream of the `.qmd` and not exercised on a
clean-machine knit.

## §4 robustness checks

Every §4 fit goes through `fit_one_costco_robust()` in `_sc_helpers.R`,
which tries `predictors = "yearly_means"` first and falls back to
`"overall_mean"` when the QP solver returns a singular matrix. Returns
`NULL` if both strategies fail; the table chunks check for `NULL` and
emit `NA` / `(fit failed)` rather than crashing.
