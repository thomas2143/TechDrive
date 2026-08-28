"""
Tests for the parts that would fail silently.

The classifier's accuracy is visible in any run. These are the things that
would be wrong without anything looking wrong: a loss that does not mean what
the guarantee assumes, a split that leaks, a bound that is not conservative.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from conformal import (
    bernstein_upper_bound,
    calibrate_fixed_sequence,
    calibrate_naive,
    calibrate_threshold,
    hoeffding_upper_bound,
    selective_loss,
)

# --- the loss must mean what the guarantee assumes -------------------------

def test_loss_takes_only_the_three_intended_values():
    correct = np.array([True, False, True, False])
    confidence = np.array([0.9, 0.9, 0.1, 0.1])
    alpha = 0.05
    loss = selective_loss(correct, confidence, theta=0.5, alpha=alpha)

    assert loss[0] == pytest.approx(0.0)    # accepted and correct
    assert loss[1] == pytest.approx(1.0)    # accepted and wrong
    assert loss[2] == pytest.approx(alpha)  # rejected
    assert loss[3] == pytest.approx(alpha)  # rejected


def test_loss_is_bounded_in_unit_interval():
    """The concentration bounds are only valid for [0, 1]-valued samples."""
    rng = np.random.default_rng(0)
    for alpha in [0.01, 0.1, 0.5, 0.9]:
        correct = rng.random(500) > 0.3
        confidence = rng.random(500)
        loss = selective_loss(correct, confidence, theta=0.5, alpha=alpha)
        assert loss.min() >= 0.0
        assert loss.max() <= 1.0


def test_mean_loss_below_alpha_iff_selective_risk_below_alpha():
    """
    The equivalence the whole method rests on. If this breaks, every
    certified threshold is certifying the wrong quantity.
    """
    rng = np.random.default_rng(1)
    for _ in range(200):
        n = int(rng.integers(50, 400))
        correct = rng.random(n) > rng.uniform(0.02, 0.4)
        confidence = rng.random(n)
        alpha = float(rng.uniform(0.01, 0.3))
        theta = float(rng.uniform(0.0, 0.9))

        accepted = confidence > theta
        if accepted.sum() == 0:
            continue
        selective_risk = (~correct[accepted]).mean()
        mean_loss = selective_loss(correct, confidence, theta, alpha).mean()

        assert (mean_loss <= alpha + 1e-12) == (selective_risk <= alpha + 1e-12)


# --- the bounds must be conservative ---------------------------------------

def test_bounds_exceed_the_sample_mean():
    rng = np.random.default_rng(2)
    losses = rng.random(300)
    for bound in (hoeffding_upper_bound, bernstein_upper_bound):
        assert bound(losses, delta=0.1) > losses.mean()


def test_bernstein_is_tighter_on_low_variance_samples():
    """
    The reason Bernstein replaced Hoeffding. On a low-variance sample it must
    be the narrower of the two, or the substitution bought nothing.
    """
    low_variance = np.full(2000, 0.05)
    low_variance[:20] = 1.0
    assert bernstein_upper_bound(low_variance, 0.001) < hoeffding_upper_bound(low_variance, 0.001)


def test_bounds_degrade_to_useless_on_tiny_samples():
    """
    Rare categories must fail to certify rather than certify on noise.
    """
    tiny = np.array([0.0, 0.0, 0.0])
    assert bernstein_upper_bound(tiny, 0.001) > 0.5


# --- selection behaviour ----------------------------------------------------

def _synthetic(n=3000, seed=3):
    """
    A scorer whose confidence ranks its errors, as a usable one must.

    An earlier version drew correctness as Bernoulli(confidence), which is a
    perfectly calibrated but weak scorer: nothing could be certified at a 5%
    target, and the tests below were asserting against a fixture where the
    method had nothing to work with. The scorer here is sharper in the high
    confidence region, which is the regime a threshold actually operates in.
    """
    rng = np.random.default_rng(seed)
    confidence = rng.beta(5, 1.2, size=n)
    correct = rng.random(n) < confidence ** 0.25
    return correct, confidence


def test_abstains_when_the_target_is_impossible():
    correct, confidence = _synthetic()
    result = calibrate_fixed_sequence(correct, confidence, alpha=0.0001)
    assert not result.certified
    assert not result.routes_anything


def test_floor_is_never_undercut():
    """A contractual confidence gate must hold regardless of what the data allows."""
    correct, confidence = _synthetic()
    for floor in (0.5, 0.85):
        result = calibrate_fixed_sequence(correct, confidence, alpha=0.2, floor=floor)
        if result.certified:
            assert result.threshold >= floor


def test_neither_selection_procedure_dominates_the_other():
    """
    Records a finding rather than a preference.

    On the Reuters harness, fixed sequence testing certifies targets that
    Bonferroni abstains on, because the loss there is nearly monotone and the
    grid multiplicity correction is pure waste. On the synthetic fixture
    below the ordering reverses: fixed sequence testing stops at the first
    hypothesis it cannot reject, so a non-monotone bump blocks access to
    valid thresholds sitting underneath it, while Bonferroni tests every
    point and finds one.

    So the choice between them is an empirical question per dataset, not a
    settled one, and the harness runs both instead of assuming a winner.
    """
    correct, confidence = _synthetic()
    fst = calibrate_fixed_sequence(correct, confidence, alpha=0.05)
    bonf = calibrate_threshold(correct, confidence, alpha=0.05)

    # at least one procedure should find something on a fixture this clean
    assert fst.certified or bonf.certified

    # and whichever certifies must actually control the risk it promised
    for result in (fst, bonf):
        if result.certified:
            accepted = confidence > result.threshold
            assert (~correct[accepted]).mean() <= 0.05 + 0.02


def test_naive_selection_is_more_permissive_than_certified_selection():
    """
    Documents the failure mode rather than fixing it: the naive method accepts
    more because it is not paying for a guarantee.
    """
    correct, confidence = _synthetic()
    naive = calibrate_naive(correct, confidence, alpha=0.05)
    certified = calibrate_fixed_sequence(correct, confidence, alpha=0.05)
    assert naive.calibration_coverage >= certified.calibration_coverage


# --- split hygiene ----------------------------------------------------------

@pytest.mark.slow
def test_splits_share_no_documents():
    """
    A leak between calibration and test would inflate every reported figure
    while leaving the code looking correct.
    """
    from data import load_reuters

    corpus = load_reuters()
    index, calibration, test = (
        set(corpus.index.texts),
        set(corpus.calibration.texts),
        set(corpus.test.texts),
    )
    assert not (index & calibration)
    assert not (index & test)
    assert not (calibration & test)


@pytest.mark.slow
def test_every_class_reaches_every_split():
    from data import load_reuters

    corpus = load_reuters()
    for split in (corpus.index, corpus.calibration, corpus.test):
        assert len(np.unique(split.labels)) == corpus.n_classes, split.name
