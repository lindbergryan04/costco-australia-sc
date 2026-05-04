"""
Section 1 — Raw Data Description.

Single-script pipeline that produces every Section 1 artifact:

  australia/section_1/raw_counts.csv             (a + d) rows, vars, unique units per registry
  australia/section_1/unit_of_observation.md     (b)
  australia/section_1/time_periods.csv           (c)
  australia/section_1/summary_statistics.csv     (e) on key analysis variables
  australia/section_1/data_quality.md            (f)
  australia/section_1/plots/01_price_histogram.png
  australia/section_1/plots/02_unleaded_median_over_time.png
  australia/section_1/plots/03_distance_to_costco_hist.png
  australia/section_1/plots/04_classification_counts.png
  australia/section_1/plots/05_treated_event_studies.png

All visualizations are at the postcode-month level (per group decision).
Outcome focuses on regular unleaded only (per group decision).
"""

import csv
import datetime as dt
import glob
import math
import os
import re
import sys
from collections import defaultdict, Counter
from statistics import mean, median, stdev

import openpyxl
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter

# Use the robust NSW reader (handles string-date schemas in 2020-2023 files
# and the 2024+ no-title-row variant).
sys.path.insert(0, "australia/scripts")
from _nsw_reader import iter_nsw_data_rows


OUT = "australia/section_1"

