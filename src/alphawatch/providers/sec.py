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
