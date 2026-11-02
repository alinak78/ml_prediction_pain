# Menstrual pain prediction midpoint report

Project progress and presentation narrative

## Title slide

Predicting menstrual pain using health and lifestyle factors

Team: Alina Kapanova, Fiona Wang and Vicky Wang

Analysis checkpoint: November 1, 2026 | Presentation: 6 minutes plus 2 minutes for questions

We have completed the core data processing, model comparison and evaluation. The main finding is that prior-day bodily symptoms improve the ranking of next-day cramp risk beyond prior-day pain severity in mcPHASES, while classification gains are mixed. Pain history remains a strong reference. Our evidence supports a multifactor forecasting analysis with explicit limits on generalization and clinical use.

## 1 Background

### Problem and research question

Menstrual pain can disrupt study, work and daily activities. A systematic review of 38 studies involving 21,573 young women estimated dysmenorrhea prevalence at 71.1%; separate pooled estimates found 20.1% reporting school or university absence and 40.9% reporting impaired classroom performance or concentration. These estimates describe the review populations, rather than the prevalence in our dataset [1].

Our research question is: do prior-day bodily symptoms, sleep, stress or mood, physical activity, bleeding history and wearable physiology add predictive information beyond previous-day cramp severity? We predict whether the following observed study day has moderate-or-higher cramps, using features recorded on the preceding day.

### Approach and research foundation

We combine existing Fitbit Sense measurements with daily symptom diaries, build one participant-day record and evaluate logistic regression, a decision tree and random forests on held-out participants. Wearable menstrual-cycle research motivates testing physiological features, but detecting fertility or cycle phase does not establish pain-prediction performance [2,3].

The four supplied sources refine our hypotheses. Slater et al. studied 432 Raine participants and linked menstrual pain with experimental pain sensitivity after adjustment; the IASP article explains that study [4,5]. Hagy analyzed 157 adults over two years: somatic symptoms distinguished some pain trajectories, while the detailed predictor table also contained one depression contrast; sleep and catastrophizing contrasts were not significant [6].

Tu et al. followed the EMPATHY adolescent cohort, with 149 first-period and 114 fourth-month diaries. Baseline psychological, parental and laboratory sensitivity measures did not distinguish subsequent pain groups [7]. Jukic et al. compared recalled discomfort with daily diaries; the main frequency analysis included 324 participants and agreement was modest. This supports careful diary-based measurement and bleeding timing [8]. Together, these studies motivate testing domains without assuming every factor must improve prediction.

## 2 Data set and sensing

### Primary dataset and analysis cohort

We use mcPHASES version 1.0.0, a University of Toronto dataset hosted on PhysioNet. The released study contains 42 Canadian young adults, with 20 returning for a second collection interval. It provides 23 linked tables spanning physiology, hormones and daily experiences [2,13]. Our analysis counts come from the downloaded files, rather than from the advertised sensor-sample total.

| Item | Verified size or decision |
| --- | --- |
| Released files | 23 CSV tables; approximately 3.68 GB extracted |
| Primary interval | 2022; 42 participants |
| Daily diary records | 3,698 participant-days |
| Usable observed cramp targets | 3,320 days; missing outcomes excluded |
| Outcome distribution | 517 moderate-or-higher days (15.6%); 2,803 lower-pain days |
| Later interval | 2024 has only 7 observed cramp labels; excluded from primary modeling |
| Bodily symptom coverage | Prior-day symptom fields available on 3,084 of 3,320 target days (92.9%) |

The binary target is 1 for Moderate, High or Very High cramps and 0 for Not at all, Very Low/Little or Low cramps. This is a project grouping of recorded responses, rather than a validated clinical cutoff.

### Sensing hardware and measurements

The original study used Fitbit Sense smartwatches and a custom smartphone diary. Fitbit outputs include heart rate, sleep, activity, temperature, respiration, HRV and device stress metrics. The broader release also includes Mira hormone measurements and, in the first interval, Dexcom G6 glucose monitoring; those measurements are outside our selected forecasting predictors [2]. We have collected no new participant or pilot sensor data.