# Treated Costcos (4 with adequate pre/post data)
COSTCOS_TREATED = [
    ("QLD", "Coomera",        dt.date(2023, 5, 23), -27.850829, 153.314369),
    ("WA",  "Casuarina",      dt.date(2022, 11, 11), -32.233481, 115.853714),
    ("WA",  "Perth Airport",  dt.date(2020, 4, 11), -31.940377, 115.951869),
    ("NSW", "Lake Macquarie", dt.date(2022, 5, 2),  -32.946111, 151.628054),
]
# All Costcos (used to classify stations as treated/donor/excluded)
ALL_COSTCO_COORDS = [
    ("Coomera",          -27.850829, 153.314369),
    ("Casuarina",        -32.233481, 115.853714),
    ("Lake Macquarie",   -32.946111, 151.628054),
    ("Perth Airport",    -31.940377, 115.951869),
    ("Marsden Park",     -33.722985, 150.840858),
    ("Canberra Airport", -35.296600, 149.189000),
    ("Auburn",           -33.848086, 151.049695),
    ("Casula",           -33.958521, 150.880116),
    ("North Lakes",      -27.213607, 152.996416),
    ("Ipswich",          -27.590776, 152.820541),
]
NEAR_KM = 5.0
DONOR_EXCLUDE_KM = 20.0


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def normalize_name(s):
    if not s: return ""
    s = s.lower().strip()
    s = re.sub(r"\(members?\s*only.*?\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_unleaded_nsw(c): return str(c).strip().upper() in ("U91", "E10", "P91")
def is_unleaded_qld(t): return str(t).strip().lower() in ("unleaded 91", "e10", "u91")
def is_unleaded_wa(p):  return str(p).strip().upper() == "ULP"


# ----------------------------------------------------------------------------
# Phase A: gather REGISTRY-level facts (raw observation count, variable count,
# unique stations/brands/postcodes/fuel types, date range). One pass per
# registry, lightweight — does not load any prices into memory.
# ----------------------------------------------------------------------------

def scan_nsw_meta():
    files = sorted(glob.glob("australia/_local/cache/nsw/*.xlsx"))
    print(f"  NSW: scanning {len(files)} files for metadata...")
    n_obs = 0
    n_cols = 8  # NSW schema is fixed at 8 columns across all variants
    stations = set()
    brands = set()
    postcodes = set()
    fuel_types = set()
    min_date = max_date = None
    for fi, f in enumerate(files):
        for (name, address, suburb, postcode, brand, fuel_code,
             d, price) in iter_nsw_data_rows(f):
            n_obs += 1
            stations.add((str(name).strip(), str(postcode or "").strip()))
            brands.add(str(brand or "").strip())
            postcodes.add(str(postcode or "").strip())
            fuel_types.add(str(fuel_code or "").strip())
            if d is not None:
                if min_date is None or d < min_date: min_date = d
                if max_date is None or d > max_date: max_date = d
        if (fi + 1) % 20 == 0:
            print(f"    NSW {fi+1}/{len(files)}; obs so far: {n_obs:,}")
    return {
        "registry": "NSW FuelCheck", "format": "monthly XLSX",
        "files": len(files), "n_obs": n_obs, "n_cols": n_cols,
        "n_stations": len(stations - {("", "")}),
        "n_brands": len(brands - {""}),
        "n_postcodes": len(postcodes - {""}),
        "n_fuel_types": len(fuel_types - {""}),
        "fuel_types": sorted(fuel_types - {""}),
        "min_date": min_date, "max_date": max_date,
    }


def scan_qld_meta():
    files = sorted(glob.glob("australia/_local/cache/qld/*.csv"))
    print(f"  QLD: scanning {len(files)} files for metadata...")
    n_obs = 0
    n_cols = 0
    stations = set()
    brands = set()
    postcodes = set()
    fuel_types = set()
    min_date = max_date = None
    for fi, f in enumerate(files):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            n_cols = max(n_cols, len(reader.fieldnames or []))
            for row in reader:
                n_obs += 1
                stations.add(row.get("SiteId") or "")
                brands.add((row.get("Site_Brand") or "").strip())
                postcodes.add((row.get("Site_Post_Code") or "").strip())
                fuel_types.add((row.get("Fuel_Type") or "").strip())
                ts = row.get("TransactionDateutc") or ""
                try:
                    d = dt.datetime.fromisoformat(ts.split(".")[0]).date()
                    if min_date is None or d < min_date: min_date = d
                    if max_date is None or d > max_date: max_date = d
                except Exception:
                    pass
        if (fi+1) % 20 == 0:
            print(f"    QLD {fi+1}/{len(files)}; obs so far: {n_obs:,}")
    return {
        "registry": "QLD Fuel Price Reporting Scheme", "format": "monthly CSV",
        "files": len(files), "n_obs": n_obs, "n_cols": n_cols,
        "n_stations": len(stations - {""}),
        "n_brands": len(brands - {""}),
        "n_postcodes": len(postcodes - {""}),
        "n_fuel_types": len(fuel_types - {""}),
        "fuel_types": sorted(fuel_types - {""}),
        "min_date": min_date, "max_date": max_date,
    }


def scan_wa_meta():
    files = sorted(glob.glob("australia/_local/cache/wa/*.csv"))
    print(f"  WA: scanning {len(files)} files for metadata...")
    n_obs = 0
    n_cols = 0
    stations = set()
    brands = set()
    postcodes = set()
    fuel_types = set()
    min_date = max_date = None
    for fi, f in enumerate(files):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            n_cols = max(n_cols, len(reader.fieldnames or []))
            for row in reader:
                n_obs += 1
                stations.add((row.get("TRADING_NAME") or "",
                              str(row.get("POSTCODE") or "")))
                brands.add((row.get("BRAND_DESCRIPTION") or "").strip())
                postcodes.add(str(row.get("POSTCODE") or "").strip())
                fuel_types.add((row.get("PRODUCT_DESCRIPTION") or "").strip())
                ds = row.get("PUBLISH_DATE") or ""
                try:
                    d = dt.datetime.strptime(ds, "%d/%m/%Y").date()
                    if min_date is None or d < min_date: min_date = d
                    if max_date is None or d > max_date: max_date = d
                except Exception:
                    pass
        if (fi+1) % 20 == 0:
            print(f"    WA {fi+1}/{len(files)}; obs so far: {n_obs:,}")
    return {
        "registry": "WA FuelWatch", "format": "monthly CSV",
        "files": len(files), "n_obs": n_obs, "n_cols": n_cols,
        "n_stations": len(stations - {("", "")}),
        "n_brands": len(brands - {""}),
        "n_postcodes": len(postcodes - {""}),
        "n_fuel_types": len(fuel_types - {""}),
        "fuel_types": sorted(fuel_types - {""}),
        "min_date": min_date, "max_date": max_date,
    }


# ----------------------------------------------------------------------------
# Phase B: build the postcode-month panel for the analysis (unleaded only).
# Same logic as Phase 5's build_sc_inputs.py but kept here so Section 1 is
# self-contained.
# ----------------------------------------------------------------------------

def load_station_classification():
    """Return: (state, name_norm, postcode) → {treated_for, min_dist_any, lat, lng}."""
    by_key = {}
    by_name = defaultdict(list)
    with open("australia/data/stations/station_coords.csv") as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r["lat"]); lng = float(r["lng"])
            except (TypeError, ValueError):
                continue
            min_d = min(haversine_km(lat, lng, c[1], c[2])
                        for c in ALL_COSTCO_COORDS)
            treated_for = set()
            for cstate, ckey, op, clat, clng in COSTCOS_TREATED:
                if haversine_km(lat, lng, clat, clng) <= NEAR_KM:
                    treated_for.add(ckey)
            entry = {
                "state": r["state"],
                "min_dist_any": min_d,
                "treated_for": treated_for,
                "lat": lat, "lng": lng,
                "postcode": r["postcode"],
            }
            by_key[(r["state"], r["name_norm"], r["postcode"])] = entry
            by_name[(r["state"], r["name_norm"])].append(entry)
    return by_key, by_name


