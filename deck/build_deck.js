// Deck for the selective routing project.
// Palette and motif deliberately match the interactive page: an instrument
// panel, with colour locked to meaning. Red is only ever a breached bound,
// moss only ever a guarantee that held.

const pptx = require("pptxgenjs");
const path = require("path");

const INK = "16202B";
const SLATE = "1F3A4D";
const GROUND = "FFFFFF";
const PANEL = "F1F4F7";
const INSTRUMENT = "2E7BA6";
const BOUND = "D14A38";
const MOSS = "5A9970";
const BRASS = "C9A227";
const MUTED = "6E7C8A";
const ICE = "CFE0EC";

const HEAD = "Cambria";
const BODY = "Calibri";
const DATA = "Courier New";

const D = path.join(__dirname);
const p = new pptx();
p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
p.author = "Thomas Hotton";
p.title = "Selective ticket routing";

const W = 13.3;

function darkSlide() {
  const s = p.addSlide();
  s.background = { color: SLATE };
  return s;
}
function lightSlide() {
  const s = p.addSlide();
  s.background = { color: GROUND };
  return s;
}
function title(s, text, color) {
  s.addText(text, {
    x: 0.75, y: 0.5, w: W - 1.5, h: 0.9, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 32, bold: true, color: color || INK,
  });
}
function eyebrow(s, text, color) {
  s.addText(text.toUpperCase(), {
    x: 0.75, y: 0.28, w: W - 1.5, h: 0.28, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 11, color: color || MUTED, charSpacing: 2,
  });
}
// the repeated motif: a certification stamp
function stamp(s, x, y, w, word, line, color) {
  s.addShape(p.ShapeType.rect, {
    x, y, w, h: 1.05, fill: { color: GROUND }, line: { color, width: 2.25 },
  });
  s.addText(word.toUpperCase(), {
    x: x + 0.2, y: y + 0.13, w: w - 0.4, h: 0.34, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 16, bold: true, color, charSpacing: 1,
  });
  s.addText(line, {
    x: x + 0.2, y: y + 0.52, w: w - 0.4, h: 0.4, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 11, color: MUTED,
  });
}
function stat(s, x, y, w, value, label, color, size) {
  s.addText(value, {
    x, y, w, h: 1.0, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: size || 54, bold: true, color, align: "left",
  });
  s.addText(label, {
    x, y: y + 1.0, w, h: 0.75, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13, color: MUTED,
  });
}
function body(s, x, y, w, h, text, size, color) {
  s.addText(text, {
    x, y, w, h, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: size || 15, color: color || INK, lineSpacing: 22,
  });
}

/* 1 — title */
{
  const s = darkSlide();
  s.addText("SELECTIVE TICKET ROUTING", {
    x: 0.9, y: 1.5, w: 11, h: 0.35, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 13, color: ICE, charSpacing: 3,
  });
  s.addText("You choose the precision.\nThe data returns the coverage.", {
    x: 0.9, y: 2.1, w: 11, h: 1.9, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 42, bold: true, color: GROUND, lineSpacing: 50,
  });
  s.addText("A response to the Astana Hub technology task for TechDrive LLC, Almaty, and the working code behind it.", {
    x: 0.9, y: 4.25, w: 9.5, h: 0.6, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 16, color: ICE,
  });
  s.addText("Thomas Hotton  ·  August 2026", {
    x: 0.9, y: 6.4, w: 8, h: 0.35, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 12, color: ICE,
  });
  s.addNotes(
    "Opening line: the brief asked for 95% routing accuracy. That number is not a specification until someone says what it costs in coverage.\n\n" +
    "This deck is the response plus the instrument built to test its central claim.\n\n" +
    "Likely question: did you submit it? No. The board requires a legal entity. The work stands on its own."
  );
}

