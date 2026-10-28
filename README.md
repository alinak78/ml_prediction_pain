# Predicting menstrual pain using health and lifestyle factors

Alina Kapanova · Fiona Wang · Vicky Wang

**Real-data checkpoint, October 24, 2026:** mcPHASES v1.0.0 has been inventoried, processed and evaluated. The primary analysis uses 3,320 labeled days from 42 participants in 2022. Eight targeted tests pass. The previous-day pain baseline has macro F1 **0.781**, compared with **0.770** for the full random forest; added features have not beaten persistence on this metric. These are exploratory participant-held-out results, not an independent clinical validation.

## Results and presentation

- `reports/midpoint_checkpoint.md`: assignment answers, dataset audit, model scores with participant-level uncertainty, limitations and revised milestones.
- `reports/initial_results.json`: aggregate scores for eight model/baseline/ablation configurations.
- `output/presentation/midpoint_six_sections.pptx`: latest six-slide presentation in the required midpoint order, restructured October 28 for six minutes plus two minutes of questions.
- `output/presentation/midpoint_six_sections_notes.md`: timed speaker notes and Q&A prompts for the latest deck.
- `output/presentation/midpoint_real_data.pptx`: earlier seven-slide real-data checkpoint, retained for reference.
- `output/presentation/speaker_notes.md`: timed notes matching the updated deck.
- `reports/data_inventory.json`: full CSV inventory (23 tables, 3.68 GB extracted; 110.1 million records, mostly repeated sensor samples).
- `proposal_answers.md`: original proposal answers, preserved as the initial plan.
- `reports/runs/mcphases_2022/`: detailed real-data outputs; ignored by Git because some files contain participant-level derivatives.

The earlier `midpoint.pptx` is retained as an October 22 implementation checkpoint. Use `midpoint_six_sections.pptx` for the class presentation; the real-data metrics are unchanged.

## Reproduce

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m src.mcphases
.venv/bin/python -m src.evaluation
.venv/bin/python scripts/report_results.py
```

The mcPHASES command automatically locates the single authorized `mcphases*` folder beside this project. Alternatively pass `--raw "/path/to/authorized/dataset"`. The evaluation command uses the source directory recorded in the real run's summary; it also accepts `--raw`. Both default to `reports/runs/mcphases_2022`.

To rebuild the inventory (pass the actual dataset directory):

```sh
.venv/bin/python -m src.pipeline inventory --raw "/path/to/authorized/dataset" --output reports/data_inventory.json
```

Do not commit the restricted raw files or participant-level derivatives. The existing download is read in place; no raw files are moved or changed. Obtain your own authorization before accessing this restricted dataset: https://physionet.org/content/mcphases/1.0.0/.

## Primary analysis decisions

- Use 2022 only: the 2024 diary has just **seven** nonmissing cramp outcomes. Primary 2022 cohort: 3,698 diary days, 3,320 observed labels; never impute missing outcomes.
- Binary target: Not at all / Very Low-Little / Low = 0; Moderate / High / Very High = 1. There are 2,803 negative and 517 positive days. This is a project threshold, not a clinical cutoff.
- Nine source tables provide **21 prior-day predictors**, including previous pain. Sleep is indexed by end day. All features are joined from **exact day t−1**, never the previous observed row across a gap. Retrospective phase/hormone labels and proprietary temperature-baseline deviations are excluded.
- Remove exact duplicate sensor records, invalid stress-score statuses and physiologically implausible values under documented broad bounds. Distinct repeated daily summaries use medians; HRV requires coverage ≥0.8. Rules and counts are recorded in `cleaning_audit.json`.
- Five-fold GroupKFold: hold out complete participants. Within each training fold, filter features with >60% missing values, median-impute with missingness indicators, scale and fit. Fixed hyperparameters and seed 42; no tuning against these test folds.
- Models: logistic regression, decision tree and random forest. Baselines: majority, previous pain (training-majority fallback if missing), prior-flow history proxy. Ablations: logistic without previous pain, wearable-only forest.
- Metrics: macro F1, balanced accuracy, ROC-AUC and confusion matrices. AUC for persistence uses hard predictions; it is not a calibrated probability model.
- Explainability: forest permutation importance on held-out folds and logistic coefficients. Previous pain dominates forest importance. Interpret associations, not causation.
- Uncertainty: 2,000 paired participant-cluster bootstrap resamples of fixed OOF predictions. No model refitting in these intervals. Coverage sensitivity restricts the same predictions to days with known previous pain.
- Subgroups: exploratory gender/ethnicity/education audit only for groups with ≥5 participants and ≥10 target days in each class. Small groups suppressed. Only one gender category is supported; income is absent from the actual demographic table.

## Limits and remaining work

This is a retrospective one-day-ahead task. Actual report/upload availability at prediction time still requires validation. The limited cohort, missing labels, uncertain sensor processing, class imbalance and substantial subgroup error differences constrain conclusions. No independent final test set exists, and the 2024 data have too few pain labels for useful external testing. Further tuning should use nested participant-grouped validation; the already inspected cohort cannot later be called an untouched final test set.

Next: inspect failure cases, examine missingness mechanisms and imputation sensitivity, review the observed-flow timing proxy and feature availability, run nested/leave-one-participant-out robustness checks, and refine explanations. No optional wearable pilot has been collected.

## Code and software checks

- `src/mcphases.py`: actual-schema adapter and cleaning audit.
- `src/pipeline.py`: models, baseline comparison and grouped evaluation. A generic manifest-driven adapter is retained for other verified CSV/TSV layouts; `configs/manifest.example.json` is illustrative and is **not** the active mcPHASES adapter.
- `src/evaluation.py`: uncertainty, sensitivity and supported subgroup results.
- `scripts/report_results.py`: aggregate report from saved real-data outputs.
- `scripts/update_midpoint.py` and `scripts/build_midpoint.mjs`: slide content and editable presentation construction using the bundled Artifact Tool runtime. The builder requires `RUNTIME_NODE_MODULES` and `RUNTIME_PYTHON`; pass a new output filename when rebuilding to preserve earlier files.
- `requirements-lock.txt`: installed versions for this workspace; other Python/platform versions may require fresh resolution from `requirements.txt`.

Synthetic smoke testing remains available with `.venv/bin/python -m src.pipeline smoke`. Its outputs are software checks only and are kept separately from real results.
