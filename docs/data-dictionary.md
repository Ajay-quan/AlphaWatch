# Person 1 data dictionary

## Canonical prices and returns

| Field | Meaning |
|---|---|
| `security_id` | Permanent AlphaWatch security identifier; never a ticker |
| `session` | Exchange trading session date |
| `available_at` | Earliest conservative UTC availability time |
| `close` | Raw provider-defined official/session close |
| `adjusted_close` | Provider-adjusted close, with adjustment policy in manifest |
| `price_return` | Raw close-to-close audit return |
| `adjusted_close_return` | Adjusted-close ratio minus one |
| `delisting_return` | Separately sourced terminal return, nullable |
| `total_return` | Principal return after any single delisting compounding |
| `corporate_action_suspected` | Raw/adjusted discontinuity requiring audit |

## Factor features

| Field | Meaning |
|---|---|
| `prediction_time` | UTC timestamp at which the feature snapshot is formed |
| `factor_name` | Stable factor identifier |
| `factor_version` | Semantic methodology version |
| `raw_value` | Untransformed economic signal when retained |
| `standardized_value` | Winsorized, optionally neutralized z-score |
| `rank` | Cross-sectional percentile rank |

## Portfolio output

| Field | Meaning |
|---|---|
| `weight` | Dollar weight; standard long-short portfolios have unit gross |
| `gross_return` | Weighted security return before implementation costs |
| `turnover` | Half the absolute weight change |
| `cost` | Versioned commission, spread, slippage and impact estimate |
| `net_return` | Gross return minus estimated cost |

All manifests bind dataset version, schema version, row count, columns and SHA-256 checksum.
No result may be labeled survivorship-safe unless its input source explicitly supports that claim.

