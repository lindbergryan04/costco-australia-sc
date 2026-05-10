"""Build Section 3 of the Plan of Attack deliverable PDF.

Section 3 is the Analysis Plan: research design, key analyses (with
illustrative figures of what the synthetic-control output will look
like), and the robustness-check menu. Stylistically modelled on the
existing Section 1 and Section 2 PDFs.

Output: deliverables/plan_of_attack_section_3.pdf (in the worktree).
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    KeepTogether, PageBreak,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTFILE = REPO_ROOT / "deliverables" / "plan_of_attack_section_3.pdf"
PLOTS = REPO_ROOT / "section_3" / "plots"


def _table(rows, col_widths, header=True):
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
    cell_small = ParagraphStyle(
        "CellSmall", parent=cell_style, fontSize=9, leading=11,
    )
    cell_small_right = ParagraphStyle(
        "CellSmallRight", parent=cell_small, alignment=2,
    )
    caption_style = ParagraphStyle(
        "Caption", parent=styles["Normal"], fontName="Times-Italic",
        fontSize=9.5, alignment=TA_CENTER, leading=12,
        spaceBefore=4, spaceAfter=10,
    )

    story = []

    # ---- Title block ----
    story.append(Paragraph(
        "Plan of Attack: Section 3, Analysis Plan", title_style))
    story.append(Spacer(1, 14))

    # ---- (a) Research design ----
    story.append(Paragraph("(a) Research design", section_style))

    story.append(Paragraph(
        "<b>Question type.</b> Causal. The identification strategy is "
        "<b>synthetic control</b>, fit separately for each of the four "
        "treated Costcos.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Why synthetic control over difference-in-differences.</b> "
        "The data has four treated Costcos and 196 candidate donor postcodes. "
        "Four treated units is too few to support a credible "
        "treated-versus-control mean comparison: a single anomalous "
        "Costco (e.g. Casuarina, with only ~3 contributing stations) "
        "would dominate the average. Synthetic control instead builds a "
        "weighted counterfactual for each treated unit individually, "
        "which is exactly the design the n=4 case calls for.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Source of variation.</b> Costco fuel-station entry into a "
        "local market isn't driven by what's happening to local fuel "
        "prices. Site selection is driven by Costco warehouse "
        "logistics, land availability, and Costco's national rollout "
        "schedule, none of which respond to the local fuel-price "
        "trajectory at the chosen site. The variation we exploit is the "
        "staggered timing of the four openings (Feb 2020, May 2022, Nov "
        "2022, May 2023) across three states.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Identifying assumptions.</b> Each assumption is paired with "
        "the figure or check that defends it.",
        body_style,
    ))
    story.append(Paragraph(
        "&bull; <b>Pre-period fit captures unobserved time-varying "
        "confounders.</b> Verified visually in Figure 1 (pre-period overlap "
        "between treated and synthetic), quantified in Table 2 "
        "(pre-period tracking error per Costco), and tested by the 12-month holdout "
        "in Robustness Check 5.",
        bullet_style,
    ))
    story.append(Paragraph(
        "&bull; <b>Donors stay clean.</b> No donor postcode is partly "
        "affected by a Costco that isn't the one we're studying. Defended "
        "by the 20 km donor buffer (4&times; the treated radius), "
        "pre-committed in Section 2(b), and explicitly tested by "
        "Robustness Check 7 (spatial placebo on the 5&ndash;20 km donut).",
        bullet_style,
    ))
    story.append(Paragraph(
        "&bull; <b>No anticipation.</b> Competitor stations do not "
        "preemptively cut prices ahead of Costco's announced opening. "
        "Tested by Robustness Check 1 (placebo in time, &minus;12 months).",
        bullet_style,
    ))
    story.append(Paragraph(
        "&bull; <b>Range coverage.</b> The treated ring's pre-period "
        "price level can be expressed as a weighted average of donor "
        "postcodes. Verified by the donor-weight bars in Figure 2 "
        "(no negative weights, no extreme single-donor concentration).",
        bullet_style,
    ))

    story.append(Paragraph(
        "<b>What the weights do.</b> One synthetic-control fit per "
        "treated Costco. For each Costco, the donor pool is restricted "
        "to <i>same-state</i> postcodes only (NSW: 104, QLD: 56, WA: 36, "
        "from <font face='Courier'>data/sc_inputs/donor_pool.csv</font>) "
        "so the synthetic absorbs state-specific shocks "
        "(state excise rates, regional refining capacity, intra-state "
        "shipping costs) by construction. Weights are chosen to minimise "
        "the average gap between the treated 5 km ring's monthly mean "
        "unleaded price and the weighted donor mean across the "
        "pre-period.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Method commitment.</b> Standard synthetic-control method "
        "via the <font face='Courier'>pysyncon.Synth</font> library. Predictors: the outcome series (monthly mean "
        "unleaded price) only. We have no postcode-level "
        "demographic panel that would justify auxiliary covariates. "
        "Pre-period objective: minimise the average gap between treated "
        "and synthetic on monthly mean unleaded price. "
        "Inference: estimate uncertainty by treating each donor "
        "postcode as a fake treated unit and measuring the resulting "
        "fake effect (Robustness Check 6); summarised as the post/pre "
        "tracking-error ratio and as a 95% CI on the post-treatment gap.",
        body_style,
    ))

    # ---- (b) Key analyses ----
    story.append(Paragraph("(b) Key analyses", section_style))
    story.append(Paragraph(
        "Three figures plus two supporting tables. The figures carry the "
        "argument; the tables quantify what the figures show. Figures in "
        "this document are <b>illustrative</b>: they show what we "
        "expect each output to look like once the synthetic-control fits "
        "are run, not a pre-committed result.",
        body_style,
    ))

    # Analysis 1 / Figure 1
    story.append(Paragraph(
        "Analysis 1 (Figure 1): synthetic-control trajectories",
        subsection_style,
    ))
    story.append(Paragraph(
        "<b>Test.</b> The headline result. Pre-period overlap between "
        "treated and synthetic measures fit quality; the post-period gap "
        "is the estimated treatment effect.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Plot.</b> 2&times;2 panel, one per treated Costco (Coomera, "
        "Casuarina, Perth Airport, Lake Macquarie). X-axis: month, "
        "from each Costco's pre-period start through the relevant "
        "state's registry end (December 2025 for QLD, January 2026 for "
        "NSW, April 2026 for WA). Y-axis: monthly mean unleaded price "
        "(&cent;/L). Two lines per panel: "
        "solid coloured = treated 5 km ring (actual), dashed black = "
        "synthetic counterfactual. Vertical dotted red line at the "
        "validated treatment date (Section 2(d)). Shaded grey 95% CI "
        "band on the synthetic from donor-permutation inference "
        "(Robustness Check 6).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>AI-executable instructions.</b> Read <font face='Courier'>"
        "data/sc_inputs/treated_units.csv</font> and "
        "<font face='Courier'>donor_pool.csv</font>. For each treated "
        "Costco, filter donors to same state, pivot both to wide format "
        "(rows&nbsp;= month, columns&nbsp;= unit), and fit "
        "<font face='Courier'>pysyncon.Synth</font> on pre-period only "
        "(months strictly before the treatment date). Project the "
        "synthetic across the full panel. Build the 95% CI by re-fitting "
        "synthetic-control on each donor as a placebo and taking the "
        "empirical 2.5&ndash;97.5 percentile of donor-side gaps at each "
        "post-treatment month. Render to <font face='Courier'>"
        "section_3/plots/01_sc_trajectories.png</font>.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Why this analysis.</b> A reader who only sees Figure 1 "
        "should be able to read off the project's conclusion: did "
        "competitor prices fall after Costco entry, and by how much. "
        "It is the canonical synthetic-control visualisation.",
        body_style,
    ))
    img1 = Image(str(PLOTS / "01_sc_trajectories_illustrative.png"),
                 width=6.4 * inch, height=4.45 * inch)
    story.append(KeepTogether([img1, Paragraph(
        "Illustrative Figure 1 (hypothetical data). Solid coloured = "
        "treated 5 km ring; dashed black = synthetic counterfactual; "
        "vertical dotted red = validated Costco opening date; shaded "
        "grey = 95% donor-permutation CI on the synthetic. The "
        "illustrative gap of ~4 &cent;/L emerges within a few months of "
        "treatment and persists; the actual fits will reveal whether and "
        "by how much the real data exhibits this pattern.",
        caption_style,
    )]))

    # Analysis 2 / Figure 2
    story.append(Paragraph(
        "Analysis 2 (Figure 2): donor weights per treated Costco",
        subsection_style,
    ))
    story.append(Paragraph(
        "<b>Test.</b> Transparency about which donors drive each "
        "counterfactual; common-support assumption.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Plot.</b> 2&times;2 panel of horizontal bar charts, one per "
        "treated Costco. One bar per donor postcode with weight &gt; 0.01, "
        "sorted descending, annotated with postcode and suburb (suburb "
        "joined from <font face='Courier'>donor_metadata.csv</font>).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>AI-executable instructions.</b> Extract the weight vector "
        "from each fitted SC model in Analysis 1. Filter to weights "
        "&gt;&nbsp;0.01. Sort descending. Render to <font face='Courier'>"
        "section_3/plots/02_donor_weights.png</font>.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Why this analysis.</b> A counterfactual leaning on one or "
        "two donors is fragile; one drawn from a balanced mix of "
        "geographically sensible donors is credible. The per-Costco "
        "panels also let the reader sanity-check geographic plausibility. "
        "Coomera should lean on Gold Coast and Brisbane "
        "postcodes, not far-North Queensland; Lake Macquarie should "
        "lean on Newcastle and the Central Coast. This figure also flags "
        "any common-support concerns.",
        body_style,
    ))
    img2 = Image(str(PLOTS / "02_donor_weights_illustrative.png"),
                 width=6.4 * inch, height=4.15 * inch)
    story.append(KeepTogether([img2, Paragraph(
        "Illustrative Figure 2 (hypothetical data). Synthetic-control "
        "weights for the top donor postcodes per treated Costco, sorted "
        "descending. The illustrative weight distributions are "
        "deliberately spread across 6&ndash;7 donors with no single "
        "donor exceeding 0.40, reflecting a credible synthetic; weights "
        "concentrated in 1&ndash;2 donors would be a flag for a fragile "
        "counterfactual.",
        caption_style,
    )]))

    # Analysis 3 / Figure 3
    story.append(Paragraph(
        "Analysis 3 (Figure 3): aggregate event study",
        subsection_style,
    ))
    story.append(Paragraph(
        "<b>Test.</b> The dynamic profile of the effect. Do competitors "
        "respond immediately, with delay, persistently, or with a fading "
        "effect?",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Plot.</b> Single-panel line plot. X-axis: months relative to "
        "Costco opening, &minus;24 to +24. Y-axis: mean (actual&nbsp;&minus;"
        "&nbsp;synthetic) gap in &cent;/L, averaged across the four "
        "treated Costcos. Shaded grey 95% CI band from cross-Costco "
        "standard error. Vertical dotted red line at month 0 (treatment).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>AI-executable instructions.</b> Take per-Costco gap series "
        "(actual&nbsp;&minus;&nbsp;synthetic) from Analysis 1. Re-index "
        "each to relative-month-since-treatment. At each relative month "
        "in [&minus;24, +24], average the four Costco gaps and compute "
        "the cross-Costco SE for the band. Render to <font face='Courier'>"
        "section_3/plots/03_event_study_aggregate.png</font>.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Why this analysis.</b> The 2&times;2 panel in Figure 1 shows "
        "the per-Costco answer but obscures the aggregate dynamic. "
        "Figure 3 turns &lsquo;Costco lowered prices on average&rsquo; "
        "into &lsquo;Costco lowered prices by X &cent;/L within Y "
        "months and the effect persisted for Z&rsquo;, much "
        "closer to a managerial answer. The &minus;24 to +24 window is "
        "the largest range over which all four Costcos contribute "
        "(limited by Coomera's 31 post-months and Perth Airport's 26 "
        "pre-months).",
        body_style,
    ))
    img3 = Image(str(PLOTS / "03_event_study_aggregate_illustrative.png"),
                 width=6.4 * inch, height=3.2 * inch)
    story.append(KeepTogether([img3, Paragraph(
        "Illustrative Figure 3 (hypothetical data). Mean gap (actual "
        "&minus; synthetic) by month relative to Costco opening, averaged "
        "across the four treated Costcos. The illustrative profile shows "
        "a pre-period gap fluctuating around zero (the identifying "
        "assumption that synthetic tracks treated absent the intervention) "
        "and a post-period gap that opens smoothly over ~4 months and "
        "stabilises near &minus;4 &cent;/L. The actual event study will "
        "reveal whether the real effect is immediate, delayed, persistent, "
        "or fading.",
        caption_style,
    )]))

    # Analysis 4 — supporting tables
    story.append(Paragraph(
        "Analysis 4: supporting tables",
        subsection_style,
    ))
    story.append(Paragraph(
        "Two tables that quantify what Figures 1 and 3 show. Both are "
        "computed alongside Analysis 1 from the fitted SC models and the "
        "permutation distribution.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Table 1.</b> Per-Costco effect-size summary.",
        subsection_style,
    ))
    t1 = _table([
        [Paragraph("<b>Costco</b>", cell_small),
         Paragraph("<b>Pre-period mean (&cent;/L)</b>", cell_small_right),
         Paragraph("<b>Mean post-treatment gap (&cent;/L)</b>",
                   cell_small_right),
         Paragraph("<b>% reduction</b>", cell_small_right),
         Paragraph("<b>Post/pre tracking-error ratio</b>", cell_small_right),
         Paragraph("<b>95% CI on gap</b>", cell_small_right),
         Paragraph("<b>Post months</b>", cell_small_right)],
        [Paragraph("Coomera",        cell_small),
         Paragraph("&mdash;",        cell_small_right)] * 1
        + [Paragraph("&mdash;", cell_small_right)] * 5,
        [Paragraph("Casuarina",      cell_small)] +
        [Paragraph("&mdash;", cell_small_right)] * 6,
        [Paragraph("Perth Airport",  cell_small)] +
        [Paragraph("&mdash;", cell_small_right)] * 6,
        [Paragraph("Lake Macquarie", cell_small)] +
        [Paragraph("&mdash;", cell_small_right)] * 6,
    ], col_widths=[1.1 * inch, 0.85 * inch, 0.95 * inch, 0.7 * inch,
                   0.85 * inch, 0.85 * inch, 0.7 * inch])
    story.append(t1)
    story.append(Paragraph(
        "<i>Table values populate from the fitted SC models. The post/pre "
        "tracking-error ratio compares how far the synthetic strays from "
        "actual after Costco entry to how closely it tracked before. A "
        "ratio of 4&ndash;5 or higher is the standard threshold for "
        "evidence of a treatment effect.</i>",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Table 2.</b> Pre-period fit quality.",
        subsection_style,
    ))
    t2 = _table([
        [Paragraph("<b>Costco</b>", cell_small),
         Paragraph("<b>Pre months</b>", cell_small_right),
         Paragraph("<b>Pre tracking error (&cent;/L)</b>", cell_small_right),
         Paragraph("<b>Tracking error as % of pre mean</b>", cell_small_right),
         Paragraph("<b>Top-3 donor weight share</b>", cell_small_right)],
        [Paragraph("Coomera",        cell_small),
         Paragraph("51", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right)],
        [Paragraph("Casuarina",      cell_small),
         Paragraph("58", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right)],
        [Paragraph("Perth Airport",  cell_small),
         Paragraph("26", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right)],
        [Paragraph("Lake Macquarie", cell_small),
         Paragraph("58", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right),
         Paragraph("&mdash;", cell_small_right)],
    ], col_widths=[1.4 * inch, 0.9 * inch, 1.1 * inch, 1.4 * inch,
                   1.6 * inch])
    story.append(t2)
    story.append(Paragraph(
        "<i>Table values populate from the fitted SC models. Lets the "
        "reader judge per-unit identification credibility at a glance. "
        "Casuarina's pre-period tracking error is expected to be visibly worse than "
        "Perth Airport's because the 5 km Casuarina ring contains only "
        "~3 contributing stations on average (Section 1's documented "
        "limitation); surfacing it transparently here is part of "
        "presenting that limitation rather than hiding it.</i>",
        body_style,
    ))

    # ---- (c) Robustness checks ----
    story.append(Paragraph(
        "(c) Robustness checks (extra credit)", section_style))
    story.append(Paragraph(
        "The biggest sources of fragility in the headline analysis are "
        "(i) the 5 km / 20 km geographic geometry, (ii) the COVID period "
        "coinciding with Perth Airport's opening, (iii) the noise in "
        "Casuarina's sparse 5 km ring, (iv) the standard "
        "synthetic-control concern that pre-period fit can be gamed by "
        "over-flexible donor selection, and (v) the lack of formal "
        "uncertainty quantification on a four-Costco point estimate. "
        "The seven checks below directly probe these concerns.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Table 3.</b> Robustness check menu.",
        subsection_style,
    ))
    t3 = _table([
        [Paragraph("<b>#</b>", cell_small),
         Paragraph("<b>Check</b>", cell_small),
         Paragraph("<b>Concern it tests</b>", cell_small),
         Paragraph("<b>Pass criterion</b>", cell_small)],
        [Paragraph("1", cell_small),
         Paragraph("Placebo in time (&minus;12 months)", cell_small),
         Paragraph("No-anticipation assumption", cell_small),
         Paragraph("Placebo gap near zero, within donor-side 95% CI",
                   cell_small)],
        [Paragraph("2", cell_small),
         Paragraph("Alternative radii (3 / 8 km treated; 15 / 30 km donor)",
                   cell_small),
         Paragraph("Geographic geometry choice", cell_small),
         Paragraph("Effect sign and approximate magnitude survive",
                   cell_small)],
        [Paragraph("3", cell_small),
         Paragraph("Casuarina at 10 km treated radius", cell_small),
         Paragraph("Sparse-ring noise (~3 stations at 5 km)", cell_small),
         Paragraph("10 km gap comparable in sign and magnitude to 5 km",
                   cell_small)],
        [Paragraph("4", cell_small),
         Paragraph("Perth Airport with March&ndash;December 2020 dropped",
                   cell_small),
         Paragraph("COVID demand collapse contaminates early post-period",
                   cell_small),
         Paragraph("Post-COVID gap comparable to full-window gap",
                   cell_small)],
        [Paragraph("5", cell_small),
         Paragraph("LOOCV donor selection + 12-month holdout", cell_small),
         Paragraph("Donor-selection overfitting", cell_small),
         Paragraph("Holdout tracking error comparable to in-sample training error",
                   cell_small)],
        [Paragraph("6", cell_small),
         Paragraph("95% CIs via permutation inference", cell_small),
         Paragraph("Statistical uncertainty on the gap", cell_small),
         Paragraph("CI excludes zero for high-coverage Costcos",
                   cell_small)],
        [Paragraph("7", cell_small),
         Paragraph("Spatial placebo: 5&ndash;20 km donut as faux donors",
                   cell_small),
         Paragraph("Donor purity / extent of Costco's spatial footprint",
                   cell_small),
         Paragraph("Either result informative (see paragraph below)",
                   cell_small)],
    ], col_widths=[0.3 * inch, 1.85 * inch, 1.95 * inch, 2.1 * inch])
    story.append(t3)
    story.append(Spacer(1, 4))

    # Per-check paragraphs
    story.append(Paragraph(
        "<b>Check 1: placebo in time.</b> For each treated Costco, "
        "backdate treatment by 12 months. Re-fit synthetic control on "
        "data up to the placebo date; project forward; compute the "
        "placebo gap. Drop all real-treatment-and-after months from the "
        "placebo fit so no real post-treatment data contaminates the "
        "placebo window. <i>Concern:</i> if a &lsquo;ban-style "
        "effect&rsquo; appears in the placebo window before Costco "
        "actually opens, the post-treatment gap reflects pre-existing "
        "trends or anticipation, not Costco entry.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Check 2: alternative radii.</b> Re-build synthetic-control "
        "inputs at (3 km treated, 15 km donor) and (8 km treated, 30 km "
        "donor). Re-fit Analysis 1 for each Costco at each geometry. "
        "Report the resulting gaps in a sensitivity table. <i>Concern:</i> "
        "the 5 km / 20 km baseline geometry is defensible (see "
        "Section 2(b)) but discretionary; a result "
        "that exists at 5 km but vanishes at 3 km or 8 km would be "
        "fragile. This is the project's most important sensitivity test "
        "because the radius geometry <i>is</i> the design.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Check 3: Casuarina at 10 km.</b> Casuarina's 5 km ring "
        "contains only ~3 contributing stations on average, the "
        "documented limitation in Section 1. A wider ring captures more "
        "signal at the cost of including some less-exposed stations. "
        "Re-fit Casuarina specifically at a 10 km treated radius "
        "(donor buffer remains 20 km). Compare gap and pre-period tracking error "
        "to the 5 km baseline. <i>Concern:</i> the headline Casuarina "
        "estimate may be driven by individual-station noise rather than "
        "competitive response.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Check 4: Perth Airport with COVID-period removal.</b> Perth "
        "Airport opens approximately four weeks before Australia's "
        "COVID demand collapse begins. Early post-treatment months are "
        "dominated by pandemic-driven price movements rather than "
        "competitive response. Re-fit Perth Airport with March&ndash;"
        "December 2020 dropped from both treated and donor panels. "
        "<i>Concern:</i> COVID compression of fuel prices may suppress "
        "the actual&nbsp;&minus;&nbsp;synthetic gap; the corrected "
        "estimate may be larger in magnitude than the full-window gap.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Check 5: LOOCV donor selection with 12-month holdout.</b> "
        "Pre-period fit can be gamed by greedy donor selection "
        "(cherry-picking donors that fit the pre-period without "
        "generalising). The check has four steps. (1) Split each "
        "Costco's pre-treatment period into a <i>training window</i> "
        "(all pre-months except the last 12) and a <i>12-month "
        "holdout</i>. The holdout is 12 months rather than 24 because "
        "Perth Airport has only 26 pre-months; a 24-month holdout would "
        "leave too few training months to fit weights. (2) For each "
        "candidate N donors &isin; {5, 10, 20, 50, full}: leave-one-out "
        "cross-validation within the training window. Hold out "
        "one training month at a time, refit weights on the rest, score "
        "tracking error at the held-out month; pick the N that "
        "minimises mean LOOCV error. (3) Refit the synthetic with the "
        "chosen N on the full training window. (4) <i>Without looking "
        "at any post-treatment data</i>, check whether the synthetic "
        "continues to track the treated series across the untouched "
        "12-month holdout. <i>Concern:</i> over-flexible donor selection "
        "can produce a tight pre-period fit that does not generalise; "
        "the holdout is the honest proof that the synthetic was not "
        "memorising the training series.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Check 6: 95% CIs via permutation inference.</b> Standard "
        "synthetic-control permutation. For each donor "
        "postcode, treat it as a &lsquo;placebo treated&rsquo; and fit "
        "synthetic control using the remaining donors. Compute the "
        "placebo gap series. Across all donor placebos, take the "
        "empirical 2.5&ndash;97.5 percentile of post-treatment gaps to "
        "construct a 95% CI on the real treatment effect. Reported on "
        "Figure 1 as a shaded band and in Table 1 as a column. "
        "<i>Concern:</i> point estimates without uncertainty bands can "
        "make a modest effect look airtight. For Casuarina specifically, "
        "a CI that includes zero will be reported transparently as the "
        "documented limitation, consistent with Section 1's noted noise "
        "issue.",
        body_style,
    ))

    story.append(Paragraph(
        "<b>Check 7: spatial placebo (5&ndash;20 km donut as "
        "faux donors).</b> The 20 km donor buffer is meant to keep "
        "donors fully outside any Costco's competitive zone, but this "
        "assumption is never verified in the main "
        "analysis. The 5&ndash;20 km donut stations (currently excluded "
        "from both treated and donor groups) are a natural laboratory: "
        "treat them as a faux donor pool, fit synthetic control, see "
        "whether they show a &lsquo;Costco effect&rsquo; post-opening. "
        "Two outcomes are both informative: (a) the donut shows an "
        "effect, meaning Costco's footprint extends beyond 5 km and our "
        "headline estimate is conservative (the true effect is probably "
        "larger); (b) the donut shows no effect, meaning the Costco "
        "effect is concentrated within 5 km and the 20 km buffer is "
        "more than sufficient. <i>Concern:</i> the spatial analog of the "
        "temporal placebo. Whichever direction the result lands, it "
        "tightens the interpretation of the headline number.",
        body_style,
    ))

    doc.build(story)
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
