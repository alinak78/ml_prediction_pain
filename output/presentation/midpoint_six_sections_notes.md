# Midcheckpoint speaker notes — October 28, 2026

Six slides, six minutes, followed by two minutes of questions. Model results are from the October 24 real-data run.

## 1. Predicting menstrual pain

Target time: 20 seconds.
We are Alina Kapanova, Fiona Wang and Vicky Wang. Our project asks whether health and lifestyle information can anticipate menstrual pain. This checkpoint covers our dataset, completed analysis, initial results and remaining work. We now have real participant-held-out results. Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## 2. Background

Target time: 50 seconds.
Menstrual pain varies across people and cycles and can interfere with daily activities. Our original proposal asks whether sleep, stress, physical activity, physiology and menstrual history can predict severity. We made this concrete as a retrospective one-day-ahead task: predict day t from information recorded on exact day t−1. We map Not at all, Very Low/Little and Low to class zero, and Moderate, High and Very High to class one. This is a project threshold, not a clinical cutoff. We compare logistic regression, decision tree and random forest against simple baselines and hold out complete people to assess generalization. Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## 3. Dataset / sensing

Target time: 65 seconds.
We use the existing mcPHASES v1.0.0 dataset, so our core project requires no new sensor collection. The download contains 23 CSV tables and 3.68 GB of files. The source study used Fitbit Sense, Mira hormone measurements and Dexcom G6 in the first interval. Our selected features come from Fitbit and daily diaries: sleep duration and quality, activity minutes, resting heart rate, HRV, breathing rate, nightly temperature, device stress and diary history. We processed nine tables into 21 prior-day predictors. The primary cohort includes 42 people and 3,320 labeled 2022 days. We excluded 378 first-round days without pain labels and never imputed outcomes. Only seven 2024 days have pain reports, so that interval cannot support a useful external test. The small Toronto cohort, missing sensor data and 15.6% positive prevalence limit generalization. Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## 4. Milestones / analysis

Target time: 85 seconds.
This table ties our completed work to the proposal. Download and exploration were planned for October 9 but completed on October 24 after the access delay. Initial cleaning and feature construction, planned for October 23, were also completed on October 24; further sensitivity work remains. We verified labels and day keys, removed 3,601 duplicate stress records, filtered failed device scores and set measurements outside broad prespecified bounds to missing. Sleep is assigned to its end day, and all features are lagged by exactly one day. We never bridge missing days or the gap between study rounds, and we exclude retrospective phase labels. Median imputation and missingness filtering are learned inside each training fold. We have already implemented the three proposed models and evaluated them in five participant-held-out folds, ahead of the November model/evaluation milestones. Initial permutation importance, participant-cluster intervals and supported subgroup checks are complete, but final validation and interpretation are not. The optional pilot has not been collected or compared; we have deferred it. Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## 5. Initial results

Target time: 70 seconds.
These are pooled out-of-fold results from five participant-grouped folds. The previous-day pain baseline has the highest macro F1 at 0.781. Random forest is the strongest of the three full classifiers at 0.770, and logistic regression is 0.716. The forest and persistence have nearly equal balanced accuracy, about 0.773. Forest detects 320 of 517 moderate-or-higher days, but gives more false positives than persistence: 207 compared with 168. All three classifiers beat the majority baseline, but none beats pain history on macro F1. Wearable-only forest reaches 0.569, and previous pain dominates permutation importance. Two thousand paired participant-cluster bootstrap resamples give a forest-minus-persistence F1 interval of about −0.022 to −0.002, conditional on fixed predictions. The higher AUC of the full models is not proof of better decisions; persistence uses hard predictions. These results do not establish clinical validity or causality. Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## 6. Next steps / discussion

Target time: 70 seconds.
Our main challenge is demonstrating useful improvement beyond pain history. We also need to check missingness mechanisms, actual report availability and error differences across people. Supported ethnicity groups show different missed-pain rates, but the samples are too small for a fairness conclusion. Only one gender category meets our minimum participant count, and income is absent. Next we will inspect failures and imputation sensitivity by October 30, then review feature timing and use nested participant-grouped validation for any tuning by November 13. We will refine robustness and subgroup comparisons by November 24, freeze explainability and a reproducible rerun by December 2, and finish the report and presentation by December 4. These are proposed work allocations. The optional pilot remains outside the critical path. Because we have already inspected this cohort, it cannot later be called an untouched independent final test. We will report any limited or null benefit honestly. Thank you; we have two minutes for questions. Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Two-minute Q&A prompts

- Why split by person? Daily records from the same person in train and test would overstate generalization.
- Why exclude 2024? It has only seven observed pain outcomes.
- Do wearables improve the prediction? The current models do not beat previous-day pain on macro F1.
- What has changed from the proposal? The target is binary, 2022 is the primary cohort, retrospective phase labels are excluded, and the optional pilot is deferred.
- Is this clinically validated? No. This is retrospective exploratory evaluation, with no independent final test cohort.
