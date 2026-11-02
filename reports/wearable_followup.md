# Wearable contribution and new-onset follow-up

Completed October 29, 2026. These are **exploratory follow-up analyses on an already inspected cohort**, not an independent confirmation. Original October 24 results are preserved.

## What was added

1. A matched feature-set comparison using the same random forest and participant folds.
2. A secondary analysis of pain onset after a day with observed no/low pain.
3. Precision, recall, average precision, precision–recall curves and false alarms per 100 evaluated days.
4. A descriptive coverage check using a prespecified threshold of at least 80% observed wearable predictors.

No temporal-trend features, new data collection, hyperparameter search or threshold optimization were introduced.

## Matched model design

All four forests use the same 42 participants, 3,320 labeled 2022 days, five participant-grouped folds, random seed, hyperparameters and training-fold preprocessing. The only intended change is the predictor set:

- Previous pain only: one predictor.
- Wearables only: 15 predictors.
- Previous pain + wearables: 16 predictors.
- All features: 21 predictors, adding diary stress, mood, sleep difficulty and flow history.

The 21-feature forest exactly reproduces the original out-of-fold probabilities, and fold assignments match the original evaluation. Filtering and imputation are fitted within training folds. Each forest uses 200 trees, maximum depth 6, minimum leaf size 5, balanced-subsample class weights and random state 42. All use the estimator's default decision rule. The fixed hyperparameter values are identical, including the default feature-subsampling rule; that rule naturally draws from different available predictor counts.

## All-day results

| Model / feature set | Macro F1 | Average precision | Precision | Recall | False alarms / 100 days |
| --- | ---: | ---: | ---: | ---: | ---: |
| RF: previous pain only | 0.781 | 0.460 | 65.1% | 60.5% | 5.06 |
| RF: wearables only | 0.569 | 0.219 | 27.8% | 25.7% | 10.39 |
| RF: previous pain + wearables | 0.760 | 0.512 | 59.8% | 59.2% | 6.20 |
| RF: all features | 0.770 | 0.555 | 60.7% | 61.9% | 6.23 |
| Previous-day pain rule | 0.781 | 0.455 | 65.1% | 60.5% | 5.06 |
| Majority class | 0.458 | 0.156 | 0.0% | 0.0% | 0.00 |

The positive prevalence is 0.156. Average precision (AP) summarizes the precision–recall ranking; it is not accuracy and does not establish calibrated clinical risk.

**Matched wearable contribution:** adding wearables to the previous-pain forest increases AP from **0.460 to 0.512** (difference +0.052). The paired participant-bootstrap 95% interval for this AP difference is approximately **[+0.007, +0.081]**, conditional on fixed OOF predictions. This provides exploratory evidence that the wearable feature package improves ranking. The package includes missingness indicators, so the result does not isolate physiological values from measurement-availability patterns.

At the default operating rule, macro F1 decreases from **0.781 to 0.760**, recall decreases from **60.5% to 59.2%**, and false alarms increase from **5.06 to 6.20 per 100 days**. Therefore, ranking improves while the current classification decisions do not improve overall. The all-feature forest reaches AP 0.555 and F1 0.770; its additional gain cannot be attributed exclusively to wearables because diary features are also included.

## New pain onset: a harder secondary question

Eligibility is determined only from **observed previous-day no/low pain**, not from today's outcome. There are **2,603 eligible days** across 42 participants and **177 positive onsets** (6.8%). These are day-level transitions, not counts of independent episodes or unique cycles. We evaluate the existing all-day-trained models on this subset; we do not retrain onset-specific classifiers.

| Model / feature set | Detected onsets | False alarms | Precision | Recall | Average precision | False alarms / 100 eligible days |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RF: previous pain only | 0 / 177 | 0 | 0.0% | 0.0% | 0.068 | 0.00 |
| RF: wearables only | 38 / 177 | 302 | 11.2% | 21.5% | 0.105 | 11.60 |
| RF: previous pain + wearables | 10 / 177 | 44 | 18.5% | 5.6% | 0.102 | 1.69 |
| RF: all features | 8 / 177 | 41 | 16.3% | 4.5% | 0.117 | 1.58 |
| Previous-day pain rule | 0 / 177 | 0 | 0.0% | 0.0% | 0.068 | 0.00 |
| Majority class | 0 / 177 | 0 | 0.0% | 0.0% | 0.068 | 0.00 |

The persistence rule predicts no/low pain throughout this subset, so it detects no onsets. The history-plus-wearables forest detects **10 of 177** with **44 false alarms**: **18.5% precision**, **5.6% recall**, and **1.69 false alarms per 100 eligible days**. Its AP is **0.102**, versus **0.068** for the matched history-only forest. The paired conditional 95% interval for the AP difference is approximately **[+0.006, +0.082]**.

The wearable-only forest detects more onsets (**38**) but produces many more false alarms (**302**), with **11.2% precision**. The all-feature forest detects **8** with **41** false alarms; its AP is **0.117**, including contributions from non-wearable diary predictors. The low onset recall and false-alarm burden prevent a claim of practical readiness.

The learned history-only forest produces slightly different scores across folds, so its pooled onset AP can differ slightly from the constant-rule prevalence reference. Neither historical pain model distinguishes onset days usefully at its current decision rule.

## Coverage sensitivity

There are 2,885 target days with at least 80% of the 15 wearable values observed and 435 with less coverage. Using the same fixed OOF predictions:

- At least 80% observed: history-plus-wearables AP **0.526**, history-only AP **0.469**; wearable-only AP **0.228**.
- Below 80% observed: history-plus-wearables AP **0.408**, history-only AP **0.391**; wearable-only AP **0.157**.

These are descriptive subcohort results. Different participants, outcome prevalence, data availability and adherence may explain some differences; they do not prove missingness causes poor predictions. No coverage threshold was selected to maximize performance.

## Uncertainty and validation boundaries

We resample participants with replacement 2,000 times, paired across models. Intervals condition on fixed OOF predictions and do not refit models. Code verifies that participants do not cross folds, the full forest reproduces the original run, and the matched models share the same target days. New tests check onset eligibility, metric denominators, no-alert baselines and weighted AP with tied scores. **Twelve tests pass.**

Because these comparisons were motivated after the original results were inspected, they are exploratory. They do not create a new untouched test cohort, establish a causal effect of physiology, or show calibrated clinical risk. A useful future operating threshold would require training-only selection; none was selected here.

## Updated conclusion

**Wearable features add modest ranking information beyond previous-day pain and detect a small number of new onsets in this exploratory evaluation. They do not improve overall macro F1 at the current decision rule, and onset detection remains limited.**

The completed work now answers both the broad prediction question and the more specific question of incremental wearable contribution. Finalization tasks remain limited to checking outputs, polishing figures and explanations, completing the written report, rehearsal and submission, all due November 30, 2026. No new major modeling or sensing milestone is introduced.

## Reproduce

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m src.followup
.venv/bin/python scripts/report_followup.py
```

Detailed and participant-level outputs are in ignored `reports/runs/wearable_followup/`. Aggregate scores and provenance are also saved in `reports/followup_results.json`. Precision–recall figures are `all_days_precision_recall.png` and `new_onset_precision_recall.png` in the run directory.