| Feature domain | Count | Candidate inputs in the expanded model |
| --- | --- | --- |
| Pain history | 1 | Previous-day ordinal cramp severity |
| Bodily symptoms | 5 | Headache, fatigue, bloating, indigestion, breast soreness |
| Stress and mood | 2 | Self-reported stress and mood swings |
| Sleep | 7 | Difficulty, duration, awake minutes, efficiency, score, deep sleep, restlessness |
| Activity | 4 | Sedentary, light, moderate and vigorous activity minutes |
| Bleeding history | 3 | Flow intensity and two observed-flow timing clocks |
| Background | 2 | Approximate age and age at menarche |
| Wearable physiology | 5 | Resting heart rate, HRV RMSSD, respiratory rate, nightly skin temperature, Fitbit stress score |

The full specification has 29 candidate predictors. Training-fold missingness filtering retains 28 in every fold; the newly defined bleeding-onset clock is sufficiently observed in only one of five folds. Thus, 29 is the offered feature count, rather than complete coverage in every fitted model.

### Representativeness and measurement limits

Recruitment was through Greater Toronto Area advocacy groups, with eligibility restrictions including no recent hormonal contraceptive use [2]. The cohort is small and selected. Device nonwear, diary adherence and unequal numbers of reports can influence results. Income is absent from the actual demographic table, and only one gender category has sufficient representation for the existing subgroup audit. These data do not establish population-wide fairness or performance across ages, devices or clinical diagnoses.

### The five bodily symptoms and why we use them

All five symptoms are present in the original hormones_and_selfreport.csv diary table. We encode the ordered responses from 0 to 5: Not at all, Very Low/Little, Low, Moderate, High and Very High. Each predictor uses the exact previous study day. These are self-reported symptom intensities, separate from the wearable signals and from the cramp outcome.

### Headache

The headaches field records reported head discomfort. We include it to test whether a nonpelvic pain symptom adds information about broader bodily symptom burden beyond cramps alone. Raine considered multisite pain, and the adult trajectory thesis examined somatic symptoms [4,6]. These findings motivate the domain; they do not establish that an individual headache report independently predicts next-day cramps or diagnoses migraine.

### Fatigue

The fatigue field records tiredness or low energy as reported in the diary. It adds the participant’s experience alongside measured sleep and activity. We test whether that experience carries information that duration or movement alone misses. This is a hypothesis informed by research on bodily symptoms and sleep [6,7,9]; fatigue may also reflect prior pain or other circumstances, so we do not assign it a causal direction.

### Bloating

The bloating field captures reported abdominal fullness or swelling. It gives the model another aspect of symptom experience besides the intensity of cramps. Including it tests whether a broader symptom pattern helps forecasting, consistent with the somatic-symptom domain in the thesis and EMPATHY [6,7]. We do not treat bloating as a hormone measurement, a confirmed cycle-phase label or a diagnosis.

### Indigestion

The indigestion field records digestive discomfort under that diary label. It tests whether gastrointestinal symptom context adds information to prior cramps, sleep and wearable physiology. The wider somatic-symptom literature motivates investigating this domain [6,7]. The recorded field does not identify a gastrointestinal disease, and the cited studies do not prove that this individual mcPHASES item improves prediction.

### Breast soreness

The sorebreasts field records breast soreness or tenderness. We include it as another co-occurring symptom that might help characterize the participant’s recent symptom pattern. That is an exploratory extension of the broader symptom-burden rationale [6,7]. It is not a substitute for measured hormone concentrations, and its presence does not establish a particular menstrual phase.

### What the evidence allows us to conclude

We evaluate the five symptoms together as a feature block. The observed improvement supports the block under this evaluation; we have not established which individual symptom contributes independently. Our diary items are not equivalent to the BSI-18 somatization scale used in the thesis or the CSSI-24 used in EMPATHY [6,7]. The thesis supports further investigation, while EMPATHY provides important null evidence. Stress and mood swings likewise cannot be renamed as validated anxiety or depression scores.

Sleep, stress, bleeding and activity remain separate domains. Mitsuhashi et al. report associations involving stress, sleep and menstrual characteristics; exercise-intervention evidence also motivates attention to activity, but treatment effects and next-day predictive utility are different questions [9,10].

