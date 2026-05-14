"""
Build Section 2 of the Plan of Attack deliverable PDF.

Section 2 is the Sample Construction Plan: the prospective description
of how raw registry data is mapped to the analysis-ready synthetic-control
inputs, with each decision justified and every filter reported with its
observation-count impact. Stylistically modelled on Section 1.

Output: deliverables/plan_of_attack_section_2.pdf (in the worktree).
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTFILE = REPO_ROOT / "deliverables" / "plan_of_attack_section_2.pdf"


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
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTFILE),
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
    bullet_style = ParagraphStyle(
        "Bullet", parent=body_style, leftIndent=18, bulletIndent=6,
        spaceAfter=4,
    )
    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"], fontName="Times-Roman",
        fontSize=10, leading=12,
    )
    cell_mono = ParagraphStyle(
        "CellMono", parent=cell_style, fontName="Courier", fontSize=10,
    )
    cell_small = ParagraphStyle(
        "CellSmall", parent=cell_style, fontSize=9, leading=11,
    )
    cell_small_right = ParagraphStyle(
        "CellSmallRight", parent=cell_small, alignment=2,  # TA_RIGHT
    )
    caption_style = ParagraphStyle(
        "Caption", parent=styles["Normal"], fontName="Times-Italic",
        fontSize=9.5, alignment=TA_CENTER, leading=12,
        spaceBefore=4, spaceAfter=10,
    )

    story = []

    # ---- Title block ----
    story.append(Paragraph(
        "Plan of Attack: Section 2, Sample Construction Plan",
        title_style))
    story.append(Spacer(1, 14))

    # ---- (a) Sample window ----
    story.append(Paragraph("(a) Sample window", section_style))
    story.append(Paragraph(
        "<b>Endpoints.</b> The pre-period for each treated Costco runs "
        "from the start of its state's price registry (December 2016 for "
        "NSW, January 2018 for WA, December 2018 for QLD) up to the day "
        "before that Costco's validated treatment date (see (d)). The "
        "post-period runs from the treatment date through April 2026, "
        "the most recent registry pull. Per-Costco pre-period lengths "
        "range from 26 (Perth Airport) to 58 months (Casuarina, Lake "
        "Macquarie); post-period lengths from 31 (Coomera) to 74 months "
        "(Perth Airport).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Pre-period length.</b> Synthetic control fits its weights on "
        "the entire pre-period <i>trajectory</i> of the dependent "
        "variable, not just on a level. More pre-period observations "
        "tighten identification rather than dilute it, the opposite of "
        "the DID logic in which long pre-periods can introduce "
        "structural breaks into the parallel-trends assumption. "
        "Same-state donors experience the same world-shifts (oil-price "
        "regime changes, vehicle fleet turnover, federal excise "
        "adjustments) over the same window, so common shocks are "
        "absorbed into the synthetic by construction. We use as much "
        "pre-period as the data allow.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>COVID.</b> The 2020 demand collapse and recovery is the only "
        "structural break large enough to warrant explicit handling. "
        "Three of the four treated Costcos opened well after the COVID "
        "disruption (Lake Macquarie May 2022, Casuarina November 2022, "
        "Coomera May 2023); for those three the COVID period sits "
        "entirely inside the pre-period and is matched by the synthetic "
        "by construction. <b>Perth Airport (treated 19 February 2020)</b> "
        "opens approximately four weeks before Australia's COVID demand "
        "collapse begins; this is the most fragile case in the analysis. "
        "Its pre-period is entirely pre-COVID, but its early "
        "post-treatment months are dominated by pandemic-driven price "
        "movements rather than competitive response to Costco's entry. "
        "The synthetic counterfactual is built from WA donor postcodes "
        "that experienced the same pandemic shock, so the post-treatment "
        "gap nets out COVID provided the pre-period weights track the "
        "treated trajectory through January 2020. As a Section&nbsp;3 "
        "robustness check, Perth Airport is re-estimated with "
        "March&ndash;December 2020 dropped from both panels.",
        body_style,
    ))

    # ---- (b) Other sample restrictions ----
    story.append(Paragraph("(b) Other sample restrictions", section_style))
    story.append(Paragraph(
        "<b>Treated unit.</b> For each treated Costco, the treated unit "
        "is the <i>local market</i> defined as all non-Costco retail "
        "stations within 5 km of the Costco's coordinates, summarised "
        "each month as the simple mean of those stations' monthly mean "
        "unleaded prices. We exclude Costco's own price quotes from the "
        "treated mean because the research question concerns competitor "
        "response, not Costco's own pricing.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Donor pool.</b> Each donor unit is a 4-digit Australian "
        "postcode, summarised the same way (monthly mean of non-Costco "
        "unleaded price across all stations within the postcode). "
        "Postcodes are the natural geographic unit of the three state "
        "registries and are consistent across NSW, QLD, and WA. A "
        "postcode is excluded from the donor pool if any of its stations "
        "lie within 20 km of <i>any</i> Costco fuel station (treated, "
        "excluded, or otherwise), so that donor postcodes are "
        "unambiguously outside any plausible Costco competitive footprint.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Asymmetric radii (5 km treated, 20 km donor buffer).</b> "
        "The economics literature on retail fuel-price competition "
        "(Houde&nbsp;2012; Eckert&nbsp;2013) finds price effects "
        "concentrated within roughly 1&ndash;5 miles. 5 km "
        "(~3.1&nbsp;mi) sits at the conservative end of that range, "
        "small enough to capture genuinely competing stations but not so "
        "small as to drop most of the local market. The 20 km donor "
        "buffer is intentionally a 4&times; multiple, providing a wide "
        "exclusion donut so that no donor postcode is partly affected "
        "by a Costco that isn't the one we're studying. The "
        "asymmetry (small treated radius, large donor buffer) biases "
        "the design <i>against</i> finding an effect: narrow treated "
        "definition shrinks the treated population to the most exposed "
        "stations, and the wide buffer shrinks the donor pool to truly "
        "untreated postcodes.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Outcome variable.</b> Regular unleaded (FuelCode in {U91, "
        "E10, P91} for NSW; <font face='Courier'>Fuel_Type</font> in "
        "{Unleaded 91, e10} for QLD; "
        "<font face='Courier'>PRODUCT_DESCRIPTION</font> = ULP for WA). "
        "Unleaded is the highest-volume retail product in Australia, "
        "comparable across the three state schemes, and Costco's headline "
        "competitive product.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Donor-pool measurement-quality filters.</b> A postcode is "
        "additionally excluded if it averages fewer than 3 unique "
        "stations per month (monthly means based on 1&ndash;2 stations "
        "are too noisy to serve as credible counterfactual building "
        "blocks) or has fewer than 24 months of any observed coverage "
        "(weights cannot be reliably fit on a short pre-period).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Treated-Costco inclusion rule.</b> A Costco fuel station is "
        "treated as a synthetic-control unit if and only if its registry "
        "history contains both <b>at least 24 pre-treatment months</b> "
        "and <b>at least 12 post-treatment months</b> in the relevant "
        "state's price registry. Four of Australia's ten Costco fuel "
        "stations satisfy both conditions (Coomera, Casuarina, Perth "
        "Airport, Lake Macquarie); six do not, and appear as descriptive "
        "context in Section&nbsp;1's coverage table. Exclusion reasons: "
        "Marsden Park (11 pre-months), Auburn (8 post-months), Canberra "
        "Airport (no pre; ACT joined NSW FuelCheck after this Costco "
        "opened), Casula and North Lakes (&le;4 pre-months each; the "
        "Costco predates the relevant registry), Ipswich (3 pre-months, "
        "predates the QLD scheme).",
        body_style,
    ))

    # Threshold table with robustness commitments
    story.append(Paragraph(
        "<b>Table 1.</b> Threshold-and-defense summary.", subsection_style))
    t1 = _table([
        [Paragraph("<b>Threshold</b>", cell_small),
         Paragraph("<b>Value</b>", cell_small),
         Paragraph("<b>Justification</b>", cell_small),
         Paragraph("<b>Robustness check (Section 3)</b>", cell_small)],
        [Paragraph("Treated radius", cell_small),
         Paragraph("&le;5 km", cell_small),
         Paragraph("Conservative end of IO-literature retail "
                   "fuel-price spillover range (1&ndash;5 mi)", cell_small),
         Paragraph("Re-run at 3 km and 8 km", cell_small)],
        [Paragraph("Donor buffer", cell_small),
         Paragraph("&gt;20 km", cell_small),
         Paragraph("4&times; the treated radius; keeps donors fully "
                   "outside any Costco's competitive zone", cell_small),
         Paragraph("Re-run at 15 km and 30 km", cell_small)],
        [Paragraph("Donor stations / month", cell_small),
         Paragraph("&ge;3", cell_small),
         Paragraph("Below 3, monthly mean has high sampling variance",
                   cell_small),
         Paragraph("Re-run at &ge;2 and &ge;5", cell_small)],
        [Paragraph("Donor coverage", cell_small),
         Paragraph("&ge;24 months", cell_small),
         Paragraph("Minimum pre-period length for stable SC weight fitting",
                   cell_small),
         Paragraph("Re-run at &ge;36 months", cell_small)],
        [Paragraph("Costco pre-period", cell_small),
         Paragraph("&ge;24 months", cell_small),
         Paragraph("Same logic, applied to treated", cell_small),
         Paragraph("Not relaxed (would re-introduce excluded Costcos that "
                   "fail the rule)", cell_small)],
        [Paragraph("Costco post-period", cell_small),
         Paragraph("&ge;12 months", cell_small),
         Paragraph("Minimum to estimate a sustained-effect gap",
                   cell_small),
         Paragraph("Not relaxed", cell_small)],
        [Paragraph("Plausible price range", cell_small),
         Paragraph("50&ndash;500 &cent;/L", cell_small),
         Paragraph("Sentinel-value floor and ceiling; AU retail unleaded "
                   "lives in 80&ndash;280", cell_small),
         Paragraph("None; not an analytic threshold", cell_small)],
    ], col_widths=[1.4 * inch, 0.8 * inch, 2.5 * inch, 1.95 * inch])
    story.append(t1)
    story.append(Spacer(1, 4))

    # ---- (c) Dependent variable integrity ----
    story.append(Paragraph(
        "(c) Dependent variable integrity", section_style))
    story.append(Paragraph(
        "<b>Construction.</b> The dependent variable is the monthly mean "
        "unleaded retail price (cents per litre) at the treated 5 km ring "
        "or the donor postcode; see (e) for the two-stage construction. "
        "Section 1's Figure 1 shows the post-aggregation "
        "distribution (n = 17,953 postcode-months, range 92&ndash;259 "
        "&cent;/L, approximately bimodal across the pre-2022 / post-2022 "
        "price-regime divide).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Sentinel-value filter.</b> Individual price quotes outside "
        "50&ndash;500 &cent;/L are dropped before aggregation. This is a "
        "data-integrity filter, not winsorisation: it removes obvious "
        "registry artifacts (out-of-stock placeholder values like "
        "<font face='Courier'>9999</font> or <font face='Courier'>0.01</font>) "
        "rather than legitimate tail observations. Australian retail "
        "unleaded post-2018 has averaged 130&ndash;220 &cent;/L; "
        "anything outside 50&ndash;500 is mechanical, not market.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Missing months.</b> A postcode-month or treated ring-month "
        "with zero contributing station observations is left as missing "
        "(<font face='Courier'>NaN</font>), never imputed as zero, never "
        "carried forward. Synthetic-control fitting handles missing months "
        "by ignoring them in the pre-period objective; Section 1 reported "
        "that the largest run of missing months in any treated panel is "
        "three (Lake Macquarie), which is not material.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>No winsorisation in the main specification.</b> Two-stage "
        "monthly aggregation smooths individual-quote outliers: an "
        "extreme single quote at one station gets averaged with the "
        "rest of that station's month, and then with the rest of the "
        "ring or postcode. If a robustness check exposes a donor-postcode "
        "month driving an estimate, we winsorise the analysis panel at "
        "the 99th percentile and report both specifications side-by-side.",
        body_style,
    ))

    # ---- (d) Independent variable integrity ----
    story.append(Paragraph(
        "(d) Independent variable integrity", section_style))
    story.append(Paragraph(
        "<b>Treatment indicator.</b> A binary post-opening flag is "
        "constructed per treated Costco by merging the hand-collected "
        "treatment-date table onto the (Costco &times; month) panel: 1 "
        "from the treatment month forward, 0 before.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Treatment-date validation.</b> Registry first-appearance can "
        "lag the true fuel-station opening if a station begins selling "
        "fuel before appearing in the state's reporting feed. Each of "
        "the four treated Costcos' registry-first-appearance dates was "
        "cross-checked against Costco Australia corporate announcements, "
        "trade press, and news coverage. The corroborating source must "
        "specifically reference the <i>fuel station</i> rather than the "
        "warehouse; warehouse opening dates are not used because fuel "
        "stations and warehouses at Costco Australia regularly open "
        "weeks apart. If a fuel-station-specific announced opening date "
        "differs from registry first-appearance by more than 30 days, "
        "the announced date supersedes.",
        body_style,
    ))
    # Validation results table
    val_table = _table([
        [Paragraph("<b>Costco</b>", cell_small),
         Paragraph("<b>Registry first-appearance</b>", cell_small),
         Paragraph("<b>Fuel-station-specific corroboration</b>", cell_small),
         Paragraph("<b>&Delta;</b>", cell_small),
         Paragraph("<b>Treatment date used</b>", cell_small)],
        [Paragraph("Coomera", cell_small),
         Paragraph("23 May 2023", cell_small),
         Paragraph("23 May 2023 (Retail World; explicit fuel-station "
                   "opening)", cell_small),
         Paragraph("0 d", cell_small),
         Paragraph("23 May 2023 (registry)", cell_small)],
        [Paragraph("Casuarina", cell_small),
         Paragraph("11 Nov 2022", cell_small),
         Paragraph("None; trade press only reports the warehouse "
                   "opening (7 Dec 2022)", cell_small),
         Paragraph("n/a", cell_small),
         Paragraph("11 Nov 2022 (registry)", cell_small)],
        [Paragraph("Perth Airport", cell_small),
         Paragraph("11 Apr 2020", cell_small),
         Paragraph("19 Feb 2020 (ACAPMAg: petrol station selling at "
                   "$1.18/L; warehouse opens 19 Mar 2020)", cell_small),
         Paragraph("&minus;52 d", cell_small),
         Paragraph("<b>19 Feb 2020 (announced)</b>", cell_small)],
        [Paragraph("Lake Macquarie", cell_small),
         Paragraph("2 May 2022", cell_small),
         Paragraph("None; no fuel-station-specific opening date in "
                   "public sources", cell_small),
         Paragraph("n/a", cell_small),
         Paragraph("2 May 2022 (registry)", cell_small)],
    ], col_widths=[1.0 * inch, 1.1 * inch, 2.5 * inch, 0.5 * inch,
                   1.55 * inch])
    story.append(val_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Three of the four registry first-appearance dates either match "
        "the gas-station-specific corroborated date exactly (Coomera) or "
        "lack any gas-station-specific external date for comparison "
        "(Casuarina, Lake Macquarie); these retain the registry date. "
        "Perth Airport is the only revision: the ACAPMAg report explicitly "
        "distinguishes the petrol station (open 19 Feb 2020, with bowser "
        "price quoted) from the warehouse (opening one month later on 19 "
        "March 2020), placing the fuel-station opening 52 days before the "
        "first FuelWatch record.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Station coordinates and distance-to-Costco.</b> Distance is "
        "computed as the great-circle distance from each "
        "station's coordinates to the nearest Costco fuel station's "
        "coordinates. NSW and WA historical registry files do not carry "
        "lat/lng, so coordinates are joined from one-time pulls of the "
        "live FuelCheck and FuelWatch APIs by (normalized name, "
        "postcode); QLD's historical files include coordinates inline. "
        "Stations that fail the coordinate join are dropped from analysis "
        "(they cannot be classified into a 5 km ring or a donor postcode "
        "without a known location); the per-registry join failure rate is "
        "reported in (f).",
        body_style,
    ))

    # ---- (e) Aggregation ----
    story.append(Paragraph("(e) Aggregation", section_style))
    story.append(Paragraph(
        "<b>Why monthly.</b> Three considerations point at month as the "
        "right level of aggregation. First, NSW and QLD are event-based "
        "registries (rows are price-change events) while WA is a "
        "daily-snapshot registry; month is the lowest common frequency "
        "at which all three speak the same language without having to "
        "invent &lsquo;daily&rsquo; observations for the event-based "
        "feeds. Second, the research question is about sustained "
        "competitive response to Costco entry, which plays out over "
        "weeks-to-months rather than days, so daily resolution would "
        "add noise without identification. Third, monthly means across "
        "multiple stations in a ring or postcode smooth single-quote "
        "outliers without requiring any winsorisation step.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Two-stage aggregation.</b> Within each station &times; month, "
        "we compute a single mean unleaded price across all of that "
        "station's price observations in the month. We then take a "
        "simple (unweighted) mean across stations to produce the "
        "(ring &times; month) treated panel and the (postcode &times; "
        "month) donor panel. The two-stage structure prevents stations "
        "that change prices more often (and therefore appear more times "
        "in the event-based NSW/QLD feeds) from contributing "
        "disproportionately to the cell mean.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Carry-forward step (NSW and QLD only).</b> For NSW and QLD, "
        "where rows are price-change events rather than daily snapshots, "
        "we construct each station's daily price series by carrying its "
        "last-observed price forward to subsequent days within the month "
        "until the next observed change. This is the standard approach "
        "for converting price-event data to a daily series and then to "
        "monthly means. WA's daily-snapshot data passes through unchanged.",
        body_style,
    ))

    # ---- (f) Data merging ----
    story.append(Paragraph("(f) Data merging", section_style))
    story.append(Paragraph(
        "Three sources are joined into a single analysis panel:",
        body_style,
    ))
    story.append(Paragraph(
        "&bull; <b>State registries</b> (NSW FuelCheck, QLD FPRS, WA "
        "FuelWatch) provide the price observations.",
        bullet_style,
    ))
    story.append(Paragraph(
        "&bull; <b>Live-API station snapshots</b> (NSW, WA) and inline "
        "coordinates (QLD) provide station latitude / longitude, joined "
        "to historical registry rows by (normalised station name, "
        "postcode).",
        bullet_style,
    ))
    story.append(Paragraph(
        "&bull; <b>The hand-collected Costco metadata</b> "
        "(<font face='Courier'>data/catalogs/usable_costcos.csv</font>) "
        "provides each Costco's lat/lng and treatment date, joined to "
        "treated panels by Costco name.",
        bullet_style,
    ))
    story.append(Paragraph(
        "<b>Expected losses in the merge.</b> Two sources of leakage. "
        "First, stations that closed, rebranded, or were re-numbered "
        "before the April 2026 live-API pull are absent from that "
        "snapshot, so historical rows that mention them fail the "
        "coordinate join. The snapshot misses <b>2,376 of 4,543 NSW "
        "historical stations (52.3%)</b> and <b>673 of 1,423 WA "
        "historical stations (47.3%)</b>; QLD is unaffected because its "
        "historical files carry coordinates inline. Row-level impact "
        "after the upstream fuel-type and sentinel-price filters is "
        "reported in (g). Second, station-name typos and mid-panel "
        "renames occasionally break the join. We address renames "
        "programmatically where we can (Section&nbsp;1 noted the May "
        "2022 NSW Costco &lsquo;Members only&rsquo; suffix; the build "
        "script strips it). The loss falls almost entirely on the donor "
        "pool (all four treated Costcos join cleanly), and 196 donor "
        "postcodes survive the downstream geographic and quality filters.",
        body_style,
    ))

    # ---- (g) Funnel: filters and transformations ----
    story.append(Paragraph(
        "(g) Filters and transformations: the funnel from raw to "
        "analysis-ready", section_style))
    story.append(Paragraph(
        "Counts are exact at every step. Row units in the upper block "
        "give way to (station&nbsp;&times;&nbsp;month) cells, "
        "(postcode&nbsp;&times;&nbsp;month) cells, postcode counts, and "
        "Costco counts as the panel is aggregated and filtered. Source: "
        "<font face='Courier'>scripts/synthetic_control_input/"
        "build_sc_inputs.py</font>.",
        body_style,
    ))

    # Funnel table
    story.append(Paragraph(
        "<b>Table 2.</b> Sample-construction funnel.", subsection_style))
    funnel = _table([
        [Paragraph("<b>Step</b>", cell_small),
         Paragraph("<b>NSW</b>", cell_small_right),
         Paragraph("<b>QLD</b>", cell_small_right),
         Paragraph("<b>WA</b>", cell_small_right),
         Paragraph("<b>Justification</b>", cell_small)],
        [Paragraph("Raw registry pull (rows)", cell_small),
         Paragraph("4,401,971", cell_small_right),
         Paragraph("4,970,650", cell_small_right),
         Paragraph("8,047,153", cell_small_right),
         Paragraph("Source data", cell_small)],
        [Paragraph("Filter to regular unleaded (rows)", cell_small),
         Paragraph("1,982,507", cell_small_right),
         Paragraph("997,680", cell_small_right),
         Paragraph("2,059,755", cell_small_right),
         Paragraph("Question is about retail unleaded competition; "
                   "premium/diesel are different markets",
                   cell_small)],
        [Paragraph("Drop sentinel prices (50&ndash;500 &cent;/L; rows)",
                   cell_small),
         Paragraph("1,982,506", cell_small_right),
         Paragraph("995,145", cell_small_right),
         Paragraph("2,059,755", cell_small_right),
         Paragraph("Removes out-of-stock placeholder values; nearly "
                   "nonbinding once the unleaded and date filters have run",
                   cell_small)],
        [Paragraph("Join station coordinates (rows)", cell_small),
         Paragraph("1,247,728", cell_small_right),
         Paragraph("995,145", cell_small_right),
         Paragraph("1,289,912", cell_small_right),
         Paragraph("Required for radius assignment; NSW/WA join from "
                   "live-API snapshots (per-registry failure rates in (f)); "
                   "QLD has inline coords",
                   cell_small)],
        [Paragraph("Aggregate to (station &times; month)", cell_small),
         Paragraph("156,864", cell_small_right),
         Paragraph("70,564", cell_small_right),
         Paragraph("68,332", cell_small_right),
         Paragraph("Carry-forward for NSW/QLD events; passthrough for WA "
                   "snapshots",
                   cell_small)],
        [Paragraph("Aggregate to (postcode &times; month)", cell_small),
         Paragraph("42,307", cell_small_right),
         Paragraph("18,186", cell_small_right),
         Paragraph("18,089", cell_small_right),
         Paragraph("Donor candidate panel (561 / 245 / 198 postcodes) "
                   "before geographic and quality filters",
                   cell_small)],
        [Paragraph("Drop postcodes &le;20 km from any Costco",
                   cell_small),
         Paragraph("&minus;231 pcds", cell_small_right),
         Paragraph("&minus;51 pcds", cell_small_right),
         Paragraph("&minus;80 pcds", cell_small_right),
         Paragraph("Donors must be unambiguously outside any Costco's "
                   "competitive footprint",
                   cell_small)],
        [Paragraph("Drop postcodes with &lt;3 stations / month avg",
                   cell_small),
         Paragraph("&minus;226 pcds", cell_small_right),
         Paragraph("&minus;138 pcds", cell_small_right),
         Paragraph("&minus;82 pcds", cell_small_right),
         Paragraph("Donor monthly mean too noisy below 3 stations",
                   cell_small)],
        [Paragraph("Drop postcodes with &lt;24 months observed",
                   cell_small),
         Paragraph("&minus;0 pcds", cell_small_right),
         Paragraph("&minus;0 pcds", cell_small_right),
         Paragraph("&minus;0 pcds", cell_small_right),
         Paragraph("Coverage was good; no postcode failed this gate",
                   cell_small)],
        [Paragraph("<b>Final donor pool</b>", cell_small),
         Paragraph("104 pcds", cell_small_right),
         Paragraph("56 pcds", cell_small_right),
         Paragraph("36 pcds", cell_small_right),
         Paragraph("196 postcodes &times; ~90 months = 17,578 "
                   "(postcode &times; month) cells",
                   cell_small)],
        [Paragraph("Costco eligibility (&ge;24 pre, &ge;12 post)",
                   cell_small),
         Paragraph("&minus;4 Costcos", cell_small_right),
         Paragraph("&minus;2 Costcos", cell_small_right),
         Paragraph("0", cell_small_right),
         Paragraph("Inclusion rule applied to all 10 Australian Costco "
                   "fuel stations (5 NSW, 3 QLD, 2 WA)",
                   cell_small)],
        [Paragraph("<b>Final treated panel</b>", cell_small),
         Paragraph("1 Costco", cell_small_right),
         Paragraph("1 Costco", cell_small_right),
         Paragraph("2 Costcos", cell_small_right),
         Paragraph("4 Costcos &times; (5 km ring) &times; ~80&ndash;100 "
                   "months = 375 (Costco &times; month) cells",
                   cell_small)],
    ], col_widths=[1.85 * inch, 0.95 * inch, 0.95 * inch, 0.85 * inch,
                   2.0 * inch])
    story.append(funnel)
    story.append(Spacer(1, 6))

    # ---- Closing line ----
    story.append(Paragraph(
        "The output is four files in <font face='Courier'>data/sc_inputs/"
        "</font>: <font face='Courier'>treated_units.csv</font> (375 "
        "Costco-month rows), <font face='Courier'>donor_pool.csv</font> "
        "(17,578 postcode-month rows), and two metadata files.",
        body_style,
    ))

    doc.build(story)
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
