from __future__ import annotations

from datetime import datetime
from typing import Protocol, TypeVar

from alphawatch.data.contracts import require_utc
from alphawatch.exceptions import DataContractError, LookAheadError


class Available(Protocol):
    @property
    def available_at(self) -> datetime: ...


T = TypeVar("T", bound=Available)


def assert_point_in_time(records: list[T] | tuple[T, ...], prediction_time: datetime) -> None:
    """Fail closed if any record was unavailable at the prediction timestamp."""
    require_utc(prediction_time, "prediction_time")
    offenders = [r.available_at for r in records if r.available_at > prediction_time]
    if offenders:
        earliest = min(offenders).isoformat()
        raise LookAheadError(
            f"{len(offenders)} record(s) violate available_at <= prediction_time; "
            f"earliest unavailable record: {earliest}"
        )


def asof_snapshot(records: list[T], prediction_time: datetime) -> list[T]:
    """Return records actually known by a timestamp; reject malformed timestamps."""
    require_utc(prediction_time, "prediction_time")
    for record in records:
        if record.available_at.tzinfo is None:
            raise DataContractError("record available_at must be timezone-aware")
    return [record for record in records if record.available_at <= prediction_time]
