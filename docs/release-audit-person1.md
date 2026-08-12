# Person 1 release audit

## Scope

This audit certifies completion of the provider-neutral public-data engineering assignment:
data correctness, point-in-time factor calculations, portfolios, costs, diagnostics, lineage,
tests and executable workflows. It does not certify that an arbitrary public dataset has CRSP-level
historical coverage.

## Reproduction

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ruff check .
.venv/bin/mypy src/alphawatch
.venv/bin/pytest --cov=alphawatch --cov-fail-under=80
```

## Enforced evidence

- CI runs on every push and pull request.
- Strict type checking covers the application package.
- Coverage must remain at or above 80%.
- PIT violations raise exceptions rather than warnings.
- Bronze run paths are append-only and checksummed.
- Silver/Gold writes are atomic and accompanied by manifests.
- Corporate-action suspicion and missing sessions are visible in quality reports.
- Net factor returns always retain a cost-model version at construction time.
- Public historical results cannot be labeled survivorship-safe by default.

## Residual risks owned by data providers

- Completeness and correctness of adjusted prices
- Historical delisting and terminal-distribution coverage
- Historical universe membership
- Exact first-public dissemination time for SEC facts
- Historical sector-classification revisions

These risks are represented through input contracts, conservative availability rules and disclosures.
They become certifiable when a provider with those fields is connected; no downstream rewrite is needed.
