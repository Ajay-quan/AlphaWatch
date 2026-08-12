"""Leakage-safe labels, time-series folds, and uncertainty estimates.

These utilities intentionally operate on ordered observations. They reject the
random train/test splitting that would invalidate forward-looking factor labels.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import TypeAlias

import numpy as np

Timestamp: TypeAlias = date | datetime


@dataclass(frozen=True, slots=True)
class DecayLabels:
    """Forward Rank-IC deterioration labels and their continuous diagnostics."""

    label: np.ndarray
    forward_mean: np.ndarray
    trailing_mean: np.ndarray
    valid: np.ndarray


@dataclass(frozen=True, slots=True)
class Fold:
    """One chronological fold expressed as integer positions."""

    train_indices: np.ndarray
    test_indices: np.ndarray


def rank_ic_deterioration_labels(
    rank_ic: Sequence[float],
    horizon: int = 63,
    trailing_window: int = 252,
    deterioration_standard_deviations: float = 0.5,
) -> DecayLabels:
    """Label future Rank-IC deterioration without using future data in features.

    At date ``t``, trailing statistics end at ``t`` and the forward mean starts
    at ``t + 1``. A label is valid only if both full windows exist. The threshold
    scale is the trailing (not full-sample) standard deviation, preventing future
    observations from influencing the event definition.
    """
    if horizon < 1 or trailing_window < 2:
        raise ValueError("horizon must be >= 1 and trailing_window must be >= 2")
    if deterioration_standard_deviations < 0:
        raise ValueError("deterioration_standard_deviations must be non-negative")
    values = np.asarray(rank_ic, dtype=float)
    if values.ndim != 1:
        raise ValueError("rank_ic must be one-dimensional")
    n = len(values)
    labels = np.zeros(n, dtype=bool)
    forward = np.full(n, np.nan)
    trailing = np.full(n, np.nan)
    valid = np.zeros(n, dtype=bool)
    for position in range(trailing_window - 1, n - horizon):
        history = values[position - trailing_window + 1 : position + 1]
        future = values[position + 1 : position + horizon + 1]
        if not np.isfinite(history).all() or not np.isfinite(future).all():
            continue
        history_mean = float(history.mean())
        history_std = float(history.std(ddof=1))
        future_mean = float(future.mean())
        trailing[position] = history_mean
        forward[position] = future_mean
        valid[position] = True
        labels[position] = future_mean <= (
            history_mean - deterioration_standard_deviations * history_std
        )
    return DecayLabels(labels, forward, trailing, valid)


class PurgedWalkForwardSplit:
    """Expanding chronological folds with label-overlap purge and embargo.

    ``label_horizon`` removes training observations whose forward label interval
    overlaps the validation block. ``embargo`` leaves an additional exclusion
    gap before validation. Both are expressed in observation periods.
    """

    def __init__(
        self,
        n_splits: int = 3,
        test_size: int = 63,
        label_horizon: int = 63,
        embargo: int = 63,
        min_train_size: int = 252,
    ) -> None:
        if n_splits < 1 or test_size < 1 or label_horizon < 1 or embargo < 0:
            raise ValueError("invalid split parameters")
        if min_train_size < 1:
            raise ValueError("min_train_size must be positive")
        self.n_splits = n_splits
        self.test_size = test_size
        self.label_horizon = label_horizon
        self.embargo = embargo
        self.min_train_size = min_train_size

    def split(self, timestamps: Sequence[Timestamp]) -> list[Fold]:
        """Return ordered folds; timestamps must be strictly increasing."""
        if len(timestamps) < 2:
            raise ValueError("at least two timestamps are required")
        if any(
            right <= left for left, right in zip(timestamps, timestamps[1:], strict=False)
        ):
            raise ValueError("timestamps must be strictly increasing")
        n_observations = len(timestamps)
        first_test_start = n_observations - self.n_splits * self.test_size
        if first_test_start <= 0:
            raise ValueError("not enough observations for requested folds")
        folds: list[Fold] = []
        for split_number in range(self.n_splits):
            test_start = first_test_start + split_number * self.test_size
            test_end = min(test_start + self.test_size, n_observations)
            # Training labels finish at index train_index + label_horizon. The
            # final training label must end before the embargo begins.
            train_end = test_start - self.embargo - self.label_horizon
            if train_end < self.min_train_size:
                raise ValueError("fold does not retain the requested minimum training size")
            folds.append(
                Fold(
                    train_indices=np.arange(train_end, dtype=int),
                    test_indices=np.arange(test_start, test_end, dtype=int),
                )
            )
        return folds


def moving_block_bootstrap_ci(
    values: Sequence[float],
    block_length: int = 21,
    confidence: float = 0.95,
    n_resamples: int = 2_000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Return mean and percentile CI while preserving local time dependence."""
    observations = np.asarray(values, dtype=float)
    if observations.ndim != 1 or len(observations) < 2:
        raise ValueError("values must be a one-dimensional sequence of at least two values")
    if not np.isfinite(observations).all():
        raise ValueError("values must be finite")
    if not 1 <= block_length <= len(observations):
        raise ValueError("block_length must be between 1 and len(values)")
    if not 0 < confidence < 1 or n_resamples < 1:
        raise ValueError("confidence must be in (0, 1) and n_resamples positive")
    generator = np.random.default_rng(seed)
    n = len(observations)
    n_blocks = int(np.ceil(n / block_length))
    starts = generator.integers(0, n - block_length + 1, size=(n_resamples, n_blocks))
    offsets = np.arange(block_length)
    samples = observations[starts[:, :, None] + offsets].reshape(n_resamples, -1)[:, :n]
    estimates = samples.mean(axis=1)
    alpha = (1 - confidence) / 2
    return (
        float(observations.mean()),
        float(np.quantile(estimates, alpha)),
        float(np.quantile(estimates, 1 - alpha)),
    )
