"""Create aggregate checkpoint report from the measured real-data run."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'reports/runs/mcphases_2022'
summary=json.loads((RUN/'summary.json').read_text())
metrics=pd.read_csv(RUN/'metrics.csv')
ci=pd.read_csv(RUN/'confidence_intervals.csv')
missing=pd.read_csv(RUN/'missingness.csv',index_col=0)
importance=pd.read_csv(RUN/'permutation_importance.csv').groupby('feature').importance.mean().sort_values(ascending=False)
audit=json.loads((RUN/'cleaning_audit.json').read_text())
inv=json.loads((ROOT/'reports/data_inventory.json').read_text())
labels={'majority':'Majority class','previous_pain':'Previous-day pain','flow_timing_proxy':'Prior flow timing proxy',
        'logistic_regression':'Logistic regression','decision_tree':'Decision tree','random_forest':'Random forest',
        'logistic_without_previous_pain':'Logistic regression without previous pain',
        'random_forest_wearables_only':'Random forest, wearables only'}
order=['majority','flow_timing_proxy','previous_pain','logistic_regression','decision_tree','random_forest',
       'logistic_without_previous_pain','random_forest_wearables_only']
rows=[]
for model in order:
 r=metrics.set_index('model').loc[model]
 interval=ci[(ci.model==model)&(ci.metric=='macro_f1')].iloc[0]
 rows.append(f"| {labels[model]} | {r.macro_f1:.3f} | [{interval.ci_low:.3f}, {interval.ci_high:.3f}] | {r.balanced_accuracy:.3f} | {r.roc_auc:.3f} |")
report=f'''# Midpoint checkpoint: real-data results

Updated October 24, 2026. Team: Alina Kapanova, Fiona Wang, Vicky Wang. Six-minute presentation plus two minutes for questions.

## 1. Title

**Predicting menstrual pain using health and lifestyle factors**

## 2. Background and approach

The question is whether previous-day health, wearable and lifestyle information helps predict next-day menstrual cramp severity for unseen participants. The initial analysis is a retrospective, one-day-ahead binary classification task. It assumes measurements assigned to day t−1 are available before the day-t prediction; actual ingestion/reporting latency is not established by these exports.

Use no/low pain (Not at all, Very Low/Little, Low) versus moderate-or-higher pain (Moderate, High, Very High). This explicit mapping follows the observed ordered response labels; it is a project convention, not a clinically validated severity threshold. No/mild in the original proposal is operationalized here as no/low on the dataset's wording.

Compare majority class, previous-day pain, and a prior-flow timing proxy against logistic regression, a shallow decision tree, and random forest. Additional feature ablations assess a logistic model without previous pain and a forest using wearable predictors only.

## 3. Dataset and sensing

- Source: authorized local mcPHASES v1.0.0 download, provided by the user. Raw files are read in place, not copied or committed.
- Size: **23 CSV tables**, **{sum(x['bytes'] for x in inv):,} bytes** across all downloaded files (3.68 GB decimal; about 3.42 GiB). Across the CSVs: **{sum(x.get('rows',0) for x in inv):,} records**, mostly repeated high-frequency sensor readings. These are not independent samples.
- Devices in the source study: Fitbit Sense, Mira hormone analyzer, Dexcom G6 in the first interval, and daily symptom diaries. This project uses existing data; no new wearable pilot has been collected.
- Diary: **5,659 participant-days**, **3,327 nonmissing cramp responses** across both intervals. The 2024 interval contributes only **7** observed cramp outcomes, so the primary supervised analysis uses **2022 only**.
- Primary cohort: **42 participants**, **3,698 diary days**, **3,320 labeled days**. Missing cramp outcomes: **378** days, excluded rather than imputed.
- Class balance: **2,803 no/low** and **517 moderate-or-higher** days (**15.6% positive**).
- Nine source tables supply **21 prior-day predictors** including previous pain. Feature groups: diary stress/mood/sleep difficulty/flow history; Fitbit activity, resting heart rate, HRV, sleep duration/quality, breathing rate, nightly temperature, and stress score.
- Selection bias: small Toronto-area cohort; recruitment and eligibility constrain generalization. Only one gender category has at least five participants. Income is mentioned in the supplied README but is absent from the actual demographic table. No male/female or income fairness claim is supported.

## 4. Completed milestones and issues faced

Completed: dataset acquisition and full file inventory; codebook/schema inspection; explicit label mapping; audited daily feature construction; participant-grouped model fitting; out-of-fold evaluation; baseline and feature-ablation comparisons; participant-cluster uncertainty; exploratory demographic audit; and explainability outputs. Eight targeted tests pass.

Cleaning and feature decisions:

- Restricted primary training to 2022 before feature construction; did not mix the sparse-label 2024 interval into headline scores.
- Kept a single diary outcome per participant-day and never imputed pain labels. Exact duplicate sensor records were removed before aggregation. Distinct repeated summaries use a median.
- Sleep is assigned to its end day, restricted to main sleep. Median session summaries avoid summing repeated or revised sleep records. This initial choice does not fully reconstruct sleep stages or all naps.
- Valid Fitbit stress scores require READY/READY_NOT_PREMIUM status and no failed calculation; IN_PROGRESS/NO_DATA zero placeholders are excluded. **3,601 exact duplicate stress-score records** were removed in 2022.
- Broad prespecified bounds flagged **782 resting-HR values**, **53 respiratory-rate values**, and **7 HRV values** as missing; these are source measurements, not outcome exclusions. HRV additionally requires coverage ≥0.8 (5,950 low/absent-coverage records excluded).
- Absolute nightly temperature is used; proprietary temperature-baseline deviations and retrospective hormone-derived phase labels are excluded to avoid uncertain use of future information.
- Exact day t−1 joins prevent gaps or collection rounds from being treated as consecutive days. The prior-flow timing feature uses only observed flow history and is not true cycle phase.
- Missingness filtering (>60% missing), median imputation with missingness indicators, and scaling are fitted separately inside each training fold.

Forecast-feature missingness ranges from **{missing.missing_fraction.min():.1%}** to **{missing.missing_fraction.max():.1%}**; Fitbit stress score has the highest missingness. Previous pain is absent on **236** labeled target days (7.1%). It remains missing for learned models; the persistence baseline falls back to the training fold's majority class.

Validation: **five GroupKFold folds**, with each participant appearing in one test fold and no participant shared between training and test. Fixed hyperparameters and random state 42; no validation-driven tuning. There is no independent final test cohort. Macro F1 and balanced accuracy address class imbalance; AUC assesses ranking. Persistence AUC uses hard 0/1 predictions, so it has only a single operating point.

## 5. Initial results

| Model / baseline | Macro F1 | 95% cluster-bootstrap interval for F1 | Balanced accuracy | ROC-AUC |
| --- | ---: | --- | ---: | ---: |
{chr(10).join(rows)}

Intervals resample 42 participants with replacement (2,000 replicates), using paired resamples across models. They are conditional on the fixed out-of-fold predictions and do not refit the models or capture every source of model-selection uncertainty.

**Main result:** all three full-feature classifiers improve on majority class, but none beats previous-day pain on macro F1. Random forest is the strongest of the three full classifiers (0.770), while persistence reaches 0.781. Their balanced accuracies are nearly equal (both round to 0.773). The paired bootstrap F1 difference (forest minus persistence) is −0.010, with a conditional 95% interval of approximately [−0.022, −0.002]. Do not claim added wearable value from this comparison. Forest/logistic AUCs are higher than the hard persistence baseline's AUC, but that alone does not demonstrate better decisions or calibration.

Random-forest confusion matrix (rows actual, columns predicted; class order no/low, moderate-or-higher):

| Actual / predicted | No/low | Moderate-or-higher |
| --- | ---: | ---: |
| No/low | 2,596 | 207 |
| Moderate-or-higher | 197 | 320 |

It identifies 320/517 moderate-or-higher days (61.9% sensitivity) and misses 197. The persistence baseline identifies 313/517 (60.5%) and produces fewer false positives (168 versus 207).

Interpretation: previous pain dominates random-forest held-out permutation importance (mean balanced-accuracy decrease **{importance['previous_pain']:.3f}**). Other individual predictors have much smaller importance; these are predictive associations, not causes. Logistic coefficients and per-fold retained features are saved for inspection. Correlation and missingness can complicate attribution.

Sensitivity: on the 3,084 labeled days with observed previous-day pain, the existing fixed OOF predictions give macro F1 **0.789** for persistence and **0.778** for forest. The central conclusion is unchanged. This coverage analysis does not refit models.

Exploratory bias check: groups require at least five participants and at least ten days of each target class. Among supported ethnicity groups, forest false-negative rates range from approximately **26% to 59%**. Small and unequal participant counts, different label prevalence, and repeated observations prevent a population fairness conclusion. Compare these results with persistence in `subgroup_metrics.csv`; do not interpret the gaps as causal demographic effects. Tiny groups are suppressed. Only the Woman gender category meets the participant threshold, preventing a supported gender comparison.

## 6. Next steps and revised milestones

| Target in 2026 | Milestone | Proposed team lead |
| --- | --- | --- |
| Oct 24 — completed | Download, inventory, audited primary dataset, first models and grouped evaluation | Team |
| Oct 30 | Inspect failure cases and missingness mechanisms; add imputation/coverage sensitivity | Vicky + Alina |
| Nov 6 | Review forecast timing and observed-flow proxy; predefine any new features | Alina + Fiona |
| Nov 13 | Nested participant-grouped tuning and leave-one-participant-out robustness | Alina + Vicky |
| Nov 24 | Refine uncertainty and subgroup comparisons; decide whether pilot is feasible | Alina + Fiona |
| Dec 2 | Final explainability and frozen reproducible rerun | Alina + Vicky |
| Dec 4 | Final report, conclusions, figures and presentation | Alina + Fiona; all review |

Keep the optional wearable pilot off the core path until a feasible protocol and device access exist. No pilot results are claimed. Because the initial results have already been inspected, this cohort cannot later be described as a pristine independent final test set. Any further model development requires nested grouped evaluation and transparent reporting, or a separate authorized cohort for an independent test.

The main open scientific question is whether signals beyond pain history add value under a defensible prospective timing convention. A null or limited improvement is a valid finding. Final success also includes reproducibility, careful validation, error analysis and honest limits.

## Run and evidence locations

- `src/mcphases.py`: actual-schema daily adapter and audit rules.
- `src/pipeline.py`: fixed model comparison and grouped evaluation.
- `src/evaluation.py`: participant-cluster intervals, coverage sensitivity and supported subgroup metrics.
- `reports/data_inventory.json`: table sizes, columns and row counts.
- `reports/runs/mcphases_2022/`: private participant-level derivatives plus aggregate metrics, missingness, plots, feature importance, coefficients, audit and run metadata. This directory is ignored by Git.
- `reports/verification.md`: completed checks.

Dataset and context source: mcPHASES v1.0.0, https://physionet.org/content/mcphases/1.0.0/ ; the downloaded README, schemas and measured files. Original proposal references remain in `proposal_answers.md`. No clinical validity or causal effects are claimed.
'''
(ROOT/'reports/midpoint_checkpoint.md').write_text(report)
# Aggregate results suitable for presentation generation; no participant identifiers.
records=metrics.set_index('model').loc[order].reset_index().to_dict('records')
(ROOT/'reports/initial_results.json').write_text(json.dumps({'date':'2026-10-24','participants':42,'labeled_days':3320,
    'positive_days':517,'metrics':records,'source_run':'reports/runs/mcphases_2022','status':'REAL_DATA_EXPLORATORY_CV'},indent=2)+'\n')
print(ROOT/'reports/midpoint_checkpoint.md')
