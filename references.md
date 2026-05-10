# References

External sources used in Sections 1, 2, and 3 of the Plan of Attack for
the Costco Australia synthetic-control study (research question: does
Costco gas-station entry into an Australian local market cause nearby
competitor stations to lower their retail fuel prices?).

## 1. Primary data sources

### NSW FuelCheck (historical monthly Excel files)

- URL: https://data.nsw.gov.au/ (NSW Government open-data portal; FuelCheck dataset)
- Used in Section 1.1 as one of the three state fuel-price registries
  feeding the analysis panel: 93 monthly XLSX files covering Dec 2016 –
  Jan 2026, totalling 4,401,971 price-update records across 4,813 NSW
  stations. Provides the raw price observations that become the
  postcode-month outcome series for NSW (and ACT, post-Nov 2023) used in
  both the treated 5 km rings and the donor pool.

### NSW FuelCheck live API

- Endpoint: `/v1/fuel/prices` on the NSW FuelCheck API (registered via
  https://api.nsw.gov.au/Account/Register)
- Used in Sections 1.1 and 2(d)/(f) for a one-time pull of the live
  station list to recover station latitude/longitude, which are missing
  from the historical XLSX files. Coordinates were joined to the
  historical NSW rows by `(normalized_name, postcode)` (3,281 NSW
  stations matched), enabling the 5 km treated-radius and 20 km
  donor-buffer geographic classifications.

### Queensland Fuel Price Reporting Scheme

- URL: https://data.qld.gov.au/ (Queensland Treasury open-data portal;
  Fuel Price Reporting Scheme dataset)
- Used in Section 1.2 as the second state registry: 85 monthly CSVs
  covering Dec 2018 – Dec 2025, 4,970,650 price-change records across
  1,883 QLD stations, with WGS84 station coordinates included inline (so
  no separate live-API join is needed for QLD). Feeds the QLD portion of
  the donor pool and the Coomera treated panel.

### WA FuelWatch (historical monthly CSV files)

- URL: https://data.wa.gov.au/ (Western Australia Government open-data
  portal; FuelWatch dataset)
- Used in Section 1.3 as the third state registry: 100 monthly CSVs
  covering Jan 2018 – Apr 2026, 8,047,153 daily-snapshot records across
  1,423 WA stations. Unlike NSW and QLD, WA publishes one record per
  station-day regardless of price change, so WA passes through the
  carry-forward step in Section 2(e) unchanged. Feeds the Casuarina and
  Perth Airport treated panels and the WA donor pool.

### WA FuelWatch live API

- Endpoint: `/api/sites` on the WA FuelWatch live API
- Used in Sections 1.3 and 2(d)/(f) for a one-time pull of station
  coordinates (the historical FuelWatch CSVs contain only address and
  postcode). Coordinates were joined to historical WA rows by
  `(normalized_name, postcode)` (921 WA stations matched), supporting
  great-circle distance computation to each Costco.

### Hand-collected Costco metadata (`data/catalogs/usable_costcos.csv`)

