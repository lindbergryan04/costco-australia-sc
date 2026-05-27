# Extract per-Costco trajectories + effect summaries from the .qmd's
# cached sc_fits chunk, write to CSVs for downstream Python plotting.
#
# Writes one trajectory CSV per Costco (slugified filenames) plus a
# combined all_trajectories.csv for small-multiples grids.
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
cache_dir      <- file.path(analysis_dir, "costco_australia_sc_cache", "pdf")
sc_fits_base   <- file.path(cache_dir, "sc_fits_16ff1d2970be3c8537f41797a5a53c2d")
rc1_base       <- file.path(cache_dir, "rc1_placebo_dd3307ecf040014885e8aa4af24d0e79")

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
source(helpers_path)

# ---- Load cache --------------------------------------------------------------
env <- new.env()
lazyLoad(sc_fits_base, envir = env)
sc_fits                 <- env$sc_fits
trajectories            <- env$trajectories
per_costco_pointwise_ci <- env$per_costco_pointwise_ci

rc1_env <- new.env()
lazyLoad(rc1_base, envir = rc1_env)
rc1_fits <- rc1_env$rc1_fits

cat("Loaded sc_fits with", nrow(sc_fits), "Costcos\n")
cat("Loaded rc1_fits with", nrow(rc1_fits), "placebo fits\n")

# ---- Per-Costco trajectories + pointwise CI bands ----------------------------
slugify <- function(x) {
  x |>
    tolower() |>
    str_replace_all("[^a-z0-9]+", "_") |>
    str_replace_all("^_|_$", "")
}

# Treatment dates pulled from sc_fits so the script stays in sync with the
# qmd's validated dates rather than hard-coding them.
treatment_dates <- sc_fits |>
  select(costco_key, treatment_date) |>
  deframe()

combined_rows <- list()

for (costco_name in trajectories$costco) {
  traj <- trajectories |>
    filter(costco == costco_name) |>
    pull(trajectory) |>
    pluck(1)

  ci <- per_costco_pointwise_ci |>
    filter(costco == costco_name) |>
    pull(ci) |>
    pluck(1)

  combined <- traj |>
    left_join(ci, by = "time_unit") |>
    mutate(
      treatment_date = as.Date(treatment_dates[[costco_name]]),
      synth_ci_lo    = synth_y + ci_lo,
      synth_ci_hi    = synth_y + ci_hi
    )

  out_path <- file.path(out_dir,
                        paste0(slugify(costco_name), "_trajectory.csv"))
  write_csv(combined, out_path)
  cat("Wrote", nrow(combined), "rows ->", out_path, "\n")

  combined_rows[[costco_name]] <- combined
}

all_trajectories <- bind_rows(combined_rows)
write_csv(all_trajectories, file.path(out_dir, "all_trajectories.csv"))
cat("Wrote combined ->",
    file.path(out_dir, "all_trajectories.csv"),
    "(", nrow(all_trajectories), "rows across",
    n_distinct(all_trajectories$costco), "Costcos )\n")

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

# ---- RC1 placebo-in-time trajectory (Perth Airport) --------------------------
# Slide 11 uses Perth Airport's placebo fit: a synthetic fitted as if Costco
# arrived 12 months earlier than it really did. Pass criterion: no visible
# divergence at the fake date — the audience sees the lines stay together
# until the real opening.
pa_placebo_row <- rc1_fits |> filter(costco_key == "Perth Airport")
pa_placebo_fit <- pa_placebo_row$fit[[1]]

pa_placebo_traj <- trajectory(pa_placebo_fit, "Perth Airport")
pa_placebo_ci   <- permutation_ci_pointwise(pa_placebo_fit)

pa_placebo_combined <- pa_placebo_traj |>
  left_join(pa_placebo_ci, by = "time_unit") |>
  mutate(
    real_treatment_date    = as.Date(pa_placebo_row$treatment_date),
    placebo_treatment_date = as.Date(pa_placebo_row$placebo_date),
    synth_ci_lo            = synth_y + ci_lo,
    synth_ci_hi            = synth_y + ci_hi
  )

placebo_path <- file.path(out_dir, "perth_airport_placebo_trajectory.csv")
write_csv(pa_placebo_combined, placebo_path)
cat("Wrote", nrow(pa_placebo_combined), "rows ->", placebo_path, "\n")

# Mean placebo gap + 95% donor-permutation CI on the placebo "post" window
# (placebo_date to real_date). This is the rigorous pass/fail signal: a CI
# that straddles zero means donor noise is wider than the placebo gap.
pa_placebo_ci_mean <- permutation_ci_mean_gap(
  pa_placebo_fit, pa_placebo_row$placebo_date
)

pa_placebo_window <- pa_placebo_combined |>
  filter(time_unit >= month_anchor(pa_placebo_row$placebo_date),
         time_unit <  month_anchor(pa_placebo_row$treatment_date))
pa_placebo_mean_gap <- mean(pa_placebo_window$gap, na.rm = TRUE)

placebo_summary <- tibble(
  costco          = "Perth Airport",
  mean_placebo_gap_cents = round(pa_placebo_mean_gap, 3),
  ci_lo           = round(unname(pa_placebo_ci_mean[["lo"]]), 3),
  ci_hi           = round(unname(pa_placebo_ci_mean[["hi"]]), 3),
  placebo_date    = as.Date(pa_placebo_row$placebo_date),
  real_date       = as.Date(pa_placebo_row$treatment_date)
)
placebo_summary_path <- file.path(out_dir, "perth_airport_placebo_summary.csv")
write_csv(placebo_summary, placebo_summary_path)
cat("Wrote placebo summary ->", placebo_summary_path, "\n")
print(placebo_summary)
