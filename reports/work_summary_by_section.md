# Predicting menstrual pain using health and lifestyle factors

Work summary by presentation section • October 28, 2026

Team: Alina Kapanova, Fiona Wang and Vicky Wang. This document describes the completed work behind the midpoint presentation. Results come from the October 24 real-data run. The six required sections can span multiple presentation slides.

## 1. Title and project scope

The project investigates whether health and lifestyle information can predict next-day menstrual cramp severity for people who were not included in model training. The implemented scope covers the complete analysis workflow: dataset inspection, daily feature preparation, model and baseline comparison, participant-held-out evaluation, uncertainty estimates, initial explainability and an exploratory demographic audit. The remaining delivery work is final review and communication of these findings.

The main finding is that previous-day pain is a strong baseline. The additional features have not improved macro F1 beyond that baseline in the current evaluation. This is a valid research result and will be reported directly rather than treated as an unfinished model-building milestone.

## 2. Background: problem and approach

Menstrual pain varies across people and cycles, which makes severity difficult to anticipate. Our proposal asks whether sleep, stress, physical activity, physiological signals and menstrual history can provide useful predictive information. We use an existing dataset rather than collecting a new sensing cohort.

The task is retrospective one-day-ahead classification: predict pain on day t using information assigned to exact day t−1. The observed response labels are mapped to no/low pain (Not at all, Very Low/Little, Low) or moderate-or-higher pain (Moderate, High, Very High). This threshold is an analysis convention, not a clinically validated cutoff.

We implemented logistic regression, a decision tree and random forest. We compare them with majority-class prediction, previous-day pain, and a prior-flow timing proxy. We also tested a logistic model without previous pain and a random forest restricted to wearable features. Holding out complete participants avoids testing the models on new days from the same people used for training.

## 3. Dataset / sensing

### Dataset size and cohort selection

The authorized mcPHASES v1.0.0 download contains 23 CSV tables and approximately 3.68 GB of extracted files. Its 110,135,462 CSV records are mostly repeated sensor samples, not independent participants. The diary contains 5,659 participant-days and 3,327 observed cramp responses across both study intervals.

The primary analysis uses 2022: 42 participants, 3,698 diary days and 3,320 days with observed pain labels. We excluded 378 days with missing outcomes. The target distribution is 2,803 no/low days and 517 moderate-or-higher days, or 15.6% positive. The 2024 interval has only seven observed cramp responses and is excluded from the headline supervised analysis.

### Hardware and included features

The source study used Fitbit Sense smartwatches, Mira hormone measurements, Dexcom G6 glucose monitoring in the first interval, and daily smartphone diaries. Our prediction workflow uses existing Fitbit and diary measurements; no new wearable pilot has been collected. Nine source tables produce 21 prior-day predictors, including previous pain.

- Sleep: minutes asleep/awake, sleep efficiency, overall sleep score, deep-sleep minutes and restlessness.

- Activity: sedentary, light, moderate and vigorous activity minutes.

- Physiology: resting heart rate, HRV RMSSD, breathing rate, absolute nightly temperature and Fitbit stress score.

- Diary history: stress, mood swings, sleep difficulty, flow, time since observed flow and previous pain.

### Bias and measurement limits

The small Toronto-area cohort and its recruitment/eligibility criteria limit generalization. Missing wearable measurements and optional second-round diaries affect coverage. The actual demographic table does not contain income, although the README mentions it. Only one gender category meets our minimum supported group size, so the data do not support a reliable gender comparison. These are study limitations, not new collection milestones for the final delivery.

## 4. Milestones / analysis: work completed

### Acquisition, inspection and cleaning

We downloaded and inventoried the dataset, verified actual schemas and response strings, and constructed one daily analysis record per participant. The original download/exploration milestone was planned for October 9; it was completed on October 24 after access was resolved. Initial cleaning and feature construction, planned for October 23, were completed on October 24. Modeling and initial evaluation were completed ahead of their proposal dates of November 13 and November 24.

- Outcome handling: validate labels and unique diary keys; exclude missing pain outcomes rather than imputing them.

- Duplicate and device-status handling: remove exact repeated sensor records, including 3,601 first-round Fitbit stress-score duplicates; reject failed, NO_DATA and IN_PROGRESS stress scores.

- Quality filtering: use broad prespecified bounds to set 782 resting-HR values, 53 respiratory-rate values and seven HRV values to missing. Require HRV coverage of at least 0.8, excluding 5,950 low/absent-coverage records.

- Daily summaries: restrict sleep to main sleep, index it by end day, and use medians for distinct repeated summaries to avoid summing repeated or revised records. Keep missing measurements missing until fold-level preprocessing.

### Feature engineering and leakage prevention

Features are joined from exact day t−1, not merely the preceding observed row. This prevents missing days or long study gaps from being treated as consecutive observations. The flow-timing proxy uses only observed flow history; it is not a ground-truth cycle phase. Retrospective hormone-derived phase labels and proprietary personal-temperature-baseline deviations are excluded. Actual upload/report latency is not established by these exports, so prospective availability remains an interpretation limit.

Predictor missingness ranges from 1.2% to 44.0%. Missingness filtering at more than 60%, median imputation with missingness indicators, and scaling are fitted only on training folds. Previous pain is unavailable on 236 labeled target days (7.1%); the persistence baseline uses the training-fold majority class for those cases.

