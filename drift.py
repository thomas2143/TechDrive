"""
Distribution shift.

Risk control certifies a threshold under exchangeability between the
calibration sample and what arrives next. A live ticket stream does not
provide that. A new product ships, an integration partner changes, a campaign
launches, and the mix of incoming categories moves away from whatever the
calibration set contained.

The natural temporal split of this corpus turns out to be too gentle to break
anything, which is worth knowing but is not an answer. This module applies a
controlled shift of adjustable severity so the question becomes quantitative:
how far can the incoming distribution move before a certified threshold stops
delivering what it certified.

The shift used is the one that matters operationally. Mass moves from the
high-volume categories, which the index covers densely and the classifier
handles well, toward the long tail, which it does not. That is what a real
product launch does to a support queue, and it is the direction that hurts.
"""

import numpy as np


def tail_shifted_indices(
    labels: np.ndarray,
    severity: float,
    head_fraction: float = 0.1,
    size: int | None = None,
    seed: int = 20260826,
) -> np.ndarray:
    """
    Resample item indices so that the class mix moves toward the tail.

    severity = 0 reproduces the observed distribution. severity = 1 samples
    head and tail classes with equal total mass, which is a severe but not
    absurd shift: it is roughly what happens when a previously rare category
    becomes a major driver of volume.

    Sampling is with replacement, so the returned array is a resample of the
    same underlying items rather than new data. That keeps the classifier's
    per-item behaviour fixed and isolates the effect of the mix.
    """
    if severity == 0:
        # exact identity, so the drift baseline matches the undrifted figures
        # rather than differing by a bootstrap resample
        return np.arange(len(labels))

    rng = np.random.default_rng(seed)
    classes, counts = np.unique(labels, return_counts=True)

    order = np.argsort(-counts)
    n_head = max(1, int(round(len(classes) * head_fraction)))
    head = set(classes[order[:n_head]].tolist())

    observed = counts / counts.sum()
    # target: head classes collapsed toward parity with the tail
    target = observed.copy()
    is_head = np.array([c in head for c in classes])

    head_mass, tail_mass = observed[is_head].sum(), observed[~is_head].sum()
    if tail_mass == 0 or head_mass == 0:
        return np.arange(len(labels))

    desired_head = (1 - severity) * head_mass + severity * 0.5
    target[is_head] = observed[is_head] / head_mass * desired_head
    target[~is_head] = observed[~is_head] / tail_mass * (1 - desired_head)

    weights = np.zeros(len(labels), dtype=np.float64)
    for cls, tgt, cnt in zip(classes, target, counts, strict=True):
        weights[labels == cls] = tgt / cnt
    weights /= weights.sum()

    n = size if size is not None else len(labels)
    return rng.choice(len(labels), size=n, replace=True, p=weights)


def total_variation(labels_a: np.ndarray, labels_b: np.ndarray, n_classes: int) -> float:
    """Total variation distance between two label distributions, for reporting."""
    pa = np.bincount(labels_a, minlength=n_classes).astype(float)
    pb = np.bincount(labels_b, minlength=n_classes).astype(float)
    pa /= pa.sum()
    pb /= pb.sum()
    return float(0.5 * np.abs(pa - pb).sum())


def taxonomy_shift(
    labels: np.ndarray,
    fraction: float,
    n_classes: int,
    seed: int = 20260826,
) -> np.ndarray:
    """
    Simulate a taxonomy change: a share of the incoming tickets now belong to
    a different class than the archive says they do.

    This is the drift mode that actually threatens the guarantee, and it is
    qualitatively different from a shift in the class mix. A mix shift sends
    unfamiliar items to the classifier, which scores them low and abstains, so
    the guarantee survives by giving up coverage. A taxonomy change leaves the
    items looking exactly as familiar as before while the correct answer moves
    underneath them. The classifier stays confident and becomes wrong, which
    is precisely the combination abstention cannot catch.

    Operationally this is not exotic. It is what happens when a category is
    split, when two teams swap ownership of an issue type, or when a product
    rename makes an old label mean something else. The TechDrive specification
    schedules monthly retraining, which is an acknowledgement that this
    happens on that timescale.

    Returns relabelled ground truth. The classifier's predictions and
    confidences are untouched: only the truth moved.
    """
    rng = np.random.default_rng(seed)
    shifted = labels.copy()
    if fraction <= 0:
        return shifted

    classes, counts = np.unique(labels, return_counts=True)
    # take the largest class, the one the classifier knows best, and move part
    # of it to the second largest. Confusing two well-populated categories is
    # the worst case: the classifier is confident about both.
    order = np.argsort(-counts)
    source, destination = classes[order[0]], classes[order[1]]

    positions = np.flatnonzero(labels == source)
    n_move = int(round(len(positions) * fraction))
    if n_move == 0:
        return shifted
    shifted[rng.choice(positions, size=n_move, replace=False)] = destination
    return shifted
