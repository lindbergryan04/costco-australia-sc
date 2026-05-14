"""
Build Section 1 of the Plan of Attack deliverable PDF.

Modelled on the Section 1 of `plan_of_attack_example_solution_synthetic_control.pdf`
(food-waste-bans example): one paragraph per dataset with a field-table,
then a unified outcome/treatment construction note, summary statistics
table, treated-Costco table, data quality issues paragraph, and a
contingencies paragraph.

Output: deliverables/plan_of_attack_section_1.pdf (in the worktree).
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    Image, PageBreak,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTFILE = str(REPO_ROOT / "deliverables" / "plan_of_attack_section_1.pdf")
PLOTS_DIR = str(REPO_ROOT / "section_1" / "plots")


def _table(rows, col_widths, header=True, body_font_size=10):
    style = TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
    if header:
        style.add("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black)
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(style)
    return t


def main():
    doc = SimpleDocTemplate(
        OUTFILE,
        pagesize=letter,
        leftMargin=0.95 * inch, rightMargin=0.95 * inch,
        topMargin=0.95 * inch, bottomMargin=0.95 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontName="Times-Bold",
        fontSize=18, alignment=TA_CENTER, spaceAfter=4, leading=22,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontName="Times-Italic",
        fontSize=12, alignment=TA_CENTER, spaceAfter=6, leading=14,
    )
    rq_style = ParagraphStyle(
        "RQ", parent=styles["Normal"], fontName="Times-Roman",
        fontSize=11, leading=14, spaceBefore=4, spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading1"], fontName="Times-Bold",
        fontSize=14, spaceBefore=14, spaceAfter=8, leading=18,
    )
    subsection_style = ParagraphStyle(
        "Subsection", parent=styles["Heading2"], fontName="Times-Bold",
        fontSize=12, spaceBefore=10, spaceAfter=4, leading=15,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Times-Roman",
        fontSize=11, leading=14, alignment=TA_JUSTIFY, spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"], fontName="Times-Roman",
        fontSize=10, leading=12,
    )
    cell_mono = ParagraphStyle(
        "CellMono", parent=cell_style, fontName="Courier", fontSize=10,
    )
    caption_style = ParagraphStyle(
        "Caption", parent=styles["Normal"], fontName="Times-Italic",
        fontSize=9.5, alignment=TA_CENTER, leading=12,
        spaceBefore=4, spaceAfter=10,
    )

    story = []

    # ---- Title block ----
    story.append(Paragraph("Plan of Attack", title_style))
    story.append(Paragraph("Costco Australia / Synthetic Control",
                           subtitle_style))
    story.append(Paragraph(
        "<b>Research question:</b> Does the entry of a Costco gas station "
        "into an Australian local market cause nearby competitor stations "
        "to lower their retail fuel prices?",
        rq_style,
    ))

    # ---- Section 1 header ----
    story.append(Paragraph("Section 1, Raw Data Description", section_style))
    story.append(Paragraph(
        "We use four datasets, described separately below: three "
        "publicly accessible Australian state fuel-price registries that "
        "we combine into a unified station-month panel, plus a "
        "hand-collected list of Costco fuel-station opening dates. The "
        "three registries together yield approximately 17.4 million "
        "station-day price records across 6,084 unique stations between "
        "January 2018 and April 2026.",
        body_style,
    ))

    # ---- Per-registry sub-sections ----

    # 1.1 NSW
    story.append(Paragraph("1.1 NSW FuelCheck", subsection_style))
    story.append(Paragraph(
        "NSW FuelCheck is maintained by the New South Wales Government and "
        "has required mandatory price reporting from every retail fuel "
        "station in NSW (and, since November 2023, the ACT) since August "
        "2016. Historical records are published as monthly Excel files "
        "via data.nsw.gov.au; we pulled 93 monthly files covering "
        "December 2016 through January 2026, totalling <b>4,401,971 "
        "price-update records</b> with 8 columns. Each row is one "
        "price-update event: a station &times; fuel type &times; the "
        "timestamp at which the operator changed (or re-confirmed) its "
        "posted price. FuelCheck stores price-change events rather than "
        "daily snapshots. Composite unique key: "
        "<font face='Courier'>(ServiceStationName, Address, FuelCode, "
        "PriceUpdatedDate)</font>. The file contains 4,813 unique "
        "stations (4,543 after the name normalization used in the "
        "live-API coordinate join, see Section 2(f)), 62 unique brands, "
        "565 unique postcodes, and 11 unique fuel-type "
        "codes (regular unleaded ULP/U91/E10, premium PUL95/PUL98, diesel "
        "DSL/PDL, LPG, and others). Coordinates are not in the historical "
        "files; we attached lat/lng by joining station name + postcode to "
        "a one-time pull from the live FuelCheck API.",
        body_style,
    ))
    nsw_table = _table([
        [Paragraph("<b>Field</b>", cell_style),
         Paragraph("<b>Description</b>", cell_style)],
        [Paragraph("ServiceStationName", cell_mono),
         Paragraph("Station name (operator-provided)", cell_style)],
        [Paragraph("Address", cell_mono),
         Paragraph("Street address", cell_style)],
        [Paragraph("Suburb", cell_mono),
         Paragraph("Suburb", cell_style)],
        [Paragraph("Postcode", cell_mono),
         Paragraph("Postcode (4-digit)", cell_style)],
        [Paragraph("Brand", cell_mono),
         Paragraph("Brand affiliation (Costco, Caltex, Shell, BP, etc.)",
                   cell_style)],
        [Paragraph("FuelCode", cell_mono),
         Paragraph("Fuel-type code (U91, E10, PUL95, PUL98, DSL, LPG, ...)",
                   cell_style)],
        [Paragraph("PriceUpdatedDate", cell_mono),
         Paragraph("Timestamp at which price was reported", cell_style)],
        [Paragraph("Price", cell_mono),
         Paragraph("Posted retail price (cents per liter)", cell_style)],
    ], col_widths=[1.8 * inch, 3.9 * inch])
    story.append(nsw_table)
    story.append(Spacer(1, 6))

    # 1.2 QLD
    story.append(Paragraph("1.2 Queensland Fuel Price Reporting Scheme",
                           subsection_style))
    story.append(Paragraph(
        "The Queensland Fuel Price Reporting Scheme is administered by "
        "Queensland Treasury; mandatory station reporting began in "
        "December 2018. Historical records are published as monthly "
        "CSVs via data.qld.gov.au; we pulled 85 monthly files covering "
        "December 2018 through December 2025, totalling <b>4,970,650 "
        "price-change records</b> with 13 columns. Each row is one "
        "price-change event: a station &times; fuel type &times; the "
        "UTC timestamp at which the price changed. Composite unique "
        "key: <font face='Courier'>(SiteId, Fuel_Type, "
        "TransactionDateutc)</font>. The file contains 1,883 unique "
        "stations, 37 brands, 375 postcodes, and 10 fuel-type strings. "
        "Coordinates are present inline.",
        body_style,
    ))
    qld_table = _table([
        [Paragraph("<b>Field</b>", cell_style),
         Paragraph("<b>Description</b>", cell_style)],
        [Paragraph("SiteId", cell_mono),
         Paragraph("Stable per-station numeric identifier", cell_style)],
        [Paragraph("Site_Name", cell_mono),
         Paragraph("Station name", cell_style)],
        [Paragraph("Site_Brand", cell_mono),
         Paragraph("Brand affiliation", cell_style)],
        [Paragraph("Sites_Address_Line_1", cell_mono),
         Paragraph("Street address", cell_style)],
        [Paragraph("Site_Suburb", cell_mono),
         Paragraph("Suburb", cell_style)],
        [Paragraph("Site_Post_Code", cell_mono),
         Paragraph("Postcode (4-digit)", cell_style)],
        [Paragraph("Site_Latitude / Site_Longitude", cell_mono),
         Paragraph("WGS84 coordinates (used for great-circle distance "
                   "to Costco)", cell_style)],
        [Paragraph("Fuel_Type", cell_mono),
         Paragraph("Fuel-type label (Unleaded 91, e10, Premium 95, ...)",
                   cell_style)],
        [Paragraph("Price", cell_mono),
         Paragraph("Posted retail price in tenths of a cent (1899 = 189.9 ¢/L)",
                   cell_style)],
        [Paragraph("TransactionDateutc", cell_mono),
         Paragraph("UTC timestamp of the price change", cell_style)],
    ], col_widths=[2.1 * inch, 3.6 * inch])
    story.append(qld_table)
    story.append(Spacer(1, 6))

    # 1.3 WA
    story.append(Paragraph("1.3 WA FuelWatch", subsection_style))
    story.append(Paragraph(
        "WA FuelWatch is maintained by the Western Australia Government "
        "and has required daily mandatory price reporting from every "
        "retail fuel station in WA since January 2001, the longest "
        "fuel-price history of any Australian state. Historical records "
        "are published as monthly CSVs via data.wa.gov.au; we pulled 100 "
        "monthly files covering January 2018 through April 2026, "
        "totalling <b>8,047,153 daily-snapshot records</b> with 11 "
        "columns. (We chose not to pull the full 2001&ndash;2017 archive "
        "because no usable Costco event has a pre-period that benefits "
        "from extending earlier than 2018.) Each row is a daily snapshot "
        "(a station &times; fuel type &times; calendar day), and unlike "
        "NSW and QLD, FuelWatch publishes one record per "
        "station per day regardless of whether the price changed. "
        "Composite unique key: <font face='Courier'>(TRADING_NAME, "
        "ADDRESS, PRODUCT_DESCRIPTION, PUBLISH_DATE)</font>. The file "
        "contains 1,423 unique stations, 47 brands, 200 postcodes, and 7 "
        "fuel-type strings. Coordinates are not in the historical files; "
        "we attached lat/lng by joining station name + postcode to a "
        "one-time pull from the live FuelWatch API.",
        body_style,
    ))
    wa_table = _table([
        [Paragraph("<b>Field</b>", cell_style),
         Paragraph("<b>Description</b>", cell_style)],
        [Paragraph("PUBLISH_DATE", cell_mono),
         Paragraph("Calendar day of the snapshot", cell_style)],
        [Paragraph("TRADING_NAME", cell_mono),
         Paragraph("Station name", cell_style)],
        [Paragraph("BRAND_DESCRIPTION", cell_mono),
         Paragraph("Brand affiliation", cell_style)],
        [Paragraph("PRODUCT_DESCRIPTION", cell_mono),
         Paragraph("Fuel-type label (ULP, 98 RON, Diesel, LPG, ...)",
                   cell_style)],
        [Paragraph("PRODUCT_PRICE", cell_mono),
         Paragraph("Posted retail price (cents per liter)", cell_style)],
        [Paragraph("ADDRESS", cell_mono),
         Paragraph("Street address", cell_style)],
        [Paragraph("LOCATION", cell_mono),
         Paragraph("Suburb / locality", cell_style)],
        [Paragraph("POSTCODE", cell_mono),
         Paragraph("Postcode (4-digit)", cell_style)],
        [Paragraph("AREA_DESCRIPTION / REGION_DESCRIPTION", cell_mono),
         Paragraph("Government-defined regional grouping (used as a "
                   "secondary geographic check)", cell_style)],
    ], col_widths=[2.4 * inch, 3.3 * inch])
    story.append(wa_table)
    story.append(Spacer(1, 6))

    # 1.4 Costco
    story.append(Paragraph("1.4 Costco gas station opening dates "
                           "(hand-collected)", subsection_style))
    story.append(Paragraph(
        "We hand-compiled a 10-row table of every Costco fuel station in "
        "Australia, recording each station&rsquo;s state, suburb, "
        "postcode, coordinates, and treatment date. Each treatment date "
        "is the station&rsquo;s first-observed date in the relevant "
        "state&rsquo;s price registry, then cross-validated against "
        "announced fuel-station opening dates and trade press "
        "(Section 2(d)). The composite unique key is "
        "<font face='Courier'>name</font>. Of the 10 stations, four are "
        "usable as treated units in the synthetic-control analysis "
        "(Coomera, Casuarina, Perth Airport, Lake Macquarie); the "
        "remaining six are excluded from formal estimation but appear "
        "as descriptive context.",
        body_style,
    ))

    # ---- Summary statistics ----
    story.append(Paragraph(
        "Summary statistics, postcode-month analysis sample (3 states, "
        "Jan 2018 &ndash; Apr 2026)", subsection_style))
    summary_table = _table([
        [Paragraph("<b>Variable</b>", cell_style),
         Paragraph("<b>n</b>", cell_style),
         Paragraph("<b>Mean</b>", cell_style),
         Paragraph("<b>SD</b>", cell_style),
         Paragraph("<b>Min</b>", cell_style),
         Paragraph("<b>p25</b>", cell_style),
         Paragraph("<b>Median</b>", cell_style),
         Paragraph("<b>p75</b>", cell_style),
         Paragraph("<b>Max</b>", cell_style)],
        [Paragraph("<i>Main outcome</i>", cell_style),
         "", "", "", "", "", "", "", ""],
        [Paragraph("Mean unleaded price (¢/L)", cell_style),
         Paragraph("17,953", cell_style),
         Paragraph("160.5", cell_style),
         Paragraph("28.4", cell_style),
         Paragraph("92.0", cell_style),
         Paragraph("137.3", cell_style),
         Paragraph("162.2", cell_style),
         Paragraph("183.6", cell_style),
         Paragraph("259.0", cell_style)],
        [Paragraph("<i>Main covariates</i>", cell_style),
         "", "", "", "", "", "", "", ""],
        [Paragraph("Station distance to nearest Costco (km)", cell_style),
         Paragraph("5,980", cell_style),
         Paragraph("204.8", cell_style),
         Paragraph("357.4", cell_style),
         Paragraph("0.0", cell_style),
         Paragraph("14.8", cell_style),
         Paragraph("48.3", cell_style),
         Paragraph("216.7", cell_style),
         Paragraph("2,214", cell_style)],
    ], col_widths=[2.1 * inch, 0.55 * inch, 0.55 * inch, 0.5 * inch,
                   0.55 * inch, 0.55 * inch, 0.6 * inch, 0.55 * inch,
                   0.55 * inch])
    story.append(summary_table)
    story.append(Paragraph(
        "Counts: 84 stations classified as treated (within 5 km of a "
        "treated Costco), 3,926 donor-eligible (>20 km from every "
        "Costco), 1,970 in the 5&ndash;20 km exclusion donut. The "
        "17,953 postcode-month rows above are the donor candidate panel "
        "before geographic and quality filters; the post-filter SC donor "
        "pool is 17,578 cells (Section 2(g)).",
        caption_style,
    ))

    # ---- Figure 1: histogram of dependent variable ----
    story.append(Spacer(1, 6))
    story.append(Image(f"{PLOTS_DIR}/01_price_histogram.png",
                       width=6.5 * inch, height=3.25 * inch))
    story.append(Paragraph(
        "<b>Figure 1.</b> Distribution of postcode-month mean unleaded "
        "prices across the 17,953 panel observations. The distribution "
        "is approximately bimodal: the lower mode reflects the "
        "2018&ndash;2020 price regime, the higher mode reflects the "
        "post-2022 elevated price era. Mean = 160.5&nbsp;¢/L, median "
        "162.2&nbsp;¢/L. No observations outside 92&ndash;259&nbsp;¢/L "
        "after our 50&ndash;500&nbsp;¢/L sanity filter.",
        caption_style,
    ))

    # ---- Figure 2: dependent variable over time ----
    story.append(Spacer(1, 6))
    story.append(Image(f"{PLOTS_DIR}/02_unleaded_median_over_time.png",
                       width=6.5 * inch, height=3.25 * inch))
    story.append(Paragraph(
        "<b>Figure 2.</b> Median of postcode-monthly mean unleaded "
        "prices over time, by state, January 2018 to April 2026. "
        "All three states track each other closely throughout: prices "
        "fall in 2018&ndash;2020 (peaking with COVID demand collapse "
        "in early 2020), rise sharply through 2022 (Russia/Ukraine "
        "energy shock), dip during the Mar&ndash;Sep 2022 fuel-excise "
        "cut, and remain elevated through 2026. State-level co-movement "
        "supports our use of within-state donor pools to absorb common "
        "national shocks.",
        caption_style,
    ))

    # ---- Treated/excluded Costcos ----
    story.append(Paragraph(
        "Australian Costco fuel stations by treatment status",
        subsection_style))
    treated_table = _table([
        [Paragraph("<b>Costco</b>", cell_style),
         Paragraph("<b>State</b>", cell_style),
         Paragraph("<b>Treatment date</b>", cell_style),
         Paragraph("<b>Pre months</b>", cell_style),
         Paragraph("<b>Post months</b>", cell_style),
         Paragraph("<b>Status</b>", cell_style)],
        [Paragraph("Coomera", cell_style),
         Paragraph("QLD", cell_style),
         Paragraph("May 2023", cell_style),
         Paragraph("51", cell_style),
         Paragraph("31", cell_style),
         Paragraph("Treated", cell_style)],
        [Paragraph("Casuarina", cell_style),
         Paragraph("WA", cell_style),
         Paragraph("Nov 2022", cell_style),
         Paragraph("58", cell_style),
         Paragraph("42", cell_style),
         Paragraph("Treated", cell_style)],
        [Paragraph("Perth Airport", cell_style),
         Paragraph("WA", cell_style),
         Paragraph("Feb 2020", cell_style),
         Paragraph("26", cell_style),
         Paragraph("74", cell_style),
         Paragraph("Treated", cell_style)],
        [Paragraph("Lake Macquarie", cell_style),
         Paragraph("NSW", cell_style),
         Paragraph("May 2022", cell_style),
         Paragraph("58", cell_style),
         Paragraph("35", cell_style),
         Paragraph("Treated", cell_style)],
        [Paragraph("Marsden Park", cell_style),
         Paragraph("NSW", cell_style),
         Paragraph("Jul 2017", cell_style),
         Paragraph("11", cell_style),
         Paragraph("105", cell_style),
         Paragraph("Excluded (pre too short)", cell_style)],
        [Paragraph("Auburn", cell_style),
         Paragraph("NSW", cell_style),
         Paragraph("Aug 2025", cell_style),
         Paragraph("107", cell_style),
         Paragraph("8", cell_style),
         Paragraph("Excluded (post too short)", cell_style)],
        [Paragraph("Canberra Airport", cell_style),
         Paragraph("ACT", cell_style),
         Paragraph("Nov 2023", cell_style),
         Paragraph("0", cell_style),
         Paragraph("29", cell_style),
         Paragraph("Excluded (no pre)", cell_style)],
        [Paragraph("Casula", cell_style),
         Paragraph("NSW", cell_style),
         Paragraph("Dec 2016", cell_style),
         Paragraph("4", cell_style),
         Paragraph("113", cell_style),
         Paragraph("Excluded (pre-registry)", cell_style)],
        [Paragraph("North Lakes", cell_style),
         Paragraph("QLD", cell_style),
         Paragraph("Jan 2019", cell_style),
         Paragraph("1", cell_style),
         Paragraph("89", cell_style),
         Paragraph("Excluded (pre-registry)", cell_style)],
        [Paragraph("Ipswich", cell_style),
         Paragraph("QLD", cell_style),
         Paragraph("Mar 2019", cell_style),
         Paragraph("3", cell_style),
         Paragraph("87", cell_style),
         Paragraph("Excluded (pre-registry)", cell_style)],
    ], col_widths=[1.2 * inch, 0.55 * inch, 0.85 * inch, 0.7 * inch,
                   0.75 * inch, 1.65 * inch])
    story.append(treated_table)
    story.append(Spacer(1, 6))

    # ---- Figure 4: per-Costco event studies ----
    story.append(Image(f"{PLOTS_DIR}/05_treated_event_studies.png",
                       width=6.5 * inch, height=7.0 * inch))
    story.append(Paragraph(
        "<b>Figure 3.</b> Treated 5&nbsp;km ring mean unleaded price "
        "(coloured solid) versus the state median across all reporting "
        "postcodes (grey dashed) for each of the four treated Costcos. "
        "The vertical red dashed line marks the validated treatment "
        "date (Section 2(d)). Three shock annotations decode the "
        "post-2020 surge: grey shading marks the COVID demand collapse "
        "(Mar&ndash;Sep 2020); the dotted vertical line at 24 Feb 2022 "
        "marks Russia&rsquo;s invasion of Ukraine; pale blue shading "
        "marks the AU federal fuel-excise cut "
        "(30 Mar&ndash;28 Sep 2022), a temporary halving of the "
        "44.2&nbsp;&cent;/L fuel excise to 22.1&nbsp;&cent;/L announced "
        "in the March 2022 budget as cost-of-living relief in response "
        "to the post-invasion price spike. The state-median overlay "
        "gives each panel a level reference: Perth Airport sits "
        "modestly below the WA median, Coomera tracks the QLD median "
        "closely, Lake Macquarie tracks NSW closely, and "
        "Casuarina&rsquo;s sparse 5&nbsp;km ring (~3 contributing "
        "stations) reads as month-to-month noise around its WA "
        "median. Coomera&rsquo;s registry coverage gradually builds "
        "up through 2018&ndash;2020 before stabilising. The state "
        "median is a descriptive level reference only; it is not the "
        "synthetic-control counterfactual, which is constructed in "
        "Section 3 from a weighted subset of donor postcodes.",
        caption_style,
    ))
    story.append(Spacer(1, 6))

    # ---- Data quality issues ----
    story.append(Paragraph("Data quality issues", subsection_style))
    story.append(Paragraph(
        "<b>Price units differ across registries.</b> NSW prices are in "
        "cents/L (e.g. <font face='Courier'>158.7</font>), QLD prices are "
        "in tenths of cents (<font face='Courier'>1899</font> = 189.9 "
        "¢/L), WA prices are in cents/L. Each registry&rsquo;s ingest "
        "applies the appropriate scaling so the panel is uniform in "
        "cents/L.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Coordinates missing in historical NSW and WA files.</b> "
        "NSW FuelCheck XLSX records carry only address text; WA FuelWatch "
        "records carry address and postcode (no lat/lng). QLD historical "
        "records do include coordinates inline. We resolved this by "
        "pulling the live NSW FuelCheck API "
        "(<font face='Courier'>/v1/fuel/prices</font>) and the live WA "
        "FuelWatch API (<font face='Courier'>/api/sites</font>) once and "
        "joining historical records to the live coords by "
        "(normalized_name, postcode). The live-API snapshot contains NSW "
        "3,281 stations, WA 921 stations, QLD 1,882 stations, totalling "
        "6,084. Stations that closed, rebranded, or were re-numbered "
        "before April 2026 are absent from the snapshot, so historical "
        "rows for them fail the join: the snapshot misses 2,376 of 4,543 "
        "NSW historical stations (52.3%) and 673 of 1,423 WA historical "
        "stations (47.3%); QLD is unaffected because its historical files "
        "carry coordinates inline. The loss falls almost entirely on the "
        "donor pool: all four treated Costcos join cleanly. Row-level "
        "impact on the analysis panel is in Section 2(g).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Brand renaming in NSW (May 2022).</b> Every NSW Costco "
        "station was renamed in the registry from e.g. \"Costco Marsden "
        "Park\" to \"Costco Marsden Park (Members only)\" on 2 May 2022. "
        "We strip the \"(Members only)\" suffix before matching so the "
        "rename is invisible to the analysis pipeline.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Outliers in <font face='Courier'>price</font>.</b> Quotes "
        "below 80 ¢/L or above 280 ¢/L are implausible for Australian "
        "retail unleaded post-2018 (national averages hover 130&ndash;220 "
        "¢/L). After our 50&ndash;500 ¢/L sanity filter, the post-aggregation "
        "panel of 17,953 postcode-months has no observations outside "
        "92&ndash;259 ¢/L, well within plausible Australian range.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Treated-Costco coverage variance.</b> Coomera&rsquo;s pre-2020 "
        "QLD coverage is sparse because the QLD scheme began in December "
        "2018 and Coomera-area stations entered the registry gradually; "
        "the relevant pre-period (Sep 2020 → May 2023) is fully covered. "
        "Casuarina has only ~3 unique stations within 5 km contributing "
        "to the treated mean, reflecting a sparse coastal residential "
        "market; coverage is 100 % but the treated mean is noisier than "
        "for the other three Costcos. Lake Macquarie has a "
        "small number of intermittent monthly gaps (largest 3 months) "
        "that do not impair pre-period fitting.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Donor pool construction.</b> Out of all postcodes with any "
        "non-Costco unleaded data, the donor pool drops 362 postcodes "
        "within 20 km of any Costco (potential contamination from "
        "Costco&rsquo;s competitive footprint), 446 with fewer than 3 "
        "stations on average per month (means too noisy), and 0 with "
        "fewer than 24 months of observations. <b>196 donor postcodes</b> "
        "survive all filters: NSW 104, QLD 56, WA 36, totalling 17,578 "
        "(postcode &times; month) panel observations. Per-state "
        "breakdown of the 362 / 446 / 0 drops is in Section 2(g).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Multiple records per station-day.</b> NSW and QLD both record "
        "price-update events rather than daily snapshots, so a station "
        "appears multiple times within a day if it changed prices on "
        "multiple fuel types. These are not duplicates; they are "
        "legitimate event-level records and are correctly aggregated to "
        "monthly means by the panel build.",
        body_style,
    ))

    doc.build(story)
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
