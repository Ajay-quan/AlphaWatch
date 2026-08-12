"""Shared fail-closed contracts for research data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Iterable


class ResearchIntegrityError(ValueError):
    """Raised when a run cannot support an auditable research conclusion."""


class AvailabilityViolation(ResearchIntegrityError):
    """Raised when an observation was not knowable at prediction time."""


@dataclass(frozen=True)
class TimedObservation:
    """A value with its economic time and true public availability time."""

    entity_id: str
    observed_at: datetime
    available_at: datetime
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.observed_at, datetime) or not isinstance(self.available_at, datetime):
            raise ResearchIntegrityError("observation timestamps must be datetime instances")
        if self.available_at < self.observed_at:
            raise ResearchIntegrityError("observation availability cannot precede observation time")
        if not math.isfinite(self.value):
            raise ResearchIntegrityError("observation value must be finite")


@dataclass(frozen=True)
class TimedLabel:
    """A realized target eligible for training only after it resolves."""

    prediction_timestamp: datetime
    available_at: datetime
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_timestamp, datetime) or not isinstance(self.available_at, datetime):
            raise ResearchIntegrityError("label timestamps must be datetime instances")
        if self.available_at < self.prediction_timestamp:
            raise ResearchIntegrityError("label availability cannot precede prediction time")
        if not math.isfinite(self.value):
            raise ResearchIntegrityError("label value must be finite")


def assert_available_as_of(
    observations: Iterable[TimedObservation], prediction_timestamp: datetime
) -> None:
    """Reject any observation that was unavailable at the prediction timestamp.

    This is intentionally a hard failure, not a warning. Call it after every join and
    before fitting/scoring a historical model.
    """
    violations = [
        item
        for item in observations
        if item.available_at > prediction_timestamp
    ]
    if violations:
        sample = ", ".join(
            f"{item.entity_id} available {item.available_at.isoformat()}"
            for item in violations[:3]
        )
        raise AvailabilityViolation(
            f"{len(violations)} observation(s) violate available_at <= prediction_timestamp: {sample}"
        )


def assert_labels_resolved_as_of(
    labels: Iterable[TimedLabel], training_timestamp: datetime
) -> None:
    """Reject labels whose outcomes were unknown in the training snapshot."""
    unresolved = [label for label in labels if label.available_at > training_timestamp]
    if unresolved:
        sample = ", ".join(label.available_at.isoformat() for label in unresolved[:3])
        raise AvailabilityViolation(
            f"{len(unresolved)} forward label(s) were unresolved at training time: {sample}"
        )
