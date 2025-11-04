
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import json
import time
import traceback
from collections import Counter

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from tqdm import tqdm
from scipy.stats import rankdata
import warnings

# Reuse the existing helpers from the original modules
from .baseline_base import read_spectrum_table, small_param_grid_preset, baseline_method_names, compute_metrics  # type: ignore
from .baseline_base_fast import fast_baseline_correction  # our accelerated drop-in

# ------------------------ utilities ------------------------
def _expand_methods(methods: Optional[List[str]], param_grid: Optional[Dict[str, List[Dict]]]) -> Tuple[List[str], List[Tuple[str, Dict]]]:
    all_methods = methods or baseline_method_names()
    labels, specs = [], []
    for m in all_methods:
        grids = (param_grid or {}).get(m, [dict()])
        for k in grids:
            label = f"{m}" if not k else f"{m}({', '.join(f'{kk}={vv}' for kk, vv in k.items())})"
            labels.append(label)
            specs.append((m, k))
    return labels, specs

def _row_ranks(values: np.ndarray, ascending: bool) -> np.ndarray:
    ranks = np.full(values.shape, np.nan, dtype=float)
    for i, row in enumerate(values):
        mask = np.isfinite(row)
        if not mask.any():
            continue
        data = row[mask]
        ranked = rankdata(data if ascending else -data, method="average")
        ranks[i, np.flatnonzero(mask)] = ranked
    return ranks

def _frame_from_array(sample_names: List[str], labels: List[str], array: np.ndarray) -> pl.DataFrame:
    data = {"sample": sample_names}
    for idx, label in enumerate(labels):
        data[label] = array[:, idx]
    return pl.DataFrame(data)

def _composite_rank(rfzn: np.ndarray, nar: np.ndarray, snr: np.ndarray, bbi: np.ndarray, br: np.ndarray, nbc: np.ndarray,
                    metric_names: Tuple[str, ...]) -> np.ndarray:
    # Build a list of (array, minimize?) in a fixed order
    pools = {
        "rfzn": (rfzn, True),
        "nar":  (nar,  True),
        "snr":  (snr,  False),
        "bbi":  (bbi,  True),
        "br":   (br,   True),
        "nbc":  (nbc,  True),
    }
    chosen = [pools[name] for name in metric_names]
    ranks = [_row_ranks(arr, ascending=minimize) for arr, minimize in chosen]
    ranks = np.stack(ranks, axis=0)  # [n_metrics, n_samples, n_methods]
    with np.errstate(invalid="ignore"):
        comp = np.nanmedian(ranks, axis=0)  # [n_samples, n_methods]
    return comp

def _metric_winners(values: np.ndarray, labels: List[str], minimize: bool) -> List[Optional[str]]:
    winners: List[Optional[str]] = []
    for row in values:
        mask = np.isfinite(row)
        if not mask.any():
            winners.append(None)
            continue
        idx = np.nanargmin(row) if minimize else np.nanargmax(row)
        winners.append(labels[int(idx)])
    return winners

