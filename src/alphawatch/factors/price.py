from __future__ import annotations

from math import log, sqrt
from statistics import stdev

from alphawatch.data.contracts import FactorSignal, PriceBar
from alphawatch.factors.base import Factor, FactorContext


def _signal(
    factor: Factor, bars: list[PriceBar], context: FactorContext, value: float | None
) -> FactorSignal:
    return FactorSignal(
        security_id=bars[-1].security_id,
        as_of=context.prediction_time,
        available_at=max(bar.available_at for bar in bars),
        factor_name=factor.name,
        factor_version=factor.version,
        raw_value=value,
    )


class Momentum12Minus1(Factor):
    """Skip-month momentum: P[t-21] / P[t-252] - 1 by default."""

    name = "momentum_12_minus_1"
    version = "1.0.0"

    def __init__(self, lookback: int = 252, skip: int = 21) -> None:
        if lookback <= skip or skip < 1:
            raise ValueError("lookback must exceed a positive skip")
        self.lookback, self.skip = lookback, skip

    def compute_one(self, bars: list[PriceBar], context: FactorContext) -> FactorSignal:
        required = max(context.minimum_observations, self.lookback + 1)
        value = None
        if len(bars) >= required:
            start = float(bars[-(self.lookback + 1)].adjusted_close)
            end = float(bars[-(self.skip + 1)].adjusted_close)
            value = end / start - 1.0
        return _signal(self, bars, context, value)


class ShortTermReversal(Factor):
    name = "short_term_reversal"
    version = "1.0.0"

    def __init__(self, lookback: int = 21) -> None:
        if lookback < 1:
            raise ValueError("lookback must be positive")
        self.lookback = lookback

    def compute_one(self, bars: list[PriceBar], context: FactorContext) -> FactorSignal:
        required = max(context.minimum_observations, self.lookback + 1)
        value = None
        if len(bars) >= required:
            past = float(bars[-(self.lookback + 1)].adjusted_close)
            latest = float(bars[-1].adjusted_close)
            value = -(latest / past - 1.0)
        return _signal(self, bars, context, value)


class LowVolatility(Factor):
    name = "low_volatility"
    version = "1.0.0"

    def __init__(self, lookback: int = 252, annualization: int = 252) -> None:
        if lookback < 2 or annualization < 1:
            raise ValueError("invalid volatility settings")
        self.lookback, self.annualization = lookback, annualization

    def compute_one(self, bars: list[PriceBar], context: FactorContext) -> FactorSignal:
        required = max(context.minimum_observations, self.lookback + 1)
        value = None
        if len(bars) >= required:
            window = bars[-(self.lookback + 1) :]
            returns = [
                log(float(right.adjusted_close) / float(left.adjusted_close))
                for left, right in zip(window, window[1:], strict=False)
            ]
            value = -stdev(returns) * sqrt(self.annualization)
        return _signal(self, bars, context, value)
