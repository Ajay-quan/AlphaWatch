from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from alphawatch.data.contracts import FactorSignal, PriceBar
from alphawatch.data.pit import assert_point_in_time


@dataclass(frozen=True, slots=True)
class FactorContext:
    prediction_time: datetime
    minimum_observations: int


class Factor(ABC):
    name: str
    version: str

    def compute(self, bars: list[PriceBar], context: FactorContext) -> list[FactorSignal]:
        assert_point_in_time(bars, context.prediction_time)
        grouped: dict[str, list[PriceBar]] = {}
        for bar in bars:
            grouped.setdefault(bar.security_id, []).append(bar)
        return [
            self.compute_one(sorted(rows, key=lambda x: x.session), context)
            for rows in grouped.values()
        ]

    @abstractmethod
    def compute_one(self, bars: list[PriceBar], context: FactorContext) -> FactorSignal:
        raise NotImplementedError
