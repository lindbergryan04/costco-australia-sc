"""
Build the synthetic-control input panels.

Outputs (default data/sc_inputs/, override with --out-dir):
  treated_units.csv      long:  costco_key × year × month × mean_price × n_obs × n_stations
  donor_pool.csv         long:  postcode × state × year × month × mean_price × n_obs × n_stations
  treated_metadata.csv   one row per Costco:  state, lat, lng, treatment_date, pre/post months
  donor_metadata.csv     one row per donor postcode: state, n_unique_stations,
                                                      n_months_observed,
                                                      min_dist_to_any_costco_km

For each Costco × month, the treated-unit price is the mean of all
non-Costco station prices within NEAR_KM_TREATED of the Costco
(or, if INNER_KM > 0, in the annulus between INNER_KM and NEAR_KM_TREATED —
used by the Section 4 spatial-placebo robustness check, which treats the
5-20 km donut around each Costco as a faux treated unit).

For each postcode × month, the donor price is the mean of all non-Costco
station prices in that postcode.

A postcode is dropped from the donor pool if:
  - it lies within DONOR_EXCLUDE_KM of ANY Costco (might be picking up Costco effects)
  - it has fewer than 3 unique stations on average (price means too noisy)
  - it has fewer than 24 months of observations (insufficient pre-period coverage)

The headline 5 km / 20 km specification runs as a script with no arguments
(reproduces analysis/sc_inputs/). Section 4 robustness checks call build()
directly from scripts/synthetic_control_input/build_sc_inputs_alt_radii.py
with alternate radii and output directories.
"""

import argparse
import csv
import datetime as dt
import glob
import math
import os
import re
import sys
from collections import defaultdict
from statistics import mean

import openpyxl

sys.path.insert(0, "scripts")
from _nsw_reader import iter_nsw_data_rows

# Headline-specification defaults. The build() function below overrides
# these per-call; the constants are kept so the rest of the module can
# read them as a single source of truth at import time.
NEAR_KM_TREATED = 5.0
DONOR_EXCLUDE_KM = 20.0
INNER_KM = 0.0
MIN_STATIONS_PER_POSTCODE = 3
MIN_MONTHS_PER_POSTCODE = 24

DEFAULT_OUT_DIR = "data/sc_inputs"

# Treated Costcos with adequate pre AND post months and acceptable
# historical coverage.
COSTCOS_TREATED = [
    # state, key, opening, lat, lng
    ("QLD", "Coomera",        dt.date(2023, 5, 23), -27.850829, 153.314369),
    ("WA",  "Casuarina",      dt.date(2022, 11, 11), -32.233481, 115.853714),
    ("WA",  "Perth Airport",  dt.date(2020, 4, 11), -31.940377, 115.951869),
    ("NSW", "Lake Macquarie", dt.date(2022, 5, 2),  -32.946111, 151.628054),
]

# All Costcos (used to exclude near-Costco postcodes from donor pool)
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


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def normalize_name(s):
    if not s: return ""
    s = s.lower().strip()
    s = re.sub(r"\(members?\s*only.*?\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_unleaded_nsw(c): return str(c).strip().upper() in ("U91", "E10", "P91")
def is_unleaded_qld(t): return str(t).strip().lower() in ("unleaded 91", "e10", "u91")
def is_unleaded_wa(p):  return str(p).strip().upper() == "ULP"


def load_station_classification(near_km=NEAR_KM_TREATED, inner_km=INNER_KM):
    """For each station, compute distance to each TREATED Costco and to any
    Costco. Return dict: (state, name_norm, postcode) → {
       'treated_for': set of Costco keys (treated radius around that Costco),
       'min_dist_any_costco': float km,
       'lat': float, 'lng': float,
    }

    A station is added to a Costco's treated_for set if its distance d to
    that Costco satisfies inner_km < d <= near_km. inner_km defaults to 0
    (the headline 5 km disc); the spatial-placebo robustness check passes
    inner_km=5, near_km=20 to define the 5-20 km donut as the faux treated
    unit."""
    by_key = {}
    by_name = defaultdict(list)
    with open("data/stations/station_coords.csv") as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r["lat"]); lng = float(r["lng"])
            except (TypeError, ValueError):
                continue
            treated_for = set()
            for cstate, ckey, op, clat, clng in COSTCOS_TREATED:
                d = haversine_km(lat, lng, clat, clng)
                if inner_km < d <= near_km:
                    treated_for.add(ckey)
            min_d_any = min(haversine_km(lat, lng, clat, clng)
                            for _, clat, clng in ALL_COSTCO_COORDS)
            entry = {
                "state": r["state"],
                "treated_for": treated_for,
                "min_dist_any_costco": min_d_any,
                "lat": lat, "lng": lng,
                "postcode": r["postcode"],
            }
            by_key[(r["state"], r["name_norm"], r["postcode"])] = entry
            by_name[(r["state"], r["name_norm"])].append(entry)
    return by_key, by_name


