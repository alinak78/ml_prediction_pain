# Predicting menstrual pain using health and lifestyle factors

Alina Kapanova · Fiona Wang · Vicky Wang

**Current midpoint materials, November 2, 2026:** [reviewed presentation](output/presentation/midpoint_checkpoint.pptx) (10 main slides plus a references backup), [speaker notes](output/presentation/midpoint_checkpoint_notes.md), [editable report](output/reports/midpoint_checkpoint_report.docx), and [report text](reports/midpoint_checkpoint_report.md). The expanded analysis considers 29 candidate predictors. Adding five prior-day bodily symptoms to pain severity raises average precision from **0.526 to 0.623**, while balanced accuracy changes from **0.804 to 0.795**. These are exploratory results. All **30 tests pass**; final delivery tasks remain due November 30. [Detailed literature and results](reports/literature_review_and_feature_plan.md).

**Real-data checkpoint, October 24, 2026:** mcPHASES v1.0.0 has been inventoried, processed and evaluated. The primary analysis uses 3,320 labeled days from 42 participants in 2022. Eight targeted tests pass. The previous-day pain baseline has macro F1 **0.781**, compared with **0.770** for the full random forest; added features have not beaten persistence on this metric. These are exploratory participant-held-out results, not an independent clinical validation.

## Results and presentation

