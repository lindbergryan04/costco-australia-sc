"""
Pull every NSW fuel station's coordinates from the live FuelCheck API.

Uses 2 API calls total:
  1. Mint OAuth access token (one call to the OneGov OAuth endpoint).
  2. Call /FuelPriceCheck/v1/fuel/prices to get the full current snapshot —
     this single response contains every station's id, name, address, brand,
     postcode AND lat/lng, plus its current price.

Output: australia/data/stations/nsw_stations.json  (full station catalog with coords)

Credentials are read from australia/_local/.nsw_credentials.json (git-ignored).
"""

import datetime as dt
import json
import os
import subprocess
import sys
import uuid

CRED_PATH = "australia/_local/.nsw_credentials.json"
OAUTH_URL = ("https://api.onegov.nsw.gov.au/oauth/client_credential/"
             "accesstoken?grant_type=client_credentials")
PRICES_URL = "https://api.onegov.nsw.gov.au/FuelPriceCheck/v1/fuel/prices"
OUTPUT = "australia/data/stations/nsw_stations.json"


def main():
    with open(CRED_PATH) as f:
        cred = json.load(f)
    auth = cred["auth_header"]
    api_key = cred["api_key"]

    # 1) Get access token
    print("Requesting OAuth access token...")
    token_res = subprocess.run(
        ["curl", "-sS", "--max-time", "30",
         "-H", f"Authorization: {auth}",
         OAUTH_URL],
        capture_output=True, check=True,
    )
    token = json.loads(token_res.stdout)
    access_token = token.get("access_token")
    if not access_token:
        print("Failed to get access token. Response:", token_res.stdout.decode())
        sys.exit(1)
    print(f"  got token (expires in {token.get('expires_in')} s)")

    # 2) Call the prices endpoint — returns all stations with coords
    print("Fetching full NSW fuel station snapshot (single call)...")
    txn_id = str(uuid.uuid4())
    ts = dt.datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
    prices_res = subprocess.run(
        ["curl", "-sS", "--max-time", "120",
         "-H", f"Authorization: Bearer {access_token}",
         "-H", f"apikey: {api_key}",
         "-H", f"transactionid: {txn_id}",
         "-H", f"requesttimestamp: {ts}",
         "-H", "Content-Type: application/json; charset=utf-8",
         PRICES_URL],
        capture_output=True, check=True,
    )
    raw = prices_res.stdout
    print(f"  response: {len(raw):,} bytes")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}")
        print("First 500 bytes of response:")
        print(raw[:500].decode("utf-8", errors="replace"))
        sys.exit(1)

    # Save full response
    with open(OUTPUT, "wb") as f:
        f.write(raw)
    print(f"  wrote {OUTPUT}")

    # Summary
    stations = data.get("stations", [])
    prices = data.get("prices", [])
    print(f"\nResponse contains:")
    print(f"  {len(stations):,} unique stations")
    print(f"  {len(prices):,} price records")
    if stations:
        s = stations[0]
        print(f"\nSample station record:")
        print(json.dumps(s, indent=2)[:500])


if __name__ == "__main__":
    main()
