# analysis/_sc_helpers.R
#
# Synthetic-control helpers for the Costco Australia analysis. Wraps
# tidysynth so the main .qmd stays readable. Sourced from
# costco_australia_sc.qmd.
#
# Required packages:
#   install.packages(c("tidyverse", "tidysynth", "lubridate",
#                      "kableExtra", "patchwork", "scales"))

suppressPackageStartupMessages({
  library(tidyverse)
  library(tidysynth)
  library(lubridate)
})

# Treatment dates in the panel are stored on the 15th of each month
# (mid-month placeholder). This helper snaps a real-world treatment
# date to that placeholder so tidysynth's `i_time` lines up with the
# panel's date column.
month_anchor <- function(d) {
  floor_date(as.Date(d), "month") + days(14)
}

# ---- Core fit ----------------------------------------------------------------

# Fit one synthetic control for a single treated Costco.
#
# Combines the treated Costco's 5km-ring panel with same-state donor
# postcodes into the long format tidysynth expects, then fits with
# generate_placebos = TRUE so the donor-permutation distribution is
# computed in the same pass (used downstream for 95% CIs).
#
# Predictors are pre-period yearly means of mean_price_cents — enough
# leverage for tidysynth to fit weights that track the treated
# trajectory, while keeping the spec compact.
#
# Returns a tidysynth object compatible with grab_* extractors.
#
# Optional `fit_end_date` shortens the predictor / weight-optimization
# window (used by §4 Robustness Check 5: fit on pre-period minus the
# last 12 months, then score the synthetic on the untouched 12-month
# holdout). When NULL the function behaves identically to the headline
# spec, so cached fits in §3 are unaffected by this argument's addition.
#
# `predictors` chooses the matching predictor set. The default
# "yearly_means" (one predictor per pre-period calendar year) is what
# §3 uses; "overall_mean" uses a single pre-period mean instead and is
# needed when the fit window is short enough that adjacent yearly
# means become near-collinear (the QP solver in kernlab::ipop returns
# a singular-matrix error in that case). §4 RC1 (placebo in time)
# and RC5 (12-month holdout) both shorten the window.
fit_one_costco <- function(treated_units, donor_pool, costco_name,
                           treatment_date, state, fit_end_date = NULL,
                           predictors = c("yearly_means", "overall_mean")) {

  predictors <- match.arg(predictors)
  treatment_month <- month_anchor(treatment_date)
  fit_end_month   <- if (is.null(fit_end_date)) treatment_month
                     else month_anchor(fit_end_date)

  # Treated unit: drop any NA-outcome months entirely (e.g. Lake
  # Macquarie's intermittent gaps). The non-NA treated months define
  # the entire panel time grid.
  treated_focal <- treated_units |>
    filter(.data$costco_key == costco_name) |>
    transmute(unit    = costco_name,
              time    = as.Date(.data$date),
              outcome = .data$mean_price_cents) |>
    filter(!is.na(.data$outcome))

  if (nrow(treated_focal) == 0) {
    stop(sprintf("No non-NA observations for treated Costco %s.",
                 costco_name))
  }

  treated_dates <- treated_focal |> pull(time) |> unique() |> sort()
  pre_dates     <- treated_dates[treated_dates < fit_end_month]

  # Donors: restrict to the treated time grid, then keep only donors
  # with non-NA outcomes at *every* treated-grid date (pre AND post).
  # tidysynth/Synth's matrix operations need a consistent grid across
  # pre-period fitting and post-period projection; any NA in Z0 or
  # mismatched length in Y_U triggers a hard error.
  donor_state <- donor_pool |>
    filter(.data$state == .env$state) |>
    transmute(unit    = paste0("pc_", .data$postcode),
              time    = as.Date(.data$date),
              outcome = .data$mean_price_cents) |>
    filter(.data$time %in% treated_dates)

  donor_complete <- donor_state |>
    group_by(unit) |>
    summarize(n_obs = sum(!is.na(outcome)), .groups = "drop") |>
    filter(n_obs == length(treated_dates)) |>
    pull(unit)

  if (length(donor_complete) < 5) {
    stop(sprintf(
      "Only %d donors with complete pre+post coverage for %s; need at least 5.",
      length(donor_complete), costco_name
    ))
  }

  donor_state <- donor_state |>
    filter(unit %in% donor_complete)

  panel <- bind_rows(treated_focal, donor_state)

  pre_years <- unique(year(pre_dates))

  spec <- panel |>
    synthetic_control(
      outcome           = outcome,
      unit              = unit,
      time              = time,
      i_unit            = costco_name,
      i_time            = treatment_month,
      generate_placebos = TRUE
    )

  if (predictors == "yearly_means") {
    for (yr in pre_years) {
      yr_window <- pre_dates[year(pre_dates) == yr]
      pred_name <- paste0("mean_", yr)
      spec <- spec |>
        generate_predictor(
          time_window = yr_window,
          !!pred_name := mean(outcome, na.rm = TRUE)
        )
    }
  } else {
    # Single pre-period mean. Robust to short fit windows where adjacent
    # yearly means become near-collinear.
    spec <- spec |>
      generate_predictor(
        time_window = pre_dates,
        mean_pre := mean(outcome, na.rm = TRUE)
      )
  }

  spec |>
    generate_weights(optimization_window = pre_dates) |>
    generate_control()
}

