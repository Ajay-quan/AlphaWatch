from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import polars as pl

from alphawatch.data.contracts import require_utc
from alphawatch.exceptions import DataContractError, LookAheadError


@dataclass(frozen=True, slots=True)
class QualityReport:
    rows: int
    duplicate_rows: int
    null_counts: dict[str, int]


def validate_prices(frame: pl.DataFrame) -> QualityReport:
    required = {"security_id", "session", "available_at", "adjusted_close", "dollar_volume"}
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"price schema missing columns: {sorted(missing)}")
    nulls = {name: frame[name].null_count() for name in required}
    if any(nulls[name] for name in ("security_id", "session", "available_at", "adjusted_close")):
        raise DataContractError(f"nulls in required price fields: {nulls}")
    invalid = frame.filter((pl.col("adjusted_close") <= 0) | (pl.col("dollar_volume") < 0)).height
    if invalid:
        raise DataContractError(f"{invalid} invalid price/volume rows")
    duplicates = frame.select(pl.struct("security_id", "session").is_duplicated().sum()).item()
    if duplicates:
        raise DataContractError(f"{duplicates} duplicate security/session rows")
    return QualityReport(frame.height, int(duplicates), nulls)


def enforce_frame_pit(frame: pl.DataFrame, prediction_time: datetime) -> None:
    """Fail closed unless all records were available in UTC at prediction time."""
    require_utc(prediction_time, "prediction_time")
    if "available_at" not in frame.columns:
        raise DataContractError("available_at is mandatory")
    available_type = frame.schema["available_at"]
    if available_type.base_type() != pl.Datetime or available_type.time_zone != "UTC":
        raise DataContractError("available_at must be a UTC timezone-aware datetime column")
    if frame["available_at"].null_count():
        raise DataContractError("available_at cannot contain nulls")
    count = frame.filter(pl.col("available_at") > pl.lit(prediction_time)).height
    if count:
        raise LookAheadError(f"{count} rows are unavailable at prediction_time")
