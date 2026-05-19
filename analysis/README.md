# Analysis: Costco Australia synthetic-control study

This folder contains the Quarto analysis for the MGT159 group project. The
`.qmd` reads its inputs from a public Dropbox folder, fits four
synthetic-control models (one per treated Costco), and produces the figures
and tables that support the project's headline causal claim. The analysis
follows the pre-committed plan in [`../deliverables/plan_of_attack_combined.pdf`](../deliverables/plan_of_attack_combined.pdf)
section-by-section.

## File layout

```
analysis/
├── README.md                     ← this file
├── costco_australia_sc.qmd       ← main analysis (R-engine Quarto)
├── costco_australia_sc.pdf       ← rendered output
├── _sc_helpers.R                 ← tidysynth wrappers (fit, gaps, CIs, summaries)
├── renv.lock                     ← pinned R package versions
├── .Rprofile                     ← auto-activates renv on R startup
└── renv/
    ├── activate.R                ← renv bootstrap (committed)
    ├── settings.json             ← renv config (committed)
    ├── .gitignore                ← excludes library/ etc.
    └── library/                  ← project-scoped package install (gitignored)
```

## How to reproduce

### Prerequisites

| Tool         | Version                          | Install                                                              |
|--------------|----------------------------------|----------------------------------------------------------------------|
| R            | 4.5+ (4.1+ minimum for `\|>`)     | `brew install r` or download from [r-project.org](https://cran.r-project.org/) |
| Quarto       | 1.4+                             | `brew install --cask quarto` (enter sudo password when prompted)     |
| LaTeX        | Any TeX distribution             | `quarto install tinytex` (recommended)                               |
| renv         | 1.x                              | `install.packages("renv")` in R                                      |

Verify each tool: `R --version`, `quarto --version`.

### Restore R packages (one-time, ~5–10 min)

R dependencies are pinned in `analysis/renv.lock` for reproducibility. From
the `analysis/` directory:

```r
renv::restore()
```

This installs the exact package versions (108 packages, including `tidyverse`,
`tidysynth`, `lubridate`, `kableExtra`, `patchwork`, `scales`, `glue`, plus
all transitive dependencies) into a project-scoped library at
`analysis/renv/library/`. The restore reads `renv.lock`; renv's global cache
(under `~/Library/Caches/org.R-project.R/`) speeds up subsequent restores on
the same machine to seconds.

When you open R in the `analysis/` folder, `.Rprofile` auto-activates the
project library so package loads pick the pinned versions, not whatever is
in your global R library.

### Add or update a package

```r
renv::install("packagename")
renv::snapshot()             # writes the new version into renv.lock
```

Then commit the updated `renv.lock` along with the code change.

### Knit the .qmd

From the repository root:

```bash
quarto render analysis/costco_australia_sc.qmd
```

This produces `analysis/costco_australia_sc.pdf`. On the first knit, the
setup chunk downloads the input data from Dropbox (~750 KB) and unzips it
into a session-local tempdir; subsequent knits reuse the cached copy.
Synthetic-control fits will eventually be cached by knitr, so iterative
edits to prose only re-render the affected chunks.

## Where the data comes from

The `.qmd` reads five CSV inputs from a single public Dropbox folder share:

> https://www.dropbox.com/scl/fo/g7lhsenilo4lza6dwnukq/AMIiPcOy1uysFMJtSC3eqrg?rlkey=ozb016wrtnrg9qj9yw789xkyg&st=73xiohe7&dl=1

The trailing `dl=1` makes Dropbox return the folder contents as a ZIP, which
the `.qmd` downloads once at the top, extracts to a session-local tempdir,
and reads from there. One URL is cleaner than five for a multi-file analysis
and matches the "single Dropbox link to the data" spirit of the assignment.

| File                       | Source in the main repo  | Purpose in the `.qmd`                                    |
|----------------------------|--------------------------|----------------------------------------------------------|
| `treated_units.csv`        | `data/sc_inputs/`        | 5 km treated rings × month (375 rows; 4 Costcos)         |
| `donor_pool.csv`           | `data/sc_inputs/`        | 196 donor postcodes × month (17,578 rows)                |
| `treated_metadata.csv`     | `data/sc_inputs/`        | Per-Costco lat/lng, validated treatment date, coverage   |
| `donor_metadata.csv`       | `data/sc_inputs/`        | Per-postcode suburb labels (used for Figure 2 in §3.3)   |
| `state_median_monthly.csv` | `section_1/`             | Per-state monthly median unleaded price (Figures 2 & 3)  |

These CSVs are the analysis-ready outputs of
`scripts/synthetic_control_input/build_sc_inputs.py`. Re-running that
pipeline from raw state-registry archives requires the 1.86 GB Dropbox
archive linked from the main repo's `README.md`; that step is upstream of
the `.qmd` and not exercised on a clean-machine knit.

## Where we are right now

| Stage                                                                | Status                                                                |
|----------------------------------------------------------------------|-----------------------------------------------------------------------|
| Plan of Attack §1–§3                                                  | ✅ Submitted as PDFs in `../deliverables/`                            |
| SC input CSVs at 5 km / 20 km radii                                  | ✅ Built (`data/sc_inputs/`) and uploaded to Dropbox folder            |
| `_sc_helpers.R` (tidysynth wrappers + extractors + summaries)        | ✅ Written                                                            |
| `costco_australia_sc.qmd` (§1 complete; §2–§6 stubbed)               | ✅ Written                                                            |
| renv set up + lockfile snapshotted (108 packages pinned)             | ✅ Done                                                               |
| First clean knit + visual sanity check                               | ⏳ Pending — needs Quarto installed (`brew install --cask quarto`)    |
| Fill in §2 sample-construction narrative + funnel table              | ⏳ Pending                                                            |
| Fill in §3 SC analysis (Figures 1–3, Tables 1–2)                     | ⏳ Pending                                                            |
| Alt-radius SC inputs (3/15, 8/30, Casuarina 10 km, 5–20 km donut)    | ⏳ Pending — only after the 5 km / 20 km headline fits look right     |
| §4 robustness checks 1–7                                              | ⏳ Pending                                                            |
| §5 recommendation + §6 limitations                                    | ⏳ Pending                                                            |
| Clean-environment reproducibility knit (no local data)               | ⏳ Pending                                                            |

## Pointers back to the main repo

- Pipeline that built `data/sc_inputs/`: [`scripts/synthetic_control_input/build_sc_inputs.py`](../scripts/synthetic_control_input/build_sc_inputs.py)
- Verifier for the donor pool: [`scripts/synthetic_control_input/verify_sc_inputs.py`](../scripts/synthetic_control_input/verify_sc_inputs.py)
- Section 1 artifacts (counts, plots, data-quality notes): [`../section_1/`](../section_1/)
- Section 3 illustrative-only plots from the plan-of-attack: [`../section_3/`](../section_3/)
