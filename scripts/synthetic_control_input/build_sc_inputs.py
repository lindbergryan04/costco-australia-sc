"""
Build the synthetic-control input panels.

Outputs (australia/data/sc_inputs/):
  treated_units.csv      long:  costco_key × year × month × mean_price × n_obs × n_stations
  donor_pool.csv         long:  postcode × state × year × month × mean_price × n_obs × n_stations
  treated_metadata.csv   one row per Costco:  state, lat, lng, treatment_date, pre/post months
  donor_metadata.csv     one row per donor postcode: state, n_unique_stations,
                                                      n_months_observed,
                                                      min_dist_to_any_costco_km

For each Costco × month, the treated-unit price is the mean of all
non-Costco station prices within 5 km of the Costco.

For each postcode × month, the donor price is the mean of all non-Costco
station prices in that postcode.

A postcode is dropped from the donor pool if:
  - it lies within 20 km of ANY Costco (might be picking up Costco effects)
  - it has fewer than 3 unique stations on average (price means too noisy)
  - it has fewer than 24 months of observations (insufficient pre-period coverage)
"""

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

sys.path.insert(0, "australia/scripts")
from _nsw_reader import iter_nsw_data_rows

NEAR_KM_TREATED = 5.0
DONOR_EXCLUDE_KM = 20.0
MIN_STATIONS_PER_POSTCODE = 3
MIN_MONTHS_PER_POSTCODE = 24

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


def load_station_classification():
    """For each station, compute distance to each TREATED Costco and to any
    Costco. Return dict: (state, name_norm, postcode) → {
       'treated_for': set of Costco keys (within 5 km),
       'min_dist_any_costco': float km,
       'lat': float, 'lng': float,
    }"""
    by_key = {}
    by_name = defaultdict(list)
    with open("australia/data/stations/station_coords.csv") as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r["lat"]); lng = float(r["lng"])
            except (TypeError, ValueError):
                continue
            treated_for = set()
            for cstate, ckey, op, clat, clng in COSTCOS_TREATED:
                if haversine_km(lat, lng, clat, clng) <= NEAR_KM_TREATED:
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
    files = sorted(glob.glob("australia/_local/cache/nsw/*.xlsx"))
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


def ingest_qld(treated_obs, donor_obs):
    files = sorted(glob.glob("australia/_local/cache/qld/*.csv"))
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
                # Treated contribution
                for cstate, ckey, op, clat, clng in COSTCOS_TREATED:
                    if cstate != "QLD": continue
                    if haversine_km(lat, lng, clat, clng) <= NEAR_KM_TREATED:
                        add_to_treated(treated_obs, ckey, ym, price, station_id)
                # Donor contribution
                if postcode:
                    add_to_donor(donor_obs, "QLD", postcode, ym, price, station_id)
        if (fi+1) % 20 == 0:
            print(f"    QLD {fi+1}/{len(files)}")


def ingest_wa(treated_obs, donor_obs, by_key, by_name):
    files = sorted(glob.glob("australia/_local/cache/wa/*.csv"))
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


def main():
    print("Loading station classification...")
    by_key, by_name = load_station_classification()
    print(f"  {len(by_key):,} stations\n")

    print("Ingesting price records (this is the slow part)...")
    treated_obs = defaultdict(dict)
    donor_obs = defaultdict(dict)
    ingest_nsw(treated_obs, donor_obs, by_key, by_name)
    ingest_qld(treated_obs, donor_obs)
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
    out = "australia/data/sc_inputs/treated_units.csv"
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
        if min_dist <= DONOR_EXCLUDE_KM:
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

    out = "australia/data/sc_inputs/donor_pool.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(donor_rows[0].keys()))
        w.writeheader()
        for r in donor_rows: w.writerow(r)
    print(f"  wrote {out} ({len(donor_rows):,} rows from {len(donor_meta_rows)} donor postcodes)")

    out = "australia/data/sc_inputs/donor_metadata.csv"
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
    out = "australia/data/sc_inputs/treated_metadata.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(treated_meta[0].keys()))
        w.writeheader()
        for r in treated_meta: w.writerow(r)
    print(f"  wrote {out}")

    # ---- Summary ----
    print("\n" + "="*70)
    print("Synthetic-control inputs ready.")
    print("="*70)
    print(f"  Treated units:     4 Costcos")
    print(f"    {'Costco':22s}  {'state':>5s}  {'pre':>4s}  {'post':>5s}  {'avg n_stns':>10s}")
    for r in treated_meta:
        print(f"    {r['costco_key']:22s}  {r['state']:>5s}  {r['n_pre_months']:4d}  "
              f"{r['n_post_months']:5d}  {r['avg_n_unique_stations']:10.1f}")
    print(f"  Donor postcodes:   {len(donor_meta_rows):,}")
    print(f"  Donor panel rows:  {len(donor_rows):,}")
    print(f"  Treated panel rows: {len(treated_rows)}")


if __name__ == "__main__":
    main()