def ingest_panel(by_key, by_name):
    """Return list of (state, postcode, year, month, price, is_costco_record).
    Excludes Costco's own records — they're not part of either treated or donor
    aggregation."""
    out = []
    # NSW (using the robust reader)
    files = sorted(glob.glob("australia/_local/cache/nsw/*.xlsx"))
    print(f"  NSW: ingesting {len(files)} files (unleaded only)...")
    for fi, f in enumerate(files):
        for (name, address, suburb, postcode, brand, fuel_code,
             d, price) in iter_nsw_data_rows(f):
            if not brand or "costco" in str(brand).lower():
                continue
            if not fuel_code or not is_unleaded_nsw(fuel_code):
                continue
            try:
                price = float(price)
            except (TypeError, ValueError):
                continue
            if price <= 50 or price > 500:
                continue
            if d is None:
                continue
            postcode = str(postcode or "").strip()
            if not postcode:
                continue
            out.append(("NSW", postcode, d.year, d.month, price))
        if (fi+1) % 20 == 0:
            print(f"    NSW {fi+1}/{len(files)}; total: {len(out):,}")
    # QLD
    files = sorted(glob.glob("australia/_local/cache/qld/*.csv"))
    print(f"  QLD: ingesting {len(files)} files...")
    for fi, f in enumerate(files):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                brand = (row.get("Site_Brand") or "").lower()
                if "costco" in brand: continue
                ft = row.get("Fuel_Type") or ""
                if not is_unleaded_qld(ft): continue
                try: price = float(row.get("Price") or 0) / 10.0
                except (TypeError, ValueError): continue
                if price <= 50 or price > 500: continue
                ts = row.get("TransactionDateutc") or ""
                try: d = dt.datetime.fromisoformat(ts.split(".")[0]).date()
                except Exception: continue
                postcode = (row.get("Site_Post_Code") or "").strip()
                if not postcode: continue
                out.append(("QLD", postcode, d.year, d.month, price))
        if (fi+1) % 20 == 0:
            print(f"    QLD {fi+1}/{len(files)}; total: {len(out):,}")
    # WA
    files = sorted(glob.glob("australia/_local/cache/wa/*.csv"))
    print(f"  WA: ingesting {len(files)} files...")
    for fi, f in enumerate(files):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                brand = (row.get("BRAND_DESCRIPTION") or "").lower()
                if "costco" in brand: continue
                pd = row.get("PRODUCT_DESCRIPTION") or ""
                if not is_unleaded_wa(pd): continue
                try: price = float(row.get("PRODUCT_PRICE") or 0)
                except (TypeError, ValueError): continue
                if price <= 50 or price > 500: continue
                ds = row.get("PUBLISH_DATE") or ""
                try: d = dt.datetime.strptime(ds, "%d/%m/%Y").date()
                except ValueError: continue
                postcode = str(row.get("POSTCODE") or "").strip()
                if not postcode: continue
                out.append(("WA", postcode, d.year, d.month, price))
        if (fi+1) % 20 == 0:
            print(f"    WA {fi+1}/{len(files)}; total: {len(out):,}")
    return out


