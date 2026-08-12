from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from alphawatch.data.calendar import UsEquityCalendar
from alphawatch.data.ingestion import BronzeWriter, ProviderResponse
from alphawatch.data.reporting import price_quality_report
from alphawatch.data.returns import assert_return_identity, build_returns
from alphawatch.data.storage import ParquetLake
from alphawatch.factors.engine import build_fundamental_factor_table
from alphawatch.portfolio.backtest import long_short_backtest
from alphawatch.portfolio.costs import LinearQuadraticCostModel
from alphawatch.providers.nasdaq import NasdaqSymbolDirectoryProvider
from alphawatch.providers.sec import SecCompanyFactsProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alphawatch")
    commands = parser.add_subparsers(dest="command", required=True)
    returns = commands.add_parser("build-returns")
    returns.add_argument("--input", type=Path, required=True)
    returns.add_argument("--data-root", type=Path, required=True)
    returns.add_argument("--version", required=True)
    returns.add_argument("--adjusted-includes-distributions", action="store_true")
    returns.add_argument("--survivorship-safe", action="store_true")
    sec = commands.add_parser("ingest-sec-facts")
    sec.add_argument("--cik", required=True)
    sec.add_argument("--user-agent", required=True, help="Project plus contact email")
    sec.add_argument("--data-root", type=Path, required=True)
    sec.add_argument("--version", required=True)
    nasdaq = commands.add_parser("ingest-nasdaq-symbols")
    nasdaq.add_argument("--user-agent", required=True, help="Project plus contact email")
    nasdaq.add_argument("--data-root", type=Path, required=True)
    nasdaq.add_argument("--version", required=True)
    factors = commands.add_parser("build-fundamental-factors")
    factors.add_argument("--input", type=Path, required=True)
    factors.add_argument("--prediction-time", type=datetime.fromisoformat, required=True)
    factors.add_argument("--data-root", type=Path, required=True)
    factors.add_argument("--version", required=True)
    backtest = commands.add_parser("backtest-factor")
    backtest.add_argument("--input", type=Path, required=True)
    backtest.add_argument("--output", type=Path, required=True)
    backtest.add_argument("--quantile", type=float, default=0.2)
    return parser


def _read_frame(path: Path) -> pl.DataFrame:
    return (
        pl.read_parquet(path)
        if path.suffix == ".parquet"
        else pl.read_csv(path, try_parse_dates=True)
    )


def run_build_returns(args: argparse.Namespace) -> int:
    prices = _read_frame(args.input)
    if prices.schema.get("available_at") == pl.String:
        prices = prices.with_columns(pl.col("available_at").str.to_datetime(time_zone="UTC"))
    result = build_returns(prices, args.adjusted_includes_distributions)
    assert_return_identity(result)
    artifact = ParquetLake(args.data_root).write("silver", "returns", args.version, result, "1.0.0")
    report = price_quality_report(result, UsEquityCalendar(), args.survivorship_safe)
    report_path = artifact.path.parent / "quality-report.json"
    report.write(report_path)
    print(
        json.dumps(
            {
                "artifact": str(artifact.path),
                "quality_report": str(report_path),
                "rows": artifact.rows,
            }
        )
    )
    return 0


def run_ingest_sec(args: argparse.Namespace) -> int:
    provider = SecCompanyFactsProvider(args.user_agent)
    requested_at = datetime.now(UTC)
    payload = provider.fetch(args.cik)
    response = ProviderResponse(
        payload,
        "sec-company-facts",
        "",
        requested_at.date().isoformat(),
        args.version,
        "1.0.0",
        requested_at,
    )
    manifest = BronzeWriter(args.data_root / "bronze").persist(response)
    facts = provider.parse(payload)
    artifact = ParquetLake(args.data_root).write(
        "silver", "sec_company_facts", args.version, facts, "1.0.0"
    )
    print(
        json.dumps(
            {
                "run_id": manifest.ingestion_run_id,
                "artifact": str(artifact.path),
                "rows": artifact.rows,
            }
        )
    )
    return 0


def run_ingest_nasdaq(args: argparse.Namespace) -> int:
    provider = NasdaqSymbolDirectoryProvider(args.user_agent)
    requested_at = datetime.now(UTC)
    outputs: dict[str, str] = {}
    for name, payload in (("nasdaq", provider.fetch_nasdaq()), ("other", provider.fetch_other())):
        response = ProviderResponse(
            payload,
            f"nasdaq-{name}-listed",
            "",
            requested_at.date().isoformat(),
            args.version,
            "1.0.0",
            requested_at,
        )
        BronzeWriter(args.data_root / "bronze").persist(response)
        artifact = ParquetLake(args.data_root).write(
            "silver", f"{name}_listed_symbols", args.version, provider.parse(payload), "1.0.0"
        )
        outputs[name] = str(artifact.path)
    print(json.dumps(outputs))
    return 0


def run_build_fundamentals(args: argparse.Namespace) -> int:
    prediction_time = args.prediction_time
    if prediction_time.tzinfo is None:
        raise ValueError("prediction-time must include a UTC offset")
    result = build_fundamental_factor_table(
        _read_frame(args.input), prediction_time.astimezone(UTC)
    )
    artifact = ParquetLake(args.data_root).write(
        "gold", "fundamental_factors", args.version, result, "1.0.0"
    )
    print(json.dumps({"artifact": str(artifact.path), "rows": artifact.rows}))
    return 0


def run_backtest(args: argparse.Namespace) -> int:
    model = LinearQuadraticCostModel("public-prototype-v1", 0.5, 5.0, 2.5, 10.0)
    result = long_short_backtest(_read_frame(args.input), model, args.quantile)
    args.output.mkdir(parents=True, exist_ok=True)
    result.weights.write_parquet(args.output / "weights.parquet")
    result.returns.write_parquet(args.output / "factor_returns.parquet")
    print(json.dumps({"weights": result.weights.height, "return_periods": result.returns.height}))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "build-returns": run_build_returns,
        "ingest-sec-facts": run_ingest_sec,
        "ingest-nasdaq-symbols": run_ingest_nasdaq,
        "build-fundamental-factors": run_build_fundamentals,
        "backtest-factor": run_backtest,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
