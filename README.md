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

## Public-data policy

The reference adapters support SEC Company Facts, Nasdaq Trader symbol snapshots,
and provider-neutral daily-price CSV files. Public symbol snapshots are not historical
membership data. Results built from them must retain `survivorship_safe: false` from
`configs/research.yaml`; the software refuses to turn a limitation into a false claim.

The default research convention assumes a USD 10 million long-short portfolio,
next-session-close execution, a 1% ADV cap, and a transparent versioned cost model.
These are defensible prototype assumptions, not calibrated live-trading estimates.
