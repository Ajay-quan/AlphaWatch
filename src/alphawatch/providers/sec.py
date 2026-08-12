from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import polars as pl

from alphawatch.exceptions import DataContractError
from alphawatch.providers.http import HttpClient

COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def normalize_cik(cik: str | int) -> str:
    value = str(cik).strip()
    if not value.isdigit() or len(value) > 10:
        raise ValueError("CIK must contain at most ten digits")
    return value.zfill(10)


class SecCompanyFactsProvider:
    def __init__(
        self, user_agent: str, dissemination_lag: timedelta = timedelta(minutes=5)
    ) -> None:
        self.client = HttpClient(user_agent)
        self.dissemination_lag = dissemination_lag

    def fetch(self, cik: str | int) -> bytes:
        return self.client.get(COMPANY_FACTS_URL.format(cik=normalize_cik(cik)))

    def parse(self, payload: bytes) -> pl.DataFrame:
        document: dict[str, Any] = json.loads(payload)
        cik = normalize_cik(document["cik"])
        rows: list[dict[str, Any]] = []
        for taxonomy, concepts in document.get("facts", {}).items():
            for concept, details in concepts.items():
                for unit, observations in details.get("units", {}).items():
                    for item in observations:
                        filed = item.get("filed")
                        if not filed or "val" not in item:
                            continue
                        # Company Facts exposes filed date, not exact dissemination timestamp.
                        # Fail conservatively: next UTC day plus an explicit safety lag.
                        available_at = datetime.fromisoformat(filed).replace(tzinfo=UTC)
                        available_at += timedelta(days=1) + self.dissemination_lag
                        rows.append(
                            {
                                "cik": cik,
                                "taxonomy": taxonomy,
                                "concept": concept,
                                "unit": unit,
                                "value": item["val"],
                                "period_start": item.get("start"),
                                "period_end": item.get("end"),
                                "filed": filed,
                                "available_at": available_at,
                                "accession": item.get("accn"),
                                "form": item.get("form"),
                                "fiscal_year": item.get("fy"),
                                "fiscal_period": item.get("fp"),
                                "frame": item.get("frame"),
                            }
                        )
        if not rows:
            raise DataContractError("SEC payload contains no usable facts")
        return pl.DataFrame(rows)


def latest_facts_asof(facts: pl.DataFrame, prediction_time: datetime) -> pl.DataFrame:
    safe = facts.filter(pl.col("available_at") <= prediction_time)
    return (
        safe.sort(["available_at", "accession"])
        .group_by(["cik", "taxonomy", "concept", "unit"], maintain_order=True)
        .tail(1)
    )


_CANONICAL_CONCEPTS: dict[str, tuple[str, ...]] = {
    "book_equity": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
    "operating_profit": ("OperatingIncomeLoss",),
    "total_assets": ("Assets",),
    "cash_flow_operations": ("NetCashProvidedByUsedInOperatingActivities",),
    "net_income": ("NetIncomeLoss", "ProfitLoss"),
}


def normalize_fundamental_inputs(
    facts: pl.DataFrame,
    security_id: str,
    prediction_time: datetime,
    market_cap: float,
    sector: str,
) -> pl.DataFrame:
    """Map SEC US-GAAP facts to one canonical, point-in-time factor input row."""
    if prediction_time.tzinfo is None:
        raise ValueError("prediction_time must be timezone-aware")
    safe = facts.filter(pl.col("available_at") <= prediction_time).filter(
        (pl.col("taxonomy") == "us-gaap") & (pl.col("unit") == "USD")
    )
    values: dict[str, float] = {}
    timestamps: list[datetime] = []
    for field, concepts in _CANONICAL_CONCEPTS.items():
        candidates = safe.filter(pl.col("concept").is_in(concepts)).sort(
            ["available_at", "accession"], descending=True
        )
        if candidates.is_empty():
            raise DataContractError(f"missing SEC concept for canonical field {field}")
        row = candidates.row(0, named=True)
        values[field] = float(row["value"])
        timestamps.append(row["available_at"])
    assets = safe.filter(pl.col("concept") == "Assets").sort(
        ["period_end", "available_at"], descending=True
    )
    distinct_assets = assets.unique(subset=["period_end"], keep="first", maintain_order=True)
    if distinct_assets.height < 2:
        raise DataContractError("two point-in-time total-assets periods are required")
    total_assets_lag = float(distinct_assets["value"][1])
    accruals = values["net_income"] - values["cash_flow_operations"]
    return pl.DataFrame(
        {
            "security_id": [security_id],
            "cik": [safe["cik"][0]],
            "available_at": [max(timestamps)],
            "sector": [sector],
            "market_cap": [market_cap],
            "book_equity": [values["book_equity"]],
            "operating_profit": [values["operating_profit"]],
            "total_assets": [values["total_assets"]],
            "total_assets_lag": [total_assets_lag],
            "accruals": [accruals],
            "cash_flow_operations": [values["cash_flow_operations"]],
        }
    )