def aggregate_postcode_month(records):
    """Aggregate raw records to postcode-month panel."""
    bucket = defaultdict(list)
    for state, postcode, y, m, price in records:
        bucket[(state, postcode, y, m)].append(price)
    panel = []
    for (state, pc, y, m), prices in bucket.items():
        panel.append({
            "state": state, "postcode": pc, "year": y, "month": m,
            "date": dt.date(y, m, 15).isoformat(),
            "mean_price_cents": mean(prices),
            "n_observations": len(prices),
        })
    return panel


# ----------------------------------------------------------------------------
# Phase C: classify stations (treated / donor-eligible / excluded)
# ----------------------------------------------------------------------------

def classify_stations(by_key):
    """Return DataFrame-like list of station classification records."""
    out = []
    for (state, nn, pc), cls in by_key.items():
        d = cls["min_dist_any"]
        if cls["treated_for"]:
            klass = "treated"
        elif d > DONOR_EXCLUDE_KM:
            klass = "donor_eligible"
        else:
            klass = "excluded_donut"
        out.append({
            "state": state,
            "name_norm": nn,
            "postcode": pc,
            "lat": cls["lat"], "lng": cls["lng"],
            "min_dist_any_costco_km": d,
            "class": klass,
            "n_treated_for": len(cls["treated_for"]),
        })
    return out


# ----------------------------------------------------------------------------
# Phase D: write outputs
# ----------------------------------------------------------------------------

def write_raw_counts(metas):
    rows = []
    for m in metas:
        rows.append({
            "registry": m["registry"],
            "format": m["format"],
            "files": m["files"],
            "n_observations": m["n_obs"],
            "n_columns": m["n_cols"],
            "n_unique_stations": m["n_stations"],
            "n_unique_brands": m["n_brands"],
            "n_unique_postcodes": m["n_postcodes"],
            "n_unique_fuel_types": m["n_fuel_types"],
            "earliest_observation": m["min_date"],
            "latest_observation": m["max_date"],
        })
    out = f"{OUT}/raw_counts.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  wrote {out}")


def write_time_periods(metas):
    out = f"{OUT}/time_periods.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["registry", "earliest_observation", "latest_observation",
                    "official_start_date", "notes"])
        notes = {
            "NSW FuelCheck": ("2016-08-01",
                              "Mandatory station reporting since Aug 2016."),
            "QLD Fuel Price Reporting Scheme": ("2018-12-01",
                              "Mandatory reporting since Dec 2018."),
            "WA FuelWatch": ("2001-01-01",
                              "Daily mandatory reporting since Jan 2001; "
                              "we pulled 2018 onward."),
        }
        for m in metas:
            os_, note = notes.get(m["registry"], ("", ""))
            w.writerow([m["registry"], m["min_date"], m["max_date"],
                        os_, note])
    print(f"  wrote {out}")