# Robust wrapper around fit_one_costco. Tries the headline `yearly_means`
# predictor strategy first; on a singular-matrix error from kernlab::ipop
# (a recurring issue for alt-radius panels with sparse WA donors or
# truncated pre-periods) falls back to the single `overall_mean`
# predictor. Returns NULL if both strategies fail. Used by every §4
# robustness check so a single fit's collinearity issue doesn't drop a
# whole table.
fit_one_costco_robust <- function(treated_units, donor_pool, costco_name,
                                  treatment_date, state,
                                  fit_end_date = NULL) {
  last_err <- NULL
  for (strat in c("yearly_means", "overall_mean")) {
    res <- tryCatch(
      fit_one_costco(treated_units, donor_pool, costco_name,
                     treatment_date, state, fit_end_date,
                     predictors = strat),
      error = function(e) e
    )
    if (!inherits(res, "error")) return(res)
    last_err <- res
  }
  warning(sprintf("All predictor strategies failed for %s: %s",
                  costco_name, conditionMessage(last_err)))
  NULL
}

# ---- Extractors --------------------------------------------------------------

trajectory <- function(synth_obj, costco_name) {
  synth_obj |>
    grab_synthetic_control(placebo = FALSE) |>
    mutate(costco = costco_name,
           gap = .data$real_y - .data$synth_y)
}

donor_weights_top <- function(synth_obj, threshold = 0.01) {
  synth_obj |>
    grab_unit_weights(placebo = FALSE) |>
    filter(.data$weight > threshold) |>
    arrange(desc(.data$weight))
}

post_pre_ratio <- function(synth_obj) {
  sig <- synth_obj |> grab_significance()
  treated_row <- sig |> filter(.data$type == "Treated")
  treated_row$mspe_ratio[1]
}

# 95% donor-permutation CI on the post-treatment mean gap. Treats each
# donor in turn as a placebo, computes its mean post-treatment gap, and
# returns the empirical 2.5 / 97.5 percentile across donors.
permutation_ci_mean_gap <- function(synth_obj, treatment_date, alpha = 0.05) {
  treatment_month <- month_anchor(treatment_date)
  placebos <- synth_obj |>
    grab_synthetic_control(placebo = TRUE) |>
    filter(.data$time_unit >= treatment_month) |>
    group_by(.data$.placebo) |>
    summarize(mean_gap = mean(.data$real_y - .data$synth_y, na.rm = TRUE),
              .groups = "drop") |>
    pull(mean_gap)

  c(lo = unname(quantile(placebos, alpha / 2,       na.rm = TRUE)),
    hi = unname(quantile(placebos, 1 - alpha / 2,   na.rm = TRUE)))
}

# 95% donor-permutation CI on the gap at each time point. Used for the
# shaded CI band on Figure 1's per-Costco trajectories.
permutation_ci_pointwise <- function(synth_obj, alpha = 0.05) {
  synth_obj |>
    grab_synthetic_control(placebo = TRUE) |>
    group_by(.data$time_unit) |>
    summarize(
      ci_lo = quantile(.data$real_y - .data$synth_y, alpha / 2,
                       na.rm = TRUE),
      ci_hi = quantile(.data$real_y - .data$synth_y, 1 - alpha / 2,
                       na.rm = TRUE),
      .groups = "drop"
    )
}

# ---- Summary tables ----------------------------------------------------------

# One-row effect-size summary per Costco. Feeds Table 1 in Section 3.5.
effect_summary <- function(synth_obj, costco_name, state, treatment_date,
                           post_months) {
  treatment_month <- month_anchor(treatment_date)
  traj <- trajectory(synth_obj, costco_name)

  pre_mean <- traj |>
    filter(.data$time_unit < treatment_month) |>
    pull(.data$real_y) |> mean(na.rm = TRUE)

  post_gap <- traj |>
    filter(.data$time_unit >= treatment_month) |>
    pull(.data$gap) |> mean(na.rm = TRUE)

  ci <- permutation_ci_mean_gap(synth_obj, treatment_date)

  tibble(
    costco              = costco_name,
    state               = state,
    pre_mean_cents      = pre_mean,
    mean_post_gap_cents = post_gap,
    pct_reduction       = 100 * post_gap / pre_mean,
    post_pre_ratio      = post_pre_ratio(synth_obj),
    ci_lo               = ci[["lo"]],
    ci_hi               = ci[["hi"]],
    post_months         = post_months
  )
}

# One-row pre-period fit-quality summary per Costco. Feeds Table 2.
fit_quality_summary <- function(synth_obj, costco_name, treatment_date,
                                pre_months) {
  treatment_month <- month_anchor(treatment_date)
  traj <- trajectory(synth_obj, costco_name)

  pre_traj <- traj |> filter(.data$time_unit < treatment_month)
  pre_mean <- mean(pre_traj$real_y, na.rm = TRUE)
  pre_err  <- sqrt(mean(
    (pre_traj$real_y - pre_traj$synth_y)^2, na.rm = TRUE
  ))

  weights <- donor_weights_top(synth_obj, threshold = 0)
  top3_share <- weights |>
    slice_head(n = 3) |>
    pull(.data$weight) |> sum()

  tibble(
    costco           = costco_name,
    pre_months       = pre_months,
    pre_rmspe_cents  = pre_err,
    pre_rmspe_pct    = 100 * pre_err / pre_mean,
    top3_donor_share = top3_share
  )
}

# ---- Event study -------------------------------------------------------------

# Convert a per-Costco trajectory to relative-month (months since
# treatment). Used to stack the four Costcos for Figure 3.
relative_month_gaps <- function(trajectory_df, treatment_date) {
  treatment_month <- month_anchor(treatment_date)
  trajectory_df |>
    select(-any_of("costco")) |>
    mutate(rel_month = (year(.data$time_unit) - year(treatment_month)) * 12
                     + (month(.data$time_unit) - month(treatment_month)))
}
