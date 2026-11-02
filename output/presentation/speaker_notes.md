# Six-minute midpoint presentation — October 24, 2026

## Slide 1

Target time: 20 seconds.
Introduce Alina Kapanova, Fiona Wang and Vicky Wang. We have processed mcPHASES and run the first real models. The main finding is that previous pain is a strong baseline and the extra features have not yet improved macro F1. Source: reports/midpoint_checkpoint.md.

## Slide 2

Target time: 45 seconds.
Pain varies across people and cycles. We predict day t from exact day t−1 information. Not at all, Very Low/Little and Low are class zero; Moderate, High and Very High are class one. This mapping is a project convention, not a clinical threshold. The task is retrospective and assumes prior-day data were available; deployment latency is not established. This is feasibility research, not a diagnostic system.
Source: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/

## Slide 3

Target time: 60 seconds.
The full source study also used Mira hormone measurements and Dexcom G6 in interval one. We use nine source tables for 21 prior-day predictors: activity, sleep, physiology and diary history. There are 110.1 million records across all tables, mostly repeated sensor samples, not independent participants. Of 3,698 first-round diary days, 378 lack pain labels and are excluded. Only seven second-round days have cramp responses, so we exclude 2024 from the primary analysis. No new sensor pilot has been collected. Recent hormonal contraception and diabetes were exclusion criteria.
Source: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/

## Slide 4

Target time: 60 seconds.
Main milestones are now complete through initial evaluation. We read the actual files and codebook. Main sleep uses its end day; distinct repeated daily summaries use median values. We removed 3,601 exact duplicate first-round Fitbit stress records and invalid zero/failed scores. Broad prespecified bounds set 782 resting heart-rate values, 53 respiratory measurements and 7 HRV records to missing. HRV requires coverage at least 0.8. Feature missingness is 1.2 to 44.0 percent. Exact day joins avoid crossing gaps. We never impute pain, and imputation/filtering use training folds only. Eight tests pass. Hyperparameters were fixed; no independent final test set exists.
Source: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/

## Slide 5

Target time: 80 seconds.
These are pooled out-of-fold scores from five participant-grouped folds. Persistence macro F1 is 0.781; forest is 0.770, so the added features have not beaten the simple baseline. Forest and persistence balanced accuracies both round to 0.773. Logistic and forest AUCs are about 0.83, but persistence uses hard predictions rather than a full probability ranking. A forest restricted to wearables reaches only 0.569 F1; a logistic model without previous pain reaches 0.581. Previous pain dominates held-out permutation importance. Two thousand participant-cluster bootstrap resamples give F1 intervals 0.716–0.826 for persistence and 0.699–0.821 for forest; the paired difference is about −0.010 with interval −0.022 to −0.002. These intervals condition on fixed OOF predictions. Forest catches 320 of 517 moderate-or-higher days and misses 197. Do not claim wearable value, clinical validity or causality.
Source: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/

## Slide 6

Target time: 55 seconds.
These are proposed team allocations and dates in 2026. Data processing and initial grouped evaluation are complete on October 24. Next inspect missingness and errors, review prospective feature timing, and use nested grouped validation for any tuning. The optional pilot remains outside the core path until a feasible protocol and devices exist. All team members review the final output.
Source: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/

## Slide 7

Target time: 40 seconds.
Among supported ethnicity groups, forest false-negative rates range roughly 26 to 59 percent. Minimum group size is five participants and ten days of each class; these estimates are exploratory. Only Woman has at least five participants, so gender comparisons are unsupported. Income is absent in the downloaded demographic table despite the README mentioning it. The 2024 interval has only seven labels and cannot serve as a useful external test here. The full cohort has now been inspected; further work cannot call it an untouched final holdout. A limited or null wearable benefit is a valid finding. Stop at six minutes and allow two minutes for questions.
Source: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/
