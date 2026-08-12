"""Chronological validation with purging and embargoes for forward-labelled research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from .contracts import ResearchIntegrityError


@dataclass(frozen=True)
class PurgedFold:
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    validation_start: datetime
    validation_end: datetime


def chronological_purged_folds(
    prediction_times: Sequence[datetime],
    label_end_times: Sequence[datetime],
    n_splits: int,
    embargo_observations: int = 0,
    min_train_size: int = 1,
    training_window_observations: int | None = None,
) -> list[PurgedFold]:
    """Make walk-forward folds, removing training labels that overlap validation.

    A training row is retained only if its label fully resolves before the validation block
    begins. The embargo removes the observations immediately preceding validation as an
    additional safeguard for serial dependence and implementation overlap.
    """
    n = len(prediction_times)
    if n != len(label_end_times) or n < 2:
        raise ResearchIntegrityError("prediction and label-end times must be equally sized with >= 2 rows")
    if (
        n_splits < 1
        or embargo_observations < 0
        or min_train_size < 1
        or training_window_observations is not None and training_window_observations < 1
    ):
        raise ResearchIntegrityError("invalid fold settings")
    if any(a >= b for a, b in zip(prediction_times, prediction_times[1:])):
        raise ResearchIntegrityError("prediction times must be strictly increasing")
    if any(end < start for start, end in zip(prediction_times, label_end_times)):
        raise ResearchIntegrityError("label end cannot precede its prediction timestamp")

    first_validation = max(min_train_size, n // (n_splits + 1))
    remaining = n - first_validation
    block = max(1, remaining // n_splits)
    folds: list[PurgedFold] = []
    for split in range(n_splits):
        val_start = first_validation + split * block
        val_stop = n if split == n_splits - 1 else min(n, val_start + block)
        if val_start >= n:
            break
        cutoff = max(0, val_start - embargo_observations)
        train_start = (
            max(0, cutoff - training_window_observations)
            if training_window_observations is not None
            else 0
        )
        train = tuple(
            i
            for i in range(train_start, cutoff)
            if label_end_times[i] < prediction_times[val_start]
        )
        if len(train) < min_train_size:
            continue
        folds.append(
            PurgedFold(
                train_indices=train,
                validation_indices=tuple(range(val_start, val_stop)),
                validation_start=prediction_times[val_start],
                validation_end=prediction_times[val_stop - 1],
            )
        )
    if not folds:
        raise ResearchIntegrityError("no valid folds; enlarge history or reduce purge/embargo settings")
    return folds
