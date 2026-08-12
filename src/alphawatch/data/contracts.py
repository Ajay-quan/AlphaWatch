from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from math import isfinite

from alphawatch.exceptions import DataContractError


def require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DataContractError(f"{field} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise DataContractError(f"{field} must be normalized to UTC")


class DataLayer(StrEnum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


@dataclass(frozen=True, slots=True)
class Observation:
    security_id: str
    observation_time: datetime
    available_at: datetime
    feature_name: str
    value: float
    dataset_version: str
    source: str

    def __post_init__(self) -> None:
        require_utc(self.observation_time, "observation_time")
        require_utc(self.available_at, "available_at")
        if not self.security_id or not self.feature_name or not self.dataset_version:
            raise DataContractError("identity, feature, and version fields must be non-empty")
        if not isfinite(self.value):
            raise DataContractError("observation value must be finite")


@dataclass(frozen=True, slots=True)
class PriceBar:
    security_id: str
    session: date
    available_at: datetime
    adjusted_close: Decimal
    dollar_volume: Decimal | None = None

    def __post_init__(self) -> None:
        require_utc(self.available_at, "available_at")
        if not self.security_id:
            raise DataContractError("security_id must be non-empty")
        if self.adjusted_close <= 0:
            raise DataContractError("adjusted_close must be positive")
        if self.dollar_volume is not None and self.dollar_volume < 0:
            raise DataContractError("dollar_volume cannot be negative")


@dataclass(frozen=True, slots=True)
class FactorSignal:
    security_id: str
    as_of: datetime
    available_at: datetime
    factor_name: str
    factor_version: str
    raw_value: float | None

    def __post_init__(self) -> None:
        require_utc(self.as_of, "as_of")
        require_utc(self.available_at, "available_at")
        if self.raw_value is not None and not isfinite(self.raw_value):
            raise DataContractError("factor value must be finite or None")
