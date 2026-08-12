"""Forward targets that keep their future realization separate from input availability."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np

from .contracts import ResearchIntegrityError, TimedLabel


@dataclass(frozen=True)
class ForwardLabel:
    prediction_timestamp: datetime
    label_end: datetime
    value: float
    available_at: datetime

    def as_timed_label(self) -> TimedLabel:
        """Adapt the label to the training-time availability contract."""
        return TimedLabel(self.prediction_timestamp, self.available_at, self.value)


def _validate_forward_inputs(
    timestamps: Sequence[datetime], values: Sequence[float], horizon: int
) -> np.ndarray:
    if horizon < 1 or len(timestamps) != len(values):
        raise ResearchIntegrityError("horizon must be positive and timestamps must match values")
    if any(not isinstance(timestamp, datetime) for timestamp in timestamps):
        raise ResearchIntegrityError("label timestamps must be datetime instances")
    if any(left >= right for left, right in zip(timestamps, timestamps[1:])):
        raise ResearchIntegrityError("label timestamps must be strictly increasing")
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ResearchIntegrityError("forward values must be a finite one-dimensional series")
    return x


def future_rank_ic_deterioration(
    timestamps: Sequence[datetime],
    rank_ic: Sequence[float],
    horizon: int,
    deterioration_threshold: float,
) -> list[ForwardLabel]:
    """Label whether mean Rank IC over the next horizon falls below a fixed threshold.

    Labels are only available once their entire forward window has elapsed. Thresholds must
    be defined in a frozen experiment configuration, never selected on the final test set.
    """
    x = _validate_forward_inputs(timestamps, rank_ic, horizon)
    labels: list[ForwardLabel] = []
    for start in range(len(x) - horizon):
        end = start + horizon
        future_mean = float(np.mean(x[start + 1 : end + 1]))
        labels.append(
            ForwardLabel(
                prediction_timestamp=timestamps[start],
                label_end=timestamps[end],
                value=float(future_mean < deterioration_threshold),
                available_at=timestamps[end],
            )
        )
    return labels


def future_mean_deterioration(
    timestamps: Sequence[datetime],
    values: Sequence[float],
    horizon: int,
    deterioration_threshold: float,
) -> list[ForwardLabel]:
    """Generic resolved forward label for Rank IC or Sharpe deterioration (Targets 1--2)."""
    x = _validate_forward_inputs(timestamps, values, horizon)
    return [
        ForwardLabel(
            timestamps[start],
            timestamps[start + horizon],
            float(x[start + 1 : start + horizon + 1].mean() < deterioration_threshold),
            timestamps[start + horizon],
        )
        for start in range(len(x) - horizon)
    ]


def future_minimum_breach(
    timestamps: Sequence[datetime],
    values: Sequence[float],
    horizon: int,
    threshold: float,
) -> list[ForwardLabel]:
    """Resolved event label for future drawdown or extreme-downside breaches (Targets 3 and 5)."""
    x = _validate_forward_inputs(timestamps, values, horizon)
    return [
        ForwardLabel(
            timestamps[start],
            timestamps[start + horizon],
            float(x[start + 1 : start + horizon + 1].min() <= threshold),
            timestamps[start + horizon],
        )
        for start in range(len(x) - horizon)
    ]


def future_structural_break(
    timestamps: Sequence[datetime], break_events: Sequence[bool], horizon: int
) -> list[ForwardLabel]:
    """Resolved event label for a subsequently detected structural break (Target 4)."""
    return future_minimum_breach(timestamps, [0.0 if event else 1.0 for event in break_events], horizon, 0.0)
