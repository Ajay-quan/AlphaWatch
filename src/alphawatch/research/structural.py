"""Transparent first-pass structural-instability diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class CusumResult:
    """One-sided cumulative-sum evidence and threshold-crossing events."""

    statistic: np.ndarray
    threshold: float
    event_indices: np.ndarray
    reference_mean: float
    reference_scale: float


def negative_mean_cusum(
    values: Sequence[float], training_window: int, threshold_scale: float = 5.0
) -> CusumResult:
    """Detect sustained negative shifts using only an initial reference window.

    This is an interpretable surveillance statistic, not proof of a structural
    break. Calibrate ``threshold_scale`` on predeclared training or synthetic data,
    then report the full statistic and false-alarm rate alongside any event.
    """
    observations = np.asarray(values, dtype=float)
    if observations.ndim != 1 or len(observations) <= training_window:
        raise ValueError("values must exceed a positive training_window")
    if not np.isfinite(observations).all() or training_window < 2 or threshold_scale <= 0:
        raise ValueError("values must be finite; training_window >= 2; threshold_scale positive")
    reference = observations[:training_window]
    scale = float(reference.std(ddof=1))
    if scale == 0:
        raise ValueError("reference window must have non-zero variation")
    mean = float(reference.mean())
    threshold = threshold_scale * scale
    statistic = np.zeros(len(observations), dtype=float)
    events: list[int] = []
    for index in range(training_window, len(observations)):
        increment = (mean - observations[index])
        statistic[index] = max(0.0, statistic[index - 1] + increment)
        if statistic[index] >= threshold:
            events.append(index)
            statistic[index] = 0.0
    return CusumResult(statistic, threshold, np.asarray(events, dtype=int), mean, scale)
