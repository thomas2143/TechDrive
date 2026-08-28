"""
Retrieval classification.

A query is embedded, compared against the labelled index by cosine similarity,
and the class is decided by a similarity-weighted vote over the k nearest
neighbours. Confidence is the winning class's share of the total vote weight.

Two properties matter more here than raw accuracy.

Explainability: every decision carries the specific index documents that
produced it. A disputed category can be inspected rather than argued about.

Updatability: adding, merging or splitting a class means rebuilding the index,
not retraining a model. A taxonomy that changes every quarter is a
configuration change, not a project.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Prediction:
    label: int
    confidence: float
    evidence: list[tuple[int, int, float]]  # (index position, class id, similarity)


class RetrievalClassifier:
    """
    Similarity-weighted k-nearest-neighbour classifier over a fixed index.

    Vote weight for a neighbour is max(cos_sim, 0) ** power. Raising power
    sharpens the vote toward the closest neighbours; power=1 is a plain
    similarity weighting. It is a knob on how confident the score is willing
    to be.

    The constructor defaults are placeholders and are not claimed to be good.
    Use tune() to select k and power on a held-out slice of the index split.
    Selecting them on calibration or test would invalidate every guarantee
    downstream, since the threshold is certified against the same sample.
    """

    def __init__(self, k: int = 15, power: float = 3.0, batch_size: int = 512):
        self.k = k
        self.power = power
        self.batch_size = batch_size
        self._vectors: np.ndarray | None = None
        self._labels: np.ndarray | None = None
        self._n_classes: int = 0

    def fit(self, vectors: np.ndarray, labels: np.ndarray, n_classes: int) -> "RetrievalClassifier":
        self._vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        self._labels = labels
        self._n_classes = n_classes
        return self

    def _scores(self, queries: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Return (vote, neighbours) where vote is (n, n_classes) normalised
        vote mass and neighbours is (n, k) index positions ordered by
        decreasing similarity.
        """
        assert self._vectors is not None and self._labels is not None

        n = len(queries)
        k = min(self.k, len(self._vectors))
        vote = np.zeros((n, self._n_classes), dtype=np.float64)
        neigh = np.zeros((n, k), dtype=np.int64)

        for start in range(0, n, self.batch_size):
            stop = min(start + self.batch_size, n)
            # both sides are unit vectors, so the dot product is cosine similarity
            sims = queries[start:stop] @ self._vectors.T

            top = np.argpartition(-sims, kth=k - 1, axis=1)[:, :k]
            top_sims = np.take_along_axis(sims, top, axis=1)
            order = np.argsort(-top_sims, axis=1)
            top = np.take_along_axis(top, order, axis=1)
            top_sims = np.take_along_axis(top_sims, order, axis=1)

            weights = np.clip(top_sims, 0.0, None) ** self.power
            labels = self._labels[top]

            block = np.zeros((stop - start, self._n_classes), dtype=np.float64)
            np.add.at(block, (np.arange(stop - start)[:, None], labels), weights)

            total = block.sum(axis=1, keepdims=True)
            # a query with no positive similarity to anything gets a flat vote,
            # which yields low confidence and is therefore rejected downstream
            flat = total.squeeze(-1) <= 0
            block[flat] = 1.0 / self._n_classes
            total[flat] = 1.0

            vote[start:stop] = block / total
            neigh[start:stop] = top

        return vote, neigh

    def predict(self, queries: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return (labels, confidences) without assembling evidence."""
        vote, _ = self._scores(queries)
        labels = vote.argmax(axis=1)
        confidence = vote.max(axis=1)
        return labels, confidence

    def predict_with_evidence(self, queries: np.ndarray, top_n: int = 5) -> list[Prediction]:
        """Return full predictions, each carrying its supporting index documents."""
        assert self._vectors is not None and self._labels is not None
        vote, neigh = self._scores(queries)
        labels = vote.argmax(axis=1)
        confidence = vote.max(axis=1)

        out: list[Prediction] = []
        for i in range(len(queries)):
            picks = neigh[i][:top_n]
            sims = queries[i] @ self._vectors[picks].T
            out.append(
                Prediction(
                    label=int(labels[i]),
                    confidence=float(confidence[i]),
                    evidence=[
                        (int(p), int(self._labels[p]), float(s))
                        for p, s in zip(picks, sims, strict=True)
                    ],
                )
            )
        return out


def tune(
    vectors: np.ndarray,
    labels: np.ndarray,
    n_classes: int,
    k_grid: tuple[int, ...] = (5, 10, 15, 25, 40),
    power_grid: tuple[float, ...] = (1.0, 2.0, 3.0, 5.0, 8.0),
    holdout: float = 0.25,
    seed: int = 20260826,
) -> tuple[dict, list[dict]]:
    """
    Select k and power on a held-out slice of the INDEX split only.

    Selection criterion is mean confidence-weighted correctness rather than
    plain accuracy: a scorer that is accurate but uninformative about its own
    errors is useless to a threshold. Concretely we maximise the area under
    the risk-coverage curve's complement, approximated by average precision
    across coverage levels, which rewards ranking errors below correct
    predictions.
    """
    rng = np.random.default_rng(seed)
    n = len(vectors)
    perm = rng.permutation(n)
    n_hold = max(1, int(round(n * holdout)))
    hold, keep = perm[:n_hold], perm[n_hold:]

    results: list[dict] = []
    for k in k_grid:
        for power in power_grid:
            clf = RetrievalClassifier(k=k, power=power).fit(
                vectors[keep], labels[keep], n_classes
            )
            pred, conf = clf.predict(vectors[hold])
            correct = pred == labels[hold]

            # mean precision across coverage levels, the quantity a threshold
            # will later be asked to exploit
            order = np.argsort(-conf)
            ranked = correct[order]
            cum_precision = np.cumsum(ranked) / np.arange(1, len(ranked) + 1)
            score = float(cum_precision.mean())

            results.append(
                {"k": k, "power": power, "accuracy": float(correct.mean()), "score": score}
            )

    results.sort(key=lambda r: -r["score"])
    return results[0], results