## 3 Milestones and analysis

### Proposal milestones completed

The proposal named acquisition, cleaning, feature engineering, three classifiers, participant-level evaluation, explainability and bias analysis. Its wearable pilot was optional [14]. The core analysis was completed in October; the literature-based symptom extension and supplementary dataset experiments were completed on November 1.

| Proposal milestone | Original target | Completed work or final scope |
| --- | --- | --- |
| Download and explore mcPHASES | Oct 9 | Completed Oct 24 after account access was resolved; files and schemas inventoried |
| Cleaning and feature engineering | Oct 23 | Core pipeline completed Oct 24; exact-day predictors and quality audit saved |
| Implement ML models | Nov 13 | Core logistic regression, decision tree and forest completed Oct 24 |
| Cross-validation and evaluation | Nov 24 | Core participant-grouped results, baselines and uncertainty completed in October |
| Explainability and bias analysis | Dec 2 | Initial coefficients, permutation importance and supported subgroup audit completed in October |
| Results and visualizations | Dec 4 | Core results completed in October; wearable follow-up Oct 29; literature extension Nov 1 |
| Optional pilot and comparison | Oct to Nov | No pilot collected; excluded from final delivery scope, consistent with the proposal contingency |

### Cleaning and feature construction

We validate diary labels and participant-day keys, exclude missing cramp outcomes and remove exact duplicated sensor records. Device-status checks reject failed, NO_DATA and IN_PROGRESS stress scores. Broad quality bounds mark implausible physiology as missing, and HRV requires at least 0.8 coverage. Main-sleep summaries are indexed by sleep end day; distinct repeated summaries use daily medians.

All changing predictors are joined from exact day t-1. Missing days are not bridged by taking the previous available row. Bleeding clocks use only observed history; the new onset clock requires an adjacent-day transition to light-or-heavier flow and resets after gaps or missing flow. Retrospective phase labels, proprietary temperature-baseline deviations and missing pain outcomes are not used to fill future information.

### Models and evaluation implemented

Logistic regression provides an additive model; the decision tree captures simple nonlinear splits; the random forest captures interactions. The main forest uses 200 trees, maximum depth 6, minimum leaf size 5, balanced subsampling and seed 42. Logistic regression uses balanced classes; the original tree has depth 4 and minimum leaf size 10. We selected the proposal’s binary task because the more severe categories are sparse.

Five-fold GroupKFold keeps each participant entirely within one test fold. Feature filtering above 60% missingness, median imputation with indicators and scaling are fitted within training folds. Baselines include majority class, prior pain and prior-flow timing. The extension compares each feature block, the full model, seven models omitting one block and models without cramp history. Settings and decision thresholds remain fixed.

Evaluation includes average precision, macro F1, balanced accuracy, ROC-AUC and confusion counts. We use 2,000 paired participant-bootstrap resamples of fixed held-out predictions. Interpretation uses logistic coefficients and held-out permutation importance; SHAP was proposed but is not part of the completed interpretation. The existing demographic audit concerns the original models and supports only sufficiently represented groups. All 30 software tests pass; saved original model predictions reproduce to a tolerance of 1e-12.

## 4 Initial results

### Original proposed classifier comparison

The original 21-feature analysis evaluates the three proposed classifiers against simple references on the same 3,320 labeled days. These are pooled out-of-fold results, with participants held out. Scores run from 0 to 1, with larger values better.

| Model or reference | Macro F1 | Balanced accuracy | ROC AUC |
| --- | --- | --- | --- |
| Majority class | 0.458 | 0.500 | 0.500 |
| Prior flow timing | 0.509 | 0.605 | 0.634 |
| Previous-day pain rule | 0.781 | 0.773 | 0.773 |
| Logistic regression | 0.716 | 0.767 | 0.829 |
| Decision tree | 0.713 | 0.750 | 0.775 |
| Random forest | 0.770 | 0.773 | 0.827 |

All three classifiers exceed the majority reference, but the prior-pain rule has the highest macro F1 in this comparison. The original forest reaches 0.770 macro F1 versus 0.781 for prior pain. Its higher AUC does not establish better classification at the chosen decision rule; the rule itself supplies only a hard binary ranking score.

