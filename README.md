# AlphaWatch

AlphaWatch is a point-in-time-correct research platform for monitoring systematic
equity factors. This repository currently contains the Person 1 foundation: data
contracts, immutable-ingestion metadata, temporal security identity resolution,
leakage guards, factor calculations, portfolio construction, costs, and tests.

## Non-negotiable invariant

No observation may be used when `available_at > prediction_timestamp`. Tickers are
labels, never identifiers; all analytical records use a permanent `security_id`.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

The core mathematical tests also run without third-party packages:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

See `docs/person1-roadmap.md`, `docs/data-contracts.md`, and
`docs/point-in-time-policy.md` before adding a data provider.

