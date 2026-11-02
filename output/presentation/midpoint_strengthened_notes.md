# Strengthened midpoint — six-minute speaker notes

## Slide 1

Target time: 15 seconds.
Introduce Alina Kapanova, Fiona Wang and Vicky Wang. We studied whether health and lifestyle factors can anticipate next-day pain. Today we report a complete initial analysis and the main finding: pain history remains a strong baseline. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 2

Target time: 35 seconds.
Menstrual pain varies across people and cycles. Our proposal asks whether sleep, stress, activity, physiology and menstrual history provide useful information. We made the task concrete: predict day-t pain using exact day t−1 data. The binary grouping follows observed labels and is a project convention, not a clinical cutoff. We combine Fitbit signals and diaries, then compare three classifiers with simple baselines for unseen participants. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 3

Target time: 35 seconds.
The existing mcPHASES download has 23 tables and 3.68 GB of files. We use 42 participants and 3,320 labeled days from 2022. Missing outcomes are excluded. Positive labels represent 15.6% of days. The later interval has only seven pain reports and is excluded from the headline results. We use nine Fitbit and diary tables for 21 predictors; source hardware is Fitbit Sense. No new pilot is part of this analysis. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 4

Target time: 40 seconds.
We inspected the codebook and real schemas, mapped the ordered pain responses and prepared daily features. We excluded 378 missing outcomes, removed 3,601 duplicate stress records and rejected failed or in-progress scores. Broad prespecified bounds flag impossible measurements as missing, and HRV requires adequate coverage. Sleep is assigned to its end day. Exact lagging avoids bridging missing days or study rounds. We exclude retrospective hormone phase labels; imputation is learned inside training folds. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 5

Target time: 40 seconds.
Download and initial preparation were completed October 24 after the access delay. The three proposed classifiers are implemented, together with three baselines and two feature-ablation checks. We have five participant-held-out folds, confusion matrices, participant-cluster uncertainty, initial explainability and supported subgroup checks. Twelve targeted tests pass and code is on GitHub. Initial interpretation is complete; remaining work is final checking and communication. The optional pilot was not collected and is outside the final deliverable scope. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 6

Target time: 50 seconds.
This is the same random forest, preprocessing, participants and five folds, with feature sets changed. Adding wearables to previous pain increases average precision from 0.460 to 0.512, with a paired conditional bootstrap interval about +0.007 to +0.081. Macro F1 falls from 0.781 to 0.760 at the default rule, so ranking improves without better overall classifications. All features reach AP 0.555, but that also includes diary predictors. Missingness indicators are part of the feature package. These are exploratory follow-ups after inspecting the initial cohort. Source: reports/wearable_followup.md.

## Slide 7

Target time: 40 seconds.
We evaluated existing OOF predictions only on days preceded by observed no/low pain. There are 177 onsets among 2,603 eligible days. Persistence and the history-only forest detect none. Adding wearables catches 10 but generates 44 false alarms: precision 18.5 percent and recall 5.6 percent. Wearables alone find 38 at the cost of 302 false alarms. Thus there is some additional signal, but onset detection is weak and there is a trade-off. No onset-specific model or threshold was tuned. This is secondary exploratory analysis. Source: reports/wearable_followup.md.

## Slide 8

Target time: 35 seconds.
Forest finds 320 of 517 moderate-or-higher days but misses 197. Compared with persistence it finds seven extra positive days at the cost of 39 more false alarms. In supported ethnicity groups, missed-pain rates vary approximately 26% to 59%, but the groups are small and comparisons are exploratory. Only one gender category meets our minimum group threshold. There is no independent final test cohort or clinical validation. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.

## Slide 9

Target time: 30 seconds.
The complete analysis now isolates wearable contribution with matched forests and tests new onset. Wearables provide a modest ranking benefit beyond history, but current overall macro F1 is lower and onset recall remains limited. All follow-ups reuse the previously inspected cohort and are exploratory. The completed comparisons strengthen the answer without claiming practical or clinical readiness. Remaining work stays final checks, figure explanations, report preparation and submission, due November 30. Source: reports/wearable_followup.md.

## Slide 10

Target time: 40 seconds.
These are proposed owners for final delivery, not new major research milestones. The October data audit, processing, model evaluation and count checks are complete. All remaining tasks are due November 30, 2026: finalize figures and explanations, finish the report, check consistency, rehearse and submit. The analysis pipeline and initial results already exist. No new sensing cohort or model rebuild is needed to complete this scope. Thank the audience and leave two minutes for questions. Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.
