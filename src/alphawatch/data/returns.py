from __future__ import annotations

import polars as pl

from alphawatch.exceptions import DataContractError

REQUIRED_PRICE_COLUMNS = {
    "security_id",
    "session",
    "available_at",
    "close",
    "adjusted_close",
    "volume",
}


def build_returns(prices: pl.DataFrame, adjusted_includes_distributions: bool) -> pl.DataFrame:
    """Build audit and principal returns without imputing missing observations."""
    missing = REQUIRED_PRICE_COLUMNS - set(prices.columns)
    if missing:
        raise DataContractError(f"return input missing columns: {sorted(missing)}")
    duplicate_count = prices.select(
        pl.struct("security_id", "session").is_duplicated().sum()
    ).item()
    if duplicate_count:
        raise DataContractError(f"{duplicate_count} duplicate security/session rows")
    if prices.filter((pl.col("close") <= 0) | (pl.col("adjusted_close") <= 0)).height:
        raise DataContractError("close and adjusted_close must be positive")
    if prices.filter(pl.col("volume") < 0).height:
        raise DataContractError("volume cannot be negative")

    ordered = prices.sort(["security_id", "session"])
    same_security = pl.col("security_id") == pl.col("security_id").shift(1)
    raw_return = (pl.col("close") / pl.col("close").shift(1) - 1).over("security_id")
    adjusted_return = (pl.col("adjusted_close") / pl.col("adjusted_close").shift(1) - 1).over(
        "security_id"
    )
    principal = adjusted_return if adjusted_includes_distributions else raw_return
    has_delisting = "delisting_return" in ordered.columns
    if has_delisting:
        delisting = pl.col("delisting_return")
        principal = (
            pl.when(delisting.is_not_null())
            .then((1 + principal) * (1 + delisting) - 1)
            .otherwise(principal)
        )
    return ordered.with_columns(
        raw_return.alias("price_return"),
        adjusted_return.alias("adjusted_close_return"),
        principal.alias("total_return"),
        (same_security & ((1 + raw_return) / (1 + adjusted_return) - 1).abs().gt(0.20)).alias(
            "corporate_action_suspected"
        ),
        pl.lit(adjusted_includes_distributions).alias("adjusted_includes_distributions"),
    )


def assert_return_identity(frame: pl.DataFrame, tolerance: float = 1e-10) -> None:
    """Verify adjusted return identity for non-delisting rows."""
    required = {"adjusted_close_return", "total_return", "adjusted_includes_distributions"}
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"return output missing columns: {sorted(missing)}")
    comparable = frame
    if "delisting_return" in frame.columns:
        comparable = comparable.filter(pl.col("delisting_return").is_null())
    violations = comparable.filter(
        pl.col("adjusted_includes_distributions")
        & (pl.col("total_return") - pl.col("adjusted_close_return")).abs().gt(tolerance)
    ).height
    if violations:
        raise DataContractError(f"{violations} adjusted-return identity violations")
