from __future__ import annotations
import numpy as np
from typing import Sequence
from numpy.typing import ArrayLike
from . import _repsim
from ._utils import _aux_checker

__all__ = ["dot_product"]


def dot_product(mats: Sequence[ArrayLike]) -> np.ndarray:
    """
    Dot product similarity

    Compute pairwise dot-product similarities between multiple representations.

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
        Array of shape ``(M, M)`` of symmetric dot-product similarities.
    """
    # check the input
    return _repsim.cpp_dot_product(_aux_checker(mats, "dot_product"))
