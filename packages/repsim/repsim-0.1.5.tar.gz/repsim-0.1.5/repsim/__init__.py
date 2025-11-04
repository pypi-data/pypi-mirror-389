# __init__.py — PEP 562 lazy exports from _func_*.py with real docstrings
from __future__ import annotations

import pkgutil
from typing import Dict, Iterable

__all__: list[str] = []

# ---------------------------
# Version (eager)
# ---------------------------
try:
    from ._version import __version__
except Exception:
    __version__ = "unknown"
__all__.append("__version__")

# ---------------------------
# Eager, pure-Python helpers (don’t need the C++ extension)
# ---------------------------
try:
    from ._func_repsim import repsim_kernels, repsim_hsic

    __all__ += ["repsim_kernels", "repsim_hsic"]
except Exception:
    pass  # optional at import time

# ---------------------------
# Discover lazily-loadable API from _func_*.py
# ---------------------------
_NAMES_TO_MODULES: Dict[str, str] = {}
try:
    for m in pkgutil.iter_modules(list(__path__)):  # type: ignore[name-defined]
        if m.ispkg:
            continue
        if not m.name.startswith("_func_"):
            continue
        if m.name == "_func_repsim":
            continue  # <-- skip the helper module entirely

        funcname = m.name.replace("_func_", "", 1)
        if not funcname or funcname == "repsim":  # <-- extra safety
            continue
        if funcname in {"repsim_kernels", "repsim_hsic"}:
            continue

        _NAMES_TO_MODULES[funcname] = m.name
except Exception:
    _NAMES_TO_MODULES = {}

# Public API list (for dir() and "from repsim import *")
__all__ += sorted(_NAMES_TO_MODULES.keys())


# ---------------------------
# PEP 562: module-level lazy attribute access
# ---------------------------
def __getattr__(name: str):
    """Lazy-load functions from _func_*.py on first attribute access."""
    modname = _NAMES_TO_MODULES.get(name)
    if modname is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    # local import avoids any reliance on cleaned-up globals
    import importlib

    mod = importlib.import_module(f".{modname}", __name__)
    try:
        obj = getattr(mod, name)
    except AttributeError as e:
        raise AttributeError(
            f"{mod.__name__} does not define attribute {name!r} (check its __all__)."
        ) from e
    return obj  # real function with full docstring


def __dir__():
    # show standard names plus lazily-available ones
    return sorted(set(globals().keys()) | set(__all__))


# ---------------------------
# Minimal cleanup: DON'T remove _NAMES_TO_MODULES
# ---------------------------
for _n in ("Iterable", "Dict", "Annotations", "pkgutil"):
    globals().pop(_n, None)
del _n