### Models, evaluation and interpretation

All three proposed classifiers and three baselines are implemented and evaluated, with two additional feature-ablation comparisons. Five-fold GroupKFold keeps each participant entirely within one test fold, with no participant shared between training and test in a fold. Hyperparameters are fixed and random state is 42. Evaluation includes macro F1, balanced accuracy, ROC-AUC, confusion matrices and out-of-fold predictions.

Completed interpretation and robustness work includes held-out random-forest permutation importance, logistic coefficients, retained-feature records, 2,000 paired participant-cluster bootstrap resamples, a sensitivity analysis restricted to days with known previous pain, and supported demographic subgroup comparisons. Eight targeted tests pass. Code and aggregate documentation have been pushed to GitHub; restricted raw files and participant-level derivatives remain outside the repository.

The optional pilot and pilot comparison were not collected and are outside the final delivery scope. Initial explainability and bias analysis are complete; final wording and visual presentation are still being refined. Independent external validation and a future tuned model would be extensions beyond the current fixed-model analysis, not remaining core milestones.

## 5. Initial results and interpretation

The table reports pooled out-of-fold scores from the same 3,320 target days and participant-grouped evaluation. Macro F1 treats both classes equally; balanced accuracy accounts for unequal class prevalence. ROC-AUC measures ranking, and the persistence baseline has only hard 0/1 predictions rather than a full probability ranking.

| Model / baseline | Macro F1 | Balanced accuracy | ROC-AUC |
| --- | --- | --- | --- |
| Majority class | 0.458 | 0.500 | 0.500 |
| Prior flow timing | 0.509 | 0.605 | 0.634 |
| Previous-day pain | 0.781 | 0.773 | 0.773 |
| Logistic regression | 0.716 | 0.767 | 0.829 |
| Decision tree | 0.713 | 0.750 | 0.775 |
| Random forest | 0.770 | 0.773 | 0.827 |
| Logistic without previous pain | 0.581 | 0.658 | 0.702 |
| Wearables-only forest | 0.569 | 0.567 | 0.572 |

All three full-feature classifiers improve on majority class, but none beats previous-day pain on macro F1. Random forest is the strongest of the three full classifiers at 0.770, compared with 0.781 for persistence. Their balanced accuracies both round to 0.773. The forest and logistic AUCs are about 0.83, but this alone does not establish better decisions or calibrated risk estimates.

The wearable-only forest scores 0.569 macro F1, and logistic regression without previous pain scores 0.581. Previous pain dominates forest permutation importance, with a mean held-out balanced-accuracy decrease of 0.241 when permuted. These comparisons show that pain history carries much of the predictive information in the current models; they do not establish that lifestyle or physiology causes pain.

### Errors, uncertainty and subgroup findings

Random forest correctly identifies 320 of 517 moderate-or-higher days (61.9% sensitivity), misses 197, and produces 207 false positives. Persistence identifies 313 positive days, misses 204, and produces 168 false positives. Thus, forest finds seven additional positive days but adds 39 false alarms at the current decision rule.

Participant-cluster bootstrap intervals for macro F1 are approximately 0.699–0.821 for forest and 0.716–0.826 for persistence. The paired forest-minus-persistence difference is −0.010, with an approximate 95% interval of −0.022 to −0.002. These intervals condition on fixed out-of-fold predictions; they do not refit the models or capture every source of development uncertainty.

On the 3,084 days with observed prior-day pain, the same predictions yield F1 of 0.778 for forest and 0.789 for persistence, preserving the main conclusion. The demographic audit requires at least five participants and at least ten target days in each class per group. Forest false-negative rates among supported ethnicity groups range roughly from 26% to 59%; small and unequal groups prevent a population-wide fairness conclusion.

## 6. Next steps / discussion: final completion only

The October data audit, processing, model evaluation and reported-count checks are complete. All remaining finalization tasks are due November 30, 2026: polish figures and explanations, complete the final report, perform the final consistency check, rehearse and submit. The final deliverable will report the lack of improvement over pain history honestly; a new model, new sensor cohort or external validation dataset is not required to complete this defined scope.

| When / status | Completion task | Proposed owner |
| --- | --- | --- |
| October — done | Data audit, models, evaluation and count checks | Team |
| Nov 30 | Finalize figures, tables and feature explanations | Alina + Vicky |
| Nov 30 | Complete final report and discussion | Alina + Fiona |
| Nov 30 | Final consistency check and presentation rehearsal | All |
| Nov 30 | Submit report, code and presentation | All |

Final discussion will state the main limits: a small selected cohort, class imbalance, missing measurements, uncertain prospective data availability, exploratory subgroup differences and no independent final test cohort. The cohort has already been inspected and cannot later be described as an untouched final holdout. These limits will be clearly documented rather than recast as unfinished core work.

### Project materials and evidence

Repository: https://github.com/alinak78/ml_prediction_pain

Detailed checkpoint report: https://github.com/alinak78/ml_prediction_pain/blob/main/reports/midpoint_checkpoint.md

Dataset and documentation: https://physionet.org/content/mcphases/1.0.0/

Original project proposal and saved run outputs support the plan-to-completion comparison. This summary reflects the completed October 24 analysis and the revised presentation/final-delivery scope on October 28. Proposed owners describe future finalization tasks, not verified attribution for past individual contributions.