/* 2 — the brief */
{
  const s = lightSlide();
  eyebrow(s, "the brief");
  title(s, "What TechDrive asked for");
  const items = [
    ["Automatic classification", "NLP microservice classifies and routes every incoming ticket in seconds", INSTRUMENT],
    ["A confidence gate at 85%", "Below it, the ticket goes to manual moderation", BRASS],
    ["Routing accuracy above 95%", "Stated as the headline target", MOSS],
    ["Analytics that are 100% reliable", "So management can find real bottlenecks", BOUND],
  ];
  items.forEach((it, i) => {
    const y = 1.75 + i * 1.22;
    s.addShape(p.ShapeType.ellipse, { x: 0.8, y: y + 0.08, w: 0.42, h: 0.42, fill: { color: it[2] } });
    s.addText(String(i + 1), {
      x: 0.8, y: y + 0.11, w: 0.42, h: 0.36, isTextBox: true, margin: 0,
      fontFace: DATA, fontSize: 14, bold: true, color: GROUND, align: "center",
    });
    s.addText(it[0], {
      x: 1.45, y, w: 5.2, h: 0.4, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 18, bold: true, color: INK,
    });
    s.addText(it[1], {
      x: 1.45, y: y + 0.42, w: 6.6, h: 0.5, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, color: MUTED,
    });
  });
  s.addShape(p.ShapeType.rect, { x: 8.6, y: 1.7, w: 3.95, h: 4.5, fill: { color: PANEL } });
  s.addText("The last two cannot both be true.", {
    x: 8.95, y: 2.5, w: 3.3, h: 1.5, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 24, bold: true, color: BOUND, lineSpacing: 30,
  });
  s.addText("Not because the target is ambitious.\nBecause of what the gate does to the tickets it holds back.", {
    x: 8.95, y: 4.15, w: 3.3, h: 1.6, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13.5, color: INK, lineSpacing: 20,
  });
  s.addNotes(
    "Read the four asks straight. Do not editorialise yet.\n\n" +
    "Decision: I did not treat the contradiction as a drafting error to smooth over. I made it the entry point of the response, because a supplier who quotes 95% back at them without saying what it costs is guessing.\n\n" +
    "Likely question: isn't 95% just aspirational? Answer: it is achievable as a guarantee on the subset the system routes. What is not knowable in advance is what share that leaves. That distinction is the whole proposal."
  );
}

/* 3 — the contradiction */
{
  const s = lightSlide();
  eyebrow(s, "the contradiction");
  title(s, "The manual path is the dirty one");
  body(s, 0.75, 1.55, 11.8, 1.0,
    "A confidence gate is sold as the safeguard on data quality: uncertain tickets go to a human, so the tags stay clean. But the human path is the least accurate path in the system, and it is the one the brief itself blames for bad tags.",
    15.5);
  const rows = [
    ["All manual, at a first line correct 75% of the time", "75.0%", MUTED],
    ["Full automation, no gate", "92.2%", INSTRUMENT],
    ["Best achievable, gate at optimum", "95.2%", MOSS],
    ["What the brief asked for", "100%", BOUND],
  ];
  rows.forEach((r, i) => {
    const y = 2.95 + i * 0.86;
    s.addShape(p.ShapeType.rect, { x: 0.75, y, w: 7.4, h: 0.7, fill: { color: i === 3 ? "FBEFED" : PANEL } });
    s.addText(r[0], {
      x: 1.0, y: y + 0.15, w: 5.2, h: 0.4, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 15, color: INK, bold: i === 2,
    });
    s.addText(r[1], {
      x: 6.3, y: y + 0.12, w: 1.6, h: 0.45, isTextBox: true, margin: 0,
      fontFace: DATA, fontSize: 20, bold: true, color: r[2], align: "right",
    });
  });
  s.addText("unreachable", {
    x: 6.3, y: 5.42, w: 1.6, h: 0.3, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 10, color: BOUND, align: "right",
  });
  s.addText("The 75% first-line rate is not measured here. It is the published figure from a comparable project on Russian-language IT support, and it is swept: at 85% the optimum is 96.3%, at 95% it is 98.3%. Never 100%.", {
    x: 0.75, y: 6.45, w: 7.4, h: 0.7, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11, color: MUTED, lineSpacing: 15,
  });
  s.addShape(p.ShapeType.rect, { x: 8.75, y: 2.95, w: 3.8, h: 3.0, fill: { color: SLATE } });
  s.addText("Past the optimum, raising precision makes the analytics worse.", {
    x: 9.05, y: 3.25, w: 3.2, h: 1.4, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 19, bold: true, color: GROUND, lineSpacing: 25,
  });
  s.addText("Every ticket withheld is handed to a process less accurate than the model was on it.", {
    x: 9.05, y: 4.72, w: 3.2, h: 1.05, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12, color: ICE, lineSpacing: 16,
  });
  s.addNotes(
    "This is the slide that reframes the brief. Take it slowly.\n\n" +
    "Composite analytics quality = share of ALL tickets correctly tagged. Auto-routed at model precision, the rest at first-line accuracy. First line at 75% is the published NLMK figure for the same problem in Russian-language IT support, not an invention.\n\n" +
    "Decision: I reported the optimum rather than the maximum precision, because the client's stated objective is analytics quality, not precision.\n\n" +
    "Likely question: why 75%? Answer: it is an assumption, and I swept it. At 85% first line the optimum is 96.3%, at 95% it is 98.3%. Never 100%. Measuring TechDrive's actual first-line rate is Phase 0.\n\n" +
    "Second likely question: so what should the acceptance criterion be? Traceability at 100%, correctness at the measured figure per category."
  );
}

