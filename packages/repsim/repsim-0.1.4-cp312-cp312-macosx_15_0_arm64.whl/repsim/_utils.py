from __future__ import annotations
from typing import Optional, Sequence, List
from numpy.typing import ArrayLike
import numpy as np

__all__ = ["_aux_checker"]


def _aux_checker(mats: Sequence[np.ndarray], func_name: str = None) -> List[np.ndarray]:
    if not isinstance(mats, (list, tuple)):
        raise TypeError(
            f"{func_name}(): `mats` must be a list or tuple of array-like 2D matrices"
        )
    if len(mats) == 0:
        raise ValueError(f"{func_name}(): `mats` must not be empty")

    out: List[np.ndarray] = []
    nrows: Optional[int] = None

    for i, X in enumerate(mats):
        # Convert to float64, C-contiguous
        try:
            X = np.asarray(X, dtype=float, order="C")
        except Exception as e:
            raise TypeError(
                f"{func_name}(): mats[{i}] could not be converted to a NumPy array"
            ) from e

        # Must be 2D
        if X.ndim != 2:
            raise ValueError(
                f"{func_name}(): mats[{i}] must be 2D (got shape {X.shape})"
            )

        # Consistent number of rows
        if nrows is None:
            nrows = X.shape[0]
        elif X.shape[0] != nrows:
            raise ValueError(
                f"{func_name}(): all matrices must have the same number of rows (samples); "
                f"found {nrows} and {X.shape[0]} at index {i}"
            )

        # No NaN/Inf
        if not np.isfinite(X).all():
            raise ValueError(f"{func_name}(): mats[{i}] contains NaN or Inf values")

        out.append(X)

    return out
