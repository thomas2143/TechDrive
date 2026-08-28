"""
Text encoders.

The point of this module is the interface, not the implementation. The
selective classification machinery downstream never sees text: it sees unit
vectors. Whatever produces them is a swappable component.

TfidfSvdEncoder is what runs here, because this environment has no access to
pretrained transformer weights. On real infrastructure the same interface is
satisfied by a sentence embedding model such as LaBSE, which is what a
multilingual ticket flow requires. Nothing downstream changes.

That substitution moves the accuracy numbers. It does not change whether the
threshold selection is valid, which is what this harness exists to test.
"""

from abc import ABC, abstractmethod

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer


class Encoder(ABC):
    """Maps text to L2-normalised dense vectors."""

    name: str
    dim: int

    @abstractmethod
    def fit(self, texts: list[str]) -> "Encoder":
        """Fit on the index corpus only. Never on calibration or test."""

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Return an (n, dim) array of unit vectors."""


class TfidfSvdEncoder(Encoder):
    """
    TF-IDF followed by truncated SVD, L2-normalised.

    Deterministic, offline, and fast enough to rebuild on every run, which
    matters for a harness whose whole purpose is repeated measurement.

    Its weakness is the one to state plainly: it has no semantic knowledge
    beyond term co-occurrence in this corpus, so it cannot match a ticket
    phrased in words the archive never used. A pretrained multilingual
    encoder can. That gap is the reason LaBSE is specified for production.
    """

    def __init__(self, dim: int = 300, min_df: int = 2, seed: int = 20260826):
        self.name = f"tfidf-svd-{dim}"
        self.dim = dim
        self._pipeline = make_pipeline(
            TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                stop_words="english",
                min_df=min_df,
                max_df=0.5,
                sublinear_tf=True,
                ngram_range=(1, 2),
            ),
            TruncatedSVD(n_components=dim, random_state=seed),
            Normalizer(copy=False),
        )

    def fit(self, texts: list[str]) -> "TfidfSvdEncoder":
        self._pipeline.fit(texts)
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._pipeline.transform(texts).astype(np.float32)
