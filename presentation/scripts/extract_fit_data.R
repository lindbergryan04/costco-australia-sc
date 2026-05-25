# Extract Perth Airport trajectory + per-Costco effect summaries from the
# .qmd's cached sc_fits chunk, write to CSVs for downstream Python plotting.
#
# Usage: from analysis/, run
#   Rscript ../presentation/scripts/extract_fit_data.R

suppressPackageStartupMessages({
  library(tidyverse)
  library(tidysynth)
  library(lubridate)
})

# Project paths (relative to analysis/, where this is invoked)
analysis_dir   <- normalizePath(".")
project_root   <- normalizePath(file.path(analysis_dir, ".."))
out_dir        <- file.path(project_root, "presentation", "data")
helpers_path   <- file.path(analysis_dir, "_sc_helpers.R")
cache_base     <- file.path(analysis_dir, "costco_australia_sc_cache", "pdf",
                            "sc_fits_16ff1d2970be3c8537f41797a5a53c2d")

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
source(helpers_path)

# ---- Load cache --------------------------------------------------------------
env <- new.env()
lazyLoad(cache_base, envir = env)
sc_fits                 <- env$sc_fits
trajectories            <- env$trajectories
per_costco_pointwise_ci <- env$per_costco_pointwise_ci

cat("Loaded sc_fits with", nrow(sc_fits), "Costcos\n")

# ---- Perth Airport: trajectory + pointwise CI band ---------------------------
pa_traj <- trajectories |>
  filter(costco == "Perth Airport") |>
  pull(trajectory) |>
  pluck(1)

pa_ci <- per_costco_pointwise_ci |>
  filter(costco == "Perth Airport") |>
  pull(ci) |>
  pluck(1)

pa_combined <- pa_traj |>
  left_join(pa_ci, by = "time_unit") |>
  mutate(
    treatment_date = as.Date("2020-02-19"),
    synth_ci_lo    = synth_y + ci_lo,
    synth_ci_hi    = synth_y + ci_hi
  )

write_csv(pa_combined, file.path(out_dir, "perth_airport_trajectory.csv"))
cat("Wrote", nrow(pa_combined), "rows ->",
    file.path(out_dir, "perth_airport_trajectory.csv"), "\n")

# ---- Per-Costco effect summary (point + 95% CI) ------------------------------
table_1 <- pmap_dfr(
  list(sc_fits$fit, sc_fits$costco_key, sc_fits$state,
       sc_fits$treatment_date, sc_fits$n_post_months),
  effect_summary
)

write_csv(table_1, file.path(out_dir, "effect_summary.csv"))
cat("Wrote", nrow(table_1), "Costcos ->",
    file.path(out_dir, "effect_summary.csv"), "\n")
print(table_1)
