from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import polars as pl

from alphawatch.data.lineage import sha256_file
from alphawatch.exceptions import DataContractError


@dataclass(frozen=True, slots=True)
class DatasetArtifact:
    path: Path
    checksum_sha256: str
    rows: int
    schema_version: str


class ParquetLake:
    """Atomic local Parquet writer; object-store adapters can implement the same contract."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def write(
        self, layer: str, dataset: str, version: str, frame: pl.DataFrame, schema_version: str
    ) -> DatasetArtifact:
        if layer not in {"bronze", "silver", "gold"}:
            raise DataContractError(f"unsupported layer: {layer}")
        if not dataset or "/" in dataset or not version:
            raise DataContractError("dataset and version must be safe, non-empty path components")
        directory = self.root / layer / dataset / f"version={version}"
        if directory.exists():
            raise DataContractError(
                f"immutable dataset version already exists: {layer}/{dataset}/{version}"
            )
        directory.mkdir(parents=True, exist_ok=False)
        target = directory / "part-00000.parquet"
        temporary = directory / f".{uuid4().hex}.parquet.tmp"
        frame.write_parquet(temporary, compression="zstd", statistics=True)
        os.replace(temporary, target)
        checksum = sha256_file(target)
        manifest = {
            "dataset": dataset,
            "layer": layer,
            "version": version,
            "schema_version": schema_version,
            "rows": frame.height,
            "columns": frame.columns,
            "checksum_sha256": checksum,
        }
        manifest_tmp = directory / f".{uuid4().hex}.manifest.tmp"
        manifest_tmp.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        os.replace(manifest_tmp, directory / "manifest.json")
        return DatasetArtifact(target, checksum, frame.height, schema_version)

    def read(self, layer: str, dataset: str, version: str) -> pl.DataFrame:
        target = self.root / layer / dataset / f"version={version}" / "part-00000.parquet"
        if not target.exists():
            raise FileNotFoundError(target)
        return pl.read_parquet(target)