### Expanded multifactor comparison

The new comparisons retain the same cohort and folds and use ordinal prior-day cramp severity as the main incremental reference. This preserves more history information than a binary pain flag and makes the added-feature comparison more informative.

| Forest inputs | Average precision | Balanced accuracy | Macro F1 |
| --- | --- | --- | --- |
| Binary pain history reference | 0.460 | 0.773 | 0.781 |
| Ordinal pain severity | 0.526 | 0.804 | 0.754 |
| Pain severity plus bodily symptoms | 0.623 | 0.795 | 0.761 |
| Pain severity plus bleeding history | 0.576 | 0.796 | 0.740 |
| Pain severity plus wearable physiology | 0.550 | 0.799 | 0.764 |
| Full model with 29 candidate features | 0.602 | 0.781 | 0.766 |
| Full model excluding cramp history | 0.495 | 0.718 | 0.714 |

Average precision summarizes how well the scores rank positive days across score cutoffs; its prevalence reference is 0.156. Balanced accuracy averages sensitivity and specificity. Macro F1 averages the two class F1 scores. Ranking and fixed-threshold classification answer different questions, and the scores have not been established as calibrated clinical probabilities.

### Main finding and error tradeoff

Adding the five bodily symptoms raises AP from 0.526 to 0.623, an increase of 0.096, with a conditional paired 95% interval of [+0.012, +0.146]. Balanced accuracy changes from 0.804 to 0.795 and macro F1 from 0.754 to 0.761. At the fixed rule, the symptom model detects 364 of 517 positive days and generates 317 false positives; severity alone detects 382 and generates 369. Thus, the symptom model produces 52 fewer false positives while missing 18 more positive days. This explains why ranking improves while balanced accuracy decreases.

### Which other domains add information

Bleeding history increases AP from 0.526 to 0.576; the paired interval for the change is [+0.008, +0.088]. Physiology gives AP 0.550, but its paired interval includes zero. Sleep, activity, stress or mood and background attributes have smaller or uncertain AP changes. These are tests of candidate domains, not evidence that every feature is beneficial.

The full model reaches AP 0.602 versus 0.526 for severity alone, with a paired interval of [+0.013, +0.120]. Its balanced accuracy is lower at 0.781. Against the original 21-feature forest (AP 0.555), the full model’s AP improvement is uncertain: paired interval [-0.010, +0.099].

In leave-one-domain-out comparisons, the full model has AP 0.602 versus 0.547 without bodily symptoms; the interval for that difference is [-0.015, +0.132], which includes zero. The stronger pain-only block comparison therefore does not establish a unique somatic contribution after all other features are present. Bleeding history contributes a smaller AP change within the full model, with interval [+0.001, +0.041].

The forest excluding previous-day cramps still achieves AP 0.495, balanced accuracy 0.718 and macro F1 0.714. Other measured domains contain signal under this evaluation, while pain history remains valuable. The full logistic model has AP 0.537 versus 0.528 for pain severity alone, so the forest’s improvement is not consistent across model families.

### Supplementary datasets and separate experiments

MPIS provides a separately fitted next-day forecasting analysis using observed diaries [11]. Its published 2,160-row grid includes 1,856 imputed rows, which we exclude from both predictors and outcomes. The primary observed control-phase cohort has 105 consecutive-day pairs from 14 people, including 14 pain outcomes at our project threshold of at least 4 out of 10. It contains no wearable measurements.

| MPIS logistic inputs | Average precision | Balanced accuracy | Macro F1 |
| --- | --- | --- | --- |
| Pain history | 0.461 | 0.720 | 0.684 |
| Pain plus clinical reproductive attributes | 0.537 | 0.775 | 0.701 |
| Full literature model | 0.490 | 0.690 | 0.668 |

The clinical block adds menarche age, cycle length, period duration, live births, reported endometriosis and adenomyosis status, and nonmenstrual pain frequency. Its balanced-accuracy gain has a paired interval of [-0.014, +0.131]. In the stricter pre-intervention-only sensitivity, balanced accuracy is approximately 0.745 for both models. Source timing and provenance inconsistencies, possible intervention carry-over and unverified participant non-overlap limit interpretation.

