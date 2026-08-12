from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import polars as pl

from alphawatch.exceptions import DataContractError, IdentityResolutionError


@dataclass(frozen=True, slots=True)
class SymbolMapping:
    security_id: str
    ticker: str
    valid_from: date
    valid_to: date | None
    exchange: str
    sector: str | None = None
    industry: str | None = None
    cik: str | None = None
    provider_id: str | None = None

    def __post_init__(self) -> None:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise DataContractError("valid_to cannot precede valid_from")

    def contains(self, when: date) -> bool:
        return self.valid_from <= when and (self.valid_to is None or when <= self.valid_to)


class SecurityMaster:
    def __init__(self, mappings: list[SymbolMapping]) -> None:
        self._mappings = tuple(mappings)
        self._validate_no_overlaps()

    def _validate_no_overlaps(self) -> None:
        groups: dict[tuple[str, str], list[SymbolMapping]] = {}
        for row in self._mappings:
            groups.setdefault((row.ticker, row.exchange), []).append(row)
        for key, rows in groups.items():
            ordered = sorted(rows, key=lambda r: r.valid_from)
            for left, right in zip(ordered, ordered[1:], strict=False):
                if left.valid_to is None or right.valid_from <= left.valid_to:
                    raise DataContractError(f"overlapping symbol validity intervals for {key}")

    def resolve(self, ticker: str, exchange: str, when: date) -> str:
        matches = [
            row.security_id
            for row in self._mappings
            if row.ticker == ticker and row.exchange == exchange and row.contains(when)
        ]
        if len(matches) != 1:
            detail = f"{ticker}/{exchange} on {when}"
            raise IdentityResolutionError(
                f"expected exactly one mapping for {detail}; got {len(matches)}"
            )
        return matches[0]

    def resolve_cik(self, cik: str, when: date) -> str:
        normalized = cik.zfill(10)
        matches = [
            row.security_id
            for row in self._mappings
            if row.cik == normalized and row.contains(when)
        ]
        if len(set(matches)) != 1:
            raise IdentityResolutionError(
                f"expected exactly one security for CIK {normalized} on {when}; got {len(matches)}"
            )
        return matches[0]

    def as_frame(self) -> pl.DataFrame:
        return pl.DataFrame(
            [
                {
                    "security_id": row.security_id,
                    "ticker": row.ticker,
                    "exchange": row.exchange,
                    "valid_from": row.valid_from,
                    "valid_to": row.valid_to,
                    "sector": row.sector,
                    "industry": row.industry,
                    "cik": row.cik,
                    "provider_id": row.provider_id,
                }
                for row in self._mappings
            ]
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.as_frame().write_parquet(path)

    @classmethod
    def read(cls, path: Path) -> SecurityMaster:
        mappings = [SymbolMapping(**row) for row in pl.read_parquet(path).to_dicts()]
        return cls(mappings)