/* 4 — so I built it */
{
  const s = lightSlide();
  eyebrow(s, "the response");
  title(s, "So I built the mechanism and measured it");
  body(s, 0.75, 1.5, 11.8, 0.7,
    "Rather than propose a method on the strength of its literature, the threshold-setting mechanism was implemented end to end on a public corpus with the same long-tailed category shape as a support taxonomy.", 15.5);
  const stages = [
    ["1", "Rules", "Deterministic pre-filter on the obvious, high-volume patterns. Zero model cost, fully auditable.", MUTED],
    ["2", "Retrieval", "Ticket embedded, compared to the labelled archive, category by distance-weighted vote. Every decision names the archive documents behind it.", INSTRUMENT],
    ["3", "Adjudication", "A model call only when the neighbour vote is too close to call. The expensive path, on a minority by design.", SLATE],
    ["4", "Certification", "The confidence threshold is not tuned. It is certified by risk control, and refused when the data cannot support it.", MOSS],
  ];
  stages.forEach((st, i) => {
    const x = 0.75 + i * 3.05;
    s.addShape(p.ShapeType.rect, { x, y: 2.6, w: 2.8, h: 3.3, fill: { color: PANEL } });
    s.addShape(p.ShapeType.ellipse, { x: x + 0.25, y: 2.85, w: 0.5, h: 0.5, fill: { color: st[3] } });
    s.addText(st[0], {
      x: x + 0.25, y: 2.89, w: 0.5, h: 0.42, isTextBox: true, margin: 0,
      fontFace: DATA, fontSize: 16, bold: true, color: GROUND, align: "center",
    });
    s.addText(st[1], {
      x: x + 0.25, y: 3.5, w: 2.3, h: 0.4, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 17, bold: true, color: INK,
    });
    s.addText(st[2], {
      x: x + 0.25, y: 3.95, w: 2.35, h: 1.85, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, color: MUTED, lineSpacing: 16,
    });
  });
  s.addText("Reuters-21578, 53 categories. Top 5 carry 79% of the volume; the median category holds 14 documents. That shape is the point.", {
    x: 0.75, y: 6.2, w: 11.8, h: 0.5, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 11.5, color: MUTED,
  });
  s.addNotes(
    "Decision: retrieval rather than a trained classifier. Three reasons, and I would give all three.\n" +
    "  1. Explainable. The decision cites named archive documents. The client's stated problem is that they cannot trust their own analytics.\n" +
    "  2. Absorbs taxonomy change through an index rebuild, no retraining cycle.\n" +
    "  3. Self-hostable, which matters because Kazakh law requires personal data of citizens to be stored in country.\n\n" +
    "Alternative rejected: fine-tuning a transformer classifier. Better accuracy ceiling, but it retrains on every taxonomy change and explains nothing.\n\n" +
    "Likely question: why Reuters and not real tickets? Answer: no real ticket corpus was accessible. Reuters was chosen for its category distribution, not its realism, and the report says so. It is easier than support tickets, which means the numbers here are an upper bound."
  );
}

