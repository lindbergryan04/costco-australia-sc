"""
Build alternate-radius SC input panels for Section 4 robustness checks.

Produces four variants by calling build_sc_inputs.build() with non-default
geometries. Each variant lands in its own subdirectory under
data/sc_inputs_alt/, ready to be uploaded alongside the headline
5 km / 20 km files in the analysis's Dropbox folder. The .qmd reads only
the rows it needs from each variant (e.g. Robustness Check 3 reads the
Casuarina row from casuarina_10km/, ignoring the other three Costcos).

Variants:
  1. 3 km treated  / 15 km donor exclusion       → 3km_15km/        (RC2)
  2. 8 km treated  / 30 km donor exclusion       → 8km_30km/        (RC2)
  3. 10 km treated / 20 km donor exclusion       → casuarina_10km/  (RC3)
  4. 5-20 km donut as treated unit               → donut_5_20km/    (RC7)

The Casuarina variant rebuilds all four Costcos at 10 km because the build
function is per-geometry rather than per-Costco; downstream analysis only
consumes the Casuarina row.

The donut variant produces a treated panel whose "5 km ring" is replaced
by the 5-20 km annulus around each Costco. Fit synthetic-control normally
against the same >20 km donor pool: if the donut shows a Costco-style
gap, the headline 5 km result is conservative; if it doesn't, the 20 km
buffer is comfortably sufficient.

Run from the repo root (the directory containing `scripts/` and
`_local/cache/`). Total runtime ~30 min on the 1.86 GB raw cache.
"""

import os
import sys
import time

# Allow running this file directly from anywhere reasonable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_sc_inputs import build

ALT_ROOT = "data/sc_inputs_alt"

VARIANTS = [
    # (label, kwargs to build())
    ("3km_15km",       dict(near_km=3.0,  exclude_km=15.0)),
    ("8km_30km",       dict(near_km=8.0,  exclude_km=30.0)),
    ("casuarina_10km", dict(near_km=10.0, exclude_km=20.0)),
    ("donut_5_20km",   dict(near_km=20.0, exclude_km=20.0, inner_km=5.0)),
]


def main():
    summaries = []
    t_total = time.time()
    for label, kwargs in VARIANTS:
        out_dir = os.path.join(ALT_ROOT, label)
        print("\n" + "#" * 72)
        print(f"# Variant: {label} → {out_dir}")
        print(f"# Args: {kwargs}")
        print("#" * 72)
        t0 = time.time()
        summary = build(out_dir=out_dir, **kwargs)
        elapsed = time.time() - t0
        summary["label"] = label
        summary["elapsed_s"] = round(elapsed, 1)
        summaries.append(summary)
        print(f"\n  ✓ {label}: {elapsed/60:.1f} min")

    print("\n" + "=" * 72)
    print(f"All four alt-radius variants built in {(time.time() - t_total)/60:.1f} min.")
    print("=" * 72)
    print(f"{'Variant':18s}  {'near_km':>8s}  {'exclude_km':>10s}  "
          f"{'inner_km':>8s}  {'treated':>8s}  {'donors':>7s}  {'rows':>7s}")
    for s in summaries:
        print(f"{s['label']:18s}  "
              f"{s['near_km']:>8.1f}  {s['exclude_km']:>10.1f}  "
              f"{s['inner_km']:>8.1f}  {s['n_treated_rows']:>8d}  "
              f"{s['n_donor_postcodes']:>7d}  {s['n_donor_rows']:>7d}")

    print("\nNext: upload the four subdirectories of "
          f"{ALT_ROOT}/ to the Dropbox folder so the .qmd setup chunk "
          "can pull them down for §4 robustness checks.")


if __name__ == "__main__":
    main()
