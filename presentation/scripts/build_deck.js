// Build the Costco Australia presentation deck.
//
//   node presentation/scripts/build_deck.js
//
// Output: presentation/costco_australia.pptx
//
// Structure (18 slides total):
//   1.   Title card                              (navy, full-bleed)
//   2.   Section divider: 01 / THE QUESTION      (navy, full-bleed)
//   3-5. Content slides 2-4                      (light, image + title)
//   6.   Section divider: 02 / DATA & METHOD     (navy)
//   7-10. Content slides 5-8                     (light)
//   11.  Section divider: 03 / WHAT WE FOUND     (navy)
//   12-14. Content slides 9-11                   (light)
//   15.  Section divider: 04 / WHAT TO DO        (navy)
//   16-17. Content slides 12-13                  (light)
//   18.  Closing: Questions?                     (navy)
//
// Design language: navy/light "sandwich" rhythm. Dividers give the
// audience visual chapter breaks. The PNGs carry the content; the
// deck adds title, slide-number chip, and speaker notes.

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// ---- Paths -------------------------------------------------------------
const PRES_DIR = path.resolve(__dirname, "..");
const PLOTS    = path.join(PRES_DIR, "plots");
const SCRIPT   = path.join(PRES_DIR, "script.txt");
const OUT_PATH = path.join(PRES_DIR, "costco_australia.pptx");

// ---- Palette (matches the PNGs) ---------------------------------------
const COL_NAVY     = "0B2545";   // dark navy for title slide
const COL_PRIMARY  = "065A82";   // deep blue (Costco)
const COL_GREEN    = "1E5F2A";   // deep green (savings)
const COL_TEXT     = "212121";   // body text
const COL_MUTED    = "6B7280";   // muted slate
const COL_BG       = "FFFFFF";   // white background
const COL_RULE     = "E5E7EB";   // very light gray rule

// ---- Content slide registry ------------------------------------------
// title:    short header (top-left on each content slide)
// image:    PNG filename in presentation/plots/
// imgAspect: width/height of the source PNG, for sizing
const contentSlides = [
  { n: 2,  title: "Why this matters",        image: "02_market_concentration.png",     imgAspect: 1746/837 },
  { n: 3,  title: "Our causal question",     image: "03_market_unit.png",              imgAspect: 1169/1153 },
  { n: 4,  title: "Where we end up",         image: "04_bluf_preview.png",             imgAspect: 1541/607 },
  { n: 5,  title: "Our data",                image: "05_data_pipeline.png",            imgAspect: 2504/933 },
  { n: 6,  title: "What the data looks like",image: "06_all_stations.png",             imgAspect: 1932/1475 },
  { n: 7,  title: "From universe to sample", image: "07_sample_funnel.png",            imgAspect: 1983/1045 },
  { n: 8,  title: "Identification strategy", image: "08_costcos_rings_donors.png",     imgAspect: 2058/1349 },
  { n: 9,  title: "Headline result",         image: "09_costco_trajectories.png",      imgAspect: 2658/2075 },
  { n: 10, title: "Does it generalize?",     image: "10_forest_plot.png",              imgAspect: 2398/1048 },
  { n: 11, title: "Did we just get lucky?",  image: "11_placebo_robustness.png",       imgAspect: 1870/1146 },
  { n: 12, title: "Recommendation",          image: "12_recommendation.png",           imgAspect: 1541/676 },
  { n: 13, title: "What we can't claim",     image: "13_limitations.png",              imgAspect: 1950/937 },
];

// ---- Section dividers -----------------------------------------------
// Each divider is inserted BEFORE the listed contentSlide.n
const dividers = [
  { before: 2,  number: "01", name: "THE QUESTION",
    tagline: "What we asked and why a regulator should care." },
  { before: 5,  number: "02", name: "DATA & METHOD",
    tagline: "Where the data came from, and how we built the counterfactual." },
  { before: 9,  number: "03", name: "WHAT WE FOUND",
    tagline: "The headline result and how it holds up across all four Costcos." },
  { before: 12, number: "04", name: "WHAT TO DO",
    tagline: "Our recommendation to the ACCC, and what we can’t claim." },
];

