# Person 2 delivery: statistical validity and research conclusions

1. **Preregister hypotheses.** `hypotheses.py` provides complete H1--H5 contracts; their
   definitions, nulls, tests, periods, and robustness checks are immutable dataclasses.
2. **Prevent leakage.** `contracts.py` makes point-in-time availability and resolved-label
   availability explicit inputs and fails a run on future data. Apply this contract after joins
   for fundamentals, macro vintages, institutional filings, corporate actions, universe
   membership, and rolling features. `labels.py` separates prediction time from label
   availability.
3. **Validate chronologically.** `validation.py` creates expanding or finite rolling
   walk-forward folds and purges all training labels that overlap the validation period, with
   an embargo control.
4. **Quantify uncertainty.** `inference.py` supplies serial-dependence-aware block-bootstrap
   intervals and Benjamini-Hochberg control for the declared hypothesis family.
5. **Constrain conclusions.** `conclusions.py` emits only conservative association categories;
   it requires PIT, untouched testing, baseline comparison, multiplicity control, and positive
   uncertainty. It never emits causal language.
6. **Test the controls.** `tests/` includes golden leakage, label, purge, inference, and
   conclusion-gating tests. CI should run this suite before factor/model work is merged.
