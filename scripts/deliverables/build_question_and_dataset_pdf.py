"""
Build the Question and Dataset deliverable PDF for the Costco AU project.

Mirrors the format of main_group_project_question_and_dataset.pdf — the
academic-style layout with numbered sections, justified paragraphs, and a
clean field-table for the dataset description. Modelled on the spec's
synthetic-control example (food waste bans, page 7 of the spec).

Output: deliverables/question_and_dataset.pdf (in the worktree).
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTFILE = REPO_ROOT / "deliverables" / "question_and_dataset.pdf"


def main():
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTFILE),
        pagesize=letter,
        leftMargin=0.95 * inch,
        rightMargin=0.95 * inch,
        topMargin=0.95 * inch,
        bottomMargin=0.95 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=18,
        leading=22,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        leading=16,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=20,
        bulletIndent=8,
        spaceAfter=4,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=12,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Courier",
        fontSize=10,
    )

    story = []

    # ---- Title ----
    story.append(Paragraph("Question and Dataset", title_style))

    # ---- Section 1: Organization ----
    story.append(Paragraph("1. Organization", section_style))
    story.append(Paragraph(
        "<b>Australian Competition and Consumer Commission (ACCC)</b> &mdash; "
        "Australia&rsquo;s national competition and markets regulator. The "
        "ACCC publishes regular monitoring reports on retail fuel "
        "competition and has flagged ongoing concerns about market "
        "concentration and pricing dynamics in Australian fuel retailing. "
        "It has a standing interest in whether new entrants &mdash; "
        "particularly hypermarket-style discount entrants like Costco &mdash; "
        "meaningfully discipline incumbent pricing, since lowering entry "
        "barriers is one of the primary tools available to the ACCC for "
        "improving competition in concentrated markets.",
        body_style,
    ))

    # ---- Section 2: Research question ----
    story.append(Paragraph("2. Research question / classification", section_style))
    story.append(Paragraph(
        "<b>Does the entry of a Costco gas station into an Australian local "
        "market cause nearby competitor stations to lower their retail fuel "
        "prices?</b>",
        body_style,
    ))
    story.append(Paragraph(
        "This is a <b>causal</b> question. We will answer it using "
        "<b>synthetic control</b>, applied separately to each of four "
        "Costco openings with adequate pre- and post-treatment data. The "
        "synthetic control method &mdash; one of the four identification "
        "strategies described in the project specification &mdash; is "
        "explicitly recommended for &ldquo;a single treated unit or a "
        "handful of treated units, a clear treatment date, and a large "
        "donor pool of comparable untreated units with pre-treatment data,"
        "&rdquo; which describes our setup precisely. Difference-in-"
        "differences was considered first but its parallel-trends "
        "identifying assumption fails empirically in our data; synthetic "
        "control does not require parallel trends and is the methodologically "
        "appropriate choice.",
        body_style,
    ))

    # ---- Section 3: Dataset ----
    story.append(Paragraph("3. Dataset", section_style))
    story.append(Paragraph(
        "We combine three publicly accessible Australian state fuel-price "
        "registries into a unified station-month panel: <b>NSW FuelCheck</b> "
        "(maintained by the NSW Government, mandatory station reporting "
        "since August 2016, accessed via api.nsw.gov.au and "
        "data.nsw.gov.au), <b>Queensland Fuel Price Reporting Scheme</b> "
        "(QLD Treasury, mandatory reporting since December 2018, accessed "
        "via data.qld.gov.au), and <b>WA FuelWatch</b> (WA Government, "
        "daily mandatory reporting since January 2001, accessed via "
        "data.wa.gov.au).",
        body_style,
    ))
    story.append(Paragraph(
        "We pull historical snapshots from each registry covering January "
        "2018 through April 2026, yielding approximately <b>4.4 million "
        "station-day price records</b> across <b>~6,000 unique stations</b> "
        "in the three states. Each row in the raw data is a station &times; "
        "day &times; fuel-type price observation. We aggregate to monthly "
        "mean prices per station for the analysis. To this panel we merge a "
        "hand-collected list of Costco gas station opening dates, verified "
        "against each station&rsquo;s first-appearance date in the relevant "
        "registry. Key fields are listed below.",
        body_style,
    ))

    # Field table
    field_rows = [
        [Paragraph("<b>Field</b>", table_cell_style),
         Paragraph("<b>Description</b>", table_cell_style)],
        [Paragraph("state", table_cell_bold),
         Paragraph("State (NSW, QLD, or WA)", table_cell_style)],
        [Paragraph("station_id", table_cell_bold),
         Paragraph("Unique station identifier (state-scoped)", table_cell_style)],
        [Paragraph("name", table_cell_bold),
         Paragraph("Service station name", table_cell_style)],
        [Paragraph("brand", table_cell_bold),
         Paragraph("Brand affiliation (Costco, Caltex, Shell, BP, "
                   "independents, etc.)", table_cell_style)],
        [Paragraph("address", table_cell_bold),
         Paragraph("Street address", table_cell_style)],
        [Paragraph("latitude / longitude", table_cell_bold),
         Paragraph("Geographic coordinates (used to compute haversine "
                   "distance to Costco)", table_cell_style)],
        [Paragraph("postcode / suburb", table_cell_bold),
         Paragraph("Postcode and suburb &mdash; used to define donor "
                   "pool units", table_cell_style)],
        [Paragraph("date / year_month", table_cell_bold),
         Paragraph("Date of price observation; aggregated to month for "
                   "the panel", table_cell_style)],
        [Paragraph("fuel_type", table_cell_bold),
         Paragraph("Regular unleaded (ULP / U91 / E10), premium, or "
                   "diesel", table_cell_style)],
        [Paragraph("price", table_cell_bold),
         Paragraph("Retail price at the pump (cents per liter)",
                   table_cell_style)],
    ]
    field_table = Table(
        field_rows,
        colWidths=[1.7 * inch, 4.0 * inch],
        hAlign="LEFT",
    )
    field_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(Spacer(1, 4))
    story.append(field_table)
    story.append(Spacer(1, 6))

    # ---- Section 4: Key components ----
    story.append(Paragraph("4. Key components", section_style))

    story.append(Paragraph(
        "<b>Method.</b> Synthetic control, applied separately to each of "
        "four Costco openings. For each treated Costco we construct a "
        "synthetic counterfactual as a weighted combination of donor "
        "postcodes whose pre-treatment price trajectory matches the "
        "treated market&rsquo;s pre-treatment trajectory. The post-treatment "
        "gap between the actual treated market and the synthetic "
        "counterfactual is the estimated treatment effect.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Treatment.</b> The opening of a Costco gas station within a "
        "local market. Treatment switches on at the Costco station&rsquo;s "
        "first-observed date in the relevant state&rsquo;s price registry "
        "and remains on thereafter.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Treated units.</b> Four Costco markets, each defined as the "
        "monthly mean unleaded price across all non-Costco stations within "
        "5&nbsp;km of that Costco&rsquo;s coordinates:",
        body_style,
    ))
    treated_table = Table(
        [
            [Paragraph("<b>Costco</b>", table_cell_style),
             Paragraph("<b>State</b>", table_cell_style),
             Paragraph("<b>Treatment date</b>", table_cell_style),
             Paragraph("<b>Pre months</b>", table_cell_style),
             Paragraph("<b>Post months</b>", table_cell_style)],
            [Paragraph("Coomera", table_cell_style),
             Paragraph("QLD", table_cell_style),
             Paragraph("May 2023", table_cell_style),
             Paragraph("51", table_cell_style),
             Paragraph("31", table_cell_style)],
            [Paragraph("Casuarina", table_cell_style),
             Paragraph("WA", table_cell_style),
             Paragraph("November 2022", table_cell_style),
             Paragraph("58", table_cell_style),
             Paragraph("42", table_cell_style)],
            [Paragraph("Perth Airport", table_cell_style),
             Paragraph("WA", table_cell_style),
             Paragraph("April 2020", table_cell_style),
             Paragraph("27", table_cell_style),
             Paragraph("73", table_cell_style)],
            [Paragraph("Lake Macquarie", table_cell_style),
             Paragraph("NSW", table_cell_style),
             Paragraph("May 2022", table_cell_style),
             Paragraph("58", table_cell_style),
             Paragraph("35", table_cell_style)],
        ],
        colWidths=[1.4 * inch, 0.6 * inch, 1.3 * inch, 1.0 * inch, 1.0 * inch],
        hAlign="LEFT",
    )
    treated_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(Spacer(1, 4))
    story.append(treated_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Australia has six additional Costco fuel stations (Marsden Park, "
        "Auburn, Canberra Airport, Casula, North Lakes, and Ipswich), but "
        "these have insufficient pre- or post-treatment data for the "
        "method &mdash; either the warehouse opened before its "
        "state&rsquo;s registry began reporting (Casula, North Lakes, "
        "Ipswich), the postcode lacked any pre-period coverage (Canberra "
        "Airport), the post-treatment window is too short (Auburn, just "
        "opened August 2025), or the pre-period is too short for stable "
        "weight fitting (Marsden Park). These stations appear in the "
        "project as descriptive context but are excluded from the formal "
        "estimation.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Donor pool.</b> Each Australian postcode in the three states "
        "with at least 3 average unique stations per month, at least 24 "
        "months of observed coverage, and located more than 20&nbsp;km "
        "from <i>any</i> Costco fuel station (whether treated or excluded) "
        "becomes one donor unit, defined as the postcode&rsquo;s monthly "
        "mean unleaded price across all stations in that postcode. After "
        "applying these filters the donor pool contains <b>196 postcodes</b>: "
        "104 in NSW, 56 in QLD, and 36 in WA, yielding 17,578 (postcode "
        "&times; month) panel observations. For each Costco&rsquo;s "
        "synthetic-control fit, donors are restricted to the same state to "
        "share state-level shocks (such as the March&ndash;September 2022 "
        "national fuel-excise cut, which we have verified to be a symmetric "
        "common shock).",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Outcome.</b> Monthly mean unleaded retail price (regular ULP / "
        "U91 / E10) at the treated market or synthetic-counterfactual "
        "market, in cents per liter.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Identifying assumption.</b> The synthetic version of each "
        "Costco&rsquo;s local market &mdash; constructed as a weighted "
        "combination of donor postcodes that closely matches the treated "
        "market&rsquo;s pre-treatment price trajectory &mdash; would have "
        "continued to track the treated market&rsquo;s outcome in the "
        "absence of Costco entry. We assess this assumption visually via "
        "pre-treatment fit plots and statistically via placebo synthetic "
        "controls run on every donor postcode in turn; the treatment effect "
        "is credible if its post-treatment magnitude exceeds the placebo "
        "distribution.",
        body_style,
    ))

    doc.build(story)
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
