"""
Regenerate every number and figure in reports/REPORT.md.

    python run_all.py

Everything the report claims is produced here. If a figure in the report has
no counterpart in this file, the report is claiming something that was not
measured by anything anyone can rerun.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from classifier import RetrievalClassifier, tune
from conformal import (
    apply_per_class,
    bernstein_upper_bound,
    calibrate_fixed_sequence,
    calibrate_naive,
    calibrate_per_class,
    calibrate_threshold,
    measure_non_monotonicity,
)
from data import Corpus, describe, load_reuters, load_reuters_temporal
from drift import tail_shifted_indices, taxonomy_shift, total_variation
from encoder import TfidfSvdEncoder

REPORTS = Path(__file__).resolve().parent / "reports"
TARGETS = [0.10, 0.05, 0.03, 0.02, 0.01]
GRID_ANALYTICS = np.round(np.arange(0.0, 1.0, 0.005), 3)
DELTA = 0.10
TRIALS = 15


def score(corpus: Corpus, k: int, power: float):
    """Fit on index, score calibration and test. The encoder never sees either."""
    encoder = TfidfSvdEncoder().fit(corpus.index.texts)
    clf = RetrievalClassifier(k=k, power=power).fit(
        encoder.encode(corpus.index.texts), corpus.index.labels, corpus.n_classes
    )
    pred_c, conf_c = clf.predict(encoder.encode(corpus.calibration.texts))
    pred_t, conf_t = clf.predict(encoder.encode(corpus.test.texts))
    return {
        "encoder": encoder,
        "clf": clf,
        "pred_cal": pred_c,
        "pred_test": pred_t,
        "correct_cal": pred_c == corpus.calibration.labels,
        "conf_cal": conf_c,
        "correct_test": pred_t == corpus.test.labels,
        "conf_test": conf_t,
    }


def evaluate(threshold: float, correct: np.ndarray, confidence: np.ndarray) -> dict:
    accepted = confidence > threshold
    if accepted.sum() == 0:
        return {"coverage": 0.0, "risk": float("nan")}
    return {"coverage": float(accepted.mean()), "risk": float((~correct[accepted]).mean())}


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    out: dict = {}

    print("=" * 70)
    print("1. CORPUS")
    print("=" * 70)
    corpus = load_reuters()
    print(describe(corpus))
    out["corpus"] = {
        "classes": corpus.n_classes,
        "index": len(corpus.index),
        "calibration": len(corpus.calibration),
        "test": len(corpus.test),
    }

    print()
    print("=" * 70)
    print("2. HYPERPARAMETERS  (selected on a held-out slice of INDEX only)")
    print("=" * 70)
    encoder = TfidfSvdEncoder().fit(corpus.index.texts)
    best, _ = tune(encoder.encode(corpus.index.texts), corpus.index.labels, corpus.n_classes)
    k, power = best["k"], best["power"]
    print(f"  k = {k}, power = {power}  (rank-score {best['score']:.4f})")
    out["hyperparameters"] = best

    s = score(corpus, k, power)
    print(f"  unconditional accuracy: calibration {s['correct_cal'].mean():.3f} "
          f"test {s['correct_test'].mean():.3f}")
    out["unconditional_accuracy"] = {
        "calibration": float(s["correct_cal"].mean()),
        "test": float(s["correct_test"].mean()),
    }

    print()
    print("=" * 70)
    print("3. THE DIAL  (precision is chosen, coverage is measured)")
    print("=" * 70)
    print(f"{'target':>7} | {'method':<20} | {'theta':>6} | {'coverage':>8} | {'risk':>6} | verdict")
    print("-" * 74)
    methods = {
        "fixed sequence": lambda a: calibrate_fixed_sequence(s["correct_cal"], s["conf_cal"], alpha=a, delta=DELTA),
        "Bonferroni grid": lambda a: calibrate_threshold(s["correct_cal"], s["conf_cal"], alpha=a, delta=DELTA),
        "naive tuning": lambda a: calibrate_naive(s["correct_cal"], s["conf_cal"], alpha=a),
    }
    out["dial"] = {}
    for alpha in TARGETS:
        out["dial"][str(alpha)] = {}
        for name, fn in methods.items():
            r = fn(alpha)
            if not r.certified:
                print(f"{1-alpha:>6.0%}  | {name:<20} |      - |        - |      - | abstains")
                out["dial"][str(alpha)][name] = {"certified": False}
                continue
            e = evaluate(r.threshold, s["correct_test"], s["conf_test"])
            verdict = "holds" if e["risk"] <= alpha else "VIOLATED"
            print(f"{1-alpha:>6.0%}  | {name:<20} | {r.threshold:>6.3f} | "
                  f"{e['coverage']:>7.1%} | {e['risk']:>5.3f} | {verdict}")
            out["dial"][str(alpha)][name] = {"certified": True, "threshold": r.threshold, **e}
        print()

    print("=" * 70)
    print("3b. ANALYTICS QUALITY  (the brief asks for 95% precision and 100% clean analytics)")
    print("=" * 70)
    print("  Composite = share of ALL tickets that end up correctly tagged.")
    print("  Auto-routed tickets are tagged at model precision; the rest by first line.")
    print("  The first-line rate is an assumption, not a measurement here, so it is swept.")
    print()
    out["analytics"] = {}
    for human in (0.75, 0.85, 0.95):
        best = (0.0, 0.0, 0.0)
        for theta in GRID_ANALYTICS:
            accepted = s["conf_test"] > theta
            c = float(accepted.mean())
            if c < 0.05:
                continue
            p_model = float(s["correct_test"][accepted].mean())
            composite = c * p_model + (1 - c) * human
            if composite > best[0]:
                best = (composite, c, p_model)
        full = float(s["correct_test"].mean())
        print(f"  first line at {human:.0%}")
        print(f"    best composite   {best[0]:.1%}  at coverage {best[1]:.1%}, model precision {best[2]:.1%}")
        print(f"    full automation  {full:.1%}")
        print(f"    all manual       {human:.1%}")
        out["analytics"][f"{human:.2f}"] = {
            "best_composite": round(best[0], 5),
            "at_coverage": round(best[1], 5),
            "at_precision": round(best[2], 5),
            "full_automation": round(full, 5),
            "all_manual": human,
        }
    print()
    print("  No operating point reaches 100%. Raising precision past the optimum lowers")
    print("  composite quality, because every ticket withheld goes to the less accurate path.")

    print()
    print("=" * 70)
    print("3c. PER-CATEGORY CERTIFICATION  (what a single global threshold hides)")
    print("=" * 70)
    print("  A global threshold is set by the categories carrying the volume. The long")
    print("  tail rides underneath it, auto-routed on a guarantee never established for")
    print("  those categories. Certifying each class on its own calibration items removes")
    print("  that, and most classes then fail to certify.")
    print()
    counts = Counter(s["pred_cal"].tolist())
    out["per_class"] = {}
    for alpha in (0.05, 0.03):
        globally = calibrate_fixed_sequence(s["correct_cal"], s["conf_cal"], alpha=alpha, delta=DELTA)
        per = calibrate_per_class(
            s["pred_cal"], s["correct_cal"], s["conf_cal"], corpus.n_classes,
            alpha=alpha, delta=DELTA,
        )
        certified = [c for c, r in per.items() if r.routes_anything]
        accepted = apply_per_class(s["pred_test"], s["conf_test"], per)

        g = evaluate(globally.threshold, s["correct_test"], s["conf_test"])
        risk = float((~s["correct_test"][accepted]).mean()) if accepted.any() else float("nan")
        print(f"  target {1 - alpha:.0%}")
        print(f"    one global threshold : coverage {g['coverage']:>6.1%}  error {g['risk']:.3f}")
        print(f"    per category         : coverage {accepted.mean():>6.1%}  error {risk:.3f}")
        print(f"    categories certified : {len(certified)} of {len(per)}")
        if certified:
            sizes = sorted(counts[c] for c in certified)
            print(f"      certified classes hold {sizes[0]} calibration items or more")
        others = sorted(counts[c] for c in per if c not in certified)
        if others:
            print(f"      uncertified classes: median {int(np.median(others))} items, largest {others[-1]}")

        # how many items would a class need, in the most favourable case possible
        floor_n = 2
        while floor_n < 20000 and bernstein_upper_bound(np.zeros(floor_n), DELTA / len(per)) > alpha:
            floor_n += 1
        unsplit = 2
        while unsplit < 20000 and bernstein_upper_bound(np.zeros(unsplit), DELTA) > alpha:
            unsplit += 1
        print(f"    minimum calibration items for any class to certify: {floor_n}")
        print(f"      ({unsplit} without the across-class correction, so sample size binds, not multiplicity)")
        out["per_class"][f"{alpha:.2f}"] = {
            "global_coverage": g["coverage"], "global_risk": g["risk"],
            "per_class_coverage": round(float(accepted.mean()), 5),
            "per_class_risk": round(risk, 5) if accepted.any() else None,
            "certified": len(certified), "classes": len(per),
            "min_items_to_certify": floor_n, "min_items_unsplit": unsplit,
        }
        print()

    print()
    print("=" * 70)
    print("4. EVIDENCE  (what a routed ticket carries with it)")
    print("=" * 70)
    r95 = calibrate_fixed_sequence(s["correct_cal"], s["conf_cal"], alpha=0.05, delta=DELTA)
    s_pred_test = s["pred_test"]
    vectors = s["encoder"].encode(corpus.test.texts[:200])
    predictions = s["clf"].predict_with_evidence(vectors, top_n=3)
    shown = 0
    out["evidence_samples"] = []
    for i, p in enumerate(predictions):
        routed = p.confidence > r95.threshold
        if shown >= 3 or (shown >= 1 and routed):
            continue
        truth = corpus.class_names[corpus.test.labels[i]]
        print(f"\n  ticket #{i}  ->  {corpus.class_names[p.label]}  "
              f"(confidence {p.confidence:.3f}, "
              f"{'auto-routed' if routed else 'manual moderation'}, true class {truth})")
        for pos, cls, sim in p.evidence:
            print(f"      because index doc {pos:>5} [{corpus.class_names[cls]}] similarity {sim:.3f}")
        out["evidence_samples"].append({
            "predicted": corpus.class_names[p.label],
            "true": truth,
            "confidence": p.confidence,
            "routed": routed,
            "evidence": [[int(a), corpus.class_names[b], float(c)] for a, b, c in p.evidence],
        })
        shown += 1

    print()
    print("=" * 70)
    print("5. NON-MONOTONICITY  (reported with its magnitude, not just its frequency)")
    print("=" * 70)
    nm = measure_non_monotonicity(s["correct_cal"], s["conf_cal"])
    print(f"  risk increases at {nm['increases']}/{nm['steps']} grid steps "
          f"({nm['increase_fraction']:.1%}), largest single increase {nm['max_increase']:+.5f}")
    out["non_monotonicity"] = {kk: vv for kk, vv in nm.items() if kk not in ("thetas", "risks")}

    print()
    print("=" * 70)
    print("6. DRIFT  (where the certified guarantee stops holding)")
    print("=" * 70)
    print("  6a. natural temporal split")
    temporal = load_reuters_temporal()
    st = score(temporal, k, power)
    out["temporal"] = {}
    for alpha in [0.10, 0.05, 0.03]:
        r = calibrate_fixed_sequence(st["correct_cal"], st["conf_cal"], alpha=alpha, delta=DELTA)
        if not r.certified:
            print(f"      target {1-alpha:>4.0%}: abstains")
            continue
        e = evaluate(r.threshold, st["correct_test"], st["conf_test"])
        print(f"      target {1-alpha:>4.0%}: coverage {e['coverage']:>5.1%} risk {e['risk']:.3f}  "
              f"{'holds' if e['risk'] <= alpha else 'VIOLATED'}")
        out["temporal"][str(alpha)] = e

    print("\n  6b. MODE 1: class mix shifts. Threshold certified once, never recalibrated.")
    print(f"      {'severity':>8} | {'TV dist':>8} | {'coverage':>8} | {'risk':>6} | status")
    out["drift"] = []
    breach = None
    for severity in [0.0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 1.75, 1.95]:
        idx = tail_shifted_indices(corpus.test.labels, severity=severity, seed=7)
        tv = total_variation(corpus.test.labels, corpus.test.labels[idx], corpus.n_classes)
        e = evaluate(r95.threshold, s["correct_test"][idx], s["conf_test"][idx])
        broken = e["risk"] > 0.05
        if broken and breach is None:
            breach = (severity, tv)
        print(f"      {severity:>8.2f} | {tv:>8.3f} | {e['coverage']:>7.1%} | {e['risk']:>5.3f} | "
              f"{'BROKEN' if broken else 'holds'}")
        out["drift"].append({"severity": severity, "tv": tv, **e})
    if breach:
        print(f"      first breach at severity {breach[0]}, total variation {breach[1]:.3f}")
        out["drift_breach"] = {"severity": breach[0], "tv": breach[1]}
    else:
        print("      no breach at any shift tested: abstention absorbs it, coverage pays")
        out["drift_breach"] = None

    print("\n  6c. MODE 2: taxonomy is redefined. Same threshold, never recalibrated.")
    print(f"      {'relabelled':>10} | {'coverage':>8} | {'risk':>6} | status")
    out["taxonomy_drift"] = []
    tax_breach = None
    for fraction in [0.0, 0.02, 0.05, 0.08, 0.12, 0.20, 0.30]:
        moved_truth = taxonomy_shift(corpus.test.labels, fraction, corpus.n_classes)
        # predictions and confidences are untouched: only the truth moved
        correct_after = s_pred_test == moved_truth
        e = evaluate(r95.threshold, correct_after, s["conf_test"])
        broken = e["risk"] > 0.05
        if broken and tax_breach is None:
            tax_breach = fraction
        print(f"      {fraction:>9.0%} | {e['coverage']:>7.1%} | {e['risk']:>5.3f} | "
              f"{'BROKEN' if broken else 'holds'}")
        out["taxonomy_drift"].append({"fraction": fraction, **e})
    if tax_breach is not None:
        print(f"      breaks once {tax_breach:.0%} of the largest category is redefined,")
        print("      with coverage unchanged throughout: nothing internal detects it")
        out["taxonomy_breach"] = tax_breach

    print()
    print("=" * 70)
    print(f"7. REPEATED TRIALS  ({TRIALS} independent splits, delta = {DELTA})")
    print("=" * 70)
    stats = {a: {m: {"certified": 0, "breaches": 0, "cov": [], "risk": []}
                 for m in ("fixed sequence", "Bonferroni grid", "naive tuning")}
             for a in (0.05, 0.03)}
    for t in range(TRIALS):
        ct = load_reuters(seed=1000 + t)
        sc = score(ct, k, power)
        for alpha, per_method in stats.items():
            for name, fn in (
                # sc is bound as a default so the closure cannot silently pick
                # up a later trial's scores if the call is ever deferred
                ("fixed sequence", lambda a, sc=sc: calibrate_fixed_sequence(sc["correct_cal"], sc["conf_cal"], alpha=a, delta=DELTA)),
                ("Bonferroni grid", lambda a, sc=sc: calibrate_threshold(sc["correct_cal"], sc["conf_cal"], alpha=a, delta=DELTA)),
                ("naive tuning", lambda a, sc=sc: calibrate_naive(sc["correct_cal"], sc["conf_cal"], alpha=a)),
            ):
                r = fn(alpha)
                if not r.certified:
                    continue
                e = evaluate(r.threshold, sc["correct_test"], sc["conf_test"])
                if e["coverage"] == 0:
                    continue
                d = per_method[name]
                d["certified"] += 1
                d["cov"].append(e["coverage"])
                d["risk"].append(e["risk"])
                if e["risk"] > alpha:
                    d["breaches"] += 1
        print(f"  trial {t+1}/{TRIALS}", flush=True)

    print()
    print(f"{'target':>7} | {'method':<20} | {'certified':>9} | {'breaches':>8} | {'mean cov':>8}")
    print("-" * 66)
    out["trials"] = {}
    for alpha, per_method in stats.items():
        out["trials"][str(alpha)] = {}
        for name, d in per_method.items():
            if d["certified"] == 0:
                print(f"{1-alpha:>6.0%}  | {name:<20} | {'0':>9} | {'-':>8} | {'-':>8}")
                out["trials"][str(alpha)][name] = {"certified": 0}
                continue
            rate = d["breaches"] / d["certified"]
            print(f"{1-alpha:>6.0%}  | {name:<20} | {d['certified']:>4}/{TRIALS:<4} | "
                  f"{rate:>7.0%} | {np.mean(d['cov']):>7.1%}")
            out["trials"][str(alpha)][name] = {
                "certified": d["certified"],
                "breach_rate": rate,
                "mean_coverage": float(np.mean(d["cov"])),
                "mean_risk": float(np.mean(d["risk"])),
            }
        print()

    (REPORTS / "results.json").write_text(json.dumps(out, indent=2))
    print(f"results written to {REPORTS / 'results.json'}")

    import make_figures

    make_figures.main()


if __name__ == "__main__":
    main()
