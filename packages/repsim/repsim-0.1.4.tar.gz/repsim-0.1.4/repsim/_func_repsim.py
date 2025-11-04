from __future__ import annotations
from typing import Optional, Sequence, List
from numpy.typing import ArrayLike
import numpy as np

__all__ = ["repsim_hsic", "repsim_kernels"]


def repsim_hsic():
    """
    List of HSIC estimators

    Returns a list of available HSIC estimators implemented in
    the package.

    Returns
    -------
    list of str
        Names of available HSIC estimators implemented in the package.
    """
    all_ests = ["gretton", "song", "lange"]
    return all_ests


def repsim_kernels():
    """
    List of kernel functions

    Returns a list of available kernel methods implemented in the package.

    Returns
    -------
    list of str
        Names of available kernel methods implemented in the package.
    """
    all_kernels = ["linear", "rbf", "rbf_mean", "rbf_dualmed"]
    return all_kernels
