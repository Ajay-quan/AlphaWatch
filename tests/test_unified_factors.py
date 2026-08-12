from datetime import UTC, datetime, timedelta

import polars as pl
import pytest

from alphawatch.exceptions import DataContractError
from alphawatch.factors.config import FactorConfig, TransformConfig, load_factor_config
from alphawatch.factors.unified import ExpressionFactor, FactorRegistry


def frame() -> pl.DataFrame:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    return pl.DataFrame(
        {
            "security_id": ["a", "b", "c", "d"],
            "available_at": [now - timedelta(days=1)] * 4,
            "sector": ["x", "x", "y", "y"],
            "market_cap": [100.0, 200.0, 300.0, 400.0],
            "log_market_cap": [4.61, 5.30, 5.70, 5.99],
            "book_equity": [50.0, 70.0, 100.0, 120.0],
            "operating_profit": [10.0, 12.0, 20.0, 24.0],
            "total_assets": [120.0, 220.0, 330.0, 430.0],
            "total_assets_lag": [100.0, 200.0, 300.0, 400.0],
            "accruals": [2.0, 4.0, 6.0, 8.0],
            "cash_flow_operations": [20.0, 30.0, 40.0, 50.0],
        }
    )


@pytest.mark.parametrize(
    "name", ["size", "value", "profitability", "investment", "quality", "accrual_quality"]
)
def test_fundamental_factors_share_one_contract(name: str) -> None:
    config = FactorConfig(name, "1.0.0", transform=TransformConfig(sector_neutral=True))
    result = ExpressionFactor(config).compute(frame(), datetime(2024, 1, 2, tzinfo=UTC))
    assert result.columns == [
        "security_id",
        "available_at",
        "prediction_time",
        "factor_name",
        "factor_version",
        "raw_value",
        "standardized_value",
        "rank",
    ]
    assert result["factor_name"].unique().item() == name


def test_registry_contains_configured_factors() -> None:
    registry = FactorRegistry([FactorConfig("size", "1"), FactorConfig("value", "1")])
    assert registry.names == ("size", "value")
    with pytest.raises(DataContractError):
        registry.get("beta")


def test_existing_yaml_loads() -> None:
    config = load_factor_config(
        __import__("pathlib").Path("configs/factors/momentum_12_minus_1.yaml")
    )
    assert config.name == "momentum_12_minus_1"
    assert config.parameters["lookback_sessions"] == 252