/* 5 — the dial */
{
  const s = lightSlide();
  eyebrow(s, "result 1");
  title(s, "Precision is a setting. Coverage is the bill.");
  s.addImage({ path: path.join(D, "fig_dial.png"), x: 0.6, y: 1.5, w: 7.6, h: 4.65 });
  stamp(s, 8.6, 1.75, 3.95, "Certified", "θ = 0.595   ·   error ≤ 5%", MOSS);
  body(s, 8.6, 3.15, 3.95, 2.6,
    "Ask for 95% precision and 87.2% of tickets can be routed automatically.\n\nThe red marker is what threshold tuning picked. More coverage, and on this split it holds. Whether it holds reliably is the next slide.", 13.5);
  s.addText("The refusal is the feature.", {
    x: 8.6, y: 5.65, w: 3.95, h: 0.5, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 17, bold: true, color: INK,
  });
  s.addNotes(
    "Walk the curve left to right: as you demand more precision you move left, and coverage falls.\n\n" +
    "Decision: I made precision the input and coverage the reported output, not the other way round. A client can act on 'here is what your target costs'. Nobody can act on 'the model is 92% accurate'.\n\n" +
    "The red X is what threshold tuning picked for the same 95% target: more coverage, and on this particular split it does hold, at 3.8% error.\n\n" +
    "Say that plainly. It is the point. A single split cannot show you the failure, which is exactly why the next slide runs fifteen.\n\n" +
    "Likely question: what does 'certified' actually mean? Answer: the error rate among routed tickets is bounded at 5% with 90% confidence, using a distribution-free finite-sample bound, with the multiple-testing across the threshold grid corrected. Not a validation-set estimate."
  );
}

/* 6 — 67% */
{
  const s = darkSlide();
  eyebrow(s, "result 2", ICE);
  title(s, "The obvious method misses its own target", GROUND);
  body(s, 0.75, 1.55, 11.8, 0.85,
    "Sweep the cutoff on held-out data, keep the one whose error rate clears the target. It is what most people would do. Over 15 independent splits:", 15.5);
  s.addShape(p.ShapeType.rect, { x: 0.75, y: 2.75, w: 5.6, h: 3.0, fill: { color: "17303F" } });
  s.addShape(p.ShapeType.rect, { x: 6.95, y: 2.75, w: 5.6, h: 3.0, fill: { color: "17303F" } });
  s.addText("RISK CONTROL", {
    x: 1.1, y: 3.0, w: 5.0, h: 0.35, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 12, color: MOSS, charSpacing: 2,
  });
  s.addText("0%", {
    x: 1.1, y: 3.45, w: 5.0, h: 1.25, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 60, bold: true, color: MOSS,
  });
  s.addText("of trials breached the target\nmean coverage 90.9%", {
    x: 1.1, y: 4.75, w: 5.0, h: 0.8, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14, color: ICE, lineSpacing: 19,
  });
  s.addText("THRESHOLD TUNING", {
    x: 7.3, y: 3.0, w: 5.0, h: 0.35, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 12, color: BOUND, charSpacing: 2,
  });
  s.addText("67%", {
    x: 7.3, y: 3.45, w: 5.0, h: 1.25, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 60, bold: true, color: BOUND,
  });
  s.addText("of trials breached the target\nmean coverage 95.0%", {
    x: 7.3, y: 4.75, w: 5.0, h: 0.8, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14, color: ICE, lineSpacing: 19,
  });
  s.addText("Tuning shows the better coverage. It buys it by not paying for a guarantee, and the failure is invisible on any single run.", {
    x: 0.75, y: 6.15, w: 11.8, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14.5, color: ICE,
  });
  s.addNotes(
    "This is the single most important number in the project. Give it room.\n\n" +
    "Why tuning fails, two reasons:\n" +
    "  1. Selective accuracy is not guaranteed monotone in the threshold, so there is no ordering argument.\n" +
    "  2. Sweeping a grid and keeping the best is multiple testing. The winner was selected because it flattered the sample.\n\n" +
    "Decision: I ran 15 splits rather than one. A single split is what a demo shows, and on a single split tuning looks fine.\n\n" +
    "Likely question: isn't 0% suspicious, shouldn't it breach sometimes? Answer: the budget was 10%, so up to 10% would be correct behaviour. 0% here means the bound is slightly conservative at this sample size. Bonferroni was more conservative still, which is why I replaced it with fixed sequence testing."
  );
}

