# AlphaWatch confirmatory research protocol

## Decision boundary

AlphaWatch tests whether information known at a prediction time is associated with later
factor deterioration. It does not infer that crowding causes deterioration. A rejection of a
null is an association conditional on the stated universe, data vintages, definitions, and
validation protocol.

## Hypotheses and outcomes

| ID | Dependent variable | Null | Primary test |
| --- | --- | --- | --- |
| H1 | Future Rank IC deterioration | Crowding coefficients are zero | Purged walk-forward logistic model |
| H2 | Future drawdown/CVaR vs mean-return deterioration | Equal predictive performance | Paired OOS comparison |
| H3 | Detection delay to confirmed deterioration | Structural delay is not shorter | Event-level paired test |
| H4 | Future deterioration | No factor-family interaction | Interaction/hierarchical model |
| H5 | Future deterioration | No OOS uplift over performance-only model | Nested walk-forward comparison |

The formal objects, periods, interpretation, and robustness checks are encoded in
`alphawatch.research.hypotheses.default_hypotheses`; experiment records must serialize the
resulting specification and its configuration hash before a confirmatory run.

## Fixed protocol

1. The universe, factor versions, data cutoff, labels, horizons, costs, and test period are
   frozen before final-test access.
2. Every post-join feature is validated with `available_at <= prediction_timestamp`.
   Violations abort the run.
3. Forward labels are unavailable until their complete forward interval ends. Training rows
   whose labels overlap validation are purged; an embargo removes adjacent observations.
   Validation may use an expanding history or a predeclared finite rolling training window;
   neither may use a shuffled split.
4. Hyperparameters and operating thresholds are selected only within training/validation
   folds. The final test set is accessed once for confirmation.
5. Results include net economic outcomes, calibration, false alarms, uncertainty, and
   negative findings. H1--H5 use Benjamini-Hochberg FDR control as one declared family.

## Interpretation rules

Use “out-of-sample association” only when the untouched test, PIT check, multiplicity control,
baseline comparison, and positive uncertainty bound pass. “Robust” additionally requires every
predeclared robustness check in a confirmatory run. Nothing in this protocol licenses a causal
claim, a claim of permanent alpha loss, or a claim of live investability.
