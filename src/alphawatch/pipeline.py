from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import polars as pl

from alphawatch.data.quality import enforce_frame_pit, validate_prices
from alphawatch.data.storage import DatasetArtifact, ParquetLake
from alphawatch.factors.cross_sectional import percentile_rank, winsorize, zscore


@dataclass(frozen=True, slots=True)
class PipelineResult:
    silver_prices: DatasetArtifact
    gold_signals: DatasetArtifact


def run_price_signal_pipeline(
    raw_prices: pl.DataFrame, prediction_time: datetime, root: Path, version: str
) -> PipelineResult:
    """Idempotent, minimal Bronze/Silver/Gold vertical slice."""
    validate_prices(raw_prices)
    enforce_frame_pit(raw_prices, prediction_time)
    lake = ParquetLake(root)
    silver = raw_prices.sort(["session", "security_id"])
    silver_artifact = lake.write("silver", "prices", version, silver, "1.0.0")
    latest = (
        silver.group_by("security_id")
        .tail(1)
        .select(
            "security_id",
            "session",
            "available_at",
            pl.col("adjusted_close").log().alias("raw_signal"),
        )
    )
    signals = percentile_rank(zscore(winsorize(latest, "raw_signal"), "raw_signal"), "raw_signal")
    gold_artifact = lake.write("gold", "sample_signals", version, signals, "1.0.0")
    return PipelineResult(silver_artifact, gold_artifact)
