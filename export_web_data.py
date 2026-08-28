"""
Export everything the static page needs.

The page has no backend, so every curve it can draw must be precomputed here.
Rather than shipping raw per-item scores, we ship, for each condition, the
coverage and error rate evaluated on a fixed threshold grid. That is a few
kilobytes instead of a few hundred, and it is the only thing the interface
ever needs to look up.

The certified thresholds come from the same calibration path as run_all.py,
so what the page reports as certified is what the harness certified.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from classifier import RetrievalClassifier, tune
from conformal import calibrate_fixed_sequence, calibrate_naive
from data import load_reuters
from drift import tail_shifted_indices, taxonomy_shift, total_variation
from encoder import TfidfSvdEncoder

GRID = np.round(np.arange(0.0, 1.0, 0.01), 3)  # certified thresholds are spliced in below
TARGETS = [0.10, 0.05, 0.03, 0.02, 0.01]
DELTA = 0.10


def build_grid(thresholds: list[float]) -> np.ndarray:
    """
    The coarse grid plus the exact certified thresholds.

    Without this the page snaps a certified threshold to the nearest grid
    point and reports figures that differ slightly from the report for no
    reason a reader could work out. Splicing the real thresholds in makes the
    page read the exact certified operating point.
    """
    return np.array(sorted(set(np.round(np.arange(0.0, 1.0, 0.01), 3)) | set(thresholds)))


def curve(correct: np.ndarray, confidence: np.ndarray) -> dict:
    """Coverage and error rate at every grid threshold. None where nothing is accepted."""
    coverage, risk = [], []
    for theta in GRID:
        accepted = confidence > theta
        n = int(accepted.sum())
        coverage.append(round(float(accepted.mean()), 5))
        risk.append(round(float((~correct[accepted]).mean()), 5) if n else None)
    return {"coverage": coverage, "risk": risk}


def main() -> None:
    corpus = load_reuters()
    encoder = TfidfSvdEncoder().fit(corpus.index.texts)
    index_vectors = encoder.encode(corpus.index.texts)

    best, _ = tune(index_vectors, corpus.index.labels, corpus.n_classes)
    clf = RetrievalClassifier(k=best["k"], power=best["power"]).fit(
        index_vectors, corpus.index.labels, corpus.n_classes
    )

    pred_c, conf_c = clf.predict(encoder.encode(corpus.calibration.texts))
    correct_c = pred_c == corpus.calibration.labels
    test_vectors = encoder.encode(corpus.test.texts)
    pred_t, conf_t = clf.predict(test_vectors)
    correct_t = pred_t == corpus.test.labels

    # first pass: find the thresholds, so they can be spliced into the grid
    thresholds = []
    for alpha in TARGETS:
        for r in (calibrate_fixed_sequence(correct_c, conf_c, alpha=alpha, delta=DELTA),
                  calibrate_naive(correct_c, conf_c, alpha=alpha)):
            if r.certified:
                thresholds.append(round(r.threshold, 3))

    global GRID
    GRID = build_grid(thresholds)

    out = {
        "meta": {
            "classes": corpus.n_classes,
            "index": len(corpus.index),
            "calibration": len(corpus.calibration),
            "test": len(corpus.test),
            "k": best["k"],
            "power": best["power"],
            "accuracy": round(float(correct_t.mean()), 4),
            "delta": DELTA,
        },
        "grid": [float(g) for g in GRID],
        "base": curve(correct_t, conf_t),
        "certified": {},
        "naive": {},
    }

    for alpha in TARGETS:
        key = f"{alpha:.2f}"
        r = calibrate_fixed_sequence(correct_c, conf_c, alpha=alpha, delta=DELTA)
        if r.certified:
            accepted = conf_t > r.threshold
            out["certified"][key] = {
                "theta": round(r.threshold, 3),
                "coverage": round(float(accepted.mean()), 5),
                "risk": round(float((~correct_t[accepted]).mean()), 5),
            }
        else:
            out["certified"][key] = None

        n = calibrate_naive(correct_c, conf_c, alpha=alpha)
        if n.certified:
            accepted = conf_t > n.threshold
            out["naive"][key] = {
                "theta": round(n.threshold, 3),
                "coverage": round(float(accepted.mean()), 5),
                "risk": round(float((~correct_t[accepted]).mean()), 5),
            }
        else:
            out["naive"][key] = None

    # drift mode 1: the class mix moves
    out["mix"] = []
    for severity in [0.0, 0.3, 0.8, 1.2, 1.6, 1.95]:
        idx = tail_shifted_indices(corpus.test.labels, severity=float(severity), seed=7)
        out["mix"].append({
            "severity": float(severity),
            "tv": round(total_variation(corpus.test.labels, corpus.test.labels[idx], corpus.n_classes), 3),
            **curve(correct_t[idx], conf_t[idx]),
        })

    # drift mode 2: the taxonomy is redefined. Predictions untouched, truth moves.
    out["taxonomy"] = []
    for fraction in [0.0, 0.02, 0.05, 0.08, 0.12, 0.20, 0.30]:
        moved = taxonomy_shift(corpus.test.labels, fraction, corpus.n_classes)
        out["taxonomy"].append({"fraction": float(fraction), **curve(pred_t == moved, conf_t)})

    # a handful of real decisions with the archive documents behind them
    out["evidence"] = []
    predictions = clf.predict_with_evidence(test_vectors[:400], top_n=3)
    wanted_routed, wanted_held = 3, 2
    for i, p in enumerate(predictions):
        certified_95 = out["certified"]["0.05"]
        routed = certified_95 is not None and p.confidence > certified_95["theta"]
        if routed and wanted_routed == 0:
            continue
        if not routed and wanted_held == 0:
            continue
        text = " ".join(corpus.test.texts[i].split())
        out["evidence"].append({
            "excerpt": text[:260] + ("..." if len(text) > 260 else ""),
            "predicted": corpus.class_names[p.label],
            "true": corpus.class_names[corpus.test.labels[i]],
            "confidence": round(p.confidence, 3),
            "routed": routed,
            "neighbours": [
                {
                    "category": corpus.class_names[cls],
                    "similarity": round(sim, 3),
                    "excerpt": " ".join(corpus.index.texts[pos].split())[:150] + "...",
                }
                for pos, cls, sim in p.evidence
            ],
        })
        if routed:
            wanted_routed -= 1
        else:
            wanted_held -= 1
        if wanted_routed == 0 and wanted_held == 0:
            break

    out["trials"] = json.loads((ROOT / "reports" / "results.json").read_text())["trials"]

    target = ROOT / "web" / "data.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {target} ({target.stat().st_size / 1024:.1f} KB)")
    print(f"  certified at 95%: theta {out['certified']['0.05']['theta']}, "
          f"coverage {out['certified']['0.05']['coverage']:.1%}")
    print(f"  evidence samples: {len(out['evidence'])}")


if __name__ == "__main__":
    main()
