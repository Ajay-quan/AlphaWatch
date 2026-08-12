from datetime import UTC, date, datetime

import polars as pl

from alphawatch.cli import main
from alphawatch.data.calendar import UsEquityCalendar, missing_sessions
from alphawatch.portfolio.backtest import long_short_backtest
from alphawatch.portfolio.costs import LinearQuadraticCostModel


def test_calendar_holidays_close_and_next_session() -> None:
    calendar = UsEquityCalendar()
    assert not calendar.is_session(date(2026, 7, 3))
    assert calendar.next_session(date(2026, 7, 2)) == date(2026, 7, 6)
    assert calendar.close_timestamp(date(2026, 7, 2)).tzinfo == UTC
    assert missing_sessions([date(2026, 7, 2), date(2026, 7, 7)], calendar) == [date(2026, 7, 6)]


def test_long_short_backtest_has_cost_below_gross() -> None:
    observations = pl.DataFrame(
        {
            "date": [date(2024, 1, 31)] * 4,
            "security_id": ["a", "b", "c", "d"],
            "signal": [1.0, 2.0, 3.0, 4.0],
            "forward_return": [-0.1, 0.0, 0.0, 0.1],
        }
    )
    model = LinearQuadraticCostModel("test", 1, 2, 3, 4)
    result = long_short_backtest(observations, model, 0.25)
    row = result.returns.row(0, named=True)
    assert row["gross_return"] == 0.1
    assert row["net_return"] < row["gross_return"]
    assert result.weights["weight"].abs().sum() == 1.0


def test_cli_builds_returns_and_quality_report(tmp_path) -> None:
    source = tmp_path / "prices.csv"
    pl.DataFrame(
        {
            "security_id": ["a", "a"],
            "session": [date(2024, 1, 2), date(2024, 1, 3)],
            "available_at": [
                datetime(2024, 1, 2, 21, tzinfo=UTC),
                datetime(2024, 1, 3, 21, tzinfo=UTC),
            ],
            "close": [10.0, 11.0],
            "adjusted_close": [10.0, 11.0],
            "volume": [100, 110],
        }
    ).write_csv(source)
    assert (
        main(
            [
                "build-returns",
                "--input",
                str(source),
                "--data-root",
                str(tmp_path / "lake"),
                "--version",
                "v1",
                "--adjusted-includes-distributions",
            ]
        )
        == 0
    )
    directory = tmp_path / "lake" / "silver" / "returns" / "version=v1"
    assert (directory / "part-00000.parquet").exists()
    assert (directory / "quality-report.json").exists()


def test_cli_runs_costed_factor_backtest(tmp_path) -> None:
    source = tmp_path / "observations.csv"
    pl.DataFrame(
        {
            "date": [date(2024, 1, 31)] * 4,
            "security_id": ["a", "b", "c", "d"],
            "signal": [1.0, 2.0, 3.0, 4.0],
            "forward_return": [-0.1, 0.0, 0.0, 0.1],
        }
    ).write_csv(source)
    output = tmp_path / "backtest"
    assert (
        main(
            [
                "backtest-factor",
                "--input",
                str(source),
                "--output",
                str(output),
                "--quantile",
                "0.25",
            ]
        )
        == 0
    )
    returns = pl.read_parquet(output / "factor_returns.parquet")
    assert returns["net_return"].item() < returns["gross_return"].item()