# ---- Aggregators ----

# We accumulate two parallel dicts:
#   treated_obs[(ckey, ym)] = {"prices": list, "stations": set}
#   donor_obs[(state, postcode, ym)] = {"prices": list, "stations": set}
# Stations contribute to ALL Costcos they're within 5km of.

def add_to_treated(treated_obs, ckey, ym, price, station_id):
    bucket = treated_obs[(ckey, ym)]
    bucket.setdefault("prices", []).append(price)
    bucket.setdefault("stations", set()).add(station_id)


def add_to_donor(donor_obs, state, postcode, ym, price, station_id):
    bucket = donor_obs[(state, postcode, ym)]
    bucket.setdefault("prices", []).append(price)
    bucket.setdefault("stations", set()).add(station_id)


def ingest_nsw(treated_obs, donor_obs, by_key, by_name):
    files = sorted(glob.glob("_local/cache/nsw/*.xlsx"))
    print(f"  NSW: {len(files)} files")
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
            ym = (d.year, d.month)
            nn = normalize_name(str(name))
            cls = by_key.get(("NSW", nn, postcode))
            if cls is None:
                hits = by_name.get(("NSW", nn))
                if hits:
                    cls = hits[0]
            station_id = f"NSW|{nn}|{postcode}"
            if cls is not None:
                for ck in cls["treated_for"]:
                    add_to_treated(treated_obs, ck, ym, price, station_id)
            if postcode:
                add_to_donor(donor_obs, "NSW", postcode, ym, price, station_id)
        if (fi+1) % 20 == 0:
            print(f"    NSW {fi+1}/{len(files)}")


def ingest_qld(treated_obs, donor_obs, near_km=NEAR_KM_TREATED, inner_km=INNER_KM):
    files = sorted(glob.glob("_local/cache/qld/*.csv"))
    print(f"  QLD: {len(files)} files")
    for fi, f in enumerate(files):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                brand = (row.get("Site_Brand") or "").lower()
                if "costco" in brand: continue
                ft = row.get("Fuel_Type") or ""
                if not is_unleaded_qld(ft): continue
                try:
                    price = float(row.get("Price") or 0) / 10.0
                    lat = float(row.get("Site_Latitude") or 0)
                    lng = float(row.get("Site_Longitude") or 0)
                except (TypeError, ValueError):
                    continue
                if price == 0 or lat == 0 or lng == 0: continue
                if price <= 50 or price > 500: continue
                ts = row.get("TransactionDateutc") or ""
                try: d = dt.datetime.fromisoformat(ts.split(".")[0]).date()
                except Exception: continue
                postcode = (row.get("Site_Post_Code") or "").strip()
                station_id = f"QLD|{row.get('SiteId') or ''}"
                ym = (d.year, d.month)
                # Treated contribution. A QLD station goes into a treated
                # Costco's bucket if its distance to the Costco falls in
                # (inner_km, near_km]. inner_km > 0 supports the donut case.
                for cstate, ckey, op, clat, clng in COSTCOS_TREATED:
                    if cstate != "QLD": continue
                    dist = haversine_km(lat, lng, clat, clng)
                    if inner_km < dist <= near_km:
                        add_to_treated(treated_obs, ckey, ym, price, station_id)
                # Donor contribution
                if postcode:
                    add_to_donor(donor_obs, "QLD", postcode, ym, price, station_id)
        if (fi+1) % 20 == 0:
            print(f"    QLD {fi+1}/{len(files)}")


def ingest_wa(treated_obs, donor_obs, by_key, by_name):
    files = sorted(glob.glob("_local/cache/wa/*.csv"))
    print(f"  WA: {len(files)} files")
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
                name = row.get("TRADING_NAME") or ""
                postcode = str(row.get("POSTCODE") or "").strip()
                nn = normalize_name(name)
                cls = by_key.get(("WA", nn, postcode))
                if cls is None:
                    hits = by_name.get(("WA", nn))
                    if hits: cls = hits[0]
                station_id = f"WA|{nn}|{postcode}"
                ym = (d.year, d.month)
                if cls is not None:
                    for ck in cls["treated_for"]:
                        add_to_treated(treated_obs, ck, ym, price, station_id)
                if postcode:
                    add_to_donor(donor_obs, "WA", postcode, ym, price, station_id)
        if (fi+1) % 20 == 0:
            print(f"    WA {fi+1}/{len(files)}")


