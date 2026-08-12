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

    def estimate_trades(
        self, trades: dict[str, float], average_dollar_volume: dict[str, float], aum: float
    ) -> float:
        """Estimate portfolio-return cost using per-name ADV participation.

        Linear charges apply to dollars traded. The quadratic term grows with
        participation, so splitting an order across liquid names is cheaper than
        concentrating the same turnover in an illiquid name.
        """
        if aum <= 0:
            raise ValueError("aum must be positive")
        linear_bps = self.commission_bps + self.half_spread_bps + self.slippage_bps
        total = 0.0
        for security_id, trade_weight in trades.items():
            traded = abs(trade_weight)
            adv = average_dollar_volume.get(security_id, 0.0)
            if traded and adv <= 0:
                raise ValueError(f"positive ADV required for traded security {security_id}")
            participation = traded * aum / adv if traded else 0.0
            total += traded * (linear_bps + self.quadratic_bps * participation) / 10_000
        return total
