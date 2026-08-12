from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from alphawatch.data.contracts import require_utc


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class IngestionManifest:
    source: str
    requested_at: datetime
    period_start: str
    period_end: str
    dataset_version: str
    schema_version: str
    checksum_sha256: str
    ingestion_run_id: str

    def __post_init__(self) -> None:
        require_utc(self.requested_at, "requested_at")
        if len(self.checksum_sha256) != 64:
            raise ValueError("checksum_sha256 must contain 64 hexadecimal characters")
        int(self.checksum_sha256, 16)

    def to_dict(self) -> dict[str, str]:
        values = asdict(self)
        values["requested_at"] = self.requested_at.isoformat()
        return values