Earlier materials (October 28–29): ten-slide presentation `output/presentation/midpoint_strengthened.pptx`, timed for six minutes; speaker notes in `output/presentation/midpoint_strengthened_notes.md`. The earlier work summary is in [Google Docs](https://docs.google.com/document/d/1rPALrh9VteeQGsUyTlLdnCj2I2kMRP_ENgaAo7enSK4/edit) and `reports/work_summary_by_section.md`. The updated report and reviewed presentation linked above include the November 1 literature extension and supplementary experiments.

- `reports/midpoint_checkpoint.md`: assignment answers, dataset audit, model scores with participant-level uncertainty, limitations and revised milestones.
- `reports/initial_results.json`: aggregate scores for eight model/baseline/ablation configurations.
- `output/presentation/midpoint_six_sections.pptx`: earlier six-slide presentation in the required midpoint order, restructured October 28 for six minutes plus two minutes of questions.
- `output/presentation/midpoint_six_sections_notes.md`: timed speaker notes and Q&A prompts for the latest deck.
- `output/presentation/midpoint_real_data.pptx`: earlier seven-slide real-data checkpoint, retained for reference.
- `output/presentation/speaker_notes.md`: timed notes matching the updated deck.
- `reports/data_inventory.json`: full CSV inventory (23 tables, 3.68 GB extracted; 110.1 million records, mostly repeated sensor samples).
- `proposal_answers.md`: original proposal answers, preserved as the initial plan.
- `reports/runs/mcphases_2022/`: detailed real-data outputs; ignored by Git because some files contain participant-level derivatives.

The earlier `midpoint.pptx` is retained as an October 22 implementation checkpoint. Use `midpoint_checkpoint.pptx` for the current class presentation. Earlier decks retain their original analysis scope and dates.

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

The core fixed-model analysis is complete. Remaining delivery work is final output review, figure and explanation polish, report assembly, rehearsal and submission. New nested tuning, external validation and optional pilot collection are extensions beyond the current final scope, not required remaining milestones. No optional wearable pilot has been collected.

## Code and software checks

- `src/mcphases.py`: actual-schema adapter and cleaning audit.
- `src/pipeline.py`: models, baseline comparison and grouped evaluation. A generic manifest-driven adapter is retained for other verified CSV/TSV layouts; `configs/manifest.example.json` is illustrative and is **not** the active mcPHASES adapter.
- `src/evaluation.py`: uncertainty, sensitivity and supported subgroup results.
- `scripts/report_results.py`: aggregate report from saved real-data outputs.
- `scripts/update_midpoint.py` and `scripts/build_midpoint.mjs`: slide content and editable presentation construction using the bundled Artifact Tool runtime. The builder requires `RUNTIME_NODE_MODULES` and `RUNTIME_PYTHON`; pass a new output filename when rebuilding to preserve earlier files.
- `requirements-lock.txt`: installed versions for this workspace; other Python/platform versions may require fresh resolution from `requirements.txt`.

Synthetic smoke testing remains available with `.venv/bin/python -m src.pipeline smoke`. Its outputs are software checks only and are kept separately from real results.

Final schedule update: October analysis and count checks are completed. All remaining finalization and submission tasks are due November 30, 2026.

## Completed October 29 follow-up

Run `.venv/bin/python -m src.followup` then `.venv/bin/python scripts/report_followup.py`. The matched forests preserve original folds and reproduce the original full-model predictions. `reports/wearable_followup.md` details average precision, new onset, false-alarm trade-offs, coverage sensitivity and conditional participant-bootstrap intervals. The Google Doc and `output/presentation/midpoint_strengthened.pptx` include these findings. Detailed participant-level outputs remain ignored under `reports/runs/wearable_followup/`.

Adding wearables to the same history-only forest improves average precision from 0.460 to 0.512, while macro F1 falls from 0.781 to 0.760. The combined model detects 10 of 177 new onsets with 44 false alarms. These are exploratory findings on the previously inspected cohort, not independent clinical validation. No tuning or threshold optimization was performed. Finalization tasks remain due November 30.

## November 1 supplementary PhysioPain experiment

The extracted PhysioPain v4 archive has been audited and its raw wristband recordings processed. Actual files contain 99 survey participants and 86 raw wristband participants. Only nine explicitly report menstrual pain. Two abdominal-pain reports were placed in the supplied menstrual folder and are excluded. Original current-pain survey responses define labels; processed severity values are not used as targets.

The separate current-pain experiment uses 17 female participants: eight with moderate-or-higher menstrual pain, one with mild menstrual pain, and eight no-pain controls. Nine raw wearable features use aligned ten-minute windows after a 30-second settling period; seven lifestyle questions provide a separate feature set. Fixed logistic and forest models use leave-one-participant-out evaluation, with preprocessing fit within training folds. Lifestyle logistic balanced accuracy is 0.646; adding wearables reduces it to 0.472. The cohort is too small to establish reliable feature utility.

Read [the analysis](reports/physiopain_analysis.md) and [aggregate results](reports/physiopain_results.json). This study has no consecutive daily predictor/outcome pairs, so these results do not externally validate the mcPHASES next-day forecasting model. The source and participant derivatives stay ignored under `data/` and `reports/runs/physiopain/`.

Reproduce modeling with `.venv/bin/python -m src.physiopain`. If rebuilding the survey conversion, first run `python -m src.physiopain --prepare-survey-only` using an interpreter with pandas/openpyxl (the bundled workspace Python supports it). The source and conversion hashes are verified before modeling. Run `.venv/bin/python -m pytest -q` for checks.

## November 1 MPIS observed-only forecasting replication

The MPIS release contains 2,160 filled participant-day rows, but 1,856 (85.9%) are imputed. Excluding imputed targets and prior-day inputs leaves 304 observed reports from 19 people. There are 178 consecutive observed-day pairs. The primary control-phase analysis has **105 pairs from 14 people**, including 14 observed outcomes with pain ≥4/10 (a project threshold).

Six fixed logistic/forest configurations and two baseline rules use leave-one-participant-out evaluation with training-only preprocessing. The previous-day pain rule has the highest primary balanced accuracy (**0.747**) and macro F1 (**0.740**). Its conditional 95% participant-bootstrap balanced-accuracy interval is **[0.488, 0.849]**. Added diary/baseline attributes do not consistently improve results. Pre-intervention-only and all-phase sensitivities, equal-person weighting, and paired bootstrap comparisons are included.

Read [the MPIS analysis](reports/mpis_analysis.md) and [aggregate results](reports/mpis_results.json). This is a separate within-MPIS forecasting replication with newly trained models, not external evaluation of a frozen mcPHASES model. MPIS has no wearable recordings, and participant-level non-overlap is unverified. Imputed outcomes and model-generated free-text labels are never used. Reproduce with `.venv/bin/python -m src.mpis`; participant-level outputs remain ignored under `reports/runs/mpis/`.

## November 1 literature-informed multifactor extension

Read [the paper review and new analysis](reports/literature_review_and_feature_plan.md). The four supplied sources use Raine, a NorthShore adult longitudinal cohort, EMPATHY, and the DES Reproductive Health Study. Their designs, measures, null findings and data-access limits are recorded in [the evidence file](reports/literature_evidence.json). Their participant records have not been obtained.

The mcPHASES extension tests 29 candidate predictors across prior-day pain severity and seven additional domains, with the original participants and folds. Five prior-day somatic symptoms improve average precision from 0.526 to 0.623 relative to ordinal pain severity alone (conditional paired 95% interval for the change: +0.012 to +0.146). Balanced accuracy falls from 0.804 to 0.795. The full forest has AP 0.602; its unique somatic-block contribution is uncertain after other domains are included. The model without pain history retains AP 0.495 and balanced accuracy 0.718. Seven leave-one-domain-out comparisons and logistic alternatives prevent interpreting the best comparison as universal improvement.

MPIS adds reproductive/clinical baseline variables to its observed-only participant-held-out analysis. The clinical block raises primary balanced accuracy from 0.720 to 0.775, but its paired interval includes zero and the gain is absent in the stricter pre-intervention sensitivity. All analyses are exploratory, use fixed settings, and preserve the original raw/run files. Somatic diary symptoms are proxies, not validated BSI/CSSI scales; mood swings are not depression scores. The proposed bleeding-onset clock survives missingness filtering in only one of five mcPHASES folds.

Reproduce after the original mcPHASES and MPIS runs:

```sh
.venv/bin/python -m src.literature_analysis
.venv/bin/python scripts/report_literature.py
.venv/bin/python -m pytest -q
```

Aggregate results are in `reports/literature_factor_results.json`; the reusable figure is `reports/figures/literature_feature_blocks.png` (also SVG). Private derivatives remain ignored under `reports/runs/literature_factors/`. The earlier presentation and Google Doc are preserved; this extension is documented in the new local report.

## Updated midpoint report

The complete cited checkpoint report is `output/reports/midpoint_checkpoint_report.docx`, with matching text in `reports/midpoint_checkpoint_report.md`. It follows the required title, background, dataset/sensing, completed milestones, initial results and next-steps order; explains all five bodily symptoms; includes the November 1 multifactor results and 14 references; and keeps remaining finalization tasks due November 30. Rebuild the editable report using the bundled workspace Python with `scripts/build_midpoint_report.py`.
