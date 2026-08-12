# Research and engineering sources

This is a curated evidence register, not a claim to have exhaustively read the internet.
Prefer primary specifications, official documentation, and original papers. Record the
access date and the design decision supported by every source.

## Current decisions

| Source | Decision supported | Accessed |
|---|---|---|
| [DuckDB Parquet overview](https://duckdb.org/docs/stable/data/parquet/overview) | Use Parquet projection/filter pushdown and inspectable metadata | 2026-08-13 |
| [DuckDB partitioned writes](https://duckdb.org/docs/lts/data/partitioning/partitioned_writes) | Use coarse Hive partitions and avoid high-cardinality partition explosion | 2026-08-13 |
| [DuckDB file-format guidance](https://duckdb.org/docs/current/guides/performance/file_formats) | Target moderate files and parallelizable row groups; benchmark before tuning | 2026-08-13 |
| [SEC EDGAR access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | Preserve accession IDs and acceptance metadata; identify automated clients | 2026-08-13 |
| [SEC timestamp guidance](https://www.sec.gov/about/webmaster-frequently-asked-questions) | Keep report period separate from acceptance time; add a conservative dissemination lag | 2026-08-13 |
| [Kenneth French momentum construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor_daily.html) | Validate the skip-month convention and distinguish our generic signal from the French 2×3 benchmark | 2026-08-13 |

## Important methodological choice

SEC states that filing documents are often available one to three minutes after the EDGAR
system timestamp and that no exact first-public-availability timestamp is supplied. Therefore,
the future EDGAR adapter must not equate report period or filing date with `available_at`; it
must apply a documented conservative availability rule and retain the raw acceptance timestamp.

The implemented momentum class is an individual-security signal. It is not labeled as the
Fama–French momentum factor, whose published construction uses size intersections and NYSE
breakpoints. A later benchmark implementation should reproduce that methodology separately.

