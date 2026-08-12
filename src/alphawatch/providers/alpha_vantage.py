from __future__ import annotations

from io import BytesIO
from urllib.parse import urlencode

import polars as pl

from alphawatch.data.calendar import UsEquityCalendar
from alphawatch.exceptions import DataContractError
from alphawatch.providers.http import HttpClient

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageDailyAdjustedProvider:
    """Documented daily adjusted endpoint; availability depends on the subscriber's plan."""

    def __init__(self, api_key: str, user_agent: str = "AlphaWatch/0.1") -> None:
        if not api_key:
            raise ValueError("Alpha Vantage API key is required")
        self.api_key = api_key
        self.client = HttpClient(f"{user_agent} research@localhost")

    def fetch(self, symbol: str) -> bytes:
        query = urlencode(
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "outputsize": "full",
                "datatype": "csv",
                "apikey": self.api_key,
            }
        )
        return self.client.get(f"{BASE_URL}?{query}")

    @staticmethod
    def parse(payload: bytes, security_id: str) -> pl.DataFrame:
        if payload.lstrip().startswith(b"{"):
            raise DataContractError(
                "Alpha Vantage returned JSON instead of adjusted CSV; "
                "check API key, plan, and limits"
            )
        frame = pl.read_csv(BytesIO(payload), try_parse_dates=True)
        required = {
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            "dividend_amount",
            "split_coefficient",
        }
        missing = required - set(frame.columns)
        if missing:
            raise DataContractError(f"Alpha Vantage schema missing columns: {sorted(missing)}")
        calendar = UsEquityCalendar()
        sessions = frame["timestamp"].to_list()
        invalid = [day for day in sessions if not calendar.is_session(day)]
        if invalid:
            raise DataContractError(f"provider returned non-session dates: {invalid[:3]}")
        return frame.select(
            pl.lit(security_id).alias("security_id"),
            pl.col("timestamp").alias("session"),
            pl.Series("available_at", [calendar.close_timestamp(day) for day in sessions]),
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            (pl.col("close") * pl.col("volume")).alias("dollar_volume"),
            "dividend_amount",
            "split_coefficient",
            pl.lit("alpha_vantage_daily_adjusted").alias("source"),
        ).sort("session")
