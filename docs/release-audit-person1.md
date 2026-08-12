# Person 1 release audit

Status: **not yet certified**.

The audit requires a clean fresh installation, a real input dataset flowing through Bronze, Silver
and Gold, all twelve factors, costed portfolio returns, diagnostics, immutable lineage, and the full
test matrix. Passing unit tests alone is insufficient.

Current verified strengths:

- Core UTC point-in-time guards
- Basic immutable raw-run directory semantics
- Local Parquet artifacts and checksums
- Temporal ticker-resolution primitive
- Initial factor mathematics
- Basic long-short portfolio and cost primitives
- Unit tests, Ruff and strict mypy checks

Current release blockers are listed in `person1-definition-of-done.md` and
`person1-roadmap.md`. Certification must not be changed to complete until every unchecked item has
executable evidence.