// ---- Parse speaker notes from script.txt -----------------------------
// Sections are delimited by the SLIDE header line:
//   SLIDE N  ·  Title                                  ~XX sec
// Body is everything between the PLOT: line and the next divider.
function parseNotes(scriptPath) {
  const text = fs.readFileSync(scriptPath, "utf8");
  const sectionRegex = /SLIDE\s+(\d+)\s+·[^\n]*\n[-=]+\n([\s\S]*?)(?=\n[-=]{40,}|\n={40,})/g;
  const notes = {};
  let m;
  while ((m = sectionRegex.exec(text)) !== null) {
    const slideNum = parseInt(m[1], 10);
    let body = m[2];
    // Strip the PLOT: line (and any leading blank lines)
    body = body.replace(/^PLOT:[^\n]*\n*/m, "").trim();
    notes[slideNum] = body;
  }
  return notes;
}

const notes = parseNotes(SCRIPT);

// ---- Slide construction ----------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";       // 13.333" × 7.5"
pres.title  = "Does Costco gas-station entry lower competitor fuel prices in Australia?";
pres.author = "MGT159 Group · advising the ACCC";

const SLIDE_W = 13.333;
const SLIDE_H = 7.5;

// ============================================================
// Slide 1 — title (dark navy, large headline)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL_NAVY };

  // Small kicker
  s.addText("MGT159  ·  Advising the ACCC", {
    x: 0.7, y: 0.7, w: 12, h: 0.4,
    fontSize: 14, fontFace: "Calibri", bold: true,
    color: "8FB8DD", charSpacing: 4,
    align: "left", valign: "top", margin: 0,
  });

  // The actual research question — verbatim from analysis qmd (line 132-133)
  s.addText(
    "Does the entry of a Costco gas station\n"
    + "into an Australian local market cause\n"
    + "nearby competitor stations to lower\n"
    + "their retail fuel prices?",
    {
      x: 0.7, y: 1.6, w: 12.2, h: 4.0,
      fontSize: 40, fontFace: "Georgia", bold: true,
      color: "FFFFFF", align: "left", valign: "top",
      lineSpacingMultiple: 1.15,
    },
  );

  // Small method tag
  s.addText(
    "A synthetic-control study, advising the Australian Competition and Consumer Commission.",
    {
      x: 0.7, y: 5.95, w: 12, h: 0.5,
      fontSize: 15, fontFace: "Calibri", italic: true,
      color: "CADCFC", align: "left", valign: "top",
    },
  );

  // Team line (placeholder — names go here)
  s.addText("[Speaker 1]  ·  [Speaker 2]  ·  [Speaker 3]  ·  [Speaker 4]", {
    x: 0.7, y: 6.7, w: 12, h: 0.4,
    fontSize: 14, fontFace: "Calibri",
    color: "8FB8DD", align: "left", valign: "middle",
  });

  // Slide-number chip (top-right, subtle)
  s.addText("01 / 13", {
    x: 11.6, y: 0.55, w: 1.2, h: 0.4,
    fontSize: 11, fontFace: "Calibri",
    color: "8FB8DD", align: "right", valign: "middle",
  });

  s.addNotes(notes[1] || "");
}

// ============================================================
// Section dividers + content slides — interleaved by position
// ============================================================
//
// Content slide geometry:
//   - title bar: y = 0.45 .. 1.05 (height 0.6)
//   - image area: y = 1.20 .. 7.20 (height 6.0)
//   - left/right margin: 0.42
//
// Image is centered within the image area, preserving aspect ratio.

const TITLE_Y       = 0.45;
const TITLE_H       = 0.6;
const IMG_TOP       = 1.20;
const IMG_BOT       = 7.20;
const IMG_AREA_H    = IMG_BOT - IMG_TOP;
const SIDE_MARGIN   = 0.42;
const IMG_AREA_W    = SLIDE_W - 2 * SIDE_MARGIN;
const AREA_ASPECT   = IMG_AREA_W / IMG_AREA_H;
const N_CONTENT     = contentSlides.length;   // 12 content slides (2-13)


