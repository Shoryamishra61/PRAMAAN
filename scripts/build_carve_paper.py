# ruff: noqa: E501
"""Build the artifact-generated CARVE v4.5 research paper as a verified PDF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/ml/carve-v4.5"
DATA = ROOT / "data/financial-evidence-integrity/v4.5"
OUTPUT = ROOT / "output/pdf/carve-fecl-bench-v4.5-paper.pdf"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


DEV = load(ARTIFACTS / "dev-calibration-results.json")
TEST = load(ARTIFACTS / "frozen-test-results.json")
RECEIPT = load(ARTIFACTS / "frozen-test-receipt.json")
MANIFEST = load(DATA / "manifest.json")

INK = colors.HexColor("#162019")
GREEN = colors.HexColor("#145A3A")
RED = colors.HexColor("#A12D26")
AMBER = colors.HexColor("#8A6200")
PAPER = colors.HexColor("#F5F2E8")
LINE = colors.HexColor("#B8B7AA")
MUTED = colors.HexColor("#566159")

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="PaperTitle",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=25,
        leading=27,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=10,
    )
)
styles.add(
    ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MUTED,
        spaceAfter=16,
    )
)
styles.add(
    ParagraphStyle(
        name="H1x",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=17,
        leading=20,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="H2x",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=GREEN,
        spaceBefore=10,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="Bodyx",
        parent=styles["BodyText"],
        fontName="Times-Roman",
        fontSize=9.3,
        leading=13.1,
        textColor=INK,
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Smallx",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.2,
        textColor=MUTED,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="Codex",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10.2,
        leftIndent=8,
        rightIndent=8,
        borderWidth=0.5,
        borderColor=LINE,
        borderPadding=7,
        backColor=colors.HexColor("#EEEADF"),
        spaceBefore=5,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="Abstract",
        parent=styles["BodyText"],
        fontName="Times-Italic",
        fontSize=9.3,
        leading=13.2,
        borderWidth=0.7,
        borderColor=INK,
        borderPadding=10,
        backColor=PAPER,
        spaceAfter=12,
    )
)


def p(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(text, styles[style])


def table(data: list[list[Any]], widths: list[float], header: bool = True) -> Table:
    value = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", 7.2),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7.2),
            ]
        )
    value.setStyle(TableStyle(commands))
    return value


def architecture() -> Drawing:
    labels = ["Evidence", "Relations", "Z3 proof", "Residual risk", "Controller", "Acquire"]
    drawing = Drawing(510, 78)
    x = 4
    for index, label in enumerate(labels):
        width = 70 if index != 3 else 82
        fill = RED if label == "Z3 proof" else (GREEN if label == "Evidence" else PAPER)
        text = colors.white if label in {"Z3 proof", "Evidence"} else INK
        drawing.add(Rect(x, 28, width, 30, fillColor=fill, strokeColor=INK, strokeWidth=0.7))
        drawing.add(
            String(
                x + width / 2,
                39,
                label,
                fontName="Helvetica-Bold",
                fontSize=7,
                fillColor=text,
                textAnchor="middle",
            )
        )
        if index < len(labels) - 1:
            drawing.add(Line(x + width, 43, x + width + 13, 43, strokeColor=INK))
            drawing.add(
                PolyLine(
                    [(x + width + 9, 47), (x + width + 13, 43), (x + width + 9, 39)],
                    strokeColor=INK,
                )
            )
        x += width + 13
    drawing.add(
        String(
            4,
            8,
            "Hard precedence: no learned component may override an UNSAT financial invariant.",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            fillColor=MUTED,
        )
    )
    return drawing


def risk_curve() -> Drawing:
    points = DEV["calibration"]["risk_coverage_curve"]
    drawing = Drawing(480, 150)
    left, bottom, width, height = 40, 24, 410, 110
    drawing.add(Line(left, bottom, left, bottom + height, strokeColor=INK))
    drawing.add(Line(left, bottom, left + width, bottom, strokeColor=INK))
    coords = [
        (left + item["coverage"] * width, bottom + (1 - item["value_weighted_risk"]) * height)
        for item in points
    ]
    drawing.add(PolyLine(coords, strokeColor=RED, strokeWidth=1.8))
    drawing.add(
        Line(
            left,
            bottom + 0.975 * height,
            left + width,
            bottom + 0.975 * height,
            strokeColor=AMBER,
            strokeDashArray=[3, 2],
        )
    )
    drawing.add(String(left, 6, "coverage", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    drawing.add(
        String(2, bottom + height - 3, "1-risk", fontName="Helvetica", fontSize=7, fillColor=MUTED)
    )
    drawing.add(
        String(
            left + 5,
            bottom + height - 12,
            "CRC target 0.025",
            fontName="Helvetica",
            fontSize=7,
            fillColor=AMBER,
        )
    )
    return drawing


def metric_rows(section: dict[str, Any]) -> list[list[str]]:
    names = [
        "literal_deterministic_rules",
        "tfidf_lr",
        "semantic_only_transformer",
        "deterministic_relational_xgboost",
        "learned_relation_xgboost",
        "formal_proof",
        "residual_risk_initial",
    ]
    output = [["System", "P", "R", "F1", "PR-AUC", "FPASS", "FBLOCK", "INR exposure"]]
    for name in names:
        metric = section[name]
        output.append(
            [
                name.replace("_", " "),
                f"{metric['precision']:.3f}",
                f"{metric['recall']:.3f}",
                f"{metric['f1']:.3f}",
                f"{metric['pr_auc']:.3f}",
                str(metric["false_pass"]),
                str(metric["false_block"]),
                f"{metric['false_pass_exposure_minor'] / 100:,.0f}",
            ]
        )
    return output


def header_footer(canvas: Any, document: Any) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 282 * mm, 192 * mm, 282 * mm)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(GREEN)
    canvas.drawString(18 * mm, 286 * mm, "CARVE / FECL-BENCH v4.5")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(
        192 * mm, 286 * mm, "Synthetic benchmark - defense-only decision support"
    )
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.drawString(18 * mm, 9 * mm, "Frozen one-shot TEST; no production prevalence claim")
    canvas.drawRightString(192 * mm, 9 * mm, str(document.page))
    canvas.restoreState()


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="CARVE: Cost-aware Active Risk-controlled Verification with Evidence acquisition",
        author="Dispute Integrity Gate research team",
        subject="Financial evidence consistency learning under asymmetric risk",
    )
    story: list[Any] = []
    story.extend(
        [
            Spacer(1, 18 * mm),
            p("CARVE", "Subtitle"),
            p(
                "Cost-aware Active Risk-controlled Verification with Evidence Acquisition",
                "PaperTitle",
            ),
            p(
                "A falsification-first study of refund and credit-not-processed disputes under "
                "heterogeneous evidence, exact financial invariants, and asymmetric merchant risk",
                "Subtitle",
            ),
            p(
                "<b>Abstract.</b> We study Financial Evidence Consistency Learning (FECL): deciding "
                "whether customer communications, refund records, identifiers, temporal events, "
                "orders, and policies describe one internally consistent financial reality. CARVE "
                "combines grounded semantic relation induction with immutable financial invariants, "
                "Z3 contradiction certificates, residual-risk estimation, selective abstention, and "
                "cost-aware evidence acquisition. FECL-Bench v4.5 contains 2,480 synthetic cases "
                "with family-isolated TRAIN/DEV/CALIBRATION/TEST/OOD splits and causal minimal pairs. "
                "A one-shot frozen TEST falsifies the broad learned-stack hypothesis: literal rules "
                "and formal proof achieve F1 1.000, while relational XGBoost drops to 0.748 and the "
                "semantic-only transformer to 0.684. Transformer relation induction shows a smaller "
                "macro-F1 lift (0.547 vs. 0.484), but learned relation features do not improve the "
                "decision. Conformal risk control certifies no safe PASS coverage, so the component "
                "is rejected. A frozen targeted acquisition policy resolves all 480 TEST cases with "
                "zero false-PASS exposure, though cheapest-first is slightly cheaper, a retained "
                "negative generalization result. The deployable conclusion is deliberately narrow: "
                "semantic extraction may assist grounding, but deterministic truth and human review "
                "retain authority.",
                "Abstract",
            ),
            table(
                [
                    ["Contribution", "Empirical disposition"],
                    ["FECL formulation and v4.5 benchmark", "Retained; synthetic only"],
                    ["Transformer relation induction", "Retained for relation semantics only"],
                    ["Relational XGBoost", "Rejected: no lift over literal rules"],
                    ["Z3 minimum contradiction certificate", "Retained: 920/920 pre-TEST exact"],
                    ["CRC selective PASS", "Rejected: zero certified PASS coverage"],
                    ["Learned acquisition policy", "Not run: simpler policy sufficient"],
                ],
                [62 * mm, 108 * mm],
            ),
            Spacer(1, 5 * mm),
            p(
                f"Artifact identity: TEST SHA-256 {hashlib.sha256((ARTIFACTS / 'frozen-test-results.json').read_bytes()).hexdigest()}<br/>"
                f"One-shot receipt: {hashlib.sha256((ARTIFACTS / 'frozen-test-receipt.json').read_bytes()).hexdigest()}",
                "Smallx",
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("1. Problem formulation", "H1x"),
            p(
                "Chargeback classification asks whether a dispute belongs to a class. FECL asks a "
                "different question: whether heterogeneous evidence is jointly satisfiable under "
                "authoritative payment state. This distinction matters because a fluent model can "
                "classify language while missing an exact one-rupee, currency, parent-payment, or "
                "temporal contradiction. Razorpay's public dispute guidance requires evidence for "
                "refund-not-processed claims, and its refund documentation distinguishes refund and "
                "payment identifiers [1,2]. We therefore model evidence verification, not outcome "
                "prediction.",
            ),
            p("1.1 Decision problem", "H2x"),
            p(
                "Let E_t be the evidence visible at step t, C(E_t) grounded claims, A(E_t) "
                "authoritative facts, and I immutable financial invariants. The formal state is:",
            ),
            p(
                "Phi(E_t) = Claims(C(E_t)) AND Authority(A(E_t)) AND Invariants(I).<br/>"
                "BLOCK if Phi(E_t) is UNSAT; PASS only if Phi(E_t) is SAT and a valid risk "
                "certificate permits PASS; otherwise REVIEW.",
                "Codex",
            ),
            p(
                "No neural, language, tree, or acquisition model can convert an UNSAT result into "
                "PASS. Missing, malformed, OOD, hash-invalid, or unsupported evidence routes to "
                "REVIEW. BLOCK is a local evidence-integrity hold, not a legal verdict or financial "
                "action.",
            ),
            p("1.2 Cost-sensitive objective", "H2x"),
            p(
                "For decisions d in {PASS, REVIEW, BLOCK}, labels y in {consistent, contradiction}, "
                "and acquired evidence S, CARVE minimizes the preregistered synthetic proxy:",
            ),
            p(
                "L(d,y,S) = 1[d=PASS,y=contradiction] * min(value, INR 50,000) + "
                "1[d=BLOCK,y=consistent] * min(INR 500, 0.05*value) + "
                "1[d=REVIEW] * INR 100 + sum(e in S) cost(e).",
                "Codex",
            ),
            p(
                "These are benchmark proxies, not observed losses or claimed merchant savings. The "
                "primary safety statistic is false-PASS count and synthetic exposure.",
            ),
            p("2. Technical whitespace and related work", "H1x"),
            p(
                "Transformer encoders such as MiniLM compress self-attention knowledge for efficient "
                "semantic representations [3]. XGBoost supplies a strong tabular relational learner "
                "[4]. Z3 provides satisfiability modulo theories for machine-checkable contradictions "
                "[5]. Conformal risk control extends conformal ideas to bounded monotone risks [6]. "
                "Active feature acquisition studies sequentially obtaining costly missing features "
                "[7]. CARVE does not claim novelty for these components. Its applied systems "
                "contribution is their safety-ordered composition and, more importantly, an empirical "
                "demonstration that most learned complexity should be rejected on this benchmark.",
            ),
            architecture(),
            p(
                "Unlike a generic chargeback responder, CARVE produces an exact span, an authoritative "
                "fact set, a compiled invariant, and a deletion-minimized UNSAT core. LLMs are outside "
                "the evaluation and may only verbalize an existing certificate.",
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("3. FECL-Bench v4.5", "H1x"),
            p(
                "The benchmark is fully synthetic and balanced by construction; it does not estimate "
                "production prevalence. Every causal pair stays within one split. Template family, "
                "entity prefix, and pair identity are split-isolated. TEST was not read until runner, "
                "model, calibration, and artifact hashes were frozen.",
            ),
            table(
                [
                    ["Split", "Cases", "Pair groups", "Families", "Purpose"],
                    ["TRAIN", "1,200", "600", "5", "Fit supervised models"],
                    ["DEV", "320", "160", "3", "Architecture and policy selection"],
                    ["CALIBRATION", "320", "160", "2", "Calibration and CRC threshold"],
                    ["TEST", "480", "240", "5 unseen", "One frozen execution"],
                    ["OOD", "160", "n/a", "8 categories", "Fail-closed safety"],
                ],
                [24 * mm, 20 * mm, 24 * mm, 32 * mm, 70 * mm],
            ),
            p("3.1 Phenomena and evidence", "H2x"),
            p(
                "Cases cover amount mismatch, one-rupee boundaries, partial and cumulative refunds, "
                "currency, RRN, ARN/UTR, refund identity, parent-payment identity, wrong-order "
                "distractors, temporal contradictions, due and overdue promises, stale status, source "
                "disagreement, policy eligibility, negation, Hinglish, OCR corruption, inert prompt "
                "injection, missing evidence, and unseen relation composition. Evidence acquisition "
                "costs range from 1 for authenticated payment/refund state to 25 for a bank statement.",
            ),
            p("3.2 Integrity corrections", "H2x"),
            p(
                "Versions v4 through v4.4 are preserved as invalid drafts. Pre-fit audits found stale "
                "state construction, nonminimal required evidence, a label-directed proof dispatch, "
                "multi-cause pairs, row identity mismatch, and label-dependent invariant names. v4.5 "
                "is the first frozen candidate to pass 9 integrity suites, 1,840 non-TEST label-blind "
                "decision checks, and 920/920 exact contradiction-certificate checks. No v4-family "
                "model was fitted before these corrections.",
            ),
            p("3.3 Leakage controls", "H2x"),
            table(
                [
                    ["Forbidden compiler/model input", "Reason"],
                    ["ground_truth_label / material_contradiction", "Direct target leakage"],
                    ["phenomenon", "Would reveal invariant family"],
                    ["hard_constraints / MCC annotations", "Would reveal expected proof"],
                    [
                        "required_for_resolution / oracle trajectory",
                        "Would reveal acquisition target",
                    ],
                    ["TEST/OOD before final receipt", "Would permit selection on holdout"],
                ],
                [68 * mm, 102 * mm],
            ),
            p("4. Method", "H1x"),
            p("4.1 Grounded relation induction", "H2x"),
            p(
                "Candidate claim spans are exact document substrings. Word/character TF-IDF and a "
                "pinned MiniLM encoder with logistic heads predict semantic relation type; neither "
                "creates offsets. Numeric amounts, identifiers, currencies, and dates are parsed "
                "deterministically. The transformer is promoted only if DEV relation macro-F1 improves "
                "by at least 0.02 and exact-span grounding is at least 0.98.",
            ),
            p("4.2 Formal compiler and MCC", "H2x"),
            p(
                "Applicable invariants are selected from grounded claim content, not benchmark labels. "
                "Tracked Z3 assertions bind the claim value, bind the authoritative value, and impose "
                "the invariant. On UNSAT, deletion minimization removes any assertion whose removal "
                "preserves UNSAT. The resulting three-fact Minimum Contradiction Certificate contains "
                "the exact source span, authoritative evidence ID, invariant ID, and proof hash.",
            ),
        ]
    )

    story.extend(
        [
            p("5. Experimental protocol", "H1x"),
            p(
                "The preregistered ladder is: literal rules; TF-IDF/logistic regression; semantic-only "
                "MiniLM; deterministic relational XGBoost; MiniLM relation features plus XGBoost; "
                "historical ESRAN; formal proof; selective risk control; and acquisition. ESRAN is "
                "reported as historical-not-comparable rather than silently adapted. XGBoost uses "
                "depth 3, 240 estimators, learning rate 0.04, subsample 0.85, column sample 0.9, and "
                "five seeds. False-PASS weight is chosen from {2,4,8} on DEV. Calibration uses only "
                "CALIBRATION. TEST selects nothing.",
            ),
            p(
                "Metrics include precision, recall, F1, PR-AUC, false PASS/BLOCK, synthetic INR "
                "exposure, Brier, NLL, ECE, risk-coverage, relation F1, exact grounding, MCC exact "
                "match, OOD REVIEW, acquisition count/cost, and counterfactual repair. Statistical "
                "tests use exact paired McNemar and 2,000 minimal-pair bootstrap resamples. Intervals "
                "describe only this generator.",
            ),
            p(
                "Algorithm 1: CARVE inference<br/>"
                "1  validate provenance hashes; if invalid return REVIEW<br/>"
                "2  induce grounded relations and parse exact financial attributes<br/>"
                "3  compile applicable invariants into Phi(E_t)<br/>"
                "4  if UNSAT return BLOCK with MCC<br/>"
                "5  if unsupported or OOD return REVIEW<br/>"
                "6  if SAT and calibrated risk certificate permits return PASS<br/>"
                "7  choose minimum-cost missing evidence; reveal it; repeat<br/>"
                "8  append every transition to the audit log",
                "Codex",
            ),
            p("6. Results", "H1x"),
            p("6.1 DEV tournament", "H2x"),
            table(
                metric_rows(DEV["models"]),
                [47 * mm, 13 * mm, 13 * mm, 13 * mm, 17 * mm, 16 * mm, 17 * mm, 34 * mm],
            ),
            p(
                "Literal rules, relational XGBoost, learned-relation XGBoost, and formal proof all "
                "reach DEV F1 1.000. The 2,000-pair bootstrap difference between rules and XGBoost is "
                "0.000 with CI [0.000, 0.000]. Therefore XGBoost and its learned-relation extension "
                "are rejected. Across five XGBoost seeds, F1 standard deviation is 0.000; the hybrid "
                "is less stable, with mean F1 0.988 and standard deviation 0.024.",
            ),
            p(
                "Transformer relation induction improves DEV macro-F1 from 0.719 to 0.907 with exact "
                "span grounding 1.000, passing the relation-specific promotion gate. It does not gain "
                "financial decision authority.",
            ),
            p("6.2 Frozen one-shot TEST", "H2x"),
            table(
                metric_rows(TEST["models"]),
                [47 * mm, 13 * mm, 13 * mm, 13 * mm, 17 * mm, 16 * mm, 17 * mm, 34 * mm],
            ),
            p(
                "The unseen-family TEST separates structural checks from fitted models. Rules and "
                "proof remain at F1 1.000 with zero false PASS and zero false BLOCK. Relational XGBoost "
                "falls to F1 0.748 through 162 false BLOCKs; the learned-relation hybrid reaches 0.762 "
                "with 150 false BLOCKs. Semantic-only MiniLM has 17 false PASS and synthetic exposure "
                "INR 258,489. TF-IDF has 18 false PASS and exposure INR 293,488. The paired McNemar "
                "comparison favors proof over XGBoost on 162 discordant cases (exact p rounded to "
                "0.0 in the artifact). The pair-bootstrap F1 delta for XGBoost minus rules is -0.252, "
                "95% CI [-0.268, -0.236].",
            ),
            p(
                "TEST relation macro-F1 is 0.547 for the transformer versus 0.484 for TF-IDF. The "
                "direction persists but the absolute performance and margin shrink substantially, "
                "supporting only a bounded assistive role.",
            ),
        ]
    )

    story.extend(
        [
            p("7. Selective risk and evidence acquisition", "H1x"),
            p("7.1 Calibration and abstention", "H2x"),
            p(
                "The initial-view residual model is weak: TEST F1 0.384, PR-AUC 0.673, and 183 false "
                "PASS at threshold 0.5. Platt calibration yields TEST ECE 0.029, but calibration alone "
                "does not create safe ranking. Under the preregistered corrected value-weighted risk "
                "target 0.025, CALIBRATION certifies zero PASS coverage. CARVE therefore sets no PASS "
                "threshold. On TEST it autonomously BLOCKs 48 formal contradictions and routes 432 "
                "cases to REVIEW: 10% coverage, zero false PASS, and no manufactured confidence.",
            ),
            risk_curve(),
            p(
                "Figure 1. DEV diagnostic risk-coverage curve. It is not a TEST guarantee.",
                "Smallx",
            ),
            p("7.2 Sequential acquisition", "H2x"),
            table(
                [
                    [
                        "Policy",
                        "TEST cost",
                        "Acquisitions/resolved",
                        "Resolved",
                        "Trajectory exact",
                        "FPASS exposure",
                    ],
                    *[
                        [
                            item["policy"],
                            str(item["acquisition_cost"]),
                            f"{item['acquisitions_per_resolved']:.3f}",
                            f"{item['resolved_cases']}/480",
                            f"{item['trajectory_exact_match']:.3f}",
                            str(item["false_pass_exposure_minor"]),
                        ]
                        for item in TEST["acquisition"]
                    ],
                ],
                [35 * mm, 23 * mm, 34 * mm, 24 * mm, 29 * mm, 28 * mm],
            ),
            p(
                "DEV selects the targeted non-refund-first policy (cost 456 versus cheapest-first "
                "488). Frozen TEST reverses the ranking: targeted costs 996 and cheapest-first 924. "
                "We do not retune after TEST. Both resolve all 480 cases with zero false-PASS exposure; "
                "acquire-all costs 23,294. A learned policy is not trained because a simple policy "
                "already resolves all cases and the preregistration forbids architecture vanity.",
            ),
            p("8. Error analysis and ablations", "H1x"),
            table(
                [
                    ["Ablation / failure", "Observation", "Disposition"],
                    [
                        "Remove formal proof",
                        "XGBoost creates 162 false BLOCK on TEST",
                        "Reject learned authority",
                    ],
                    [
                        "Add learned relations to XGBoost",
                        "F1 0.748 -> 0.762; still below rules",
                        "Reject hybrid",
                    ],
                    [
                        "Semantic classifier only",
                        "17 false PASS; INR 258,489 exposure",
                        "Research only",
                    ],
                    ["Residual risk at 0.5", "183 false PASS", "Never use raw threshold"],
                    ["CRC PASS", "0 certified coverage", "Reject PASS automation"],
                    [
                        "DEV-selected acquisition",
                        "Loses cost ranking on TEST",
                        "Retain frozen result",
                    ],
                    [
                        "OOD controller",
                        "160/160 REVIEW; 0 false PASS",
                        "Retain fail-closed boundary",
                    ],
                ],
                [48 * mm, 77 * mm, 45 * mm],
            ),
            p(
                "The perfect rule/proof result is not evidence of production perfection. It indicates "
                "that v4.5's synthetic contradictions are exactly represented by its explicit "
                "invariants. The benchmark is valuable for falsifying unnecessary learned authority "
                "but insufficient for claiming general payment-risk performance.",
            ),
        ]
    )

    story.extend(
        [
            p("9. Deployment and safety architecture", "H1x"),
            p(
                "Production order is provenance validation -> semantic relation extraction -> "
                "deterministic verification and proof -> interpretable features -> optional residual "
                "risk ranking -> selective controller -> PASS/BLOCK/REVIEW -> evidence acquisition -> "
                "append-only audit. Authoritative payment and refund exports are immutable inputs. "
                "Every evidence artifact carries a SHA-256 digest; mismatch returns REVIEW. Requests "
                "are idempotent and no component can initiate a refund, debit, acceptance, submission, "
                "or other financial write.",
            ),
            p("9.1 Analyst interaction", "H2x"),
            p(
                "The product begins with an incomplete case. CARVE names the minimum missing evidence "
                "and its acquisition cost. After acquisition, the same compiler either proves an exact "
                "contradiction and shows its MCC or returns SAT. Findings link to exact source offsets "
                "and authoritative facts. Counterfactual repair changes one causal fact and recomputes "
                "the decision; it never rewrites history or performs an autonomous financial action.",
            ),
            p("9.2 Threat model", "H2x"),
            table(
                [
                    ["Threat", "Response"],
                    [
                        "Prompt injection in evidence",
                        "Treat as inert text; only grounded claims compile",
                    ],
                    ["Model outage", "REVIEW; no fallback PASS"],
                    ["Malformed amount / OCR", "Reject or REVIEW at parser boundary"],
                    ["Missing ledger state", "REVIEW and acquire authoritative state"],
                    ["Hash mismatch", "REVIEW before any semantic or financial check"],
                    ["OOD language / schema", "REVIEW; 160/160 constructed OOD rejected"],
                    ["Hostile learned score", "Cannot override UNSAT or failed invariant"],
                ],
                [54 * mm, 116 * mm],
            ),
            p("10. Limitations", "H1x"),
            p(
                "All counts and currency values are synthetic. Balanced class prevalence, explicit "
                "templates, clean structured payloads, and known evidence costs limit external "
                "validity. The relation taxonomy is narrow. The CRC calculation is a preregistered "
                "empirical controller, not a guarantee under distribution shift; indeed it certifies "
                "no PASS. OOD categories are constructed rather than sampled from deployment. We do "
                "not evaluate multilingual Indian language coverage beyond synthetic Hinglish, bank "
                "network latency, access-control failures, or adversarial corruption of authoritative "
                "systems. No claim of novelty, merchant savings, production readiness, or dispute-win "
                "improvement follows from this study.",
            ),
            p("11. Conclusion", "H1x"),
            p(
                "CARVE's strongest result is a rejection. Learned relations help interpret language, "
                "but modern classifiers and relational boosting do not beat a strong deterministic "
                "baseline for exact synthetic financial consistency. Risk control refuses to certify "
                "PASS. The surviving system is smaller: grounded semantic assistance, immutable "
                "financial invariants, formal contradiction certificates, fail-closed REVIEW, and a "
                "simple evidence policy. That is a more credible fintech AI contribution than a "
                "larger model stack.",
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("References", "H1x"),
            p(
                "[1] Razorpay. Submit Evidence for Disputes. https://razorpay.com/docs/payments/disputes/submit-evidence/",
                "Smallx",
            ),
            p(
                "[2] Razorpay. Refunds and Customer Refunds. https://razorpay.com/docs/payments/refunds/",
                "Smallx",
            ),
            p(
                "[3] W. Wang et al. MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers. NeurIPS 2020. https://proceedings.neurips.cc/paper/2020/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html",
                "Smallx",
            ),
            p(
                "[4] T. Chen and C. Guestrin. XGBoost: A Scalable Tree Boosting System. KDD 2016, pp. 785-794. DOI 10.1145/2939672.2939785.",
                "Smallx",
            ),
            p(
                "[5] L. de Moura and N. Bjorner. Z3: An Efficient SMT Solver. TACAS 2008, pp. 337-340. DOI 10.1007/978-3-540-78800-3_24.",
                "Smallx",
            ),
            p(
                "[6] A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei, and T. Schuster. Conformal Risk Control. arXiv:2208.02814, 2022. https://arxiv.org/abs/2208.02814",
                "Smallx",
            ),
            p(
                "[7] O. B. Guney et al. Active Feature Acquisition via Explainability-Driven Ranking. ICML 2025, PMLR 267:20748-20765. https://proceedings.mlr.press/v267/guney25a.html",
                "Smallx",
            ),
            p("Appendix A. Reproducibility record", "H1x"),
            table(
                [
                    ["Artifact", "SHA-256"],
                    *[[name, digest] for name, digest in MANIFEST["hashes"].items()],
                    [
                        "frozen TEST result",
                        hashlib.sha256(
                            (ARTIFACTS / "frozen-test-results.json").read_bytes()
                        ).hexdigest(),
                    ],
                    [
                        "frozen TEST receipt",
                        hashlib.sha256(
                            (ARTIFACTS / "frozen-test-receipt.json").read_bytes()
                        ).hexdigest(),
                    ],
                ],
                [45 * mm, 125 * mm],
            ),
            p(
                "Reproduction commands:<br/>"
                "uv sync --extra research --extra dev<br/>"
                "python scripts/generate_fecl_v4_2.py  # preserved generator for final v4.5<br/>"
                "python -m pytest backend/tests/test_fecl_v4_2_integrity.py backend/tests/test_carve_proof.py -q<br/>"
                "python scripts/run_carve_v4.py dev<br/>"
                "python scripts/run_carve_v4.py test --confirm-frozen-test YES  # receipt prevents rerun",
                "Codex",
            ),
            p(
                f"Receipt status: {RECEIPT['status']}. The final TEST command cannot be re-executed "
                "without deleting the receipt, which would be an explicit integrity violation.",
            ),
            p("Appendix B. Reproducibility checklist", "H1x"),
            table(
                [
                    ["Item", "Status"],
                    ["Hypotheses and promotion gates preregistered", "Yes"],
                    ["TRAIN/DEV/CALIBRATION/TEST/OOD family isolation", "Yes"],
                    ["Causal pairs kept within splits", "Yes"],
                    ["Generator seed and five stochastic seeds recorded", "Yes"],
                    ["Model and feature schema serialized", "Yes"],
                    ["Protocol, data, code, models, calibration frozen before TEST", "Yes"],
                    ["Single TEST receipt", "Yes"],
                    ["Negative and rejected methods reported", "Yes"],
                    ["Synthetic-data and no-savings boundary", "Yes"],
                    ["External production validation", "No"],
                ],
                [115 * mm, 55 * mm],
            ),
        ]
    )
    document.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
