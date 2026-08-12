from datetime import UTC, date, datetime

import polars as pl
import pytest

from alphawatch.data.quality import validate_prices
from alphawatch.diagnostics import information_coefficient, performance_metrics
from alphawatch.exceptions import DataContractError, LookAheadError
from alphawatch.factors.cross_sectional import neutralize, percentile_rank, winsorize, zscore
from alphawatch.factors.fundamental import compute_fundamental_signals
from alphawatch.pipeline import run_price_signal_pipeline


def prices() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "security_id": ["a", "b", "c"],
            "session": [date(2024, 1, 2)] * 3,
            "available_at": [datetime(2024, 1, 2, 23, tzinfo=UTC)] * 3,
            "adjusted_close": [10.0, 20.0, 30.0],
            "dollar_volume": [1_000.0, 2_000.0, 3_000.0],
        }
    )


def test_pipeline_writes_versioned_parquet(tmp_path) -> None:
    result = run_price_signal_pipeline(
        prices(), datetime(2024, 1, 3, tzinfo=UTC), tmp_path, "test-v1"
    )
    assert result.silver_prices.path.exists()
    assert result.gold_signals.path.exists()
    assert len(result.gold_signals.checksum_sha256) == 64


def test_pipeline_rejects_future_data(tmp_path) -> None:
    with pytest.raises(LookAheadError):
        run_price_signal_pipeline(prices(), datetime(2024, 1, 1, tzinfo=UTC), tmp_path, "bad")


def test_quality_rejects_duplicates() -> None:
    with pytest.raises(DataContractError):
        validate_prices(pl.concat([prices(), prices()]))


def test_cross_sectional_transforms() -> None:
    frame = pl.DataFrame(
        {
            "security_id": ["a", "b", "c", "d"],
            "x": [0.0, 1.0, 2.0, 100.0],
            "size": [1.0, 2.0, 3.0, 4.0],
        }
    )
    transformed = percentile_rank(zscore(winsorize(frame, "x", 0.0, 0.75), "x"), "x")
    assert transformed["x_rank"].min() == 0.0
    assert 0.5 < transformed["x_rank"].max() <= 1.0
    residualized = neutralize(frame, "x", ["size"])
    assert "x_neutral" in residualized.columns


def test_fundamental_signs() -> None:
    frame = pl.DataFrame(
        {
            "security_id": ["a"],
            "available_at": [datetime(2024, 1, 1, tzinfo=UTC)],
            "market_cap": [100.0],
            "book_equity": [50.0],
            "operating_profit": [10.0],
            "total_assets": [120.0],
            "total_assets_lag": [100.0],
            "accruals": [5.0],
            "cash_flow_operations": [20.0],
        }
    )
    result = compute_fundamental_signals(frame).row(0, named=True)
    assert result["value"] == 0.5
    assert result["profitability"] == 0.2
    assert result["investment"] == pytest.approx(-0.2)


def test_diagnostics() -> None:
    metrics = performance_metrics([0.01, -0.02, 0.03, -0.01])
    assert metrics["maximum_drawdown"] <= 0
    assert information_coefficient([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
