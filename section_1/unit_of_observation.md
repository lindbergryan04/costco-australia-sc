# Unit of observation, by registry

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