PhysioPain supplies a separate current-pain experiment using Empatica E4 recordings and lifestyle surveys [12]. Our usable contrast has 17 participants: 8 with moderate-or-higher menstrual pain, 1 with mild menstrual pain and 8 no-pain controls. Lifestyle logistic balanced accuracy is 0.646, wearable logistic 0.465 and combined logistic 0.472. Adding wearables did not help that model. These short recordings cannot validate next-day forecasting, and neither supplementary analysis evaluates a frozen mcPHASES model externally.

## 5 Next steps and discussion

### Issues encountered and how we handled them

Access delayed the original download, and the later mcPHASES interval had too few observed cramp labels for a meaningful final test. We used the authorized extraction and retained 2022 as the primary cohort. Missing sensors and diaries required explicit quality rules and training-only imputation. Class imbalance required balanced metrics and simple baselines. Correlated symptoms and physiology required block comparisons rather than interpreting a large feature list as evidence of independent effects.

The evidence remains exploratory. The cohorts have already been inspected, and no independent final test set exists. Bootstrap intervals condition on saved predictions, without refitting, and have no correction for the many comparisons. Repeated daily records do not increase the number of independent participants. Prior pain can influence symptoms, sleep and activity, and common diary reporting may contribute to correlations. Actual report or upload availability at forecast time is not established. We do not infer causes, treatment effects, diagnosis or clinical readiness.

### Project conclusion at midpoint

We have implemented a reproducible multifactor menstrual-pain forecasting analysis. The clearest additional ranking information comes from the five bodily symptoms when added to pain severity alone. Bleeding history also helps ranking; broader classification and supplementary-cohort gains are inconsistent. We will report both the added information and the limits, rather than selecting one metric to claim universal improvement.

### Final completion timeline

The October core milestones are complete, and the November 1 extensions are complete. Only delivery and presentation tasks remain. New participant collection, restricted-data applications, prospective deployment, threshold tuning and external clinical validation are future extensions outside this final course scope.

| Due date | Remaining task | Completion evidence |
| --- | --- | --- |
| November 30, 2026 | Review figures, metric labels and symptom explanations | Every displayed value matches the saved aggregate run |
| November 30, 2026 | Finalize report, references and presentation text | Consistent claims, correct citations and clear study limitations |
| November 30, 2026 | Rehearse and review the six minute presentation | Timed run and prepared responses for two minutes of questions |
| November 30, 2026 | Submit final report, code and presentation | Final files packaged; restricted participant data excluded |

### Suggested six minute presentation allocation

| Required section | Speaking time |
| --- | --- |
| Title slide | 15 seconds |
| Background | 45 seconds |
| Data set and sensing including the five symptoms | 75 seconds |
| Milestones and analysis | 55 seconds |
| Initial results | 110 seconds |
| Next steps and discussion | 60 seconds |
| Total presentation | 360 seconds |

## References

Bracketed numbers identify supporting literature or data sources. Our own model scores are calculated from saved participant-held-out predictions. Published findings motivate candidate features; they do not establish effects for each individual diary item.

[1] Armour M, Parry K, Manohar N, et al. The Prevalence and Academic Impact of Dysmenorrhea in 21,573 Young Women: A Systematic Review and Meta-Analysis. Journal of Women's Health. 2019;28(8):1161-1171. https://doi.org/10.1089/jwh.2018.7615

[2] Lin B, Li JY, Kalani K, Truong K, Mariakakis A. mcPHASES: A Dataset of Physiological, Hormonal, and Self-reported Events and Symptoms for Menstrual Health Tracking with Wearables. Version 1.0.0. PhysioNet; 2025. https://doi.org/10.13026/zx6a-2c81

[3] Goodale BM, Shilaih M, Falco L, Dammeier F, Hamvas G, Leeners B. Wearable Sensors Reveal Menses-Driven Changes in Physiology and Enable Prediction of the Fertile Window: Observational Study. Journal of Medical Internet Research. 2019;21(4):e13404. https://doi.org/10.2196/13404

