# Verification record — October 24, 2026

- Full raw directory inventoried: 23 CSVs, 110,135,462 CSV records and 3,676,157,365 bytes across downloaded files. Source files were read without modification.
- Verified actual diary labels, per-interval counts, sensor schemas, duplicate records and available demographic columns against the supplied README and CSVs.
- Real primary run completed: 2022, 42 participants, 3,320 observed target days, five participant-grouped folds, 21 predictors. Three full classifiers, three baselines and two feature-ablation configurations completed.
- Model code asserts disjoint training/test participant groups. Evaluation checks that each participant belongs to one test fold, each model has one prediction per target day, and OOF coverage matches the forecast table.
- Training-fold-only missingness filtering, imputation and scaling; no outcome imputation.
- 2,000 paired participant-cluster bootstrap resamples; coverage sensitivity; supported demographic subgroup audit.
- Eight targeted unit tests pass, covering exact-day lagging/participant boundaries, gaps, missing labels, missing aggregation sums, unknown labels, duplicate diary rows, training-only filtering, causal flow-history construction and count-based uncertainty metrics.
- Detailed evidence is in ignored `reports/runs/mcphases_2022/`: metrics, OOF predictions, per-fold metrics, CIs, paired differences, sensitivity, subgroup results, missingness, retained features, coefficients, forest permutation importance, plots and cleaning/run metadata.
- Source SHA256 hashes for the nine selected tables are recorded in `cleaning_audit.json`. They identify the processed inputs; comparison with the publisher's checksum list has not been performed.
- Updated presentation uses aggregate real-data results. Native tables and editable text are checked by the presentation finalizer and visual rendering workflow.

Limits: no independent final cohort, no clinical validation, no prospective ingestion latency verification, no causal interpretation, no pilot collection. Bootstrap intervals condition on fixed OOF predictions. Subgroup findings are exploratory.
