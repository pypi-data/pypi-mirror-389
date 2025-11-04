from __future__ import annotations
import numpy as np
from typing import Sequence, Optional
from numpy.typing import ArrayLike
from . import _repsim
from ._utils import _aux_checker

__all__ = ["cca"]


def cca(mats: Sequence[ArrayLike], summary_type: Optional[str] = None) -> np.ndarray:
    """
    Canonical Correlation Analysis

    Compute pairwise CCA-based similarities between multiple representations,
    summarized by either Yanai's GCD measure or Pillai's trace statistic.

    Parameters
    ----------
    mats : sequence of array-like, length M
        List or tuple of *M* data representations, each of shape ``(n_samples, n_features_k)``.
        All matrices must share the same number of rows for matching samples.
        Each element can be a NumPy array or any object convertible to one via
        ``numpy.asarray``.
    summary_type : str, optional
        Summary statistic for canonical correlations. One of ``"yanai"`` and ``"pillai"``.
        Defaults to ``"yanai"``.

    Returns
    -------
    numpy.ndarray
        Array of shape ``(M, M)`` of CCA summary similarities.
    """
    # check the summary type
    if summary_type is None or (
        isinstance(summary_type, str) and len(summary_type.strip()) == 0
    ):
        par_summary = "yanai"
    else:
        par_summary = summary_type.strip().lower()
        if par_summary not in {"yanai", "pillai"}:
            raise ValueError("* cca : summary_type must be one of {'yanai', 'pillai'}.")

    # run
    return _repsim.cpp_cca(_aux_checker(mats, "cca"), par_summary)
