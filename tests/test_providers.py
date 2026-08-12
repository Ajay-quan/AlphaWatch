import json
from datetime import UTC, datetime

from alphawatch.providers.nasdaq import NasdaqSymbolDirectoryProvider
from alphawatch.providers.prices import parse_daily_price_csv
from alphawatch.providers.sec import SecCompanyFactsProvider, latest_facts_asof, normalize_cik


def test_sec_parser_preserves_vintages_and_availability() -> None:
    payload = json.dumps(
        {
            "cik": 1,
            "facts": {
                "us-gaap": {
                    "Assets": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2023-12-31",
                                    "val": 10,
                                    "filed": "2024-02-01",
                                    "accn": "a",
                                    "form": "10-K",
                                },
                                {
                                    "end": "2023-12-31",
                                    "val": 11,
                                    "filed": "2024-03-01",
                                    "accn": "b",
                                    "form": "10-K/A",
                                },
                            ]
                        }
                    }
                }
            },
        }
    ).encode()
    provider = SecCompanyFactsProvider("AlphaWatch test@example.com")
    facts = provider.parse(payload)
    early = latest_facts_asof(facts, datetime(2024, 2, 15, tzinfo=UTC))
    late = latest_facts_asof(facts, datetime(2024, 3, 15, tzinfo=UTC))
    assert early["value"].item() == 10
    assert late["value"].item() == 11
    assert normalize_cik(1) == "0000000001"


def test_nasdaq_directory_drops_footer() -> None:
    payload = (
        b"Symbol|Security Name|Test Issue\nAAPL|Apple Inc.|N\nFile Creation Time: 0101202412:00||\n"
    )
    result = NasdaqSymbolDirectoryProvider.parse(payload)
    assert result.height == 1


def test_daily_price_parser() -> None:
    result = parse_daily_price_csv(
        b"Date,Open,High,Low,Close,Volume\n2024-01-02,10,11,9,10.5,1000\n", "sec-a"
    )
    assert result["security_id"].item() == "sec-a"
    assert result["close"].item() == 10.5