/* 7 — per category */
{
  const s = lightSlide();
  eyebrow(s, "result 3");
  title(s, "One number over 53 categories hides the damage");
  body(s, 0.75, 1.5, 11.8, 0.75,
    "Every figure so far is an aggregate. A support desk does not experience an aggregate: it experiences one queue per team.", 15.5);
  stat(s, 0.85, 2.5, 3.6, "1/53", "categories can carry their own certified guarantee at the 95% target", BOUND);
  stat(s, 4.75, 2.5, 3.4, "805", "calibration items held by the one that qualifies. The median of the rest holds 7.", INSTRUMENT);
  stat(s, 8.65, 2.5, 3.9, "317", "labelled items a category needs before any guarantee can be certified for it", SLATE);
  s.addShape(p.ShapeType.rect, { x: 0.75, y: 4.9, w: 11.8, h: 1.35, fill: { color: PANEL } });
  s.addText("At the 97% target, none of the 53 certify at all.", {
    x: 1.1, y: 5.08, w: 11.1, h: 0.4, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 19, bold: true, color: BOUND,
  });
  s.addText("This is the number the proposal needed: Phase 0 should size the labelling exercise at roughly 300 examples per category to be automated, not by a global sample target.",
    { x: 1.1, y: 5.55, w: 11.1, h: 0.55, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 14, color: INK });
  s.addNotes(
    "This result came last and turned out to be the most useful to a client.\n\n" +
    "Decision: I conditioned on the PREDICTED class, not the true class. At decision time the true class is unknown, so a guarantee conditioned on it could not be applied. Conditioning on the prediction gives the operational statement: of the tickets sent to team X, at most alpha are wrong.\n\n" +
    "The confidence budget is split across the 43 categories, because certifying 43 of them is 43 tests. Note: 317 items needed with that correction, 141 without. Sample size binds, not multiplicity. Worth saying, because it pre-empts 'your correction is too harsh'.\n\n" +
    "Denominator, worth being precise about: the certification routine runs over the 43 categories the classifier ever predicts, so from inside the method it is 1 of 43. But 10 categories are never predicted even once, holding one to five tickets each. They fail more completely than the 42 that merely fail to certify. 1 of 53 is the figure that describes what the desk would actually get, and it is the one on the slide.\n\nLikely question: doesn't this undermine your earlier numbers? Answer: yes, and deliberately. The 87.2% coverage is a true statement about the mixture and not about any team's queue. Both facts are in the report. A proposal quoting the first without the second is quoting half a result."
  );
}

/* 8 — drift */
{
  const s = lightSlide();
  eyebrow(s, "result 4");
  title(s, "Two kinds of drift. Only one is visible.");
  s.addImage({ path: path.join(D, "fig_drift.png"), x: 0.6, y: 1.45, w: 12.1, h: 4.5 });
  s.addText("Left: the guarantee survives an extreme shift because unfamiliar tickets score low and get held back. Right: coverage does not move by a tenth of a point while the error rate triples.",
    { x: 0.75, y: 6.15, w: 11.8, h: 0.6, isTextBox: true, margin: 0, fontFace: BODY, fontSize: 14, color: INK });
  s.addNotes(
    "The two panels are the same certified threshold under two different kinds of change. Never recalibrated in either.\n\n" +
    "Left, the category mix moves, which is what a product launch does to a queue. Abstention absorbs it: the system pays in automation, not in mistakes. Self-correcting and visible on a dashboard.\n\n" +
    "Right, the taxonomy is redefined: a category split, two teams swapping ownership, a product rename. The tickets still look familiar, the model stays confident, and the right answer moved underneath it.\n\n" +
    "Decision: I tested the natural temporal split first and it broke nothing, so I induced the shift deliberately. Reporting only the temporal result would have been a comfortable non-finding.\n\n" +
    "Likely question: how would you detect the right-hand case in production? That is the next slide."
  );
}