# ---- Postcode → distance to nearest Costco ----

def compute_postcode_distances(by_key):
    """Return dict postcode → min distance to any Costco (km), keyed by
    (state, postcode). Distance = mean of station-level min-distances within
    that postcode (a postcode covers an area, so we use station means)."""
    accum = defaultdict(list)
    for (state, _, postcode), cls in by_key.items():
        if not postcode:
            continue
        accum[(state, postcode)].append(cls["min_dist_any_costco"])
    out = {}
    for k, dists in accum.items():
        out[k] = mean(dists)
    return out


def build(near_km=NEAR_KM_TREATED, exclude_km=DONOR_EXCLUDE_KM,
          out_dir=DEFAULT_OUT_DIR, inner_km=INNER_KM):
    """Run the full pipeline once with the given geometry.

    near_km     stations within (inner_km, near_km] of a treated Costco
                form that Costco's treated unit.
    exclude_km  postcodes within exclude_km of any Costco are dropped
                from the donor pool.
    out_dir     directory the four CSVs are written into (created if
                needed).
    inner_km    lower-bound annulus radius for the treated unit; >0
                produces a donut (used by Section 4 spatial-placebo
                robustness check). Default 0.
    """
    os.makedirs(out_dir, exist_ok=True)

    geom = (f"inner_km={inner_km:g}, near_km={near_km:g}, "
            f"exclude_km={exclude_km:g}, out_dir={out_dir}")
    print(f"Building SC inputs ({geom})...")

    print("Loading station classification...")
    by_key, by_name = load_station_classification(near_km=near_km,
                                                  inner_km=inner_km)
    print(f"  {len(by_key):,} stations\n")

    print("Ingesting price records (this is the slow part)...")
    treated_obs = defaultdict(dict)
    donor_obs = defaultdict(dict)
    ingest_nsw(treated_obs, donor_obs, by_key, by_name)
    ingest_qld(treated_obs, donor_obs, near_km=near_km, inner_km=inner_km)
    ingest_wa(treated_obs, donor_obs, by_key, by_name)
    print(f"\n  Treated buckets: {len(treated_obs):,}")
    print(f"  Donor buckets:   {len(donor_obs):,}\n")

    # ---- Treated units output ----
    print("Building treated_units.csv...")
    treated_rows = []
    for (ckey, ym), bucket in sorted(treated_obs.items()):
        prices = bucket["prices"]; stations = bucket["stations"]
        if not prices: continue
        # Find state for this Costco
        cstate = next(s for s, k, *_ in COSTCOS_TREATED if k == ckey)
        treated_rows.append({
            "costco_key": ckey,
            "state": cstate,
            "year": ym[0],
            "month": ym[1],
            "date": dt.date(ym[0], ym[1], 15).isoformat(),
            "mean_price_cents": round(mean(prices), 4),
            "n_observations": len(prices),
            "n_unique_stations": len(stations),
        })
    out = os.path.join(out_dir, "treated_units.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(treated_rows[0].keys()))
        w.writeheader()
        for r in treated_rows: w.writerow(r)
    print(f"  wrote {out} ({len(treated_rows)} rows)")

    # ---- Per-postcode aggregation + filtering ----
    print("\nAggregating donor postcodes...")
    # Group donor_obs by (state, postcode) → list of monthly stats
    by_pc = defaultdict(list)
    for (state, postcode, ym), bucket in donor_obs.items():
        prices = bucket["prices"]; stations = bucket["stations"]
        if not prices: continue
        by_pc[(state, postcode)].append({
            "year": ym[0], "month": ym[1],
            "date": dt.date(ym[0], ym[1], 15).isoformat(),
            "mean_price_cents": round(mean(prices), 4),
            "n_observations": len(prices),
            "n_unique_stations": len(stations),
        })

    # Compute postcode-level aggregate stats for filtering + metadata
    pc_dists = compute_postcode_distances(by_key)
    print(f"  {len(by_pc):,} (state, postcode) pairs with any data")

    donor_rows = []
    donor_meta_rows = []
    n_excluded_near = 0
    n_excluded_sparse = 0
    n_excluded_short = 0
    for (state, postcode), monthly in by_pc.items():
        # Average unique stations across months
        avg_stations = mean(m["n_unique_stations"] for m in monthly)
        n_months = len(monthly)
        min_dist = pc_dists.get((state, postcode), 0)
        # Apply filters
        if min_dist <= exclude_km:
            n_excluded_near += 1; continue
        if avg_stations < MIN_STATIONS_PER_POSTCODE:
            n_excluded_sparse += 1; continue
        if n_months < MIN_MONTHS_PER_POSTCODE:
            n_excluded_short += 1; continue
        # Keep
        for m in monthly:
            donor_rows.append({
                "postcode": postcode,
                "state": state,
                "year": m["year"], "month": m["month"], "date": m["date"],
                "mean_price_cents": m["mean_price_cents"],
                "n_observations": m["n_observations"],
                "n_unique_stations": m["n_unique_stations"],
            })
        donor_meta_rows.append({
            "postcode": postcode, "state": state,
            "avg_unique_stations": round(avg_stations, 2),
            "n_months_observed": n_months,
            "min_dist_any_costco_km": round(min_dist, 2),
        })

    out = os.path.join(out_dir, "donor_pool.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(donor_rows[0].keys()))
        w.writeheader()
        for r in donor_rows: w.writerow(r)
    print(f"  wrote {out} ({len(donor_rows):,} rows from {len(donor_meta_rows)} donor postcodes)")

    out = os.path.join(out_dir, "donor_metadata.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(donor_meta_rows[0].keys()))
        w.writeheader()
        for r in donor_meta_rows: w.writerow(r)
    print(f"  wrote {out}")
    print(f"  donor filtering: excluded {n_excluded_near} near-Costco, "
          f"{n_excluded_sparse} sparse-stations, {n_excluded_short} short-history")

    # ---- Treated metadata ----
    treated_meta = []
    for cstate, ckey, op, clat, clng in COSTCOS_TREATED:
        rs = [r for r in treated_rows if r["costco_key"] == ckey]
        n_pre = sum(1 for r in rs if dt.date(r["year"], r["month"], 15) < op)
        n_post = sum(1 for r in rs if dt.date(r["year"], r["month"], 15) >= op)
        treated_meta.append({
            "costco_key": ckey, "state": cstate,
            "lat": clat, "lng": clng,
            "treatment_date": op.isoformat(),
            "n_pre_months": n_pre, "n_post_months": n_post,
            "avg_n_unique_stations": round(mean(r["n_unique_stations"] for r in rs), 2) if rs else 0,
        })
    out = os.path.join(out_dir, "treated_metadata.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(treated_meta[0].keys()))
        w.writeheader()
        for r in treated_meta: w.writerow(r)
    print(f"  wrote {out}")

    # ---- Summary ----
    print("\n" + "="*70)
    print(f"Synthetic-control inputs ready ({geom}).")
    print("="*70)
    print(f"  Treated units:     4 Costcos")
    print(f"    {'Costco':22s}  {'state':>5s}  {'pre':>4s}  {'post':>5s}  {'avg n_stns':>10s}")
    for r in treated_meta:
        print(f"    {r['costco_key']:22s}  {r['state']:>5s}  {r['n_pre_months']:4d}  "
              f"{r['n_post_months']:5d}  {r['avg_n_unique_stations']:10.1f}")
    print(f"  Donor postcodes:   {len(donor_meta_rows):,}")
    print(f"  Donor panel rows:  {len(donor_rows):,}")
    print(f"  Treated panel rows: {len(treated_rows)}")

    return {
        "near_km": near_km, "exclude_km": exclude_km, "inner_km": inner_km,
        "out_dir": out_dir,
        "n_treated_rows": len(treated_rows),
        "n_donor_rows": len(donor_rows),
        "n_donor_postcodes": len(donor_meta_rows),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build SC input panels at the headline 5/20 km geometry "
                    "(or alternate radii via --near-km / --exclude-km).")
    parser.add_argument("--near-km",    type=float, default=NEAR_KM_TREATED,
                        help="Treated radius around each Costco (default 5.0).")
    parser.add_argument("--exclude-km", type=float, default=DONOR_EXCLUDE_KM,
                        help="Donor exclusion radius around any Costco (default 20.0).")
    parser.add_argument("--inner-km",   type=float, default=INNER_KM,
                        help="Inner annulus radius (>0 enables donut mode; default 0).")
    parser.add_argument("--out-dir",    default=DEFAULT_OUT_DIR,
                        help="Output directory for the four CSVs.")
    args = parser.parse_args()
    build(near_km=args.near_km, exclude_km=args.exclude_km,
          out_dir=args.out_dir, inner_km=args.inner_km)


if __name__ == "__main__":
    main()
