from __future__ import annotations

from datetime import datetime
from typing import Protocol

import polars as pl

from alphawatch.data.quality import enforce_frame_pit
from alphawatch.exceptions import DataContractError
from alphawatch.factors.config import FactorConfig
from alphawatch.factors.cross_sectional import (
    group_neutralize,
    neutralize,
    percentile_rank,
    winsorize,
    zscore,
)
from alphawatch.factors.specifications import FACTOR_SPECIFICATIONS


class ConfiguredFactor(Protocol):
    config: FactorConfig

    def compute(self, frame: pl.DataFrame, prediction_time: datetime) -> pl.DataFrame: ...


class ExpressionFactor:
    """Shared PIT and transformation lifecycle for cross-sectional factors."""

    def __init__(self, config: FactorConfig) -> None:
        if config.name not in FACTOR_SPECIFICATIONS:
            raise DataContractError(f"unknown factor: {config.name}")
        self.config = config

    def raw_expression(self) -> pl.Expr:
        name = self.config.name
        expressions = {
            "size": -pl.col("market_cap").log(),
            "value": pl.col("book_equity") / pl.col("market_cap"),
            "profitability": pl.col("operating_profit") / pl.col("book_equity"),
            "investment": -(pl.col("total_assets") / pl.col("total_assets_lag") - 1),
            "quality": (
                pl.col("cash_flow_operations") / pl.col("total_assets")
                - pl.col("accruals").abs() / pl.col("total_assets")
            ),
            "accrual_quality": -pl.col("accruals") / pl.col("total_assets"),
            "beta": -pl.col("beta"),
            "liquidity": pl.col("liquidity"),
            "turnover": -pl.col("turnover_signal"),
            "momentum_12_minus_1": pl.col("momentum_12_minus_1"),
            "short_term_reversal": pl.col("short_term_reversal"),
            "low_volatility": pl.col("low_volatility"),
        }
        return expressions[name]

    def compute(self, frame: pl.DataFrame, prediction_time: datetime) -> pl.DataFrame:
        enforce_frame_pit(frame, prediction_time)
        spec = FACTOR_SPECIFICATIONS[self.config.name]
        missing = set(spec.required_fields) - set(frame.columns)
        # Market and price factors may arrive as precomputed canonical columns.
        if missing and self.config.name not in frame.columns:
            raise DataContractError(f"{self.config.name} missing inputs: {sorted(missing)}")
        result = frame.with_columns(self.raw_expression().alias("raw_value"))
        result = winsorize(
            result,
            "raw_value",
            self.config.transform.winsor_lower,
            self.config.transform.winsor_upper,
        )
        working = "raw_value"
        if self.config.transform.sector_neutral:
            result = group_neutralize(result, working, "sector")
            working = f"{working}_neutral"
        if self.config.transform.size_neutral:
            result = neutralize(result, working, ["log_market_cap"])
            working = f"{working}_neutral"
        if self.config.transform.standardize:
            result = zscore(result, working)
        if self.config.transform.rank:
            result = percentile_rank(result, working)
        columns = [
            "security_id",
            "available_at",
            pl.lit(prediction_time).alias("prediction_time"),
            pl.lit(self.config.name).alias("factor_name"),
            pl.lit(self.config.version).alias("factor_version"),
            pl.col("raw_value"),
            pl.col(working).alias("standardized_value"),
        ]
        rank_column = f"{working}_rank"
        columns.append(
            pl.col(rank_column).alias("rank")
            if rank_column in result.columns
            else pl.lit(None).alias("rank")
        )
        return result.select(columns)


class FactorRegistry:
    def __init__(self, configs: list[FactorConfig]) -> None:
        names = [config.name for config in configs]
        if len(names) != len(set(names)):
            raise DataContractError("factor configurations must be unique by name")
        self._factors = {config.name: ExpressionFactor(config) for config in configs}

    def get(self, name: str) -> ExpressionFactor:
        try:
            return self._factors[name]
        except KeyError as error:
            raise DataContractError(f"factor not configured: {name}") from error

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factors))
