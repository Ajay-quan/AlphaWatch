# Statistical Validity Protocol

This protocol governs AlphaWatch research conclusions.

1. Features must satisfy `available_at <= prediction_timestamp`; forward labels start at `t + 1`.
2. Use chronological expanding-window validation with purging for the forward-label horizon and an embargo. Never shuffle observations.
3. Freeze a final untouched test period before model/threshold/horizon selection.
4. The primary predictive comparison is full model versus a performance-only baseline, using PR-AUC and paired moving-block-bootstrap confidence intervals.
5. Report calibration (Brier score and reliability), prevalence, sample sizes, and multiple-testing-adjusted p-values for secondary hypothesis families.
6. Report net—not only gross—economic simulations, including transaction-cost sensitivity.
7. Treat crowding relationships as predictive associations. Do not infer causation or call a result live-investable.

An experiment that fails any data or validation gate is inconclusive, not positive evidence.