/* 9 — the consequence */
{
  const s = darkSlide();
  eyebrow(s, "what it changed", ICE);
  title(s, "Coverage is not a health signal", GROUND);
  body(s, 0.75, 1.6, 7.3, 1.5,
    "Nothing inside the service detects a taxonomy change. It breaks the guarantee once 8% of one category is redefined, with every internal metric flat.\n\nThe only thing that catches it is ground truth coming back from production: agents re-routing tickets the system routed automatically.", 15.5, ICE);
  s.addShape(p.ShapeType.rect, { x: 0.75, y: 3.5, w: 7.3, h: 2.6, fill: { color: "17303F" } });
  s.addText("In the proposal, feedback capture moved from a refinement to a requirement.", {
    x: 1.1, y: 3.8, w: 6.6, h: 0.9, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 20, bold: true, color: GROUND, lineSpacing: 26,
  });
  s.addText("Re-route rate per category becomes the primary production health metric, and the trigger for recalibrating ahead of schedule.", {
    x: 1.1, y: 4.85, w: 6.6, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13.5, color: ICE, lineSpacing: 19,
  });
  s.addShape(p.ShapeType.rect, { x: 8.6, y: 1.6, w: 3.95, h: 4.5, fill: { color: "17303F" } });
  s.addText("8%", {
    x: 8.95, y: 2.2, w: 3.3, h: 1.2, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 56, bold: true, color: BOUND,
  });
  s.addText("of one high-volume category redefined is enough to break a certified guarantee", {
    x: 8.95, y: 3.4, w: 3.3, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13.5, color: ICE, lineSpacing: 18,
  });
  s.addText("87.2%", {
    x: 8.95, y: 4.5, w: 3.3, h: 0.6, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 26, bold: true, color: MUTED,
  });
  s.addText("coverage before, during and after. It never moves.", {
    x: 8.95, y: 5.1, w: 3.3, h: 0.7, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, color: MUTED, lineSpacing: 17,
  });
  s.addNotes(
    "This is the slide that connects measurement back to a design decision, which is what a client is actually buying.\n\n" +
    "Before this result, the proposal described feedback capture as costing the agent nothing because re-routing is an action they already perform. True but weak. Now it has a measured reason to exist.\n\n" +
    "Likely question: couldn't you monitor input drift instead? Answer: I tried. Monitoring the shift in the category mix was my first recommendation, and it was wrong. Mix shift is the safe mode. It was one of two findings I had to retract, which is slide 12."
  );
}

/* 10 — decisions by measurement */
{
  const s = lightSlide();
  eyebrow(s, "engineering");
  title(s, "Three decisions made by measurement");
  const rows = [
    ["Hoeffding → empirical Bernstein",
     "The first bound could not certify anything below a 10% error target, refusing the exact operating point the exercise was about. It charges for the full range regardless of observed spread; this loss is almost always 0 or alpha.",
     "Recovered the 95%, 97% and 98% targets at the same rigour.", MOSS],
    ["Bonferroni → fixed sequence testing",
     "Testing 200 grid points at delta/200 pays a multiplicity price for grid resolution, which is an implementation detail the data has no stake in.",
     "Bought 4 to 9 points of coverage. But it is not universally better, and the harness runs both.", INSTRUMENT],
    ["Multi-start: tried and rejected",
     "The variant splits the budget across several entry points to survive non-monotone bumps in the risk.",
     "Splitting the budget cost more than the bumps did. The code is left in place, unused, with the result recorded.", BRASS],
  ];
  rows.forEach((r, i) => {
    const y = 1.7 + i * 1.62;
    s.addShape(p.ShapeType.rect, { x: 0.75, y, w: 11.8, h: 1.42, fill: { color: PANEL } });
    s.addShape(p.ShapeType.ellipse, { x: 1.02, y: y + 0.5, w: 0.34, h: 0.34, fill: { color: r[3] } });
    s.addText(r[0], {
      x: 1.55, y: y + 0.14, w: 5.0, h: 0.45, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 16, bold: true, color: INK,
    });
    s.addText(r[1], {
      x: 1.55, y: y + 0.6, w: 5.6, h: 0.75, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 11.5, color: MUTED, lineSpacing: 15,
    });
    s.addText(r[2], {
      x: 7.4, y: y + 0.36, w: 4.85, h: 0.8, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, color: INK, lineSpacing: 18,
    });
  });
  s.addText("Each was a measurement, not a preference. The one that did not work is on the slide too.", {
    x: 0.75, y: 6.65, w: 11.8, h: 0.4, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 11.5, color: MUTED,
  });
  s.addNotes(
    "If a technical interviewer goes deep anywhere, it is here.\n\n" +
    "Hoeffding vs Bernstein: Hoeffding's width depends only on sample size and the range of the loss. Bernstein's width scales with the observed variance. This loss takes value 0 on an accepted correct item, alpha on a rejected one, and 1 only on an accepted error, which is rare by design. So the variance is tiny and Hoeffding overcharges badly.\n\n" +
    "Fixed sequence testing: order the grid in advance, test each at full delta, stop at the first failure. Family-wise error still controlled. The ordering must be chosen without looking at the calibration data; I ordered by descending threshold, most conservative first.\n\n" +
    "Honest caveat I would volunteer: fixed sequence testing stops at the first failure, so a valid threshold underneath a non-monotone bump is never reached. On a synthetic fixture in the test suite, Bonferroni wins. Neither dominates."
  );
}

