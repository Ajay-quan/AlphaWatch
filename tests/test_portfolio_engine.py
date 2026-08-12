from datetime import date

import polars as pl
import pytest

from alphawatch.portfolio.costs import LinearQuadraticCostModel
from alphawatch.portfolio.engine import PortfolioConfig, Weighting, construct_target, run_portfolio


def rows() -> list[dict[str, object]]:
    return [
        {
            "security_id": name,
            "signal": float(i),
            "market_cap": float(100 + i),
            "volatility": float(i + 1),
            "average_dollar_volume": 1_000_000_000.0,
        }
        for i, name in enumerate("abcdef")
    ]


@pytest.mark.parametrize("weighting", list(Weighting))
def test_all_weighting_modes_are_constrained(weighting: Weighting) -> None:
    target = construct_target(
        rows(),
        PortfolioConfig(weighting=weighting, quantile=0.25, max_absolute_weight=0.5),
    )
    assert sum(target.values()) == pytest.approx(0)
    assert sum(abs(value) for value in target.values()) == pytest.approx(1)


def test_exits_are_included_in_turnover_and_holding_cohorts_overlap() -> None:
    data = []
    for period, ordering in ((date(2024, 1, 31), "abcdef"), (date(2024, 2, 29), "bcdefa")):
        for i, name in enumerate(ordering):
            data.append(
                {
                    "date": period,
                    "security_id": name,
                    "signal": float(i),
                    "return": 0.01 * i,
                    "average_dollar_volume": 100_000_000.0,
                }
            )
    weights, returns = run_portfolio(
        pl.DataFrame(data),
        PortfolioConfig(quantile=0.25, holding_periods=2, max_absolute_weight=0.5),
        LinearQuadraticCostModel("v1", 1, 1, 1, 1),
    )
    assert (
        weights.filter(
            (pl.col("date") == date(2024, 2, 29)) & (pl.col("trade_weight") != 0)
        ).height
        > 0
    )
    assert returns["turnover"][1] > 0
    assert (returns["net_return"] < returns["gross_return"]).all()
