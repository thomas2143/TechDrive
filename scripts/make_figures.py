"""
Draw the two figures the report embeds.

Kept separate from run_all.py so a figure can be redrawn without repeating the
repeated-trials section, which is where nearly all the runtime lives.
"""

import sys

sys.path.insert(0, "src")

import matplotlib  # backend must be selected before pyplot loads

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from classifier import RetrievalClassifier
from conformal import calibrate_fixed_sequence, calibrate_naive
from data import load_reuters
from drift import tail_shifted_indices, taxonomy_shift, total_variation
from encoder import TfidfSvdEncoder

K, POWER, ALPHA = 15, 5.0, 0.05
INSTRUMENT, BOUND, MUTED = "#1F5673", "#B22D1F", "#7A9CC6"

plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150})


def prepare():
    corpus = load_reuters()
    encoder = TfidfSvdEncoder().fit(corpus.index.texts)
    clf = RetrievalClassifier(k=K, power=POWER).fit(
        encoder.encode(corpus.index.texts), corpus.index.labels, corpus.n_classes
    )
    pred_c, conf_c = clf.predict(encoder.encode(corpus.calibration.texts))
    pred_t, conf_t = clf.predict(encoder.encode(corpus.test.texts))
    return {
        "corpus": corpus,
        "correct_cal": pred_c == corpus.calibration.labels,
        "conf_cal": conf_c,
        "pred_test": pred_t,
        "correct_test": pred_t == corpus.test.labels,
        "conf_test": conf_t,
    }


def figure_dial(d, certified):
    """Precision against coverage, with the certified and tuned operating points."""
    fig, ax = plt.subplots(figsize=(7, 4.2))

    coverage, precision = [], []
    for theta in np.linspace(0, 0.995, 200):
        accepted = d["conf_test"] > theta
        if accepted.sum() < 30:
            continue
        coverage.append(accepted.mean() * 100)
        precision.append(d["correct_test"][accepted].mean() * 100)
    ax.plot(coverage, precision, lw=1.8, color=INSTRUMENT, label="achievable operating points")

    for alpha, marker in [(0.05, "o"), (0.03, "s"), (0.02, "^")]:
        result = calibrate_fixed_sequence(d["correct_cal"], d["conf_cal"], alpha=alpha)
        if not result.certified:
            continue
        accepted = d["conf_test"] > result.threshold
        ax.scatter(
            [accepted.mean() * 100], [d["correct_test"][accepted].mean() * 100],
            s=70, marker=marker, zorder=5, label=f"certified at {(1 - alpha) * 100:.0f}% target",
        )
        ax.axhline((1 - alpha) * 100, ls=":", lw=0.8, color="grey")

    naive = calibrate_naive(d["correct_cal"], d["conf_cal"], alpha=ALPHA)
    accepted = d["conf_test"] > naive.threshold
    ax.scatter(
        [accepted.mean() * 100], [d["correct_test"][accepted].mean() * 100],
        s=80, marker="x", color=BOUND, zorder=5, label="tuned threshold, 95% target",
    )

    ax.set_xlabel("coverage: share of tickets routed automatically (%)")
    ax.set_ylabel("precision on routed tickets (%)")
    ax.set_title("Precision is chosen, coverage is what the data returns")
    ax.legend(fontsize=7.5, loc="lower left")
    fig.tight_layout()
    fig.savefig("reports/fig1_dial.png")
    plt.close(fig)


def figure_drift(d, certified):
    """The two drift modes side by side. Only one of them is visible from inside."""
    corpus = d["corpus"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.2))

    distances, mix_risk, mix_cov = [], [], []
    for severity in np.linspace(0, 1.95, 12):
        idx = tail_shifted_indices(corpus.test.labels, severity=float(severity), seed=7)
        distances.append(total_variation(corpus.test.labels, corpus.test.labels[idx], corpus.n_classes))
        accepted = d["conf_test"][idx] > certified.threshold
        mix_risk.append((~d["correct_test"][idx][accepted]).mean() * 100)
        mix_cov.append(accepted.mean() * 100)

    left.plot(distances, mix_risk, "o-", lw=1.8, color=INSTRUMENT, label="error rate")
    left.plot(distances, mix_cov, "s--", lw=1.4, color=MUTED, label="coverage")
    left.axhline(ALPHA * 100, color=BOUND, ls="--", lw=1.2, label="certified bound")
    left.set_xlabel("total variation distance of the class mix")
    left.set_ylabel("percent")
    left.set_title("Mix shift: coverage falls, guarantee holds")
    left.set_ylim(0, 100)
    left.legend(fontsize=7.5, loc="center left")

    fractions = [0, 0.02, 0.05, 0.08, 0.12, 0.20, 0.30]
    tax_risk, tax_cov = [], []
    for fraction in fractions:
        moved = taxonomy_shift(corpus.test.labels, fraction, corpus.n_classes)
        accepted = d["conf_test"] > certified.threshold
        tax_risk.append((d["pred_test"][accepted] != moved[accepted]).mean() * 100)
        tax_cov.append(accepted.mean() * 100)

    right.plot(np.array(fractions) * 100, tax_risk, "o-", lw=1.8, color=BOUND, label="error rate")
    right.plot(np.array(fractions) * 100, tax_cov, "s--", lw=1.4, color=MUTED, label="coverage")
    right.axhline(ALPHA * 100, color=BOUND, ls="--", lw=1.2, label="certified bound")
    right.set_xlabel("percent of the largest category redefined")
    right.set_title("Taxonomy shift: coverage flat, guarantee breaks")
    right.set_ylim(0, 100)
    right.legend(fontsize=7.5, loc="center left")

    fig.suptitle("Only one of these two drift modes is visible from inside the system", fontsize=10)
    fig.tight_layout()
    fig.savefig("reports/fig2_drift.png")
    plt.close(fig)


def main():
    d = prepare()
    certified = calibrate_fixed_sequence(d["correct_cal"], d["conf_cal"], alpha=ALPHA)
    figure_dial(d, certified)
    figure_drift(d, certified)
    print("figures written")


if __name__ == "__main__":
    main()
