from __future__ import annotations

from io import BytesIO

import polars as pl

from alphawatch.exceptions import DataContractError


def parse_daily_price_csv(
    payload: bytes, security_id: str, source_timezone: str = "UTC"
) -> pl.DataFrame:
    """Parse Date,Open,High,Low,Close,Volume CSV; prices remain provider-defined."""
    frame = pl.read_csv(BytesIO(payload), try_parse_dates=True)
    rename = {name: name.lower() for name in frame.columns}
    frame = frame.rename(rename)
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"daily-price CSV missing columns: {sorted(missing)}")
    if source_timezone != "UTC":
        raise DataContractError(
            "non-UTC source timezone requires an explicit exchange-calendar adapter"
        )
    return frame.select(
        pl.lit(security_id).alias("security_id"),
        pl.col("date").alias("session"),
        "open",
        "high",
        "low",
        "close",
        "volume",
    )
