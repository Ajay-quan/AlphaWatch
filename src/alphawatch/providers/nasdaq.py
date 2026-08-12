from __future__ import annotations

from io import BytesIO

import polars as pl

from alphawatch.exceptions import DataContractError
from alphawatch.providers.http import HttpClient

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


class NasdaqSymbolDirectoryProvider:
    """Current-day reference snapshot. Never use it as historical membership."""

    def __init__(self, user_agent: str) -> None:
        self.client = HttpClient(user_agent)

    def fetch_nasdaq(self) -> bytes:
        return self.client.get(NASDAQ_LISTED_URL)

    def fetch_other(self) -> bytes:
        return self.client.get(OTHER_LISTED_URL)

    @staticmethod
    def parse(payload: bytes) -> pl.DataFrame:
        frame = pl.read_csv(BytesIO(payload), separator="|", infer_schema=False)
        first = frame.columns[0]
        frame = frame.filter(~pl.col(first).str.starts_with("File Creation Time"))
        if frame.is_empty():
            raise DataContractError("Nasdaq symbol directory has no security rows")
        return frame
