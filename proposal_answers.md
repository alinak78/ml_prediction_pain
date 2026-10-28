# Proposal answers: Predicting menstrual pain using health and lifestyle factors

Source: `Proposal project. (2).pdf`, slides 1–9. Questions: the assignment text supplied by the user. These answers summarize the existing proposal; planned work is not evidence of completed work. External claims and references below are transcribed or paraphrased from the proposal and have not been independently verified.

## 1. Project name and team

**Project:** Predicting menstrual pain using health and lifestyle factors.

**Team:** Alina Kapanova, Fiona Wang, and Vicky Wang. (Slide 1)

## 2. What is the goal? What questions will the project answer?

Investigate whether sleep, stress, physical activity, physiological signals, and menstrual-cycle timing can predict menstrual pain/cramp severity. The central research question asks whether these features can distinguish no or mild pain from moderate or severe pain. The proposal also considers multiclass prediction of mild, moderate, and severe pain. The final target definition remains to be selected. (Slides 2–3, 5–6)

## 3. Why does this matter? What value and impact will it bring?

Menstrual pain is common, affects school attendance and concentration, and varies across cycles. The proposal cites a meta-analysis reporting 71.1% dysmenorrhea prevalence, 20.1% missing school/university, and 40.9% impaired academic performance or concentration. Combining lifestyle and wearable signals could help establish whether pain severity can be anticipated. The intended contribution is evidence of predictive feasibility and interpretable associations, rather than a clinically validated diagnostic system. (Slides 2–3, 6)

## 4. What relevant work supports the project?

- Armour et al. (2019): prevalence and academic impact of dysmenorrhea.
- Harlow and Park (1996): variation and risk factors for menstrual cramp occurrence, duration, and severity.
- Mitsuhashi et al. (2023): associations between menstrual symptoms and factors such as stress, short sleep, and late bedtime.
- Matthewman et al. (2018): physical activity interventions and dysmenorrhea pain intensity.
- Goodale et al. (2019): menstrual-cycle variation in wearable physiological measurements.
- Kilungeja et al. (2025): machine learning for menstrual phase identification using wearable data. This supports the use of wearable features, but its reported performance is not a pain-prediction result.
- Lin et al. (2025, 2026): the mcPHASES dataset and its accompanying publication.

The proposed research gap is whether lifestyle, physiological, and menstrual features together predict pain severity. (Slides 2–4, 9)

## 5. How will the project achieve its goal? What dataset and sensors will it use?

The primary dataset is **mcPHASES**, released on PhysioNet by University of Toronto researchers. The proposal describes 42 menstruating young adults observed across three-month periods, with 20 returning for a second period. It contains 23 structured tables linked by participant and study day. (Slides 4–5)

The original study used **Fitbit Sense** smartwatches and daily smartphone diaries. Available measurements described in the proposal include heart rate, activity, active minutes, sleep duration/stages/scores, respiratory rate, skin temperature, stress metrics, VO₂ max, oxygen variation, cramps, mood, flow, sleep quality, and self-reported stress. The planned analysis uses selected self-report, heart rate, sleep, activity, temperature, and respiratory-rate tables, with HRV where available. (Slides 4–5)

The main project does not require owning a wearable because the dataset has already been collected. An Apple Watch or Fitbit pilot is an optional extension. Access to a particular pilot device is not confirmed. (Slide 4)

## 6. How large is the dataset? Where will it be stored and how will it be extracted?

The proposal specifies the participant count and 23-table structure, but does **not** give the download size, total row count, or number of usable labeled participant-days.

Data will be processed locally using Python/pandas and the provided mcPHASES Jupyter code. Tables will be linked by participant and study day to construct one observation per participant-day. The proposal states that no dedicated server is required. It does not name a database, local storage format, download/access procedure, or measured memory requirement. (Slides 4–5)

## 7. What analysis and algorithms will be used? How does dataset size affect the plan?

The analysis pipeline includes exploratory data analysis, missingness assessment, feature engineering, classification, participant-level cross-validation, comparison with simple baselines, explainability, and exploratory subgroup analysis.

Candidate models are logistic regression, a decision tree, and a random forest. The dataset contains repeated daily observations from only 42 participants, so the number of daily rows should not be treated as the number of independent people. The proposal does not give model runtime estimates, an inference latency requirement, or a formal sample-size justification. (Slides 5–7)

## 8. What data-quality problems might arise? How will they be handled?

Expected issues include missing wearable measurements, incomplete features, pain-class imbalance, physiological outliers, correlated features, and variation between participants.

