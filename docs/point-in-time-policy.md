# Point-in-time policy

`observation_time` describes the economic period. `available_at` records the first
instant at which the exact value could have been known to the strategy. They are not
interchangeable.

Every research query must receive an explicit UTC `prediction_time` and enforce:

```text
available_at <= prediction_time
```

The pipeline fails closed when this invariant is violated. Fundamental data must use
filing/publication timestamps, not fiscal-period ends. Restatements are separate
vintages. Universe membership and symbol mappings are temporal. Forward returns are
labels and must never enter feature generation.

## Required leakage tests

- A filing released after the prediction timestamp is rejected.
- A later macro revision is rejected even if it describes an earlier period.
- A ticker maps through the validity interval effective on that historical date.
- Rolling windows contain only records available at prediction time.
- Forward-label intervals do not overlap training observations after purging/embargo.

