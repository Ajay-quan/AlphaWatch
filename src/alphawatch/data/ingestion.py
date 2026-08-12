from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from alphawatch.data.lineage import IngestionManifest, sha256_file


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    payload: bytes
    source: str
    period_start: str
    period_end: str
    dataset_version: str
    schema_version: str
    requested_at: datetime


class DataProvider(Protocol):
    def fetch(self, period_start: str, period_end: str) -> ProviderResponse: ...


class BronzeWriter:
    """Append-only raw-object writer with atomic payload and lineage sidecar."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def persist(self, response: ProviderResponse, run_id: str | None = None) -> IngestionManifest:
        resolved_run_id = run_id or uuid4().hex
        directory = self.root / response.source / f"run_id={resolved_run_id}"
        directory.mkdir(parents=True, exist_ok=False)
        temporary = directory / ".payload.tmp"
        target = directory / "payload.bin"
        temporary.write_bytes(response.payload)
        os.replace(temporary, target)
        manifest = IngestionManifest(
            source=response.source,
            requested_at=response.requested_at,
            period_start=response.period_start,
            period_end=response.period_end,
            dataset_version=response.dataset_version,
            schema_version=response.schema_version,
            checksum_sha256=sha256_file(target),
            ingestion_run_id=resolved_run_id,
        )
        manifest_tmp = directory / ".manifest.tmp"
        manifest_tmp.write_text(json.dumps(manifest.to_dict(), sort_keys=True, indent=2) + "\n")
        os.replace(manifest_tmp, directory / "manifest.json")
        return manifest
