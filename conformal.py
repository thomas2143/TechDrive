"""
Threshold selection by risk control.

The requirement is a selective risk guarantee: among the items the system
chooses to route automatically, the error rate must stay at or below alpha.

    P( Yhat != Y | conf > theta ) <= alpha

The obvious approach is to sweep theta on held-out data and keep the smallest
one whose empirical selective risk clears alpha. That is unsound for two
reasons, and both are visible in practice.

First, selective risk is not monotone in theta. Raising the threshold does not
reliably lower the error rate among accepted items, so there is no ordering
argument that lets a single sweep stand in for a guarantee.

Second, sweeping a grid and keeping the best result is multiple testing. The
winning threshold is selected precisely because its empirical risk looked
good, so that estimate is optimistically biased by construction.

The fix used here follows the risk control formulation for non-monotonic
losses. Define, for a fixed theta, the per-item loss

    L = 1{error and accepted} - alpha * 1{accepted} + alpha

which takes value 1 on an accepted error, 0 on an accepted correct item, and
alpha on a rejected item. It is bounded in [0, 1], and its expectation is at
most alpha exactly when the selective risk is at most alpha. That turns a
conditional statement into an ordinary bounded mean, which concentration
bounds can handle.

Each theta on the grid is then a hypothesis test: bound E[L] from above on the
calibration sample, and keep theta only if the bound clears alpha. Bonferroni
across the grid controls the family-wise error. Among the survivors, take the
one with the highest coverage.

What this buys: a threshold whose guarantee was not chosen after seeing which
threshold flattered the data.

What it assumes: exchangeability between the calibration sample and what
arrives next. A live ticket stream drifts. The guarantee degrades exactly when
the incoming distribution stops resembling the calibration set, which is why
production monitoring and periodic recalibration are not optional extras.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class ThresholdResult:
    threshold: float          # np.inf means no threshold could be certified
    alpha: float
    delta: float
    certified: bool
    calibration_coverage: float
    calibration_risk: float   # empirical selective risk at the chosen threshold
    n_calibration: int
    grid_size: int

    @property
    def routes_anything(self) -> bool:
        return self.certified and np.isfinite(self.threshold)


def selective_loss(
    correct: np.ndarray, confidence: np.ndarray, theta: float, alpha: float
) -> np.ndarray:
    """
    Per-item loss whose mean is at most alpha exactly when the selective risk
    is at most alpha. Bounded in [0, 1].
    """
    accepted = confidence > theta
    error = accepted & ~correct
    return error.astype(np.float64) - alpha * accepted.astype(np.float64) + alpha


def hoeffding_upper_bound(losses: np.ndarray, delta: float) -> float:
    """
    One-sided Hoeffding bound on the mean of a [0, 1]-bounded sample.

    Distribution-free and finite-sample. Its weakness is that it charges for
    the full [0, 1] range regardless of how little the sample actually varies.
    On this loss that is a large and avoidable penalty, which is why it is
    kept only as a comparison point.
    """
    n = len(losses)
    if n == 0:
        return 1.0
    return float(losses.mean() + np.sqrt(np.log(1.0 / delta) / (2.0 * n)))


def bernstein_upper_bound(losses: np.ndarray, delta: float) -> float:
    """
    Empirical Bernstein bound (Maurer and Pontil) on the mean of a
    [0, 1]-bounded sample.

    Same finite-sample, distribution-free character as Hoeffding, but the
    width scales with the observed standard deviation instead of the range.

    That matters here because the loss is extremely low variance by
    construction: it is 0 on an accepted correct item, alpha on a rejected
    one, and 1 only on an accepted error, which is rare by design. Hoeffding
    prices this sample as if it were spread across the whole interval and
    ends up unable to certify anything at the error rates that were the point
    of the exercise. Bernstein prices it for what it is.

    Requires n >= 2.
    """
    n = len(losses)
    if n < 2:
        return 1.0
    mean = float(losses.mean())
    var = float(losses.var(ddof=1))
    log_term = np.log(2.0 / delta)
    return float(
        mean
        + np.sqrt(2.0 * var * log_term / n)
        + 7.0 * log_term / (3.0 * (n - 1))
    )


BOUNDS = {"hoeffding": hoeffding_upper_bound, "bernstein": bernstein_upper_bound}


def calibrate_threshold(
    correct: np.ndarray,
    confidence: np.ndarray,
    alpha: float,
    delta: float = 0.10,
    grid: np.ndarray | None = None,
    floor: float = 0.0,
    bound: str = "bernstein",
) -> ThresholdResult:
    """
    Select the lowest-abstention threshold whose selective risk is certified
    at level alpha with confidence 1 - delta.

    floor sets a hard minimum below which no threshold is considered, which is
    how a contractual confidence gate is honoured regardless of what the data
    would otherwise allow.
    """
    if grid is None:
        grid = np.round(np.arange(0.0, 1.00, 0.005), 3)
    grid = np.asarray([g for g in grid if g >= floor - 1e-12], dtype=np.float64)

    if len(grid) == 0 or len(correct) == 0:
        return ThresholdResult(np.inf, alpha, delta, False, 0.0, float("nan"), len(correct), 0)

    # Bonferroni across the grid: every theta is a separate test
    delta_per_test = delta / len(grid)
    upper_bound = BOUNDS[bound]

    best: tuple[float, float, float] | None = None  # (coverage, theta, risk)
    for theta in grid:
        losses = selective_loss(correct, confidence, theta, alpha)
        if upper_bound(losses, delta_per_test) > alpha:
            continue

        accepted = confidence > theta
        coverage = float(accepted.mean())
        if coverage == 0.0:
            continue
        risk = float((~correct[accepted]).mean())
        if best is None or coverage > best[0]:
            best = (coverage, float(theta), risk)

    if best is None:
        return ThresholdResult(
            np.inf, alpha, delta, False, 0.0, float("nan"), len(correct), len(grid)
        )

    coverage, theta, risk = best
    return ThresholdResult(
        threshold=theta,
        alpha=alpha,
        delta=delta,
        certified=True,
        calibration_coverage=coverage,
        calibration_risk=risk,
        n_calibration=len(correct),
        grid_size=len(grid),
    )


def calibrate_naive(
    correct: np.ndarray, confidence: np.ndarray, alpha: float,
    grid: np.ndarray | None = None, floor: float = 0.0,
) -> ThresholdResult:
    """
    The unsound baseline, implemented so the difference can be measured rather
    than asserted: sweep the grid, keep the highest-coverage threshold whose
    empirical selective risk is at or below alpha. No correction, no bound.
    """
    if grid is None:
        grid = np.round(np.arange(0.0, 1.00, 0.005), 3)
    grid = np.asarray([g for g in grid if g >= floor - 1e-12], dtype=np.float64)

    best: tuple[float, float, float] | None = None
    for theta in grid:
        accepted = confidence > theta
        if accepted.sum() == 0:
            continue
        risk = float((~correct[accepted]).mean())
        if risk > alpha:
            continue
        coverage = float(accepted.mean())
        if best is None or coverage > best[0]:
            best = (coverage, float(theta), risk)

    if best is None:
        return ThresholdResult(np.inf, alpha, 0.0, False, 0.0, float("nan"), len(correct), len(grid))

    coverage, theta, risk = best
    return ThresholdResult(theta, alpha, 0.0, True, coverage, risk, len(correct), len(grid))


def measure_non_monotonicity(
    correct: np.ndarray, confidence: np.ndarray, grid: np.ndarray | None = None
) -> dict:
    """
    Quantify how far the empirical selective risk departs from being
    decreasing in theta. Reported rather than assumed, because the argument
    for risk control rests on it.
    """
    if grid is None:
        grid = np.round(np.arange(0.0, 0.99, 0.005), 3)

    thetas, risks = [], []
    for theta in grid:
        accepted = confidence > theta
        if accepted.sum() < 20:  # ignore the tail where the estimate is noise
            continue
        thetas.append(float(theta))
        risks.append(float((~correct[accepted]).mean()))

    r = np.asarray(risks)
    if len(r) < 2:
        return {"steps": 0, "increases": 0, "increase_fraction": 0.0, "max_increase": 0.0}

    diffs = np.diff(r)
    return {
        "steps": int(len(diffs)),
        "increases": int((diffs > 0).sum()),
        "increase_fraction": float((diffs > 0).mean()),
        "max_increase": float(diffs.max()),
        "thetas": thetas,
        "risks": risks,
    }


def calibrate_fixed_sequence(
    correct: np.ndarray,
    confidence: np.ndarray,
    alpha: float,
    delta: float = 0.10,
    grid: np.ndarray | None = None,
    floor: float = 0.0,
    bound: str = "bernstein",
    n_starts: int = 1,
) -> ThresholdResult:
    """
    Fixed sequence testing instead of a Bonferroni-corrected grid sweep.

    Bonferroni tests every threshold at level delta / |grid|. With a few
    hundred grid points that log factor dominates the confidence width and
    throws away most of the calibration sample's power for no reason other
    than the resolution of the grid, which is an implementation detail rather
    than anything the data cares about.

    Fixed sequence testing exploits the fact that these hypotheses are not
    independent: nearby thresholds accept nearly the same items. Order the
    grid in advance from the threshold most likely to be certifiable to the
    least, test each at the full level delta, and stop at the first failure.
    Family-wise error is still controlled at delta.

    The ordering must be fixed without consulting the calibration data. Here
    it is descending threshold: the most conservative setting, which rejects
    the most and therefore has the lowest risk, is tested first. That is the
    natural ordering for a nearly monotone risk, and this loss is nearly
    monotone in practice.

    The cost is a real one. Stopping at the first failure means a valid
    threshold sitting below a non-monotone bump is never reached. n_starts > 1
    mitigates it by restarting from several points at level delta / n_starts.
    """
    if grid is None:
        grid = np.round(np.arange(0.0, 1.00, 0.005), 3)
    grid = np.asarray(sorted({g for g in grid if g >= floor - 1e-12}), dtype=np.float64)

    if len(grid) == 0 or len(correct) == 0:
        return ThresholdResult(np.inf, alpha, delta, False, 0.0, float("nan"), len(correct), 0)

    upper_bound = BOUNDS[bound]
    ordered = grid[::-1]  # most conservative first, fixed in advance
    starts = np.unique(np.linspace(0, len(ordered) - 1, n_starts).astype(int))
    delta_per_start = delta / len(starts)

    certified: list[float] = []
    for start in starts:
        for j in range(start, len(ordered)):
            theta = float(ordered[j])
            if theta in certified:
                continue
            losses = selective_loss(correct, confidence, theta, alpha)
            if upper_bound(losses, delta_per_start) > alpha:
                break  # stop at the first failure, as the procedure requires
            certified.append(theta)

    if not certified:
        return ThresholdResult(
            np.inf, alpha, delta, False, 0.0, float("nan"), len(correct), len(grid)
        )

    # among certified thresholds, the lowest one accepts the most
    theta = min(certified)
    accepted = confidence > theta
    coverage = float(accepted.mean())
    risk = float((~correct[accepted]).mean()) if accepted.sum() else float("nan")
    return ThresholdResult(
        threshold=theta,
        alpha=alpha,
        delta=delta,
        certified=True,
        calibration_coverage=coverage,
        calibration_risk=risk,
        n_calibration=len(correct),
        grid_size=len(grid),
    )


def calibrate_per_class(
    predicted: np.ndarray,
    correct: np.ndarray,
    confidence: np.ndarray,
    n_classes: int,
    alpha: float,
    delta: float = 0.10,
    floor: float = 0.0,
    bound: str = "bernstein",
) -> dict[int, ThresholdResult]:
    """
    Certify a threshold separately for each predicted class.

    A single global threshold hides the thing that matters operationally. It is
    set by the categories that carry the volume, and the long tail rides along
    underneath it, auto-routed on a guarantee that was never established for
    those categories specifically.

    Certifying per class removes that. Each class is calibrated only on the
    items the classifier assigned to it, so a category with forty calibration
    examples must clear the bound on those forty. Most will not: the confidence
    width on a small sample is wide, and a wide bound cannot certify a tight
    error target.

    That failure is the correct outcome, not a defect. A category that cannot
    demonstrate its own error rate should not be routed without a human, and
    the honest way to express that is a system that declines to certify it.

    The multiplicity across classes is handled the same way as across the
    threshold grid: delta is split over the classes being certified, so the
    family-wise error across the whole per-class decision remains at delta.
    Conditioning on the predicted class rather than the true one is what makes
    the guarantee usable at routing time, when the true class is unknown.
    """
    classes = [c for c in range(n_classes) if (predicted == c).any()]
    if not classes:
        return {}

    delta_per_class = delta / len(classes)
    results: dict[int, ThresholdResult] = {}
    for cls in classes:
        mask = predicted == cls
        results[cls] = calibrate_fixed_sequence(
            correct[mask], confidence[mask],
            alpha=alpha, delta=delta_per_class, floor=floor, bound=bound,
        )
    return results


def apply_per_class(
    predicted: np.ndarray,
    confidence: np.ndarray,
    thresholds: dict[int, ThresholdResult],
) -> np.ndarray:
    """
    Which items a per-class threshold set would route automatically.

    An item whose predicted class was never certified is held, which is what
    makes the long tail fall out of automation rather than through it.
    """
    accepted = np.zeros(len(predicted), dtype=bool)
    for cls, result in thresholds.items():
        if not result.routes_anything:
            continue
        accepted |= (predicted == cls) & (confidence > result.threshold)
    return accepted
