# Six-minute presentation — expanded structure

## Slide 1: Predicting menstrual pain

Target time: 15 seconds.
Introduce Alina Kapanova, Fiona Wang and Vicky Wang. We studied whether health and lifestyle factors can anticipate next-day pain. Today we report a complete initial analysis and the main finding: pain history remains a strong baseline. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 2: Predicting next-day menstrual pain

Target time: 35 seconds.
Menstrual pain varies across people and cycles. Our proposal asks whether sleep, stress, activity, physiology and menstrual history provide useful information. We made the task concrete: predict day-t pain using exact day t−1 data. The binary grouping follows observed labels and is a project convention, not a clinical cutoff. We combine Fitbit signals and diaries, then compare three classifiers with simple baselines for unseen participants. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 3: Dataset and cohort

Target time: 35 seconds.
The existing mcPHASES download has 23 tables and 3.68 GB of files. We use 42 participants and 3,320 labeled days from 2022. Missing outcomes are excluded. Positive labels represent 15.6% of days. The later interval has only seven pain reports and is excluded from the headline results. We use nine Fitbit and diary tables for 21 predictors; source hardware is Fitbit Sense. No new pilot is part of this analysis. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 4: Completed cleaning and features

Target time: 40 seconds.
We inspected the codebook and real schemas, mapped the ordered pain responses and prepared daily features. We excluded 378 missing outcomes, removed 3,601 duplicate stress records and rejected failed or in-progress scores. Broad prespecified bounds flag impossible measurements as missing, and HRV requires adequate coverage. Sleep is assigned to its end day. Exact lagging avoids bridging missing days or study rounds. We exclude retrospective hormone phase labels; imputation is learned inside training folds. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 5: Completed analysis milestones

Target time: 40 seconds.
Download and initial preparation were completed October 24 after the access delay. The three proposed classifiers are implemented, together with three baselines and two feature-ablation checks. We have five participant-held-out folds, confusion matrices, participant-cluster uncertainty, initial explainability and supported subgroup checks. Eight targeted tests pass and code is on GitHub. Initial interpretation is complete; remaining work is final checking and communication. The optional pilot was not collected and is outside the final deliverable scope. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 6: Pain history remains the strongest baseline

Target time: 50 seconds.
This chart shows macro F1 on the same out-of-fold target days. Persistence is 0.781; forest is 0.770, logistic is 0.716 and tree is 0.713. All beat majority class, but none beats previous-day pain. Forest and persistence balanced accuracies both round to 0.773. Forest and logistic AUCs are around 0.83, but a higher AUC does not establish better decisions than a hard-prediction baseline. Two thousand participant-cluster resamples support a small F1 disadvantage for forest, conditional on fixed predictions. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 7: Previous pain dominates feature importance

Target time: 40 seconds.
Held-out permutation importance asks how much balanced accuracy decreases when a feature is shuffled. Previous pain causes a mean decrease of 0.241, much larger than the other predictors. Wearable-only forest has F1 of 0.569; a logistic model without previous pain has F1 of 0.581. These comparisons suggest that symptom history explains much of the current performance. Importance is a predictive association, not evidence of a cause; correlated features and missingness affect interpretation. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 8: Errors and subgroup limitations

Target time: 35 seconds.
Forest finds 320 of 517 moderate-or-higher days but misses 197. Compared with persistence it finds seven extra positive days at the cost of 39 more false alarms. In supported ethnicity groups, missed-pain rates vary approximately 26% to 59%, but the groups are small and comparisons are exploratory. Only one gender category meets our minimum group threshold. There is no independent final test cohort or clinical validation. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 9: Core analysis complete; final refinements remain

Target time: 30 seconds.
Our completed work answers the initial feasibility question under a defined retrospective task. The extra features do not beat pain history on macro F1. We will preserve that finding and its caveats. Only final reviews, figure improvements, clear explanations and submission preparation remain. A new model, a new pilot and independent external validation are not requirements for this final scope; the absence of external validation is documented as a limit. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 10: October complete; final tasks due November 30

Target time: 40 seconds.
These are proposed owners for final delivery, not new major research milestones. The October data audit, processing, model evaluation and count checks are complete. All remaining tasks are due November 30, 2026: finalize figures and explanations, finish the report, check consistency, rehearse and submit. The analysis pipeline and initial results already exist. No new sensing cohort or model rebuild is needed to complete this scope. Thank the audience and leave two minutes for questions. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

Allow two minutes for questions.
