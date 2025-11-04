
from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

import warnings
import numpy as np
from scipy import signal, ndimage

# Reuse utilities & metrics from the original base module to avoid duplication
from .baseline_base import read_spectrum_table, MetricResult, compute_metrics, small_param_grid_preset, baseline_method_names  # type: ignore

# Build a single Baseline() instance and a method dispatch table ONCE.
try:
    from pybaselines import Baseline as _PBBaseline
    _BASELINE = _PBBaseline()
except Exception as e:  # pragma: no cover
    raise ImportError("pybaselines is required. pip install pybaselines") from e

_SKIP = {"pentapy_solver", "banded_solver"}
_DISPATCH: Dict[str, callable] = {}
for _name in dir(_BASELINE):
    if _name.startswith("_") or _name in _SKIP:
        continue
    _attr = getattr(_BASELINE, _name)
    if callable(_attr):
        _DISPATCH[_name] = _attr
# Convenience alias (exposed name -> underlying callable)
_DISPATCH["poly"] = _BASELINE.poly  # type: ignore[attr-defined]

# --- Fast baseline correction (no pandas; single Baseline() and cached dispatch) ---
def fast_baseline_correction(
    intensities: Union[np.ndarray, List[float]],
    method: str = "airpls",
    return_baseline: bool = False,
    clip_negative: bool = False,
    **kwargs,
):
    """
    Faster drop-in replacement for baseline_base.baseline_correction:
    - Uses a module-level pybaselines.Baseline() singleton
    - Reuses a cached dispatch dictionary (no reflection in the hot loop)
    - Implements 'median_filter' and 'adaptive_window' locally
    - Applies the same polynomial rescaling heuristic for numerical stability
    """
    y = np.asarray(intensities, dtype=float).ravel()
    if y.ndim != 1:
        raise ValueError("intensities must be 1-D")
    method_lower = str(method).lower()

    # Numeric stability: scale polynomial family
    poly_like = {"poly", "modpoly", "imodpoly"}
    needs_rescale = method_lower in poly_like
    scale = 1.0
    y_for_baseline = y
    if needs_rescale:
        finite_mask = np.isfinite(y)
        if finite_mask.any():
            max_mag = float(np.max(np.abs(y[finite_mask])))
            if max_mag > 0:
                scale = max_mag
                y_for_baseline = y / scale

    bl = None

    # Custom filter shorthands (kept to match the original API)
    if method_lower == "median_filter":
        window_size = int(kwargs.pop("window_size", 101) or 101)
        if window_size % 2 == 0:
            window_size += 1
        bl = signal.medfilt(y_for_baseline, kernel_size=window_size)
    elif method_lower == "adaptive_window":
        window_size = int(kwargs.pop("window_size", 101) or 101)
        if window_size < 3:
            window_size = 3
        # simple uniform/box smoothing as a baseline proxy
        bl = ndimage.uniform_filter1d(y_for_baseline, size=window_size, mode="nearest")
    else:
        fn = _DISPATCH.get(method_lower)
        if fn is None:
            raise ValueError(f"Unknown baseline method: {method}")
        # Quiet the very common numerical warnings; caller may capture warnings if needed.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            # numpy.polyfit warnings (RankWarning) can occur for poly-like methods
            warnings.filterwarnings("ignore", message=".*Polyfit may be poorly conditioned.*")
            result = fn(y_for_baseline, **kwargs)  # pybaselines returns (baseline, params)
        if isinstance(result, tuple) and len(result) >= 1:
            bl = np.asarray(result[0], dtype=float).ravel()
        else:
            bl = np.asarray(result, dtype=float).ravel()

    if bl is None:
        raise RuntimeError(f"Baseline method '{method}' produced no result.")
    if bl.shape != y_for_baseline.shape:
        raise RuntimeError(f"Baseline method '{method}' returned shape {bl.shape}, expected {y_for_baseline.shape}.")

    if needs_rescale and scale != 1.0:
        bl = bl * scale

    y_corr = y - bl
    if clip_negative:
        y_corr = np.maximum(y_corr, 0.0)

    return (y_corr, bl) if return_baseline else y_corr
