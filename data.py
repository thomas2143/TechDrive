"""
Corpus loading and splitting.

Stands in for TechDrive's historical ticket archive. Reuters-21578 is used
because its category distribution has the same shape as a support taxonomy:
a handful of high-volume categories and a long tail of rare ones.

Three splits, with distinct roles that must not be confused:

  index        the labelled reference archive the classifier retrieves against
  calibration  held out, used only to select thresholds (never for retrieval)
  test         held out, used only for reporting (never seen during calibration)

Keeping calibration and test disjoint is what makes the reported coverage and
risk figures mean anything.
"""

from collections import Counter
from dataclasses import dataclass

import numpy as np


def _deduplicated_fileids(reuters) -> list[str]:
    """
    Single-label documents, with exact text duplicates removed.

    Reuters carries 85 documents whose text is byte-identical to another,
    one of them repeated seven times. Left in, a duplicate straddling the
    index and test splits lets the classifier retrieve an exact copy of the
    item it is being asked to classify. That is leakage, and it inflates
    accuracy in a way no amount of split hygiene elsewhere would catch.
    """
    seen: set[str] = set()
    kept: list[str] = []
    for fid in sorted(reuters.fileids()):
        if len(reuters.categories(fid)) != 1:
            continue
        text = reuters.raw(fid)
        if text in seen:
            continue
        seen.add(text)
        kept.append(fid)
    return kept


@dataclass
class Split:
    texts: list[str]
    labels: np.ndarray  # integer class ids
    name: str

    def __len__(self) -> int:
        return len(self.texts)


@dataclass
class Corpus:
    index: Split
    calibration: Split
    test: Split
    class_names: list[str]

    @property
    def n_classes(self) -> int:
        return len(self.class_names)


def load_reuters(
    min_docs_per_class: int = 4,
    fractions: tuple[float, float, float] = (0.60, 0.20, 0.20),
    seed: int = 20260826,
) -> Corpus:
    """
    Load the single-label portion of Reuters and split it three ways,
    stratified by class.

    min_docs_per_class drops only classes with too few documents to appear in
    all three splits at all. It is set as low as the split arithmetic allows,
    because the long tail is the part of the taxonomy this harness exists to
    stress, and filtering it away would be measuring an easier problem.
    """
    from nltk.corpus import reuters

    fileids = _deduplicated_fileids(reuters)

    by_class: dict[str, list[str]] = {}
    for fid in fileids:
        by_class.setdefault(reuters.categories(fid)[0], []).append(fid)

    kept = {c: fids for c, fids in by_class.items() if len(fids) >= min_docs_per_class}
    class_names = sorted(kept)
    class_id = {c: i for i, c in enumerate(class_names)}

    rng = np.random.default_rng(seed)
    buckets: dict[str, list[tuple[str, int]]] = {"index": [], "calibration": [], "test": []}

    f_index, f_cal, _ = fractions
    for cls, fids in kept.items():
        fids = list(fids)
        rng.shuffle(fids)
        n = len(fids)
        # every split needs at least one document of every class. Without the
        # index floor, a class with few documents ends up with no exemplar at
        # all: it can never be predicted, yet it still appears in calibration
        # and test contributing guaranteed errors. That silently degrades
        # every reported figure while nothing looks broken.
        n_index = min(max(1, int(round(n * f_index))), n - 2)
        n_cal = min(max(1, int(round(n * f_cal))), n - n_index - 1)

        cid = class_id[cls]
        buckets["index"] += [(f, cid) for f in fids[:n_index]]
        buckets["calibration"] += [(f, cid) for f in fids[n_index:n_index + n_cal]]
        buckets["test"] += [(f, cid) for f in fids[n_index + n_cal:]]

    def build(name: str) -> Split:
        items = buckets[name]
        rng.shuffle(items)
        return Split(
            texts=[reuters.raw(f) for f, _ in items],
            labels=np.array([c for _, c in items], dtype=np.int64),
            name=name,
        )

    return Corpus(
        index=build("index"),
        calibration=build("calibration"),
        test=build("test"),
        class_names=class_names,
    )


def describe(corpus: Corpus) -> str:
    counts = Counter(corpus.index.labels.tolist())
    sizes = np.array(sorted(counts.values(), reverse=True))
    lines = [
        f"classes                        {corpus.n_classes}",
        f"index / calibration / test     {len(corpus.index)} / {len(corpus.calibration)} / {len(corpus.test)}",
        f"volume share of top 5 classes  {sizes[:5].sum() / sizes.sum():.1%}",
        f"classes with <50 index docs    {(sizes < 50).sum()} of {len(sizes)}",
        f"median index docs per class    {int(np.median(sizes))}",
    ]
    return "\n".join(lines)


def load_reuters_temporal(
    min_docs_per_class: int = 2,
    calibration_fraction: float = 0.30,
    seed: int = 20260826,
) -> Corpus:
    """
    Same corpus, split by time rather than at random.

    Reuters carries the ModApte partition in its file identifiers: documents
    are prefixed 'training' or 'test' according to a date cutoff. Using that
    boundary gives index and calibration from the earlier period and test from
    the later one.

    This deliberately breaks the exchangeability that risk control assumes.
    The random split measures whether the method works when its assumption
    holds. This one measures what happens when it does not, which is the
    situation any live ticket stream eventually produces.
    """
    from nltk.corpus import reuters

    single = _deduplicated_fileids(reuters)
    earlier = [f for f in single if f.startswith("training")]
    later = [f for f in single if f.startswith("test")]

    def counts(fids):
        out = {}
        for f in fids:
            out.setdefault(reuters.categories(f)[0], []).append(f)
        return out

    c_early, c_late = counts(earlier), counts(later)
    class_names = sorted(
        c for c in set(c_early) & set(c_late)
        if len(c_early[c]) >= min_docs_per_class
    )
    class_id = {c: i for i, c in enumerate(class_names)}

    rng = np.random.default_rng(seed)

    early_items = []
    for c in class_names:
        fids = list(c_early[c])
        rng.shuffle(fids)
        early_items += [(f, class_id[c]) for f in fids]
    rng.shuffle(early_items)

    n_cal = int(round(len(early_items) * calibration_fraction))
    cal_items, index_items = early_items[:n_cal], early_items[n_cal:]
    test_items = [(f, class_id[c]) for c in class_names for f in c_late[c]]
    rng.shuffle(test_items)

    def build(items, name):
        return Split(
            texts=[reuters.raw(f) for f, _ in items],
            labels=np.array([c for _, c in items], dtype=np.int64),
            name=name,
        )

    return Corpus(
        index=build(index_items, "index"),
        calibration=build(cal_items, "calibration"),
        test=build(test_items, "test"),
        class_names=class_names,
    )
