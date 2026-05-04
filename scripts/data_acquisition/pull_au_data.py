"""
Pull historical fuel price data for the three states with usable Costco
events: NSW (FuelCheck), WA (FuelWatch), QLD (Fuel Price Reporting).

Each state's data goes into australia/_local/cache/{state}/{filename}.

Strategy:
  - NSW: monthly XLSX, fetched from data.nsw.gov.au CKAN API (Aug 2016+).
  - WA:  monthly CSV, fetched from FuelWatch's Azure blob storage (Jan 2001+).
  - QLD: monthly CSV, fetched across four CKAN datasets (2019-2022, 2023,
         2024, 2025).

We don't need every month for every state. We pull the windows around our
treatment events with at least 2 years of pre-period buffer:
  - NSW: 2016-08 → 2026-04 (full FuelCheck history; covers Marsden Park
         2017 and Auburn 2025).
  - WA:  2018-01 → 2026-04 (covers Perth Airport 2020 and Casuarina 2022;
         abundant pre-period without pulling 17 years of pre-2018 data).
  - QLD: full 2019-01 → 2026-04 (covers Coomera 2023; full QLD history).

Cache is keyed on filename so re-runs skip already-downloaded files.
"""

import datetime as dt
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE = "australia/_local/cache"
WORKERS = 4
MAX_RETRIES = 3

# ----- Per-state config -----

NSW_CKAN = "https://data.nsw.gov.au/data/api/3/action/package_show?id=fuel-check"

QLD_CKAN_DATASETS = [
    "fuel-price-reporting",            # 2023
    "fuel-price-reporting-2019-2022",
    "fuel-price-reporting-2024",
    "fuel-price-reporting-2025",
]

WA_API = "https://www.fuelwatch.wa.gov.au/api/report/monthly-retail-prices"


def log(msg):
    print(msg, flush=True)


def fetch(url, dest_path, expect_json=False, min_bytes=10_000):
    """Download url to dest_path with retries and minimal validation.
    Returns True if downloaded, False if already cached."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) >= min_bytes:
        return False
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            tmp = dest_path + ".tmp"
            res = subprocess.run(
                ["curl", "-sSL", "--max-time", "300", "--retry", "2",
                 "--retry-delay", "3", "-o", tmp, url],
                capture_output=True, check=True,
            )
            sz = os.path.getsize(tmp) if os.path.exists(tmp) else 0
            if sz < min_bytes:
                raise RuntimeError(f"short response: {sz} bytes")
            if expect_json:
                with open(tmp, "rb") as f:
                    json.loads(f.read())
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            os.rename(tmp, dest_path)
            return True
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            log(f"    retry {attempt+1}/{MAX_RETRIES} ({e})")
            time.sleep(wait)
    raise last_err


def list_nsw_files():
    """Return [(filename, url)] for all monthly NSW XLSX history files."""
    raw = subprocess.run(
        ["curl", "-sS", "--max-time", "60", NSW_CKAN],
        capture_output=True, check=True,
    ).stdout
    rs = json.loads(raw)["result"]["resources"]
    out = []
    for r in rs:
        if r.get("format") != "XLSX":
            continue
        name = (r.get("name") or "").lower()
        if "history" not in name and "history" not in (r.get("url") or "").lower():
            continue
        url = r["url"]
        fname = url.rsplit("/", 1)[-1]
        out.append((fname, url))
    return out


def list_qld_files():
    """Use the CKAN datastore_dump endpoint (bypasses CloudFront WAF that
    blocks the standard /resource/.../download/... URLs)."""
    out = []
    for ds_id in QLD_CKAN_DATASETS:
        raw = subprocess.run(
            ["curl", "-sS", "--max-time", "60",
             f"https://www.data.qld.gov.au/api/3/action/package_show?id={ds_id}"],
            capture_output=True, check=True,
        ).stdout
        rs = json.loads(raw)["result"]["resources"]
        for r in rs:
            if r.get("format") != "CSV":
                continue
            rid = r["id"]
            # Try to extract a year-month tag from the resource name so
            # cached filenames are sortable.
            name = (r.get("name") or "").lower()
            fname = f"{rid[:8]}_{name.replace(' ', '_')[:60]}.csv"
            url = f"https://www.data.qld.gov.au/datastore/dump/{rid}"
            out.append((fname, url))
    return out


def list_wa_files(start_year=2018):
    raw = subprocess.run(
        ["curl", "-sS", "--max-time", "60", WA_API],
        capture_output=True, check=True,
    ).stdout
    files = json.loads(raw)
    out = []
    for r in files:
        # fileName like "FuelWatchRetail-04-2026.csv"
        name = r["fileName"]
        try:
            mm, yyyy = name.replace("FuelWatchRetail-", "").replace(".csv", "").split("-")
            year = int(yyyy)
            if year < start_year:
                continue
        except Exception:
            continue
        out.append((name, r["url"]))
    return out


def pull_state(state, files, ext_hint):
    log(f"\n=== {state.upper()}: {len(files)} files ===")
    new_count = 0
    n_done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {}
        for fname, url in files:
            dest = os.path.join(CACHE, state, fname)
            futs[ex.submit(fetch, url, dest, False, 5_000)] = (fname, url)
        for f in as_completed(futs):
            fname, url = futs[f]
            try:
                downloaded = f.result()
                if downloaded:
                    new_count += 1
            except Exception as e:
                log(f"  FAIL {fname}: {e}")
            n_done += 1
            if n_done % 20 == 0 or n_done == len(files):
                log(f"  progress: {n_done}/{len(files)} ({new_count} new)")
    log(f"  {state}: {new_count} new files; total cached = "
        f"{len(os.listdir(os.path.join(CACHE, state)))}")


def main():
    os.makedirs(os.path.join(CACHE, "nsw"), exist_ok=True)
    os.makedirs(os.path.join(CACHE, "wa"), exist_ok=True)
    os.makedirs(os.path.join(CACHE, "qld"), exist_ok=True)

    log("Discovering files via state APIs...")
    nsw = list_nsw_files()
    qld = list_qld_files()
    wa = list_wa_files(start_year=2018)
    log(f"  NSW: {len(nsw)} files")
    log(f"  QLD: {len(qld)} files")
    log(f"  WA:  {len(wa)} files (2018+)")

    pull_state("nsw", nsw, ".xlsx")
    pull_state("qld", qld, ".csv")
    pull_state("wa",  wa,  ".csv")

    log("\nDone.")
    for state in ("nsw", "qld", "wa"):
        files = os.listdir(os.path.join(CACHE, state))
        total = sum(os.path.getsize(os.path.join(CACHE, state, f)) for f in files)
        log(f"  {state}: {len(files)} files, {total/1e6:.0f} MB")


if __name__ == "__main__":
    main()
