from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from alphawatch.data.calendar import UsEquityCalendar
from alphawatch.data.reporting import price_quality_report
from alphawatch.data.returns import assert_return_identity, build_returns
from alphawatch.data.storage import ParquetLake


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alphawatch")
    subcommands = parser.add_subparsers(dest="command", required=True)
    returns = subcommands.add_parser("build-returns")
    returns.add_argument("--input", type=Path, required=True)
    returns.add_argument("--data-root", type=Path, required=True)
    returns.add_argument("--version", required=True)
    returns.add_argument("--adjusted-includes-distributions", action="store_true")
    returns.add_argument("--survivorship-safe", action="store_true")
    return parser


def run_build_returns(args: argparse.Namespace) -> int:
    prices = pl.read_csv(args.input, try_parse_dates=True)
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "build-returns":
        return run_build_returns(args)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
