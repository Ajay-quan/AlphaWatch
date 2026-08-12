from datetime import UTC, datetime, timedelta

import polars as pl

from alphawatch.diagnostics import exposure_diagnostics, rolling_metrics
from alphawatch.factors.cross_sectional import group_neutralize
from alphawatch.factors.engine import build_fundamental_factor_table, build_market_factor_table
from alphawatch.factors.specifications import FACTOR_SPECIFICATIONS


def test_all_twelve_factor_specs_exist() -> None:
    assert len(FACTOR_SPECIFICATIONS) == 12


def test_sector_neutralization_removes_group_means() -> None:
    frame = pl.DataFrame({"sector": ["a", "a", "b", "b"], "x": [1.0, 3.0, 5.0, 9.0]})
    result = group_neutralize(frame, "x", "sector")
    assert result.group_by("sector").agg(pl.col("x_neutral").mean())["x_neutral"].abs().max() == 0


def test_complete_fundamental_factor_table() -> None:
    now = datetime(2024, 5, 1, tzinfo=UTC)
    frame = pl.DataFrame(
        {
            "security_id": ["a", "b", "c", "d"],
            "available_at": [now - timedelta(days=1)] * 4,
            "sector": ["tech", "tech", "energy", "energy"],
            "market_cap": [100.0, 200.0, 150.0, 300.0],
            "book_equity": [50.0, 80.0, 75.0, 100.0],
            "operating_profit": [10.0, 12.0, 20.0, 18.0],
            "total_assets": [120.0, 220.0, 180.0, 350.0],
            "total_assets_lag": [100.0, 200.0, 150.0, 300.0],
            "accruals": [5.0, 7.0, 4.0, 10.0],
            "cash_flow_operations": [20.0, 25.0, 30.0, 35.0],
        }
    )
    result = build_fundamental_factor_table(frame, now)
    assert result["factor_name"].n_unique() == 6
    assert result.height == 24


def test_market_factor_table() -> None:
    now = datetime(2024, 5, 1, tzinfo=UTC)
    rows = []
    for security, multiplier in (("a", 1.0), ("b", 1.5)):
        for i in range(30):
            rows.append(
                {
                    "security_id": security,
                    "session": i,
                    "return": 0.001 * i * multiplier,
                    "market_return": 0.001 * i,
                    "dollar_volume": 1_000_000.0 + i,
                    "turnover": 0.01,
                    "available_at": now - timedelta(days=1),
                }
            )
    result = build_market_factor_table(pl.DataFrame(rows), now, 20)
    assert set(result["factor_name"]) == {"beta", "liquidity", "turnover"}


def test_exposure_and_rolling_diagnostics() -> None:
    result = exposure_diagnostics([0.5, -0.5], [1.0, 0.5], [1.0, -1.0], [2.0, 1.0])
    assert result["gross_exposure"] == 1.0
    assert result["beta_exposure"] == 0.25
    assert len(rolling_metrics([0.01, -0.01, 0.02], 2)) == 2
