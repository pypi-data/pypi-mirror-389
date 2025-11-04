from __future__ import annotations
import numpy as np
from typing import Sequence, Optional
from numpy.typing import ArrayLike
from . import _repsim
from ._utils import _aux_checker

__all__ = ["pwcca"]


def pwcca(mats: Sequence[ArrayLike]) -> np.ndarray:
    """
    Projection-Weighted Canonical Correlation Analysis

    Compute pairwise projection-weighted CCA (PWCCA) similarities between multiple representations.
    PWCCA reweights canonical directions by the magnitude of each representation’s projection onto those directions,
    emphasizing components that are most used by the representation.

    Parameters
    ----------
    mats : sequence of array-like, length M
        List or tuple of *M* data representations, each of shape ``(n_samples, n_features_k)``.
        All matrices must share the same number of rows for matching samples.
        Each element can be a NumPy array or any object convertible to one via
        ``numpy.asarray``.

    Returns
    -------
    numpy.ndarray
        Array of shape ``(M, M)`` of PWCCA similarities.
    """
    # run
    return _repsim.cpp_pwcca(_aux_checker(mats, "cca"))