The proposed missingness strategy is to assess missingness, drop highly incomplete features, impute remaining predictor values, never impute pain outcomes, and run sensitivity analyses. Data-quality checks will compare missingness across participants/features, inspect class balance and outliers, assess feature correlations, and examine whether a few participants drive predictions. (Slides 5, 7–8)

The proposal does not specify thresholds for dropping features, an imputation algorithm, an explicit procedure for inconsistent or mislabeled self-reports, or a class-imbalance treatment during training. Balanced metrics are planned for evaluation.

## 9. Is the data biased? How will bias be evaluated?

The cohort consists of Canadian young adults who menstruate, recruited in the Greater Toronto Area, and is not representative of all ages or populations.

The plan is to compare performance by available age, race/ethnicity, and socioeconomic variables, where groups have sufficient representation. Metrics include macro F1, balanced accuracy, false-positive rate, and false-negative rate. With only 42 participants, these comparisons will be reported as exploratory and will not establish population-wide fairness. (Slides 5, 7)

The assignment's example of comparing males and females is not explicitly addressed in the proposal. Such a comparison depends on the actual demographic fields and representation; it should not be assumed possible. Specific bias-mitigation interventions beyond evaluating and reporting limitations are not defined.

## 10. What feature engineering is planned?

Each model observation will represent a participant-day. Planned feature groups are:

| Feature group | Planned transformations or variables |
| --- | --- |
| Sleep | Total sleep duration, sleep score, sleep-stage proportions |
| Activity | Active minutes, sedentary minutes, activity intensity |
| Physiology | Mean/resting heart rate, HRV where available, respiratory rate, temperature deviation |
| Menstrual and lifestyle | Cycle phase/day, stress, mood, previous-day cramps |

The proposal does not define aggregation windows, temperature reference values, feature scaling, or the exact time at which a prediction will be made. (Slide 5)

## 11. What is the training/testing/CV plan? How will overfitting be avoided?

Split by **participant rather than day**, using GroupKFold or leave-one-subject-out cross-validation. Train on some participants and evaluate on entirely unseen participants to assess generalization. (Slide 5)

The exact fold count, final held-out test set, hyperparameter search, and model-selection protocol are not specified. The implementation must also settle how preprocessing is fitted within training folds and which features are available before the intended prediction time; the proposal does not provide those details.

## 12. What tools will be used?

Python, pandas, NumPy, scikit-learn, Matplotlib, and the official mcPHASES Jupyter analysis code. SHAP is proposed for prediction explanations. Local processing is planned; no specific storage database is named. (Slides 5, 7)

## 13. What sensing-system work is required?

The primary project analyzes an existing sensing dataset, so new recruitment, sensor deployment, or 3D-printed attachments are not required for its core scope.

The optional pilot would collect Apple Watch or Fitbit data alongside daily symptom reports. Its proposed use is exploratory external validation. Device access, participant count, collection protocol, and cross-device harmonization are not specified. The timeline includes pilot tasks, but the proposal explicitly makes the pilot optional and keeps mcPHASES as the primary dataset. (Slides 4, 8)

## 14. How will results be validated? What metrics and baselines will be used?

Evaluate on unseen participants using:

- **Macro F1:** give each pain class equal weight.
- **Balanced accuracy:** account for unequal class frequencies.
- **Confusion matrix:** show which pain categories are confused.
- **ROC-AUC where appropriate:** assess discrimination for the selected classification target.

Compare against three baselines: majority class, cycle timing only, and previous pain only. The optional pilot may provide an exploratory external-validation set. (Slides 6, 8)

## 15. What counts as success?

Success means outperforming simple baselines, generalizing to held-out participants, producing interpretable relationships, and maintaining a reproducible pipeline. It is a predictive-feasibility project. No numerical performance threshold or required margin over the baselines is specified. (Slide 6)

## 16. How will the model be explained?

- Logistic regression: inspect coefficients for the direction and strength of associations.
- Decision tree: visualize decision rules and feature splits.
- Random forest: calculate permutation feature importance.
- SHAP: explain how features contribute to individual predictions.

Feature importance will be interpreted as predictive association, not evidence that a feature causes menstrual pain. (Slide 7)

## 17. What tests will assess data and result quality?

Planned tests include missingness comparisons, class-balance checks, outlier inspection, feature-correlation analysis, participant-variation analysis, participant-held-out validation, baseline comparisons, missing-data sensitivity analyses, and exploratory subgroup performance comparisons. The proposal does not provide the exact test procedures, uncertainty estimates, or minimum subgroup sample sizes. (Slides 5–7)

