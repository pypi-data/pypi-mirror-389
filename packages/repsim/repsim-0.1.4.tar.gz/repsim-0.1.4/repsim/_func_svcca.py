from __future__ import annotations
import numpy as np
from typing import Sequence, Optional
from numpy.typing import ArrayLike
from . import _repsim
from ._utils import _aux_checker

__all__ = ["svcca"]


def svcca(mats: Sequence[ArrayLike], summary_type: Optional[str] = None) -> np.ndarray:
    """
    Singular Vector Canonical Correlation Analysis

    Compute pairwise singular vector CCA (SVCCA) similarities between multiple representations.
    SVCCA first mean-centers and denoises each representation via SVD,
    retaining components explaining a high fraction of variance at 99% threshold. Then,
    CCA is applied to the reduced representations, and the similarity is summarized
    with either Yanai’s GCD or Pillai’s trace.

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
        Array of shape ``(M, M)`` of SVCCA summary similarities.
    """
    # check the summary type
    if summary_type is None or (
        isinstance(summary_type, str) and len(summary_type.strip()) == 0
    ):
        par_summary = "yanai"
    else:
        par_summary = summary_type.strip().lower()
        if par_summary not in {"yanai", "pillai"}:
            raise ValueError(
                "* svcca : summary_type must be one of {'yanai', 'pillai'}."
            )

    # run
    return _repsim.cpp_svcca(_aux_checker(mats, "cca"), par_summary)
