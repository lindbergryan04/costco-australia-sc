"""
Build a unified station-coordinate lookup for NSW + WA + QLD.

Sources:
  NSW: live FuelCheck API snapshot (australia/data/stations/nsw_stations.json)
  WA:  live FuelWatch API snapshot (australia/data/stations/wa_stations.json)
  QLD: extracted from historical CSVs (which already include lat/lng)

Output: australia/data/stations/station_coords.csv
Schema: state, station_id, name, address, suburb, postcode, lat, lng

Matching strategy for historical records (NSW/WA):
  We'll later match historical records to this catalog by (name, postcode)
  to attach coordinates. Stations that closed before today are lost (a
  small fraction).
"""

import csv
import glob
import json
import os
import re


def normalize_name(s):
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"\(members?\s*only.*?\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main():
    rows = []

    # NSW from live API
    print("Loading NSW FuelCheck stations...")
    with open("australia/data/stations/nsw_stations.json") as f:
        nsw = json.load(f)
    for s in nsw.get("stations", []):
        loc = s.get("location") or {}
        addr = s.get("address") or ""
        # Try to pluck postcode from end of address
        m = re.search(r"\b(\d{4})\b", addr)
        postcode = m.group(1) if m else ""
        # Pluck suburb (the word(s) before "NSW <postcode>" or "ACT <postcode>")
        m2 = re.search(r"([A-Z][A-Za-z\s]+?)\s+(?:NSW|ACT)\s+\d{4}", addr)
        suburb = (m2.group(1).strip() if m2 else "").upper()
        rows.append({
            "state": "NSW",
            "station_id": s.get("stationid", ""),
            "name": s.get("name", ""),
            "name_norm": normalize_name(s.get("name", "")),
            "address": addr,
            "suburb": suburb,
            "postcode": postcode,
            "lat": loc.get("latitude", ""),
            "lng": loc.get("longitude", ""),
        })

    # WA from live API
    print("Loading WA FuelWatch stations...")
    with open("australia/data/stations/wa_stations.json") as f:
        wa = json.load(f)
    for s in wa:
        addr = s.get("address") or {}
        rows.append({
            "state": "WA",
            "station_id": str(s.get("id", "")),
            "name": s.get("siteName", ""),
            "name_norm": normalize_name(s.get("siteName", "")),
            "address": addr.get("line1", ""),
            "suburb": (addr.get("location") or "").upper(),
            "postcode": str(addr.get("postCode") or ""),
            "lat": addr.get("latitude", ""),
            "lng": addr.get("longitude", ""),
        })

    # QLD from historical CSVs (extract unique stations)
    print("Extracting QLD stations from historical CSVs...")
    qld_seen = {}
    for f in sorted(glob.glob("australia/_local/cache/qld/*.csv")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                sid = row.get("SiteId") or ""
                if not sid or sid in qld_seen:
                    continue
                try:
                    lat = float(row.get("Site_Latitude") or 0)
                    lng = float(row.get("Site_Longitude") or 0)
                except (TypeError, ValueError):
                    continue
                if lat == 0 or lng == 0:
                    continue
                qld_seen[sid] = {
                    "state": "QLD",
                    "station_id": sid,
                    "name": row.get("Site_Name", ""),
                    "name_norm": normalize_name(row.get("Site_Name", "")),
                    "address": row.get("Sites_Address_Line_1", ""),
                    "suburb": (row.get("Site_Suburb") or "").upper(),
                    "postcode": str(row.get("Site_Post_Code") or ""),
                    "lat": lat,
                    "lng": lng,
                }
    rows.extend(qld_seen.values())
    print(f"  QLD: {len(qld_seen)} unique stations")

    fields = ["state", "station_id", "name", "name_norm", "address",
              "suburb", "postcode", "lat", "lng"]
    out = "australia/data/stations/station_coords.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {out}")
    print(f"Total stations with coords:")
    counts = {"NSW": 0, "WA": 0, "QLD": 0}
    for r in rows:
        counts[r["state"]] += 1
    for s, n in counts.items():
        print(f"  {s}: {n:,}")
    print(f"  TOTAL: {sum(counts.values()):,}")


if __name__ == "__main__":
    main()