## 18. What are the milestones, dates, and responsibilities?

The proposal includes a Gantt chart and the following planned milestone dates. Dates are reproduced as written; the slide does not explicitly state a year or confirm completion. (Slide 8)

| Planned date | Milestone | Team allocation shown in the Gantt chart |
| --- | --- | --- |
| Oct 9 | Download/explore mcPHASES; finalize pilot protocol | Fiona: dataset exploration; Alina: research question/protocol |
| Oct 12 | Begin wearable and daily symptom collection | All |
| Oct 23 | Complete data cleaning and feature engineering | Vicky: cleaning/missingness; Alina: EDA/features |
| Nov 13 | Implement ML models; process pilot sensor data | Alina and Vicky: models; Fiona: pilot data |
| Nov 24 | Complete cross-validation, evaluation, and pilot comparison | Alina: validation/model comparison; Fiona: pilot comparison |
| Dec 2 | Complete explainability and bias analysis | Alina |
| Dec 4 | Complete final results, conclusions, and visualizations | Alina and Fiona: final results/visualizations |

The chart spans blocks labeled Sep 28, Oct 5, Oct 19, Nov 2, Nov 16, and Nov 30, with the last block ending Dec 4. Work-hour estimates are not provided.

## 19. What roadblocks are expected? What is the contingency plan?

Potential roadblocks are limited pilot participants or sensor data, missing wearable measurements, pain-class imbalance, and variation between participants. The contingency is to keep mcPHASES as the primary dataset and treat the pilot as exploratory external validation rather than a dependency for completion. (Slide 8)

## 20. References recorded in the proposal

1. Armour et al. (2019). *The Prevalence and Academic Impact of Dysmenorrhea in 21,573 Young Women: A Systematic Review and Meta-Analysis.* Journal of Women's Health 28(8):1161–1171. https://doi.org/10.1089/jwh.2018.7615
2. Goodale et al. (2019). *Wearable Sensors Reveal Menses-Driven Changes in Physiology and Enable Prediction of the Fertile Window: Observational Study.* JMIR 21(4):e13404. https://doi.org/10.2196/13404
3. Harlow and Park (1996). *A Longitudinal Study of Risk Factors for the Occurrence, Duration and Severity of Menstrual Cramps in a Cohort of College Women.* British Journal of Obstetrics and Gynaecology 103(11):1134–1142. https://doi.org/10.1111/j.1471-0528.1996.tb09597.x
4. Kilungeja et al. (2025). *Machine Learning-Based Menstrual Phase Identification Using Wearable Device Data.* npj Women's Health 3:29. https://doi.org/10.1038/s44294-025-00078-8
5. Lin, Blue, et al. (2025). *mcPHASES: A Dataset of Physiological, Hormonal, and Self-Reported Events and Symptoms for Menstrual Health Tracking with Wearables.* PhysioNet, version 1.0.0. https://physionet.org/content/mcphases/1.0.0/
6. Lin, Georgianna, et al. (2026). *A Longitudinal Dataset of Physiological, Hormonal, Metabolic, and Self-Reported Menstrual Health Data.* Scientific Data 13:411. No URL is supplied on the reference slide.
7. Matthewman et al. (2018). *Physical Activity for Primary Dysmenorrhea: A Systematic Review and Meta-Analysis of Randomized Controlled Trials.* American Journal of Obstetrics and Gynecology 219(3):255.e1–255.e20. https://doi.org/10.1016/j.ajog.2018.04.001
8. Mitsuhashi et al. (2023). *Factors Associated with the Prevalence and Severity of Menstrual-Related Symptoms: A Systematic Review and Meta-Analysis.* IJERPH 20(1):569. https://doi.org/10.3390/ijerph20010569

## Details to finalize before implementation

- Choose binary or multiclass pain prediction and define how the recorded pain values map to labels, including no-pain observations.
- Define the prediction horizon and ensure inputs are available at prediction time.
- Confirm dataset access, download size, row counts, usable participant-days, and storage format.
- Specify missingness thresholds, imputation, label checks, and any class-imbalance treatment.
- Fix the participant-based validation/model-selection protocol and fit preprocessing within training folds.
- Confirm which demographic fields are available and which subgroup comparisons have enough participants.
- Set a quantitative success criterion if the team wants a numerical target.
- Confirm whether the optional pilot will proceed, including devices, participants, and protocol.
- Update milestone status and confirm the schedule year.
