import json
from datetime import UTC, date, datetime

import polars as pl
import pytest
from hypothesis import given
from hypothesis import strategies as st

from alphawatch.cli import main
from alphawatch.data.storage import ParquetLake
from alphawatch.diagnostics import factor_diagnostics
from alphawatch.exceptions import DataContractError
from alphawatch.portfolio.costs import LinearQuadraticCostModel
from alphawatch.providers.sec import SecCompanyFactsProvider, normalize_fundamental_inputs
from alphawatch.security_master.master import SecurityMaster, SymbolMapping


@given(st.floats(min_value=0, max_value=2, allow_nan=False, allow_infinity=False))
def test_transaction_cost_is_nonnegative_and_monotone(turnover: float) -> None:
    model = LinearQuadraticCostModel("test", 1, 2, 3, 4)
    assert 0 <= model.estimate(turnover) <= model.estimate(turnover + 0.01)


def test_dataset_versions_are_immutable(tmp_path) -> None:
    lake = ParquetLake(tmp_path)
    lake.write("silver", "x", "v1", pl.DataFrame({"x": [1]}), "1")
    with pytest.raises(DataContractError, match="immutable"):
        lake.write("silver", "x", "v1", pl.DataFrame({"x": [2]}), "1")


def test_security_master_round_trip_and_cik_resolution(tmp_path) -> None:
    master = SecurityMaster(
        [
            SymbolMapping(
                "sec-1", "ABC", date(2020, 1, 1), None, "XNAS", cik="0000000001"
            )
        ]
    )
    path = tmp_path / "master.parquet"
    master.write(path)
    assert SecurityMaster.read(path).resolve_cik("1", date(2024, 1, 1)) == "sec-1"


def test_sec_facts_normalize_to_factor_contract() -> None:
    observations = []
    concepts = {
        "StockholdersEquity": [("2023-12-31", 50.0)],
        "OperatingIncomeLoss": [("2023-12-31", 12.0)],
        "Assets": [("2022-12-31", 90.0), ("2023-12-31", 100.0)],
        "NetCashProvidedByUsedInOperatingActivities": [("2023-12-31", 8.0)],
        "NetIncomeLoss": [("2023-12-31", 10.0)],
    }
    for concept, values in concepts.items():
        observations.append(
            (
                concept,
                [
                    {"end": end, "val": value, "filed": "2024-02-01", "accn": end}
                    for end, value in values
                ],
            )
        )
    payload = {
        "cik": 1,
        "facts": {
            "us-gaap": {
                concept: {"units": {"USD": values}} for concept, values in observations
            }
        },
    }
    facts = SecCompanyFactsProvider("AlphaWatch test@example.com").parse(
        json.dumps(payload).encode()
    )
    result = normalize_fundamental_inputs(
        facts, "sec-1", datetime(2024, 3, 1, tzinfo=UTC), 200.0, "Technology"
    )
    assert result["total_assets_lag"].item() == 90.0
    assert result["accruals"].item() == 2.0


def test_diagnostics_and_cli_portfolio_end_to_end(tmp_path) -> None:
    rows = []
    for period in (date(2024, 1, 31), date(2024, 2, 29)):
        for index in range(10):
            rows.append(
                {
                    "date": period,
                    "security_id": f"s{index}",
                    "factor_name": "value",
                    "signal": float(index),
                    "forward_return": float(index) / 100,
                    "return": float(index) / 100,
                    "average_dollar_volume": 1_000_000_000.0,
                }
            )
    frame = pl.DataFrame(rows)
    detail, summary = factor_diagnostics(frame)
    assert detail.height == 2
    assert summary["quantile_monotonicity"].item() > 0.99
    input_path = tmp_path / "input.parquet"
    frame.write_parquet(input_path)
    assert (
        main(
            [
                "run-portfolio",
                "--input",
                str(input_path),
                "--data-root",
                str(tmp_path / "lake"),
                "--version",
                "release-test",
            ]
        )
        == 0
    )
    assert (tmp_path / "lake/gold/factor_returns/version=release-test/manifest.json").exists()