# ------------------------ evaluator (fast + diagnostic) ------------------------
@dataclass
class BaselineMethodEvaluatorFast:
    """Faster evaluator with diagnostics (warnings+errors+timings).

    It keeps the public surface similar to the original BaselineMethodEvaluator,
    but adds:
      - prefer_threads: use joblib threads (often faster for NumPy/SciPy work)
      - suppress_known_warnings: silence console spam but capture a structured log
      - per-method time measurement
      - per-method warning & exception capture
    """

    data_dir: Union[str, Path]
    pattern: str = "*.csv"
    recursive: bool = False
    methods: Optional[List[str]] = None
    param_grid: Optional[Dict[str, List[Dict]]] = None
    use_small_param_preset: bool = False
    eval_clip_negative: bool = False
    topk_for_snr: int = 5
    raw_noise_quantile: float = 0.2
    flat_windows: Optional[List[Tuple[float, float]]] = None
    metrics_for_composite: Tuple[str, ...] = ("rfzn", "nar", "snr", "bbi", "br", "nbc")
    n_jobs: int = -1

    # new knobs
    prefer_threads: bool = True
    suppress_known_warnings: bool = True

    # populated at runtime
    files: List[Path] = field(default_factory=list, init=False)
    labels: List[str] = field(default_factory=list, init=False)
    specs: List[Tuple[str, Dict]] = field(default_factory=list, init=False)

    # results
    _rfzn: Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _nar:  Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _snr:  Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _bbi:  Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _br:   Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _nbc:  Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _comp: Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _win_counts: Optional[pl.DataFrame] = field(default=None, init=False, repr=False)
    _overall_best: Optional[str] = field(default=None, init=False, repr=False)

    # diagnostics
    _error_log: List[Dict] = field(default_factory=list, init=False, repr=False)
    _warn_log:  List[Dict] = field(default_factory=list, init=False, repr=False)
    _time_log:  List[Dict] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        self.data_dir = Path(self.data_dir)
        glob_pat = f"**/{self.pattern}" if self.recursive else self.pattern
        self.files = sorted(self.data_dir.glob(glob_pat))
        if not self.files:
            raise FileNotFoundError(f"No files match {glob_pat} in {self.data_dir}")
        if self.param_grid is None and self.use_small_param_preset:
            self.param_grid = small_param_grid_preset()
        self.labels, self.specs = _expand_methods(self.methods, self.param_grid)

    # -- core ---------------------------------------------------------
    def _noise_mask_from_quantile(self, y_raw: np.ndarray, q: float) -> np.ndarray:
        y_raw = np.asarray(y_raw, dtype=float).ravel()
        finite = np.isfinite(y_raw)
        if not finite.any():
            raise ValueError("No finite values in spectrum.")
        thresh = np.nanquantile(y_raw[finite], q)
        return (y_raw <= thresh) & finite

    def _score_one(self, file: Path):
        """Return metrics arrays + diagnostics for one file."""
        df = read_spectrum_table(file)
        x = np.asarray(df["mz"].to_numpy(), dtype=float)
        y = np.asarray(df["intensity"].to_numpy(), dtype=float)

        # one noise mask per file
        if self.flat_windows:
            noise_mask = np.zeros_like(x, dtype=bool)
            for lo, hi in self.flat_windows:
                noise_mask |= (x >= float(lo)) & (x <= float(hi))
        else:
            noise_mask = self._noise_mask_from_quantile(y, self.raw_noise_quantile)

        rfzn_row = np.empty(len(self.specs), dtype=float)
        nar_row  = np.empty_like(rfzn_row)
        snr_row  = np.empty_like(rfzn_row)
        bbi_row  = np.empty_like(rfzn_row)
        br_row   = np.empty_like(rfzn_row)
        nbc_row  = np.empty_like(rfzn_row)

        err_entries: List[Dict] = []
        warn_entries: List[Dict] = []
        time_entries: List[Dict] = []

        for j, (method, kwargs) in enumerate(self.specs):
            t0 = time.perf_counter()
            with warnings.catch_warnings(record=True) as wrec:
                if self.suppress_known_warnings:
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    warnings.filterwarnings("ignore", message=".*Polyfit may be poorly conditioned.*")
                else:
                    warnings.simplefilter("always")
                try:
                    # Always evaluate with clip_negative=False so NAR/NBC/BBI are meaningful
                    y_corr, bl = fast_baseline_correction(
                        y, method=method, return_baseline=True, clip_negative=self.eval_clip_negative, **kwargs
                    )
                    met = compute_metrics(y_corr, y, bl, x, noise_mask=noise_mask, topk=self.topk_for_snr,
                                          raw_noise_quantile=self.raw_noise_quantile)
                    rfzn_row[j] = met.rfzn
                    nar_row[j]  = met.nar
                    snr_row[j]  = met.snr
                    bbi_row[j]  = met.bbi
                    br_row[j]   = met.br
                    nbc_row[j]  = met.nbc
                except Exception as e:
                    rfzn_row[j] = np.nan; nar_row[j] = np.nan; snr_row[j] = np.nan
                    bbi_row[j]  = np.nan; br_row[j]  = np.nan; nbc_row[j]  = np.nan
                    tb = traceback.format_exc(limit=3)
                    err_entries.append({
                        "file": file.name,
                        "method": method,
                        "params": json.dumps(kwargs, sort_keys=True),
                        "exc_type": type(e).__name__,
                        "exc_msg": str(e),
                        "traceback": tb,
                    })
                finally:
                    dt = (time.perf_counter() - t0) * 1000.0
                    time_entries.append({
                        "file": file.name,
                        "method": method,
                        "params": json.dumps(kwargs, sort_keys=True),
                        "ms": float(dt),
                    })
                    # log warnings (if any)
                    for w in (wrec or []):
                        warn_entries.append({
                            "file": file.name,
                            "method": method,
                            "params": json.dumps(kwargs, sort_keys=True),
                            "category": w.category.__name__,
                            "message": str(w.message),
                        })

        return file.name, rfzn_row, nar_row, snr_row, bbi_row, br_row, nbc_row, err_entries, warn_entries, time_entries

    def evaluate(self, noise_quantile: Optional[float] = None, n_jobs: Optional[int] = None):
        if noise_quantile is not None:
            self.raw_noise_quantile = float(noise_quantile)
        if n_jobs is not None:
            self.n_jobs = int(n_jobs)

        worker = delayed(self._score_one)
        it = (worker(f) for f in self.files)
        parallel = Parallel(
            n_jobs=self.n_jobs,
            prefer=("threads" if self.prefer_threads else "processes"),
            batch_size="auto",
        )
        results = parallel(tqdm(it, total=len(self.files), desc="baseline eval (fast)", ncols=96))

        # assemble
        sample_names = [r[0] for r in results]
        rfzn_arr = np.vstack([r[1] for r in results]); nar_arr  = np.vstack([r[2] for r in results])
        snr_arr  = np.vstack([r[3] for r in results]); bbi_arr  = np.vstack([r[4] for r in results])
        br_arr   = np.vstack([r[5] for r in results]); nbc_arr  = np.vstack([r[6] for r in results])

        rfzn = _frame_from_array(sample_names, self.labels, rfzn_arr)
        nar  = _frame_from_array(sample_names, self.labels, nar_arr)
        snr  = _frame_from_array(sample_names, self.labels, snr_arr)
        bbi  = _frame_from_array(sample_names, self.labels, bbi_arr)
        br   = _frame_from_array(sample_names, self.labels, br_arr)
        nbc  = _frame_from_array(sample_names, self.labels, nbc_arr)

        comp = _composite_rank(rfzn_arr, nar_arr, snr_arr, bbi_arr, br_arr, nbc_arr, self.metrics_for_composite)
        comp_df = _frame_from_array(sample_names, self.labels, comp)

        # overall ranking (median across samples)
        values = np.nanmedian(comp, axis=0)  # lower is better
        order = np.argsort(values)
        methods = [self.labels[i] for i in order]
        ordered_pairs = list(zip(methods, values[order]))
        overall_best = next((label for label, val in ordered_pairs if np.isfinite(val)),
                            ordered_pairs[0][0] if ordered_pairs else None)

        # metric winners (per file)
        def _w(values, minimize): return [w for w in _metric_winners(values, self.labels, minimize=minimize) if w]
        win_counters = {
            "RFZN": Counter(_w(rfzn_arr, True)),
            "NAR":  Counter(_w(nar_arr,  True)),
            "SNR":  Counter(_w(snr_arr,  False)),
            "BBI":  Counter(_w(bbi_arr,  True)),
            "BR":   Counter(_w(br_arr,   True)),
            "NBC":  Counter(_w(nbc_arr,  True)),
        }
        win_counts = pl.DataFrame({
            "method": self.labels,
            "RFZN": [int(win_counters["RFZN"].get(label, 0)) for label in self.labels],
            "NAR":  [int(win_counters["NAR"].get(label, 0)) for label in self.labels],
            "SNR":  [int(win_counters["SNR"].get(label, 0)) for label in self.labels],
            "BBI":  [int(win_counters["BBI"].get(label, 0)) for label in self.labels],
            "BR":   [int(win_counters["BR"].get(label, 0)) for label in self.labels],
            "NBC":  [int(win_counters["NBC"].get(label, 0)) for label in self.labels],
        })

        # stash
        self._rfzn, self._nar, self._snr, self._bbi, self._br, self._nbc = rfzn, nar, snr, bbi, br, nbc
        self._comp, self._win_counts, self._overall_best = comp_df, win_counts, overall_best

        # diagnostics
        self._error_log = sum((r[7] for r in results), [])
        self._warn_log  = sum((r[8] for r in results), [])
        self._time_log  = sum((r[9] for r in results), [])

        return self  # fluent

    # -- exports ------------------------------------------------------
    def write_outputs(self, out_dir: Union[str, Path]) -> List[Path]:
        if self._comp is None:
            raise RuntimeError("Call evaluate() first.")
        out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
        saved: List[Path] = []

        # Export numeric results
        self._rfzn.write_csv(out_dir / "rfzn_by_file.csv")
        self._nar.write_csv(out_dir / "nar_by_file.csv")
        self._snr.write_csv(out_dir / "snr_by_file.csv")
        self._bbi.write_csv(out_dir / "bbi_by_file.csv")
        self._br.write_csv(out_dir / "br_by_file.csv")
        self._nbc.write_csv(out_dir / "nbc_by_file.csv")
        self._comp.write_csv(out_dir / "composite_rank_by_file.csv")
        self._win_counts.write_csv(out_dir / "win_counts_by_metric.csv")

        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump({
                "overall_best_method": self._overall_best,
                "metrics_for_composite": list(self.metrics_for_composite)
            }, f, indent=2)

        # Diagnostics
        if self._error_log:
            pl.DataFrame(self._error_log).write_csv(out_dir / "errors_by_method.csv")
        if self._warn_log:
            pl.DataFrame(self._warn_log).write_csv(out_dir / "warnings_by_method.csv")
        if self._time_log:
            pl.DataFrame(self._time_log).write_csv(out_dir / "timings_by_method.csv")

        return saved

    # Optional: a quick-look overlay for one file
    def preview_overlay(self, file: Union[str, Path], methods: Optional[List[str]] = None,
                        max_methods: int = 5, save_to: Optional[Union[str, Path]] = None):
        df = read_spectrum_table(file)
        x = np.asarray(df["mz"].to_numpy(), dtype=float)
        y = np.asarray(df["intensity"].to_numpy(), dtype=float)

        if not methods:
            # sample 1-2 from each family
            methods = ["asls", "arpls", "modpoly", "imodpoly", "airpls", "drpls"]

        plt.figure(figsize=(10, 4.2))
        plt.plot(x, y, lw=1, alpha=0.8, label="raw")
        for m in methods[:max_methods]:
            try:
                y_corr, bl = fast_baseline_correction(y, method=m, return_baseline=True, clip_negative=False)
            except Exception:
                continue
            plt.plot(x, bl, lw=1, linestyle=":", label=f"baseline: {m}")
            plt.plot(x, y_corr, lw=1, label=f"corrected: {m}")
        plt.xlabel("m/z"); plt.ylabel("Intensity (a.u.)"); plt.title(Path(file).name)
        plt.legend(ncol=2, frameon=False); plt.tight_layout()
        if save_to:
            save_to = Path(save_to); save_to.parent.mkdir(parents=True, exist_ok=True)
            for ext in (".pdf", ".png"):
                plt.savefig(save_to.with_suffix(ext), bbox_inches="tight", dpi=300)
        plt.show()
