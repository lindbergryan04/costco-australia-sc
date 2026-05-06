# Data quality issues, by variable

## `price`
- **Cross-registry unit conventions differ**: NSW prices are in cents/L
  (e.g. `158.7`), QLD prices are in tenths of cents (e.g. `1899` =
  `189.9 ¢/L`), WA prices are in cents/L. Mishandled units would silently
  contaminate the analysis. **Resolution**: each registry's ingest applies
  the appropriate scaling so the panel is uniform in cents/L.
- **Outliers**: price quotes below 80 ¢/L or above 280 ¢/L are
  implausible for Australian retail unleaded post-2018 (national average
  hovers 130–220 ¢/L). After filtering, the postcode-month panel contains
  **0** observations below 80 ¢/L and **0**
  above 280 ¢/L out of 17,953 total.
- **Contingency**: extreme tail values within a single postcode-month
  will be winsorized at the 1st and 99th percentile of the panel before
  synthetic-control fitting.

## `latitude` / `longitude`
- **Missing in NSW and WA historical files**: NSW FuelCheck historical
  XLSX records carry only address text (no coordinates); WA FuelWatch
  records carry address + postcode (no coordinates). QLD historical
  records DO include lat/lng inline.
- **Resolution**: coordinates were pulled from each state's live API
  (NSW FuelCheck `/v1/fuel/prices`, WA FuelWatch `/api/sites`) and joined
  to historical records by `(normalized_name, postcode)`. Coverage:
  NSW = 3,281 stations, WA = 921 stations, QLD = 1,882 stations,
  total = 6,084.
- **Limitation**: stations that closed, rebranded, or were re-numbered
  before the April 2026 live-API pull do not appear in the snapshot, so
  their historical rows fail the `(state, normalised name, postcode)`
  join. The snapshot misses **2,376 of 4,543 NSW historical stations
  (52.3%)** and **673 of 1,423 WA historical stations (47.3%)**. QLD
  is unaffected because its historical files carry lat/lng inline. The
  loss falls almost entirely on the donor pool (all four treated
  Costcos join cleanly), and 196 donor postcodes survive the downstream
  three-station / 24-month filters. Row-level impact on the analysis
  panel is reported in Section 2(g)'s funnel.

## `brand`
- **NSW Costco rename in May 2022**: every NSW Costco station was renamed
  in the registry from e.g. "Costco Marsden Park" to "Costco Marsden Park
  (Members only)" on 2 May 2022. This shows up as one station appearing
  to disappear and a new one appearing on the same day at the same
  address.
- **Resolution**: name-normalization strips the "(Members only)" suffix
  before matching, so the rename is invisible to the analysis pipeline.

## Coverage gaps in the treated panel
- **Coomera (QLD)**: pre-2020 coverage is sparse because the QLD scheme
  began in December 2018 and Coomera-area stations entered the registry
  gradually. The relevant pre-period for Coomera (Sep 2020 → May 2023)
  is fully covered.
- **Casuarina (WA)**: only ~3 unique stations within 5 km contribute to
  the treated mean (sparse coastal residential market). Treated mean is
  noisier than for the other three Costcos but coverage is 100 %.
- **Lake Macquarie (NSW)**: a small number of intermittent month-level
  gaps (largest 3 months) are present but do not affect a credible
  pre-period fit; Lake Macquarie spans 2016-12 → 2026-01.

## Costco-station completeness
- **10 Costco fuel stations identified in Australia.** 4 are usable as
  treated units (Coomera, Casuarina, Perth Airport, Lake Macquarie). 6
  are excluded: Marsden Park (only 11 pre-months), Auburn (opened Aug
  2025, 8 post-months), Canberra Airport (no pre-period observations in
  the postcode), Casula / North Lakes / Ipswich (warehouses opened
  before their state's registry began reporting). These appear in the
  project as descriptive context.

## Duplicate rows
- NSW: not duplicates; multiple price-change rows per station-day are
  legitimate operator price updates.
- QLD: same; price-change-event records, not snapshots.
- WA: at most one row per station-day-fuel; no duplicate concern.

## Donor-pool filtering
- Out of all postcodes with any non-Costco unleaded data, the donor pool
  drops **362** postcodes within 20 km of any Costco (potential
  contamination from Costco's competitive footprint), **446** with fewer
  than 3 stations on average per month (means too noisy), and **0** with
  fewer than 24 months of observations. **196** donor postcodes survive
  all filters: NSW = 104, QLD = 56, WA = 36.

## Station classification at the registry level
- **Treated**: 84 stations (within 5 km of one of the 4 treated Costcos).
- **Donor-eligible**: 3926 stations (>20 km from every Costco).
- **Excluded (5–20 km donut)**: 1970 stations (potential Costco
  spillover; excluded from both treated and donor groups).

## Source-document confidence
- Treatment dates were initially set to each Costco's first-appearance
  date in the relevant state's price registry, then cross-validated
  against trade press, Costco corporate announcements, and news coverage
  (Section 2(d)). Coomera matched its announced fuel-station opening
  exactly. Casuarina and Lake Macquarie had no fuel-station-specific
  announced date in public sources and retained the registry date.
  Perth Airport had a 52-day discrepancy: the ACAPMAg trade press
  reported the petrol station selling fuel on 19 February 2020, while
  the first FuelWatch record dates 11 April 2020. The announced date
  supersedes per the 30-day validation rule.