/* 11 — I was wrong twice */
{
  const s = darkSlide();
  eyebrow(s, "what the tests caught", ICE);
  title(s, "Three things I got wrong", GROUND);
  body(s, 0.75, 1.55, 11.8, 0.65,
    "All three were caught by the test suite, not by looking at the output. The numbers looked perfectly reasonable while they were wrong.", 15.5, ICE);
  const rows = [
    ["The finding I retracted", "I reported that the guarantee broke at a specific amount of mix shift, and recommended monitoring that distance in production. With the bugs fixed it survives twice as far. The recommendation was wrong, and the replacement finding is the opposite in character."],
    ["Two bugs behind it", "Categories with few documents were getting no exemplar in the retrieval index, and the corpus carries 85 exact duplicate documents, one appearing seven times. A duplicate straddling index and test lets the classifier retrieve a copy of the item it is classifying."],
    ["A third, worse one", "Two definitions of the per-category function existed; the later one, mine, failed to split the confidence budget across classes. Python keeps the last definition, so the statistically incorrect one was the one running."],
  ];
  rows.forEach((r, i) => {
    const y = 2.5 + i * 1.35;
    s.addShape(p.ShapeType.rect, { x: 0.75, y, w: 11.8, h: 1.15, fill: { color: "17303F" } });
    s.addText(r[0], {
      x: 1.1, y: y + 0.16, w: 3.3, h: 0.8, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 15, bold: true, color: BOUND, lineSpacing: 19,
    });
    s.addText(r[1], {
      x: 4.6, y: y + 0.16, w: 7.65, h: 0.9, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, color: ICE, lineSpacing: 17,
    });
  });
  s.addText("A measurement you cannot check is not a measurement. This is why the test suite exists, and why it is in the report.", {
    x: 0.75, y: 6.5, w: 11.8, h: 0.45, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 16, bold: true, color: GROUND,
  });
  s.addNotes(
    "Do not rush this slide and do not apologise for it. It is the strongest thing in the deck.\n\n" +
    "The point to land: none of these were caught by looking at output. Every one was caught by a test asserting a property the report claims. The numbers looked perfectly reasonable while they were wrong.\n\n" +
    "The third one is worth dwelling on if the audience is technical: silent shadowing of a function definition, where the wrong version wins because it was defined second, and the failure mode is a guarantee that is quietly weaker than stated.\n\n" +
    "Likely question: how do you know there aren't more? Answer: I don't. What I have is 12 tests targeting the specific claims the report makes, a single script that regenerates every number, and a log so any figure can be traced to the run that produced it."
  );
}