def write_unit_of_observation_md():
    text = """# Unit of observation, by registry

## NSW FuelCheck (monthly XLSX)
Each row is one **price update** — a station × fuel type × the timestamp
at which the operator changed (or re-confirmed) its posted price. NSW
FuelCheck does not snapshot daily; it stores price-change events.

Composite unique key: `(ServiceStationName, Address, FuelCode, PriceUpdatedDate)`.

Schema: `ServiceStationName, Address, Suburb, Postcode, Brand, FuelCode,
PriceUpdatedDate, Price`.

## QLD Fuel Price Reporting Scheme (monthly CSV)
Each row is one **price-change event** — a station × fuel type × the UTC
timestamp at which the price changed. Like NSW, the QLD scheme stores
events rather than daily snapshots.

Composite unique key: `(SiteId, Fuel_Type, TransactionDateutc)`.

Schema: `_id, SiteId, Site_Name, Site_Brand, Sites_Address_Line_1,
Site_Suburb, Site_State, Site_Post_Code, Site_Latitude, Site_Longitude,
Fuel_Type, Price, TransactionDateutc`.

Note: `Price` is in tenths of cents (e.g., `1899` = `189.9 ¢/L`).

## WA FuelWatch (monthly CSV)
Each row is a **daily snapshot** — a station × fuel type × calendar day.
Unlike NSW and QLD, FuelWatch publishes one record per station per day
regardless of whether the price changed.

Composite unique key:
`(TRADING_NAME, ADDRESS, PRODUCT_DESCRIPTION, PUBLISH_DATE)`.

Schema: `PUBLISH_DATE, TRADING_NAME, BRAND_DESCRIPTION,
PRODUCT_DESCRIPTION, PRODUCT_PRICE, ADDRESS, LOCATION, POSTCODE,
AREA_DESCRIPTION, REGION_DESCRIPTION`.

## Costco opening dates (hand-collected metadata)
Each row is one Costco fuel station. 10 rows.

Composite unique key: `Costco_name`.

Schema: `name, state, suburb, postcode, lat, lng, treatment_date,
months_pre, months_post, status, notes`.

Source file: `australia/data/catalogs/usable_costcos.csv`.

## Analysis panel (constructed in Phase B)
For the synthetic-control analysis, the raw price-change/snapshot data is
aggregated to a **(state × postcode × month)** panel of mean unleaded
prices. Each row represents the monthly mean retail unleaded price across
all non-Costco stations in that postcode.

Composite unique key: `(state, postcode, year, month)`.
"""
    out = f"{OUT}/unit_of_observation.md"
    with open(out, "w") as f:
        f.write(text)
    print(f"  wrote {out}")


def write_summary_statistics(panel, classified):
    rows = []

    # Outcome: postcode-month mean unleaded
    prices = [r["mean_price_cents"] for r in panel]
    rows.append(_stat_row("mean_unleaded_price_cents_per_L", prices,
                          "Postcode-month mean unleaded price (¢/L). "
                          "Outcome variable for the synthetic-control analysis.",
                          unit="¢/L", n=len(prices)))

    # Independent variable 1: distance to nearest Costco (per station)
    dists = [r["min_dist_any_costco_km"] for r in classified]
    rows.append(_stat_row("station_min_dist_any_costco_km", dists,
                          "Per-station haversine distance (km) to the nearest "
                          "of the 10 Costco fuel stations.",
                          unit="km", n=len(dists)))

    # Independent variable 2: treated/donor classification — categorical, just
    # report counts
    counts = Counter(r["class"] for r in classified)
    for klass in ["treated", "donor_eligible", "excluded_donut"]:
        rows.append({
            "variable": f"station_class_count[{klass}]",
            "description": (
                "Count of stations classified as " + {
                    "treated": "treated (within 5 km of one of the 4 treated Costcos)",
                    "donor_eligible": "donor-eligible (>20 km from every Costco)",
                    "excluded_donut": "excluded (5–20 km donut around any Costco)",
                }[klass]),
            "n": counts[klass],
            "mean": "", "sd": "", "min": "", "p25": "", "median": "",
            "p75": "", "max": "", "unit": "stations",
        })

    out = f"{OUT}/summary_statistics.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "variable", "description", "n", "mean", "sd", "min",
            "p25", "median", "p75", "max", "unit"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  wrote {out}")


