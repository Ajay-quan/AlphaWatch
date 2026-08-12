from datetime import UTC, date, datetime, timedelta

import polars as pl
import pytest

from alphawatch.data.returns import assert_return_identity, build_returns
from alphawatch.exceptions import DataContractError


def fixture() -> pl.DataFrame:
    start = date(2024, 1, 2)
    return pl.DataFrame(
        {
            "security_id": ["a", "a", "a"],
            "session": [start + timedelta(days=i) for i in range(3)],
            "available_at": [datetime(2024, 1, 2 + i, 22, tzinfo=UTC) for i in range(3)],
            "close": [100.0, 50.0, 55.0],
            "adjusted_close": [50.0, 50.0, 55.0],
            "volume": [1000, 2000, 1200],
        }
    )


def test_adjusted_return_avoids_false_split_loss() -> None:
    result = build_returns(fixture(), adjusted_includes_distributions=True)
    assert result["price_return"][1] == pytest.approx(-0.5)
    assert result["total_return"][1] == pytest.approx(0.0)
    assert result["corporate_action_suspected"][1]
    assert_return_identity(result)


def test_delisting_return_is_compounded_once() -> None:
    prices = fixture().with_columns(pl.Series("delisting_return", [None, None, -0.5]))
    result = build_returns(prices, adjusted_includes_distributions=True)
    assert result["total_return"][2] == pytest.approx((1.1 * 0.5) - 1)


def test_duplicate_rows_are_rejected() -> None:
    with pytest.raises(DataContractError):
        build_returns(pl.concat([fixture(), fixture().head(1)]), True)


def test_invalid_prices_are_rejected() -> None:
    bad = fixture().with_columns(
        pl.when(pl.int_range(pl.len()) == 0).then(0).otherwise("close").alias("close")
    )
    with pytest.raises(DataContractError):
        build_returns(bad, True)