/* 12 — limits */
{
  const s = lightSlide();
  eyebrow(s, "limits");
  title(s, "What this is not");
  const items = [
    ["The encoder is TF-IDF, not a sentence model", "The build environment had no access to pretrained transformer weights. It has no semantic knowledge beyond term co-occurrence in this corpus and cannot handle a multilingual flow at all. Swapping it moves every accuracy number here. It does not change whether the threshold selection is valid, which is what was being tested."],
    ["Reuters is easier than support tickets", "Newswire is well written, consistently labelled and monolingual. A published project on Russian-language IT support with roughly a million training tickets reached 84% precision at 61% coverage, against human operators at 75%."],
    ["The conformal work is application, not contribution", "The methods are from the literature and cited. What is mine is the implementation, the measurement, and the decisions between variants."],
    ["Label noise is not modelled", "Every corpus label is treated as correct. In a real archive that assumption is usually false, which is precisely why measuring it is Phase 0 of the proposal rather than an assumption inside it."],
  ];
  items.forEach((it, i) => {
    const y = 1.65 + i * 1.28;
    s.addShape(p.ShapeType.ellipse, { x: 0.78, y: y + 0.14, w: 0.3, h: 0.3, fill: { color: BRASS } });
    s.addText(it[0], {
      x: 1.28, y, w: 4.35, h: 0.85, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 15, bold: true, color: INK, lineSpacing: 19,
    });
    s.addText(it[1], {
      x: 5.85, y, w: 6.7, h: 1.1, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, color: MUTED, lineSpacing: 16,
    });
  });
  s.addNotes(
    "Say these before anyone asks. Volunteering a limit is worth more than defending one.\n\n" +
    "The TF-IDF point is the one a machine learning person will spot in thirty seconds, so name it first. The framing that holds: the claim was never that this encoder is good. It was that the threshold machinery works and has known failure modes. The encoder sits behind an interface precisely so it can be swapped.\n\n" +
    "Likely question: so what would you actually deploy? A multilingual sentence embedding model, self-hosted, benchmarked on the client's own tickets during Phase 0 rather than chosen from a vendor page. Kazakh coverage in particular has to be tested, not assumed."
  );
}

/* 13 — close */
{
  const s = darkSlide();
  s.addText("What the client would actually get", {
    x: 0.9, y: 1.35, w: 11, h: 0.7, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 32, bold: true, color: GROUND,
  });
  const items = [
    ["A target that means something", "Precision chosen by the client, coverage reported as the measured consequence, per category rather than as one aggregate."],
    ["A number proven before go-live", "Four weeks of shadow mode on live traffic, writing nothing, before automated routing touches a ticket."],
    ["A system that says no", "It refuses to certify what the data cannot support, and every decision carries the archive documents behind it."],
  ];
  items.forEach((it, i) => {
    const y = 2.5 + i * 1.28;
    s.addShape(p.ShapeType.ellipse, { x: 0.9, y: y + 0.08, w: 0.44, h: 0.44, fill: { color: MOSS } });
    s.addText(String(i + 1), {
      x: 0.9, y: y + 0.12, w: 0.44, h: 0.38, isTextBox: true, margin: 0,
      fontFace: DATA, fontSize: 15, bold: true, color: SLATE, align: "center",
    });
    s.addText(it[0], {
      x: 1.6, y, w: 4.3, h: 0.5, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 17, bold: true, color: GROUND,
    });
    s.addText(it[1], {
      x: 1.6, y: y + 0.5, w: 10.6, h: 0.65, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, color: ICE, lineSpacing: 18,
    });
  });
  s.addText("Report, source, tests and the interactive version: github.com/thomas2143/TechDrive", {
    x: 0.9, y: 6.5, w: 11, h: 0.4, isTextBox: true, margin: 0,
    fontFace: DATA, fontSize: 12, color: ICE,
  });
  s.addNotes(
    "Close on what the client buys, not on what I built.\n\n" +
    "If there is time, the interactive page is the thing to open live: drag the precision target to 99% and let them watch the instrument refuse.\n\n" +
    "Repository: github.com/thomas2143/TechDrive"
  );
}

p.writeFile({ fileName: path.join(D, "selective-routing-deck.pptx") })
  .then(f => console.log("wrote", f));
