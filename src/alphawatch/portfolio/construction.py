from __future__ import annotations

from dataclasses import dataclass

from alphawatch.data.contracts import FactorSignal


@dataclass(frozen=True, slots=True)
class PortfolioWeight:
    security_id: str
    weight: float


def rank_long_short(signals: list[FactorSignal], quantile: float = 0.2) -> list[PortfolioWeight]:
    """Equal-weight tails, dollar neutral with unit gross exposure."""
    if not 0 < quantile <= 0.5:
        raise ValueError("quantile must be in (0, 0.5]")
    usable = sorted(
        (s for s in signals if s.raw_value is not None), key=lambda s: (s.raw_value, s.security_id)
    )
    if len(usable) < 2:
        return []
    count = max(1, int(len(usable) * quantile))
    count = min(count, len(usable) // 2)
    short, long = usable[:count], usable[-count:]
    side_weight = 0.5 / count
    return [
        *[PortfolioWeight(s.security_id, -side_weight) for s in short],
        *[PortfolioWeight(s.security_id, side_weight) for s in long],
    ]


def turnover(previous: dict[str, float], current: dict[str, float]) -> float:
    """One-way turnover: half the absolute portfolio weight change."""
    names = previous.keys() | current.keys()
    return 0.5 * sum(abs(current.get(name, 0.0) - previous.get(name, 0.0)) for name in names)


def weighted_long_short(
    signals: list[FactorSignal], auxiliaries: dict[str, float], quantile: float = 0.2
) -> list[PortfolioWeight]:
    """Weight each tail by a positive auxiliary such as market cap or inverse volatility."""
    if not 0 < quantile <= 0.5:
        raise ValueError("quantile must be in (0, 0.5]")
    usable = sorted(
        (s for s in signals if s.raw_value is not None and auxiliaries.get(s.security_id, 0) > 0),
        key=lambda signal: (signal.raw_value, signal.security_id),
    )
    count = min(max(1, int(len(usable) * quantile)), len(usable) // 2)
    if count == 0:
        return []
    tails = ((usable[:count], -1.0), (usable[-count:], 1.0))
    result: list[PortfolioWeight] = []
    for side, sign in tails:
        denominator = sum(auxiliaries[s.security_id] for s in side)
        result.extend(
            PortfolioWeight(s.security_id, sign * 0.5 * auxiliaries[s.security_id] / denominator)
            for s in side
        )
    return result