function addSectionDivider(div) {
  const s = pres.addSlide();
  s.background = { color: COL_NAVY };

  // Faint guide rule above the section number
  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.0, y: 2.65, w: 0.7, h: 0.045,
    fill: { color: "5E8EBF" }, line: { color: "5E8EBF", width: 0 },
  });

  // Big section number (Roman-style numeric)
  s.addText(div.number, {
    x: 1.0, y: 2.85, w: 3.0, h: 1.6,
    fontSize: 96, fontFace: "Georgia", bold: true,
    color: "5E8EBF",
    align: "left", valign: "top", margin: 0,
  });

  // Section name
  s.addText(div.name, {
    x: 1.0, y: 4.6, w: 11, h: 1.0,
    fontSize: 48, fontFace: "Georgia", bold: true,
    color: "FFFFFF",
    align: "left", valign: "top", margin: 0, charSpacing: 2,
  });

  // Tagline below the section name
  s.addText(div.tagline, {
    x: 1.0, y: 5.65, w: 11, h: 0.8,
    fontSize: 16, fontFace: "Calibri",
    color: "CADCFC", align: "left", valign: "top",
  });

  // Small chip in the corner
  s.addText("Section " + div.number + " of 04", {
    x: SLIDE_W - 2.3, y: 0.55, w: 1.9, h: 0.4,
    fontSize: 10, fontFace: "Calibri",
    color: "5E8EBF", align: "right", valign: "middle", charSpacing: 2,
  });
}

function addContentSlide(meta) {
  const s = pres.addSlide();
  s.background = { color: COL_BG };

  // Slide title (top-left)
  s.addText(meta.title, {
    x: SIDE_MARGIN, y: TITLE_Y, w: 9.5, h: TITLE_H,
    fontSize: 32, fontFace: "Georgia", bold: true,
    color: COL_TEXT, align: "left", valign: "middle", margin: 0,
  });

  // Slide-number chip — N of 13 content slides (dividers don't count)
  const numStr = String(meta.n).padStart(2, "0") + " / " + String(N_CONTENT + 1).padStart(2, "0");
  s.addText(numStr, {
    x: SLIDE_W - SIDE_MARGIN - 1.5, y: TITLE_Y, w: 1.5, h: TITLE_H,
    fontSize: 11, fontFace: "Calibri",
    color: COL_MUTED, align: "right", valign: "middle",
  });

  // Fit image inside the image area, preserving aspect
  let imgW, imgH;
  if (meta.imgAspect >= AREA_ASPECT) {
    imgW = IMG_AREA_W;
    imgH = imgW / meta.imgAspect;
  } else {
    imgH = IMG_AREA_H;
    imgW = imgH * meta.imgAspect;
  }
  const imgX = (SLIDE_W - imgW) / 2;
  const imgY = IMG_TOP + (IMG_AREA_H - imgH) / 2;

  s.addImage({
    path: path.join(PLOTS, meta.image),
    x: imgX, y: imgY, w: imgW, h: imgH,
  });

  s.addNotes(notes[meta.n] || "");
}

// Walk content slides in order; insert a divider before each slide
// whose number appears in the dividers `before` field.
for (const meta of contentSlides) {
  const div = dividers.find(d => d.before === meta.n);
  if (div) addSectionDivider(div);
  addContentSlide(meta);
}

// ============================================================
// Closing slide — Questions?  (navy, mirrors the title slide)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL_NAVY };

  // Small kicker (echoes the title slide)
  s.addText("MGT159  ·  Advising the ACCC", {
    x: 0.7, y: 0.7, w: 12, h: 0.4,
    fontSize: 14, fontFace: "Calibri", bold: true,
    color: "8FB8DD", charSpacing: 4,
    align: "left", valign: "top", margin: 0,
  });

  // Big "Questions?"
  s.addText("Questions?", {
    x: 0.7, y: 2.6, w: 12, h: 1.7,
    fontSize: 84, fontFace: "Georgia", bold: true,
    color: "FFFFFF", align: "left", valign: "top",
  });

  // Sub-line: where to find the work
  s.addText(
    "Full Quarto analysis and reproducible pipeline:\n"
    + "github.com  ·  costco-australia-sc",
    {
      x: 0.7, y: 4.6, w: 11.5, h: 1.2,
      fontSize: 18, fontFace: "Calibri",
      color: "CADCFC", align: "left", valign: "top",
      lineSpacingMultiple: 1.3,
    },
  );

  // Team line at the bottom (matches title slide)
  s.addText("[Speaker 1]  ·  [Speaker 2]  ·  [Speaker 3]  ·  [Speaker 4]", {
    x: 0.7, y: 6.6, w: 12, h: 0.4,
    fontSize: 14, fontFace: "Calibri",
    color: "8FB8DD", align: "left", valign: "middle",
  });

  s.addNotes(
    "Thank you. Happy to take any questions on the methodology, "
    + "the robustness checks, or the back-of-envelope assumptions."
  );
}

// ---- Write + report ---------------------------------------------------
pres.writeFile({ fileName: OUT_PATH }).then((fn) => {
  console.log("Wrote " + fn);
});