[4] Slater H, Paananen M, Smith AJ, et al. Heightened cold pain and pressure pain sensitivity in young female adults with moderate-to-severe menstrual pain. Pain. 2015;156(12):2468-2478. https://doi.org/10.1097/j.pain.0000000000000317

[5] International Association for the Study of Pain. Painful periods. Undated research explainer of Slater et al. Supplied PDF, pages 1-4. This is a secondary explanation of reference 4, rather than a separate participant dataset.

[6] Hagy HMA. Menstrual Pain Trajectories and Their Psychological and Behavioral Predictors. MA thesis. Loyola University Chicago; 2021. Methods: supplied PDF pages 23-28. Predictor results: pages 43-47, especially Table 4 on page 47. The abstract emphasizes somatic symptoms; the detailed table additionally reports one depression contrast. https://ecommons.luc.edu/luc_theses/4410/

[7] Tu FF, Hellman KM, Darnell SE, et al. A multidimensional appraisal of early menstrual pain experience. American Journal of Obstetrics and Gynecology. 2024;230(5):550.e1-550.e10. Supplied file nihms-1963694.pdf; baseline predictor table on PDF page 20. https://doi.org/10.1016/j.ajog.2024.01.017

[8] Jukic AMZ, Weinberg CR, Baird DD, Hornsby PP, Wilcox AJ. Measuring Menstrual Discomfort: A comparison of interview and diary data. Epidemiology. 2008;19(6):846-850. Supplied file nihms87949.pdf; methods and results on PDF pages 2-5. https://doi.org/10.1097/EDE.0b013e318187ac9e

[9] Mitsuhashi R, Sawai A, Kiyohara K, Shiraki H, Nakata Y. Factors Associated with the Prevalence and Severity of Menstrual-Related Symptoms: A Systematic Review and Meta-Analysis. International Journal of Environmental Research and Public Health. 2023;20(1):569. Published online December 29, 2022. https://doi.org/10.3390/ijerph20010569

[10] Matthewman G, Lee A, Kaur JG, Daley AJ. Physical activity for primary dysmenorrhea: a systematic review and meta-analysis of randomized controlled trials. American Journal of Obstetrics and Gynecology. 2018;219(3):255.e1-255.e20. https://doi.org/10.1016/j.ajog.2018.04.001

[11] Tisch V, Konigorski S, Neumayer H. MPIS Study Data. Version 1.0. Zenodo; 2026. Dataset description, baseline codebook and observed-only source tables; source-imputed rows are excluded in our analysis. https://doi.org/10.5281/zenodo.21538147

[12] Patlar Akbulut F, Toktay B, Isik Orhan I, Yildirim E. PhysioPain Dataset. Version 4. Mendeley Data; 2025. Source counts and usable menstrual-pain labels were audited from the downloaded archive. https://doi.org/10.17632/mf2cgph9cy.4

[13] Pollard T, Moody BE, Lehman LW, et al. PhysioNet as a global platform for biomedical research. Nature Health. 2026;1:792-795. Platform citation requested by the mcPHASES repository. https://doi.org/10.1038/s44360-026-00096-z

[14] Kapanova A, Wang F, Wang V. Predicting menstrual pain using health and lifestyle factors. Project proposal presentation. Unpublished course material; supplied file Proposal project. (2).pdf. Analysis plan: slides 4-7. Milestones and optional-pilot contingency: slide 8.

### Project evidence and reproducibility

Primary counts and original classifier results: reports/initial_results.json and reports/runs/mcphases_2022. Expanded block comparisons, intervals, feature coverage and hashes: reports/literature_factor_results.json. Supplementary sources: reports/mpis_results.json and reports/physiopain_results.json. The source-to-feature mapping is in reports/literature_evidence.json. Detailed participant records remain in ignored local folders.

Modeling commands: .venv/bin/python -m src.mcphases; .venv/bin/python -m src.mpis; .venv/bin/python -m src.literature_analysis. This report is rebuilt from saved aggregate results with the bundled Python running scripts/build_midpoint_report.py. Repository: https://github.com/alinak78/ml_prediction_pain. The saved local run files, rather than an assumption about the latest GitHub revision, support the new results.
