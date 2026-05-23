# CLAUDE.md

Project guide for Claude Code (and any other agent) working in this repository.
Read this once at session start, then dive in.

## TL;DR

- **MGT159 group project** — a Quarto-driven synthetic-control study of whether
  Costco gas-station entry lowers competitor fuel prices in Australia. The
  organization being advised is the **Australian Competition and Consumer
  Commission (ACCC)**.
- **The authoritative spec is [`deliverables/plan_of_attack_combined.pdf`](deliverables/plan_of_attack_combined.pdf).** Every threshold,
  figure, table, and robustness check is pre-committed there. Don't second-guess
  it without checking against the plan first.
- **The analysis is complete.** [`analysis/costco_australia_sc.qmd`](analysis/costco_australia_sc.qmd)
  renders to a 27-page PDF covering §1–§6 of the plan. Pipelines, helpers, and
  alt-radius inputs are all committed.
- **The user is Ryan Lindberg** (lindbergryan04@gmail.com), macOS. He cares
  about precision, doesn't want re-litigation of settled choices, and reads the
  rendered PDF carefully — visible defects matter.

## What this project actually is

**Research question (causal):** Does Costco gas-station entry into an Australian
local market cause nearby competitor stations to lower their retail fuel prices?

**Method:** Synthetic control via R's `tidysynth`, fit separately for each of
four treated Costcos:

| Costco | State | Treatment date | Pre | Post |
|---|---|---|---:|---:|
| Coomera | QLD | May 2023 | 51 | 31 |
| Casuarina | WA | Nov 2022 | 58 | 42 |
| Perth Airport | WA | Feb 2020 | 26 | 74 |
| Lake Macquarie | NSW | May 2022 | 58 | 35 |

Six other Costcos (Marsden Park, Auburn, Canberra Airport, Casula, North Lakes,
Ipswich) are documented but excluded for insufficient pre- or post-coverage.

**Donor pool:** 196 Australian postcodes (NSW: 104, QLD: 56, WA: 36) located
more than 20 km from any Costco, with ≥ 3 stations/month on average and
≥ 24 months coverage. Each Costco's synthetic is built from same-state donors
only, so state-level shocks are absorbed by construction.

## Repository layout

See [`README.md`](README.md) for the full tree. Quick map:

```
.
├── deliverables/             ← AUTHORITATIVE SPECS (plan_of_attack PDFs)
├── analysis/                 ← Quarto analysis (.qmd + .pdf + renv)
│   ├── costco_australia_sc.qmd    ← the main document
│   ├── costco_australia_sc.pdf    ← rendered PDF
│   ├── _sc_helpers.R              ← tidysynth wrappers
│   ├── renv.lock                  ← 110 pinned R packages
│   └── README.md                  ← reproduction details
├── scripts/
│   ├── _nsw_reader.py             ← shared NSW XLSX parser
│   ├── data_acquisition/          ← pull live data from state APIs
│   ├── synthetic_control_input/   ← build the SC input panels
│   │   ├── build_sc_inputs.py            ← headline 5/20 km panel + alt geometries
│   │   ├── build_sc_inputs_alt_radii.py  ← orchestrator: builds all four §4 variants
│   │   └── verify_sc_inputs.py
│   └── deliverables/              ← PDFs of the plan-of-attack
├── data/
│   ├── stations/                  ← station coordinate lookups
│   ├── catalogs/                  ← Costco metadata, observed dates
│   ├── sc_inputs/                 ← headline 5/20 km SC inputs (committed)
│   └── sc_inputs_alt/             ← §4 alt-radius SC inputs (committed)
│       ├── 3km_15km/
│       ├── 8km_30km/
│       ├── casuarina_10km/
│       └── donut_5_20km/
├── section_1/                ← Section 1 artifacts (plots, counts, data-quality notes)
├── section_3/                ← Section 3 illustrative-only plots from the plan-of-attack
└── _local/                   ← GITIGNORED, holds the 2.2 GB raw cache + creds
    ├── .nsw_credentials.json
    └── cache/{nsw,qld,wa}/        ← raw monthly XLSX/CSV files
```

