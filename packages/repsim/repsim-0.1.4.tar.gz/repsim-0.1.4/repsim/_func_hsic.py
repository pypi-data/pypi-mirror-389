from __future__ import annotations
import numpy as np
from typing import Sequence, Optional
from numpy.typing import ArrayLike
from . import _repsim
from ._utils import _aux_checker
from ._func_repsim import repsim_hsic, repsim_kernels

__all__ = ["hsic"]


def hsic(
    mats: Sequence[ArrayLike],
    kernel_type: Optional[str] = None,
    estimator: Optional[str] = None,
) -> np.ndarray:
    """
    Hilbert Schmidth Independence Criterion

    Compute pairwise HSIC similarities between multiple representations using a chosen kernel and estimator.

    Parameters
    ----------
    mats : sequence of array-like, length M
        List or tuple of *M* data representations, each of shape ``(n_samples, n_features_k)``.
        All matrices must share the same number of rows for matching samples.
        Each element can be a NumPy array or any object convertible to one via
        ``numpy.asarray``.
    kernel_type : str, optional
        Kernel type for HSIC computation. Defaults to ``"rbf"``. See
        ``repsim.repsim_kernels()`` for the list of supported
        kernels at runtime.
    estimator: str, optional
        Estimator type for HSIC computation. Defaults to ``"gretton"``. See
        ``repsim.repsim_hsic()`` for the list of supported estimators at runtime.

    Returns
    -------
    numpy.ndarray
        Array of shape ``(M, M)`` of HSIC similarities.

    Notes
    -----
        ``kernel_type=None`` and ``estimator=None`` select the defaults
        ``"rbf"`` and ``"gretton"``, respectively.
    """
    # check the kernel type
    if kernel_type is None or (
        isinstance(kernel_type, str) and len(kernel_type.strip()) == 0
    ):
        par_kernel = "rbf"
    else:
        par_kernel = kernel_type.strip().lower()
        all_kernel = repsim_kernels()
        if par_kernel not in all_kernel:
            raise ValueError(f"* hsic : kernel_type must be one of {all_kernel}.")

    # check the estimator
    if estimator is None or (
        isinstance(estimator, str) and len(estimator.strip()) == 0
    ):
        par_estimator = "gretton"
    else:
        par_estimator = estimator.strip().lower()
        all_estimator = repsim_hsic()
        if par_estimator not in all_estimator:
            raise ValueError(f"* hsic : estimator must be one of {all_estimator}.")

    # run
    return _repsim.cpp_hsic(_aux_checker(mats, "cka"), par_kernel, par_estimator)
