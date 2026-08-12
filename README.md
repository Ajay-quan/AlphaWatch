# AlphaWatch

AlphaWatch is a quantitative research platform for evaluating factor deterioration without
confusing temporary underperformance, structural instability, cost drag, or crowding with a
permanent loss of predictive power.

## Current foundation: statistical validity (Person 2)

This repository starts with the non-negotiable research controls:

- point-in-time availability validation that fails closed;
- forward-label construction with an explicit information cutoff;
- chronological purged-and-embargoed folds for overlapping labels;
- preregistered hypothesis specifications and a hypothesis ledger;
- bootstrap confidence intervals and Benjamini-Hochberg multiple-testing control;
- structured, evidence-bounded research conclusions.

These controls are deliberately provider- and framework-agnostic so ingestion, factors, and
models can use them as a common contract.

## Quick start

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

See `docs/research_protocol.md` for the confirmatory protocol and
`docs/person2_delivery.md` for the implementation inventory.
