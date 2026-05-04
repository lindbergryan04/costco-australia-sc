"""
Robust NSW FuelCheck XLSX reader.

NSW historical XLSX files have three different schemas across years:

  2018-2019:  row 0 = title ("Price_History_Dec_2018", ...),
              row 1 = column header,
              row 2+ = data,
              PriceUpdatedDate stored as Python datetime objects.

  2020-2023:  row 0 = title ("Price History Checks"),
              row 1 = blank,
              row 2 = column header,
              row 3+ = data,
              PriceUpdatedDate stored as a string
              (e.g. "1/04/2020 12:13:08 AM").

  2024+:      row 0 = column header (no title row),
              row 1+ = data,
              PriceUpdatedDate stored as datetime objects.

This module provides a single robust iterator that handles all three
schema variants and normalizes the date to a Python `date` object.
Use it everywhere NSW historical XLSX files are read.
"""

import datetime as dt

import openpyxl


_DATE_FORMATS = [
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %I:%M %p",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def parse_nsw_date(d):
    """Convert NSW PriceUpdatedDate to a date; return None if unparseable.
    Handles datetime objects (2018, 2024+) and Aussie-format strings
    (2020-2023)."""
    if d is None:
        return None
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, dt.date):
        return d
    if isinstance(d, str):
        s = d.strip().split(".")[0]
        for fmt in _DATE_FORMATS:
            try:
                return dt.datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def iter_nsw_data_rows(filepath):
    """Iterate (ServiceStationName, Address, Suburb, Postcode, Brand,
    FuelCode, PriceUpdatedDate, Price) tuples from an NSW XLSX,
    correctly handling all known schema variants. PriceUpdatedDate is
    yielded as a `date` object (not datetime, not string)."""
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    seen_header = False
    for row in ws.iter_rows(values_only=True):
        if not seen_header:
            # Search forward for the column-header row.
            if row and row[0] and str(row[0]).strip().lower() == "servicestationname":
                seen_header = True
            continue
        # Past the header now; data row.
        if not row or not row[0]:
            continue
        try:
            name = row[0]
            address = row[1]
            suburb = row[2]
            postcode = row[3]
            brand = row[4]
            fuel_code = row[5]
            price_date = parse_nsw_date(row[6])
            price = row[7]
        except IndexError:
            continue
        yield (name, address, suburb, postcode, brand, fuel_code,
               price_date, price)
    wb.close()
