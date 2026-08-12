"""Immutable research-run metadata needed to reproduce conclusions."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from alphawatch.data.contracts import require_utc


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    experiment_id: str
    created_at: datetime
    git_commit: str
    configuration_hash: str
    dataset_version: str
    data_cutoff: datetime
    factor_version: str
    feature_version: str
    target_definition: str
    model_version: str
    train_interval: str
    validation_interval: str
    test_interval: str
    transaction_cost_version: str
    random_seed: int

    def __post_init__(self) -> None:
        require_utc(self.created_at, "created_at")
        require_utc(self.data_cutoff, "data_cutoff")
        if not all(
            (
                self.experiment_id,
                self.git_commit,
                self.configuration_hash,
                self.dataset_version,
                self.factor_version,
                self.feature_version,
                self.target_definition,
                self.model_version,
                self.train_interval,
                self.validation_interval,
                self.test_interval,
                self.transaction_cost_version,
            )
        ):
            raise ValueError("experiment manifest fields must be non-empty")

    def to_dict(self) -> dict[str, str | int]:
        value = asdict(self)
        value["created_at"] = self.created_at.isoformat()
        value["data_cutoff"] = self.data_cutoff.isoformat()
        return value


def write_experiment_manifest(manifest: ExperimentManifest, root: Path) -> Path:
    """Atomically write one immutable manifest per experiment identifier."""
    directory = root / f"experiment_id={manifest.experiment_id}"
    directory.mkdir(parents=True, exist_ok=False)
    target = directory / "manifest.json"
    temporary = directory / ".manifest.tmp"
    temporary.write_text(json.dumps(manifest.to_dict(), sort_keys=True, indent=2) + "\n")
    os.replace(temporary, target)
    return target