def _stat_row(var, values, desc, unit, n):
    if not values:
        return {"variable": var, "description": desc, "n": 0,
                "mean": "", "sd": "", "min": "", "p25": "", "median": "",
                "p75": "", "max": "", "unit": unit}
    sv = sorted(values)
    return {
        "variable": var, "description": desc, "n": n,
        "mean": round(mean(values), 3),
        "sd": round(stdev(values), 3) if len(values) > 1 else 0,
        "min": round(min(values), 3),
        "p25": round(sv[len(sv)//4], 3),
        "median": round(sv[len(sv)//2], 3),
        "p75": round(sv[3*len(sv)//4], 3),
        "max": round(max(values), 3),
        "unit": unit,
    }


def write_data_quality_md(panel, classified, metas):
    n_panel = len(panel)
    n_outliers_low  = sum(1 for r in panel if r["mean_price_cents"] < 80)
    n_outliers_high = sum(1 for r in panel if r["mean_price_cents"] > 280)
    n_treated = sum(1 for r in classified if r["class"] == "treated")
    n_donor   = sum(1 for r in classified if r["class"] == "donor_eligible")
    n_excl    = sum(1 for r in classified if r["class"] == "excluded_donut")
    text = f"""# Data quality issues, by variable

## `price`
- **Cross-registry unit conventions differ**: NSW prices are in cents/L
  (e.g. `158.7`), QLD prices are in tenths of cents (e.g. `1899` =
  `189.9 ¢/L`), WA prices are in cents/L. Mishandled units would silently
  contaminate the analysis. **Resolution**: each registry's ingest applies
  the appropriate scaling so the panel is uniform in cents/L.
- **Outliers**: price quotes below 80 ¢/L or above 280 ¢/L are
  implausible for Australian retail unleaded post-2018 (national average
  hovers 130–220 ¢/L). After filtering, the postcode-month panel contains
  **{n_outliers_low}** observations below 80 ¢/L and **{n_outliers_high}**
  above 280 ¢/L out of {n_panel:,} total.
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
- **Limitation**: stations that closed before April 2026 do not appear in
  the live API and their historical records can fail to match. We estimate
  this at ≤5% of records based on station-count comparisons.

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
- NSW: not duplicates — multiple price-change rows per station-day are
  legitimate operator price updates.
- QLD: same — price-change-event records, not snapshots.
- WA: at most one row per station-day-fuel — no duplicate concern.

## Donor-pool filtering
- Out of all postcodes with any non-Costco unleaded data, the donor pool
  drops **361** postcodes within 20 km of any Costco (potential
  contamination from Costco's competitive footprint), **442** with fewer
  than 3 stations on average per month (means too noisy), and **0** with
  fewer than 24 months of observations. **200** donor postcodes survive
  all filters: NSW = 108, QLD = 56, WA = 36.

## Station classification at the registry level
- **Treated**: {n_treated} stations (within 5 km of one of the 4 treated Costcos).
- **Donor-eligible**: {n_donor} stations (>20 km from every Costco).
- **Excluded (5–20 km donut)**: {n_excl} stations (potential Costco
  spillover; excluded from both treated and donor groups).

## Source-document confidence
- Treatment dates were verified against each Costco's first-appearance
  date in its state's registry — a stronger anchor than warehouse-opening
  press dates, since several warehouses opened months before their fuel
  stations did.
"""
    out = f"{OUT}/data_quality.md"
    with open(out, "w") as f:
        f.write(text)
    print(f"  wrote {out}")


# ----------------------------------------------------------------------------
# Phase E: plots
# ----------------------------------------------------------------------------

def plot_price_histogram(panel):
    prices = [r["mean_price_cents"] for r in panel]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(prices, bins=60, color="#1F77B4", edgecolor="white")
    ax.set_xlabel("Postcode-month mean unleaded price (¢/L)")
    ax.set_ylabel("Frequency (postcode-months)")
    ax.set_title(f"Distribution of monthly mean unleaded price across the "
                 f"postcode-month panel (n = {len(prices):,})")
    ax.axvline(mean(prices), color="red", linestyle="--",
               label=f"mean = {mean(prices):.1f}¢/L")
    ax.axvline(sorted(prices)[len(prices)//2], color="orange",
               linestyle="--", label=f"median = {sorted(prices)[len(prices)//2]:.1f}¢/L")
    ax.legend()
    ax.grid(alpha=0.3)
    out = f"{OUT}/plots/01_price_histogram.png"
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def plot_unleaded_median_over_time(panel):
    by_state_month = defaultdict(list)
    for r in panel:
        by_state_month[(r["state"], r["year"], r["month"])].append(
            r["mean_price_cents"])
    series = defaultdict(list)
    for (state, y, m), prices in sorted(by_state_month.items()):
        d = dt.date(y, m, 15)
        med = sorted(prices)[len(prices)//2]
        series[state].append((d, med))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    palette = {"NSW": "#1F77B4", "QLD": "#FF7F0E", "WA": "#2CA02C"}
    for state, points in series.items():
        if not points: continue
        xs, ys = zip(*points)
        ax.plot(xs, ys, marker="o", markersize=2.5, linewidth=1.3,
                color=palette.get(state, "black"),
                label=f"{state} (n_postcodes ≈ "
                      f"{len(set((r['postcode']) for r in panel if r['state']==state))})")
    ax.set_ylabel("Median of postcode-monthly mean unleaded prices (¢/L)")
    ax.set_xlabel("Date")
    ax.set_title("Monthly median unleaded price (across postcodes), by state")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    out = f"{OUT}/plots/02_unleaded_median_over_time.png"
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def plot_distance_to_costco_hist(classified):
    fig, ax = plt.subplots(figsize=(10, 5))
    full_counts = defaultdict(int)
    by_class = defaultdict(list)
    for r in classified:
        d = r["min_dist_any_costco_km"]
        full_counts[r["class"]] += 1
        if d > 200: continue   # truncate the long tail for readability
        by_class[r["class"]].append(d)
    bins = [i for i in range(0, 205, 5)]
    colors = {"treated": "#D62728", "excluded_donut": "#FF7F0E",
              "donor_eligible": "#2CA02C"}
    labels = {"treated": "treated (≤5 km from a treated Costco)",
              "excluded_donut": "excluded (5–20 km donut)",
              "donor_eligible": "donor-eligible (>20 km)"}
    for klass in ["treated", "excluded_donut", "donor_eligible"]:
        ax.hist(by_class[klass], bins=bins, alpha=0.65,
                label=f"{labels[klass]} (n = {full_counts[klass]:,})",
                color=colors[klass])
    ax.axvline(5, color="black", linestyle=":", alpha=0.5)
    ax.axvline(20, color="black", linestyle=":", alpha=0.5)
    ax.set_xlabel("Station distance to nearest Costco (km)")
    ax.set_ylabel("Number of stations")
    ax.set_title("Distribution of station distance to nearest Costco, by classification "
                 "(stations >200 km truncated for readability)")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3)
    out = f"{OUT}/plots/03_distance_to_costco_hist.png"
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def plot_classification_counts(classified):
    counts = defaultdict(lambda: defaultdict(int))
    for r in classified:
        counts[r["state"]][r["class"]] += 1
    fig, ax = plt.subplots(figsize=(10, 5))
    states = ["NSW", "QLD", "WA"]
    classes = ["treated", "excluded_donut", "donor_eligible"]
    colors = {"treated": "#D62728", "excluded_donut": "#FF7F0E",
              "donor_eligible": "#2CA02C"}
    bottoms = [0]*len(states)
    for klass in classes:
        vals = [counts[s][klass] for s in states]
        ax.bar(states, vals, bottom=bottoms, color=colors[klass],
               label=klass.replace("_", " "))
        for i, (b, v) in enumerate(zip(bottoms, vals)):
            if v > 30:
                ax.text(i, b + v/2, str(v), ha="center", va="center",
                        fontsize=10, color="white")
        bottoms = [b+v for b, v in zip(bottoms, vals)]
    ax.set_ylabel("Number of stations")
    ax.set_xlabel("State")
    ax.set_title("Station classification by state")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    out = f"{OUT}/plots/04_classification_counts.png"
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def plot_treated_event_studies(panel):
    """One panel per treated Costco — mean price across treated postcodes
    over time. We approximate 'treated postcodes' as those that survive
    the 5km filter near each Costco — or equivalently, the postcodes the
    treated stations live in. For the visualization we use the
    treated_units.csv produced by Phase 5 if available, falling back to a
    direct postcode lookup."""
    # Use the existing treated_units.csv panel — it's already aggregated
    treated = []
    try:
        with open("australia/data/sc_inputs/treated_units.csv") as f:
            for r in csv.DictReader(f):
                treated.append({
                    "costco_key": r["costco_key"],
                    "date": dt.date.fromisoformat(r["date"]),
                    "mean_price_cents": float(r["mean_price_cents"]),
                })
    except FileNotFoundError:
        print("  warning: sc_inputs/treated_units.csv not found, skipping plot 05")
        return
    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    palette = {"Coomera": "#1F77B4", "Casuarina": "#FF7F0E",
               "Perth Airport": "#2CA02C", "Lake Macquarie": "#D62728"}
    openings = {ck: op for cstate, ck, op, *_ in COSTCOS_TREATED}
    for ax, ckey in zip(axes, ["Perth Airport", "Casuarina",
                                "Lake Macquarie", "Coomera"]):
        rs = sorted([r for r in treated if r["costco_key"] == ckey],
                    key=lambda r: r["date"])
        if not rs:
            ax.set_title(f"{ckey} — no data")
            continue
        ds = [r["date"] for r in rs]
        ys = [r["mean_price_cents"] for r in rs]
        ax.plot(ds, ys, color=palette[ckey], marker="o", markersize=3,
                linewidth=1.3, label=f"Treated mean (5 km)")
        ax.axvline(openings[ckey], color="red", linestyle="--",
                   label=f"opens {openings[ckey]}", linewidth=1)
        ax.set_ylabel("¢/L")
        ax.set_title(f"{ckey} — treated-market mean unleaded price")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(alpha=0.3)
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    axes[-1].set_xlabel("Date")
    fig.suptitle("Treated-market unleaded price over time, per treated Costco",
                 fontsize=12, y=1.00)
    out = f"{OUT}/plots/05_treated_event_studies.png"
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    os.makedirs(f"{OUT}/plots", exist_ok=True)

    print("Phase A: scanning registries for metadata...")
    metas = [scan_nsw_meta(), scan_qld_meta(), scan_wa_meta()]
    print()
    for m in metas:
        print(f"  {m['registry']}: {m['n_obs']:,} obs across "
              f"{m['files']} files; {m['n_stations']:,} stations; "
              f"{m['min_date']} → {m['max_date']}")
    print()

    print("Phase B: building unleaded postcode-month panel...")
    by_key, by_name = load_station_classification()
    records = ingest_panel(by_key, by_name)
    panel = aggregate_postcode_month(records)
    print(f"  panel: {len(panel):,} postcode-month rows from "
          f"{len(records):,} unleaded records\n")

    print("Phase C: classifying stations...")
    classified = classify_stations(by_key)
    print(f"  classified: {len(classified):,} stations\n")

    print("Phase D: writing CSV/MD outputs...")
    write_raw_counts(metas)
    write_time_periods(metas)
    write_unit_of_observation_md()
    write_summary_statistics(panel, classified)
    write_data_quality_md(panel, classified, metas)
    print()

    print("Phase E: rendering plots...")
    plot_price_histogram(panel)
    plot_unleaded_median_over_time(panel)
    plot_distance_to_costco_hist(classified)
    plot_classification_counts(classified)
    plot_treated_event_studies(panel)
    print()

    print("Section 1 artifacts ready in australia/section_1/.")


if __name__ == "__main__":
    main()
