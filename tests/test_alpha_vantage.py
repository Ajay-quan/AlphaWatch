from datetime import date

import pytest

from alphawatch.data.universe import rolling_universe
from alphawatch.exceptions import DataContractError
from alphawatch.providers.alpha_vantage import AlphaVantageDailyAdjustedProvider

PAYLOAD = b"""timestamp,open,high,low,close,adjusted_close,volume,dividend_amount,split_coefficient
2024-01-03,101,103,100,102,102,20000,0.0,1.0
2024-01-02,100,102,99,101,101,10000,0.0,1.0
"""


def test_alpha_vantage_parser_outputs_canonical_prices() -> None:
    result = AlphaVantageDailyAdjustedProvider.parse(PAYLOAD, "sec-1")
    assert result["session"].to_list() == [date(2024, 1, 2), date(2024, 1, 3)]
    assert result["available_at"].dtype.time_zone == "UTC"
    assert result["dollar_volume"][0] == 1_010_000


def test_alpha_vantage_json_error_fails_closed() -> None:
    with pytest.raises(DataContractError):
        AlphaVantageDailyAdjustedProvider.parse(b'{"Note":"rate limit"}', "sec-1")


def test_rolling_universe_uses_trailing_history() -> None:
    prices = AlphaVantageDailyAdjustedProvider.parse(PAYLOAD, "sec-1").with_columns(
        __import__("polars").lit("common").alias("share_class")
    )
    result = rolling_universe(
        prices,
        minimum_price=5,
        minimum_median_dollar_volume=1_000,
        liquidity_window=2,
        minimum_history=2,
    )
    assert result["eligible"].to_list() == [False, True]
