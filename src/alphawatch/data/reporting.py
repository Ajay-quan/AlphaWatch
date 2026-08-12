from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import polars as pl

from alphawatch.data.calendar import UsEquityCalendar, missing_sessions


@dataclass(frozen=True, slots=True)
class DatasetQualityReport:
    rows: int
    securities: int
    start_session: str | None
    end_session: str | None
    missing_sessions: dict[str, list[str]]
    null_counts: dict[str, int]
    suspected_corporate_actions: int
    survivorship_safe: bool

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")


def price_quality_report(
    frame: pl.DataFrame, calendar: UsEquityCalendar, survivorship_safe: bool
) -> DatasetQualityReport:
    gaps: dict[str, list[str]] = {}
    for security_id, group in frame.group_by("security_id"):
        observed = group["session"].to_list()
        gaps[str(security_id[0])] = [
            day.isoformat() for day in missing_sessions(observed, calendar)
        ]
    sessions = frame["session"]
    actions = (
        frame["corporate_action_suspected"].sum()
        if "corporate_action_suspected" in frame.columns
        else 0
    )
    return DatasetQualityReport(
        rows=frame.height,
        securities=frame["security_id"].n_unique(),
        start_session=str(sessions.min()) if frame.height else None,
        end_session=str(sessions.max()) if frame.height else None,
        missing_sessions=gaps,
        null_counts={name: frame[name].null_count() for name in frame.columns},
        suspected_corporate_actions=int(actions or 0),
        survivorship_safe=survivorship_safe,
    )
