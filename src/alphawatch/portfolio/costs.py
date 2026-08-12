from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LinearQuadraticCostModel:
    """Costs in decimal return units for a one-way turnover fraction."""

    version: str
    commission_bps: float
    half_spread_bps: float
    slippage_bps: float
    quadratic_bps: float = 0.0

    def estimate(self, one_way_turnover: float) -> float:
        if one_way_turnover < 0:
            raise ValueError("turnover cannot be negative")
        linear_bps = self.commission_bps + self.half_spread_bps + self.slippage_bps
        return (linear_bps * one_way_turnover + self.quadratic_bps * one_way_turnover**2) / 10_000