- File: `data/catalogs/usable_costcos.csv` in this repository
- A 10-row hand-compiled catalogue of every Australian Costco fuel
  station: state, suburb, postcode, latitude/longitude, treatment date,
  and treated/excluded status. Used in Section 1.4 to define the
  treatment universe and in Section 2(d)/(f) as the join key for
  building treated panels and the post-opening binary indicator. Updated
  during the Section 2(d) treatment-date validation pass (Perth
  Airport's date was revised to 2020-02-19; see ACAPMAg below).

## 2. Treatment-date validation sources (Section 2(d))

### Coomera (QLD): fuel-station opening 23 May 2023

- Retail World, "Costco Wholesale unveils Coomera Fuel Station":
  https://retailworldmagazine.com.au/costco-wholesale-unveils-coomera-fuel-station/
  Used in Section 2(d) as the explicit fuel-station-specific
  corroborating source confirming the Coomera fuel station opened on
  23 May 2023, exactly matching the QLD registry first-appearance date,
  so the registry date is retained for treatment.

- Servo Pro, "Costco introduces new fuel station and warehouse in
  Coomera, QLD":
  https://servopro.com.au/costco-introduces-new-fuel-station-and-warehouse-in-coomera-qld/
  Used as a secondary corroborating trade-press article supporting the
  Coomera fuel-station and warehouse opening; backstop for the Retail
  World source above.

### Casuarina (WA): only warehouse-specific date in public sources

- Retail World, "Costco Wholesale unveils $80.7m warehouse at
  Casuarina, Perth":
  https://retailworldmagazine.com.au/costco-wholesale-unveils-80-7m-warehouse-at-casuarina-perth/
  Used in Section 2(d) to document that the only public Casuarina
  opening date is the warehouse opening (7 December 2022), with no
  fuel-station-specific date available. Because warehouses and fuel
  stations at Costco Australia regularly open weeks apart, this source
  cannot be used for fuel-station treatment validation, so the WA
  FuelWatch registry first-appearance date (11 Nov 2022) is retained.

- Petrolspy, Casuarina station entry:
  https://petrolspy.com.au/map/station/636dd3e9b9914209d956f64b
  Used in Section 2(d) as supporting context: the third-party fuel-price
  monitoring service began monitoring this station around 10 Nov 2022,
  consistent with the FuelWatch first-appearance date of 11 Nov 2022.
  Not a primary opening source.

### Perth Airport (WA): basis of the only treatment-date revision

- ACAPMAg (Australian Convenience and Petroleum Marketers Association
  magazine), "Costco opens petrol station near Perth Airport":
  https://acapmag.com.au/2020/02/costco-opens-petrol-station-near-perth-airport/
  Used in Section 2(d) as the basis for the Perth Airport treatment-date
  revision. The 19 Feb 2020 trade-press article explicitly distinguishes
  the petrol station (open that day, with bowser price quoted at
  $1.18/L) from the warehouse (separately opening on 19 March 2020).
  Because this is 52 days before the FuelWatch registry first-appearance
  (11 Apr 2020), exceeding the 30-day rule, the announced date
  supersedes, and `usable_costcos.csv` /
  `data/sc_inputs/treated_metadata.csv` were updated to 2020-02-19.

### Lake Macquarie (NSW): no fuel-station-specific date located

- Petrolspy, Lake Macquarie station entry:
  https://petrolspy.com.au/map/station/611b6cdab9914250cf968ffd
  Used in Section 2(d) to document that no primary-source
  fuel-station-specific opening date could be located in the public
  record for Lake Macquarie; the NSW FuelCheck registry first-appearance
  date (2 May 2022) is retained as the treatment date.

## 3. Methods and academic literature

### Houde (2012): IO literature on retail-gasoline spatial competition

- Houde, Jean-François. "Spatial Differentiation and Vertical Mergers in
  Retail Markets for Gasoline." American Economic Review 102 (5):
  2147–82, 2012.
  https://www.aeaweb.org/articles?id=10.1257/aer.102.5.2147
- Cited in Section 2(b) (Table 1, "Asymmetric radii") as part of the
  economics evidence base that retail-gasoline price effects are
  concentrated within roughly 1–5 miles. Used to defend the choice of a
  conservative 5 km treated radius and a 20 km donor buffer.

### Eckert (2013): IO literature survey on gasoline retailing

- Eckert, Andrew. "Empirical Studies of Gasoline Retailing: A Guide to
  the Literature." Journal of Economic Surveys 27 (1): 140–166, 2013.
  https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-6419.2011.00698.x
- Cited alongside Houde (2012) in Section 2(b) as a survey of empirical
  gasoline-retailing studies that bracket the retail price-competition
  spillover range used to motivate the 5 km treated / 20 km donor
  geometry.

### Abadie, Diamond & Hainmueller (2010): synthetic-control method

- Abadie, A., Diamond, A., and Hainmueller, J. "Synthetic Control
  Methods for Comparative Case Studies: Estimating the Effect of
  California's Tobacco Control Program." Journal of the American
  Statistical Association 105 (490): 493–505, 2010.
- The canonical synthetic-control method, foundational to the project's
  identification strategy. Sections 1–3 use the term "synthetic control"
  without inline citation, treating the method as standard; this
  references doc is the only place the original paper is formally
  cited. Provides the weight-fitting framework that takes the
  treated-ring and donor-postcode panels built in Sections 1–2 and
  produces the counterfactual estimates evaluated in Section 3.

Notes on ambiguity: the Petrolspy entries for Casuarina and Lake
Macquarie are best understood as supporting context rather than primary
opening-date sources; they are listed under treatment-date validation
because that is the only place their information is consulted. The
`pysyncon` library and `reportlab` are inferred from the project
description (synthetic control + ReportLab-built PDFs); they are tools
rather than cited works.