`_local/` is on disk at `/Users/ryanlindberg/Desktop/Github/costco-australia-sc/_local/`
in the main repo (not in worktrees — it's gitignored). If running the pipeline
from a worktree, use the main checkout instead.

## Data flow

```
state-registry archives          live-API station coords          hand-collected
(_local/cache/{nsw,qld,wa}/)     (data/stations/station_coords.csv) (data/catalogs/)
                          \         |                            /
                           \        |                           /
                            v       v                          v
                    scripts/synthetic_control_input/build_sc_inputs.py
                                       |
                                       v
                        data/sc_inputs/{treated_units, donor_pool,
                                        treated_metadata, donor_metadata}.csv
                                       |
                          (uploaded to public Dropbox folder)
                                       |
                                       v
              analysis/costco_australia_sc.qmd (downloads at knit time)
                                       |
                                       v
                      analysis/costco_australia_sc.pdf
```

For §4 robustness checks RC2/RC3/RC7, the same pipeline runs four more times at
alt geometries via `build_sc_inputs_alt_radii.py`, producing
`data/sc_inputs_alt/<variant>/`. Those four subdirectories are also uploaded to
the same Dropbox folder under a top-level `sc_inputs_alt/` subfolder.

## Reproducing the analysis with Claude

The top-level [`README.md`](README.md) tells users that the recommended way
to reproduce this analysis is to ask Claude. This section is how to handle
that ask.

The `.qmd` reads its inputs from a public Dropbox folder, so you don't need
the raw cache to knit. From a fresh R session:

```bash
cd analysis
Rscript -e 'renv::restore()'           # one-time: install 110 pinned packages (~5–10 min cold; seconds if the user's global renv cache is warm)
quarto render costco_australia_sc.qmd  # ~20 min cold (renv + sc_fits + §4 fits + LaTeX); <1 min once chunks are cached
```

Rendering produces `analysis/costco_australia_sc.pdf` and pulls a ~3.7 MB ZIP
of input CSVs from Dropbox into a session-tempdir cache. The R-chunk cache
lives at `analysis/costco_australia_sc_cache/` (gitignored), so the first
render on a clean clone always pays the full cold cost once.

If R, Quarto, or LuaLaTeX aren't installed, tell the user the exact
`brew install` / `quarto install tinytex` commands rather than installing
silently — installs require user confirmation on macOS.

Common follow-ups after the first render:

- **"Explain §X."** — read the rendered PDF or the `.qmd` directly; both
  are self-contained.
- **"Change a robustness check."** — find the relevant `rcN_*` chunk in
  the `.qmd`. For RC2/RC3/RC7 (alt-geometry) changes, see "Re-build SC
  inputs at a new geometry" below — those require regenerating the input
  CSVs, uploading them to Dropbox, and adding the variant name to the
  `alt_variants` vector in the setup chunk.
- **"Re-fit a Costco."** — every §4 fit goes through
  `fit_one_costco_robust()` in `_sc_helpers.R`. Add new fits in their own
  chunks; never edit the `sc_fits` chunk body, since that invalidates the
  ~10-min cache for all four headline fits plus their donor permutations.

**Re-running the upstream pipeline** (only needed if `data/sc_inputs*/` is
stale or you want to verify the build; requires the 2.2 GB raw cache):

```bash
# from the repo root
python3 scripts/synthetic_control_input/build_sc_inputs.py            # headline 5/20 (~10 min)
python3 scripts/synthetic_control_input/build_sc_inputs_alt_radii.py  # four §4 variants (~16 min)
```

After re-running the pipeline, upload the new CSVs to the Dropbox folder so
the `.qmd` can find them. The Dropbox URL is hardcoded near the top of the
`.qmd`'s setup chunk.

## How the analysis is structured

`analysis/costco_australia_sc.qmd` is the single source of truth. Six sections,
all complete:

| § | Section | What it does |
|---|---|---|
| 1 | Raw Data Description | Three state registries, panel construction, summary stats, data-quality issues. |
| 2 | Sample Construction | Mirrors plan-of-attack §2(a)–(g): window, restrictions, dependent/independent vars, aggregation, merging, funnel table. |
| 3 | Synthetic-Control Analysis | Research design, the four fits, Figures 1–3 (trajectories, donor weights, aggregate event study), Tables 1–2 (effect summary, fit quality). |
| 4 | Robustness Checks | All seven pre-committed checks RC1–RC7. |
| 5 | Recommendation | Per-Costco honest read, three ACCC recommendations, two-scenario back-of-envelope. |
| 6 | Limitations | Five concerns §4 cannot resolve. |

§4 detail:

- **RC1** placebo-in-time (-12 months)
- **RC2** alt radii (3 km / 15 km and 8 km / 30 km)
- **RC3** Casuarina at 10 km treated radius
- **RC4** Perth Airport with Mar–Dec 2020 dropped
- **RC5** 12-month holdout (the LOOCV N-selection grid from the plan was
  simplified to the holdout test only — `tidysynth` lacks an N-restriction
  primitive and adding one would re-introduce the researcher discretion the
  holdout is itself trying to remove. Documented in §4.5 prose.)
- **RC6** 95% CIs via donor-permutation inference (already powers the bands
  in @fig-sc-trajectories and the CI column in @tbl-effect-summary)
- **RC7** spatial placebo on the 5–20 km donut

Every §4 fit goes through `fit_one_costco_robust()` in `_sc_helpers.R`, which
tries `predictors = "yearly_means"` first and falls back to `"overall_mean"`
when the QP solver returns a singular matrix. Returns `NULL` if both strategies
fail; the table chunks check for `NULL` and emit `NA` / `(fit failed)` rather
than crashing.

## Conventions

These are settled and should not be re-litigated:

- **R Quarto + `tidysynth`**, not Python + `pysyncon`. The plan-of-attack
  mentions pysyncon; we chose R for course-homework parity. Document this
  deviation if writing a verification report; don't try to switch back.
- **Cross-refs:** label figures `fig-XXX` and tables `tbl-XXX`; reference them
  in prose as `@fig-XXX` / `@tbl-XXX`. Quarto resolves the numbers.
- **Section headers** are descriptive (e.g. "Raw Data Description", not
  "Section 1: Raw Data Description"). Quarto auto-numbers them.
  "Question and motivation" and "Appendix" are marked `{.unnumbered}`.
- **American English** throughout (`color`, `summarize`, `normalize`,
  `parameterize`, `gray`, etc.).
- **Table captions** go in `#| tbl-cap:` chunk options, not in `kbl(caption =)`.
  Mixing the two produces a double caption.
- **The `sc_fits` chunk source MUST stay stable.** It caches in ~10 min;
  changing the chunk body invalidates the cache and forces re-fitting all four
  Costcos plus their donor permutations. Always add new fits in their own
  chunks rather than editing `sc_fits`.

## Gotchas (do NOT re-introduce these)

Hit, fixed, documented. If you find yourself debugging one of these, stop and
read this section.

- **Pandoc inline math + digit.** A closing `$` followed by a digit does NOT
  close math mode (per Pandoc's rules). `$\geq$24` is parsed as an open math
  block, and pandoc keeps reading until it finds a valid closer — typically
  swallowing prose. Use `$\geq 24$` (single math block containing the digit)
  or `$\geq$ 24` (space between `$` and digit) instead.
- **Unicode math glyphs in body text.** LuaLaTeX's default font (Computer
  Modern) lacks `≥` / `≤` / `≈` in text mode and silently drops them. In body
  prose, use `$\geq$` / `$\leq$` / `$\approx$` in math mode. **But:**
- **Math mode inside kableExtra cells fails when Quarto wraps the table.**
  Cells emitted via `kbl(..., escape = FALSE)` containing `$\geq$` render as
  literal text (`$\geq$ 3` shows up as five characters, not "≥ 3") under the
  `#| tbl-cap` wrapping path. **Use plain-English fallbacks in tribble cells:**
  `"at least 3"`, `"at most 5 km"`. Bonus: more readable for a regulator
  audience.
- **Donor completeness in `fit_one_costco`.** The Synth backend errors on any
  NA in Z0. The helper filters donors to those non-NA across the *entire*
  treated time grid (pre + post). The plan-of-attack mentions pysyncon's
  "NAs ignored in pre-period objective" — that's pysyncon, not tidysynth.
- **`cairo_pdf` device** requires XQuartz; we use plain `pdf` instead.
- **LaTeX caption escapes.** `%` is a comment marker — escape as `\\%` when
  inside R-emitted captions. `_` and `&` similarly. `\\$` for currency.
- **`#| cache: true`** on every fit chunk. First knit takes ~10 min for §3
  plus another ~10 min for §4 fits. Subsequent re-knits hit cache and are
  effectively free.

## Common tasks

### Knit the analysis

```bash
cd analysis
quarto render costco_australia_sc.qmd
```

If `renv` packages aren't restored yet, run `Rscript -e 'renv::restore()'`
first. The cache lives in `analysis/costco_australia_sc_cache/` (gitignored)
so iterative prose edits re-render in seconds.

### Add a new robustness check

1. Pick a unique label `rcN_descriptor`.
2. Add a fit chunk that uses `fit_one_costco_robust()` so the singular-matrix
   fallback applies automatically.
3. Add a table or figure chunk labeled `tbl-rcN` / `fig-rcN`.
4. Guard the downstream chunk against `NULL` fits.
5. Match the four-paragraph structure of the existing §4 subsections:
   Concern / Procedure / [code chunks] / Interpretation.

### Re-build SC inputs at a new geometry

```bash
# from repo root, after _local/cache/ is populated
python3 scripts/synthetic_control_input/build_sc_inputs.py \
    --near-km 4 --exclude-km 18 --out-dir data/sc_inputs_alt/custom/
```

Then upload the four new CSVs to the Dropbox folder under
`sc_inputs_alt/<your-variant>/`, and add the variant name to the
`alt_variants` vector in the `.qmd` setup chunk.

### Update the rendered PDF in git

The PDF is intentionally committed (it's a deliverable artifact). After any
prose change to the `.qmd`, re-render and commit the new `costco_australia_sc.pdf`
together with the `.qmd` change.

### Spawn a new worktree for parallel work

Claude Code's default worktree creation branches off whatever branch you're
on, NOT off `main`. If you want a clean branch off main, check out main first
or use `git worktree add` explicitly.

## Current state

The analysis is complete and on `main`:

- Plan of Attack §1–§3 PDFs in `deliverables/` (and the combined PDF).
- Pipeline parameterized; orchestrator for §4 alt-radius variants.
- Sixteen alt-radius CSVs committed under `data/sc_inputs_alt/` and uploaded
  to the Dropbox folder.
- `_sc_helpers.R` with `fit_end_date`, `predictors`, and
  `fit_one_costco_robust()`.
- `.qmd` covers §1–§6, renders cleanly end-to-end on a fresh environment.

## Where to find things

- **Authoritative spec:** [`deliverables/plan_of_attack_combined.pdf`](deliverables/plan_of_attack_combined.pdf)
- **Repo layout:** [`README.md`](README.md)
- **Reproduction details:** [`analysis/README.md`](analysis/README.md)
- **Section 1 artifacts:** [`section_1/`](section_1/)
- **Section 3 illustrative plots:** [`section_3/`](section_3/)
- **Dropbox folder URL** is hardcoded at the top of the `.qmd` setup chunk.

## Person & tone

Ryan reads the rendered PDF carefully and notices visible defects (double table
captions, double section numbering, dropped unicode glyphs). He prefers honest
prose to confident prose: when the data is mixed, say so rather than
overclaiming. He values reproducibility (`renv` is pinned for a reason) and
incremental, well-scoped commits over giant blobs.

When in doubt: read the plan-of-attack, render the .qmd, and check the actual
output before changing anything.
