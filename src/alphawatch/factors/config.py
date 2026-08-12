from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from alphawatch.exceptions import DataContractError


@dataclass(frozen=True, slots=True)
class TransformConfig:
    winsor_lower: float = 0.01
    winsor_upper: float = 0.99
    standardize: bool = True
    rank: bool = True
    sector_neutral: bool = False
    size_neutral: bool = False


@dataclass(frozen=True, slots=True)
class FactorConfig:
    name: str
    version: str
    parameters: dict[str, Any] = field(default_factory=dict)
    transform: TransformConfig = TransformConfig()


def load_factor_config(path: Path) -> FactorConfig:
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise DataContractError("factor configuration must be a mapping")
    name, version = payload.get("name"), payload.get("version")
    if not isinstance(name, str) or not isinstance(version, str):
        raise DataContractError("factor configuration requires string name and version")
    neutral = payload.get("neutralization", {})
    winsor = payload.get("winsorization", {})
    transform = TransformConfig(
        winsor_lower=float(winsor.get("lower", 0.01)),
        winsor_upper=float(winsor.get("upper", 0.99)),
        standardize=payload.get("standardization", "zscore") == "zscore",
        rank=bool(payload.get("ranking", True)),
        sector_neutral=bool(neutral.get("sector", False)),
        size_neutral=bool(neutral.get("size", False)),
    )
    reserved = {
        "name",
        "version",
        "winsorization",
        "standardization",
        "ranking",
        "neutralization",
        "portfolio",
    }
    return FactorConfig(
        name, version, {k: v for k, v in payload.items() if k not in reserved}, transform
    )
