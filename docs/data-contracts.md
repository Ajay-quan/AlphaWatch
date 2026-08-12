# Data contracts

## Bronze

Provider bytes are immutable. Each object has a sidecar manifest containing source,
UTC request time, requested period, provider dataset version, schema version, SHA-256,
and ingestion run ID. Corrections create a new object; they never overwrite history.

## Silver

Normalized records use permanent `security_id`, UTC availability timestamps, explicit
units, and temporal mappings. Uniqueness keys and adjustment conventions belong in each
dataset specification.

## Gold

Research tables are versioned Parquet datasets. Partition only on commonly filtered,
low-cardinality fields (normally year/month or date); avoid security-level partitions.
Sort by date and security before writing. Dataset manifests bind schema, configuration,
input checksums, code commit, and row-level quality results.

The typed contracts in `src/alphawatch/data/contracts.py` are the executable minimum.

