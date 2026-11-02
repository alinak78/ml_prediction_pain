# Midpoint checkpoint presentation speaker notes

The main talk uses slides 1–10. Slide 11 is a references backup. Allocated main-slide times total six minutes; actual delivery requires rehearsal.

## Slide 1

(~15s) Hi, we are Alina, Fiona and Vicky. Our project asks whether health and lifestyle signals can forecast next-day menstrual cramps. Headline: prior-day bodily symptoms improve how well we rank next-day cramp risk, beyond pain history alone, though classification gains are mixed.

## Slide 2

(~25s) Menstrual pain is common and disruptive: a review of 21,573 young women found 71.1% prevalence, 20.1% missing school and 40.9% reporting impaired concentration. Those are review figures, not our dataset. Our question: do prior-day symptoms, sleep, stress or mood, activity, bleeding history and wearable physiology add information beyond yesterday's cramp severity? We predict whether the next observed day has moderate-or-higher cramps.

## Slide 3

(~20s) The literature motivates which domains to test, but does not guarantee gains. Pain sensitivity and somatic symptoms show associations; EMPATHY gives important null evidence; diary studies support careful daily measurement. Wearables detect cycle phase, which is not the same as predicting pain.

## Slide 4

(~30s) We use mcPHASES from PhysioNet: 42 young adults in the 2022 interval, 3,320 days with an observed cramp label, 15.6% of them moderate or higher. The 2024 interval had only 7 labels, so we excluded it. Biases: small, selected Toronto-area cohort with contraceptive restrictions and missing diary and device data, so results do not generalize broadly.

## Slide 5

(~45s) Talk track: 29 candidate predictors across eight domains; 28 survive filtering in every fold, and the bleeding-onset clock in one. Focus on the five bodily symptoms, coded 0 to 5 from the previous day.

• Headache: head discomfort; tests whether nonpelvic pain adds broader symptom-burden information [4,6].
• Fatigue: tiredness or low energy; experience that sleep duration or movement alone may miss [6,7,9].
• Bloating: abdominal fullness or swelling; a broader symptom pattern beyond cramp intensity [6,7].
• Indigestion: digestive discomfort; gastrointestinal context beyond cramps, sleep and physiology [6,7].
• Breast soreness: co-occurring symptom characterizing the recent symptom pattern [6,7].

Evaluated together as a block; no single symptom is shown to contribute independently. None are diagnoses, hormone measures or phase labels.

## Slide 6

(~30s) Core analysis is complete. Acquisition and cleaning finished Oct 24, after the original targets because of access delays; modeling, evaluation and interpretation finished in October, earlier than the November and December targets. On Nov 1 we added the literature-based symptom extension and two supplementary datasets. The optional pilot was excluded from final scope, as the proposal allowed.

## Slide 7

(~25s) Cleaning validates labels, removes duplicates and rejects failed device readings. All time-varying predictors come from day t−1; age and menarche age are historical. We compare logistic regression, a decision tree and a random forest with five-fold participant-grouped cross-validation, so nobody appears in both training and test. Metrics include average precision and balanced accuracy, with 2,000 paired participant-bootstrap resamples.

## Slide 8

(~40s) First, the original three classifiers. All beat the majority baseline, but the simple previous-day pain rule has the best macro F1, 0.781 versus 0.770 for the forest. Higher AUC does not mean better classification at our decision rule. Pain history is a strong reference.

## Slide 9

(~70s) Main finding. Using ordinal pain severity as the reference, adding the five symptoms raises average precision from 0.526 to 0.623, paired 95% interval +0.012 to +0.146. Balanced accuracy dips slightly because at the fixed rule we get 52 fewer false positives but miss 18 more positive days. Bleeding history also helps; physiology is uncertain. Without cramp history the forest still reaches AP 0.495, and the logistic model shows little gain, so improvement is not consistent across model families.

Backup: supplementary datasets

• MPIS [11]: 105 observed consecutive-day pairs from 14 people (14 pain outcomes, ≥4/10), no wearables. Logistic AP: pain history 0.461; + clinical reproductive attributes 0.537; full literature model 0.490. Balanced-accuracy gain interval [-0.014, +0.131].
• PhysioPain [12]: current-pain experiment, 17 participants (Empatica E4 + lifestyle surveys). Balanced accuracy: lifestyle 0.646, wearable 0.465, combined 0.472.
• Neither validates a frozen mcPHASES model externally.

## Slide 10

(~60s) We handled access delays, sparse labels, missing data and class imbalance. Limits: exploratory, no independent test set, no multiple-comparison correction, no causal or clinical claims. Conclusion: symptoms give the clearest added ranking information, bleeding history also helps, classification gains are inconsistent. Remaining work, all by November 30: verify figures, finalize report and references, rehearse, submit. Thank you, happy to take questions.

## Slide 11

Backup slide: full reference list for the numbered citations in the deck. Show only if asked about sources.
