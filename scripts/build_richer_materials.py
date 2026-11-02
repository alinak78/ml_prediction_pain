"""Prepare richer midpoint slides and a section-by-section Google Docs manuscript."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/runs/mcphases_2022'
m=pd.read_csv(R/'metrics.csv').set_index('model')
importance=pd.read_csv(R/'permutation_importance.csv').groupby('feature').importance.mean().sort_values(ascending=False)
labels={'majority':'Majority class','flow_timing_proxy':'Prior flow timing','previous_pain':'Previous-day pain',
'logistic_regression':'Logistic regression','decision_tree':'Decision tree','random_forest':'Random forest',
'logistic_without_previous_pain':'Logistic without previous pain','random_forest_wearables_only':'Wearables-only forest'}
order=list(labels)
final_rows=[['When / status','Completion task','Proposed owner'],
['October — done','Data audit, models, evaluation and count checks','Team'],
['Nov 30','Finalize figures, tables and feature explanations','Alina + Vicky'],
['Nov 30','Complete final report and discussion','Alina + Fiona'],
['Nov 30','Final consistency check and presentation rehearsal','All'],
['Nov 30','Submit report, code and presentation','All']]
blocks=[]
def add(kind,text,**kwargs):blocks.append({'kind':kind,'text':text,**kwargs})
add('TITLE','Predicting menstrual pain using health and lifestyle factors')
add('SUBTITLE','Work summary by presentation section • October 28, 2026')
add('body','Team: Alina Kapanova, Fiona Wang and Vicky Wang. This document describes the completed work behind the midpoint presentation. Results come from the October 24 real-data run. The six required sections can span multiple presentation slides.')
add('HEADING_1','1. Title and project scope')
add('body','The project investigates whether health and lifestyle information can predict next-day menstrual cramp severity for people who were not included in model training. The implemented scope covers the complete analysis workflow: dataset inspection, daily feature preparation, model and baseline comparison, participant-held-out evaluation, uncertainty estimates, initial explainability and an exploratory demographic audit. The remaining delivery work is final review and communication of these findings.')
add('body','The main finding is that previous-day pain is a strong baseline. The additional features have not improved macro F1 beyond that baseline in the current evaluation. This is a valid research result and will be reported directly rather than treated as an unfinished model-building milestone.')
add('HEADING_1','2. Background: problem and approach')
add('body','Menstrual pain varies across people and cycles, which makes severity difficult to anticipate. Our proposal asks whether sleep, stress, physical activity, physiological signals and menstrual history can provide useful predictive information. We use an existing dataset rather than collecting a new sensing cohort.')
add('body','The task is retrospective one-day-ahead classification: predict pain on day t using information assigned to exact day t−1. The observed response labels are mapped to no/low pain (Not at all, Very Low/Little, Low) or moderate-or-higher pain (Moderate, High, Very High). This threshold is an analysis convention, not a clinically validated cutoff.')
add('body','We implemented logistic regression, a decision tree and random forest. We compare them with majority-class prediction, previous-day pain, and a prior-flow timing proxy. We also tested a logistic model without previous pain and a random forest restricted to wearable features. Holding out complete participants avoids testing the models on new days from the same people used for training.')
add('HEADING_1','3. Dataset / sensing')
add('HEADING_2','Dataset size and cohort selection')
add('body','The authorized mcPHASES v1.0.0 download contains 23 CSV tables and approximately 3.68 GB of extracted files. Its 110,135,462 CSV records are mostly repeated sensor samples, not independent participants. The diary contains 5,659 participant-days and 3,327 observed cramp responses across both study intervals.')
add('body','The primary analysis uses 2022: 42 participants, 3,698 diary days and 3,320 days with observed pain labels. We excluded 378 days with missing outcomes. The target distribution is 2,803 no/low days and 517 moderate-or-higher days, or 15.6% positive. The 2024 interval has only seven observed cramp responses and is excluded from the headline supervised analysis.')
add('HEADING_2','Hardware and included features')
add('body','The source study used Fitbit Sense smartwatches, Mira hormone measurements, Dexcom G6 glucose monitoring in the first interval, and daily smartphone diaries. Our prediction workflow uses existing Fitbit and diary measurements; no new wearable pilot has been collected. Nine source tables produce 21 prior-day predictors, including previous pain.')
add('bullet','Sleep: minutes asleep/awake, sleep efficiency, overall sleep score, deep-sleep minutes and restlessness.')
add('bullet','Activity: sedentary, light, moderate and vigorous activity minutes.')
add('bullet','Physiology: resting heart rate, HRV RMSSD, breathing rate, absolute nightly temperature and Fitbit stress score.')
add('bullet','Diary history: stress, mood swings, sleep difficulty, flow, time since observed flow and previous pain.')
add('HEADING_2','Bias and measurement limits')
add('body','The small Toronto-area cohort and its recruitment/eligibility criteria limit generalization. Missing wearable measurements and optional second-round diaries affect coverage. The actual demographic table does not contain income, although the README mentions it. Only one gender category meets our minimum supported group size, so the data do not support a reliable gender comparison. These are study limitations, not new collection milestones for the final delivery.')
add('HEADING_1','4. Milestones / analysis: work completed')
add('HEADING_2','Acquisition, inspection and cleaning')
add('body','We downloaded and inventoried the dataset, verified actual schemas and response strings, and constructed one daily analysis record per participant. The original download/exploration milestone was planned for October 9; it was completed on October 24 after access was resolved. Initial cleaning and feature construction, planned for October 23, were completed on October 24. Modeling and initial evaluation were completed ahead of their proposal dates of November 13 and November 24.')
add('bullet','Outcome handling: validate labels and unique diary keys; exclude missing pain outcomes rather than imputing them.')
add('bullet','Duplicate and device-status handling: remove exact repeated sensor records, including 3,601 first-round Fitbit stress-score duplicates; reject failed, NO_DATA and IN_PROGRESS stress scores.')
add('bullet','Quality filtering: use broad prespecified bounds to set 782 resting-HR values, 53 respiratory-rate values and seven HRV values to missing. Require HRV coverage of at least 0.8, excluding 5,950 low/absent-coverage records.')
add('bullet','Daily summaries: restrict sleep to main sleep, index it by end day, and use medians for distinct repeated summaries to avoid summing repeated or revised records. Keep missing measurements missing until fold-level preprocessing.')
add('HEADING_2','Feature engineering and leakage prevention')
add('body','Features are joined from exact day t−1, not merely the preceding observed row. This prevents missing days or long study gaps from being treated as consecutive observations. The flow-timing proxy uses only observed flow history; it is not a ground-truth cycle phase. Retrospective hormone-derived phase labels and proprietary personal-temperature-baseline deviations are excluded. Actual upload/report latency is not established by these exports, so prospective availability remains an interpretation limit.')
add('body','Predictor missingness ranges from 1.2% to 44.0%. Missingness filtering at more than 60%, median imputation with missingness indicators, and scaling are fitted only on training folds. Previous pain is unavailable on 236 labeled target days (7.1%); the persistence baseline uses the training-fold majority class for those cases.')
add('HEADING_2','Models, evaluation and interpretation')
add('body','All three proposed classifiers and three baselines are implemented and evaluated, with two additional feature-ablation comparisons. Five-fold GroupKFold keeps each participant entirely within one test fold, with no participant shared between training and test in a fold. Hyperparameters are fixed and random state is 42. Evaluation includes macro F1, balanced accuracy, ROC-AUC, confusion matrices and out-of-fold predictions.')
add('body','Completed interpretation and robustness work includes held-out random-forest permutation importance, logistic coefficients, retained-feature records, 2,000 paired participant-cluster bootstrap resamples, a sensitivity analysis restricted to days with known previous pain, and supported demographic subgroup comparisons. Eight targeted tests pass. Code and aggregate documentation have been pushed to GitHub; restricted raw files and participant-level derivatives remain outside the repository.')
add('body','The optional pilot and pilot comparison were not collected and are outside the final delivery scope. Initial explainability and bias analysis are complete; final wording and visual presentation are still being refined. Independent external validation and a future tuned model would be extensions beyond the current fixed-model analysis, not remaining core milestones.')
add('HEADING_1','5. Initial results and interpretation')
add('body','The table reports pooled out-of-fold scores from the same 3,320 target days and participant-grouped evaluation. Macro F1 treats both classes equally; balanced accuracy accounts for unequal class prevalence. ROC-AUC measures ranking, and the persistence baseline has only hard 0/1 predictions rather than a full probability ranking.')
add('table','RESULTS_TABLE',rows=[['Model / baseline','Macro F1','Balanced accuracy','ROC-AUC']]+[[labels[k],f'{m.loc[k,"macro_f1"]:.3f}',f'{m.loc[k,"balanced_accuracy"]:.3f}',f'{m.loc[k,"roc_auc"]:.3f}'] for k in order])
add('body','All three full-feature classifiers improve on majority class, but none beats previous-day pain on macro F1. Random forest is the strongest of the three full classifiers at 0.770, compared with 0.781 for persistence. Their balanced accuracies both round to 0.773. The forest and logistic AUCs are about 0.83, but this alone does not establish better decisions or calibrated risk estimates.')
add('body','The wearable-only forest scores 0.569 macro F1, and logistic regression without previous pain scores 0.581. Previous pain dominates forest permutation importance, with a mean held-out balanced-accuracy decrease of 0.241 when permuted. These comparisons show that pain history carries much of the predictive information in the current models; they do not establish that lifestyle or physiology causes pain.')
add('HEADING_2','Errors, uncertainty and subgroup findings')
add('body','Random forest correctly identifies 320 of 517 moderate-or-higher days (61.9% sensitivity), misses 197, and produces 207 false positives. Persistence identifies 313 positive days, misses 204, and produces 168 false positives. Thus, forest finds seven additional positive days but adds 39 false alarms at the current decision rule.')
add('body','Participant-cluster bootstrap intervals for macro F1 are approximately 0.699–0.821 for forest and 0.716–0.826 for persistence. The paired forest-minus-persistence difference is −0.010, with an approximate 95% interval of −0.022 to −0.002. These intervals condition on fixed out-of-fold predictions; they do not refit the models or capture every source of development uncertainty.')
add('body','On the 3,084 days with observed prior-day pain, the same predictions yield F1 of 0.778 for forest and 0.789 for persistence, preserving the main conclusion. The demographic audit requires at least five participants and at least ten target days in each class per group. Forest false-negative rates among supported ethnicity groups range roughly from 26% to 59%; small and unequal groups prevent a population-wide fairness conclusion.')
add('HEADING_1','6. Next steps / discussion: final completion only')
add('body','The October data audit, processing, model evaluation and reported-count checks are complete. All remaining finalization tasks are due November 30, 2026: polish figures and explanations, complete the final report, perform the final consistency check, rehearse and submit. The final deliverable will report the lack of improvement over pain history honestly; a new model, new sensor cohort or external validation dataset is not required to complete this defined scope.')
add('table','TIMELINE_TABLE',rows=final_rows)
add('body','Final discussion will state the main limits: a small selected cohort, class imbalance, missing measurements, uncertain prospective data availability, exploratory subgroup differences and no independent final test cohort. The cohort has already been inspected and cannot later be described as an untouched final holdout. These limits will be clearly documented rather than recast as unfinished core work.')
add('HEADING_2','Project materials and evidence')
add('body','Repository: https://github.com/alinak78/ml_prediction_pain')
add('body','Detailed checkpoint report: https://github.com/alinak78/ml_prediction_pain/blob/main/reports/midpoint_checkpoint.md')
add('body','Dataset and documentation: https://physionet.org/content/mcphases/1.0.0/')
add('body','Original project proposal and saved run outputs support the plan-to-completion comparison. This summary reflects the completed October 24 analysis and the revised presentation/final-delivery scope on October 28. Proposed owners describe future finalization tasks, not verified attribution for past individual contributions.')
(ROOT/'reports/google_doc_summary_content.json').write_text(json.dumps(blocks,indent=2)+'\n')

# Richer presentation: ten slides within the same six rubric sections.
INK,ACCENT='#24342E','#29695B'
def box(text,x=76.8,y=172.8,w=1123.2,h=450,size=32,bold=False,color=INK):
 return {'x':x,'y':y,'w':w,'h':h,'paragraphs':text if isinstance(text,list) else [text],'size':size,'bold':bold,'color':color}
slides=[]
source=' Sources: original proposal; reports/midpoint_checkpoint.md; saved mcPHASES_2022 metrics, cleaning audit and permutation importance. Dataset: https://physionet.org/content/mcphases/1.0.0/.'
def slide(title,section,seconds,notes,body=None):
 n=len(slides)+1
 s={'boxes':[box(title,x=67.2,y=48,w=1152,h=96,size=45.33,bold=True),box(section+' • October 28, 2026',y=672,w=950,h=24,size=14.67,color=ACCENT),box(str(n),x=1180,y=672,w=40,h=24,size=14.67,color=ACCENT)],'table':None,'notes':f'Target time: {seconds} seconds.\n'+notes+source,'seconds':seconds}
 if body:s['boxes'].insert(1,box(body))
 slides.append(s);return s
s=slide('Predicting menstrual pain','1. Title',15,'Introduce Alina Kapanova, Fiona Wang and Vicky Wang. We studied whether health and lifestyle factors can anticipate next-day pain. Today we report a complete initial analysis and the main finding: pain history remains a strong baseline.')
s['boxes'] += [box('Using health and lifestyle factors',y=201.6,h=124.8,size=45.33,color=ACCENT),box('Alina Kapanova · Fiona Wang · Vicky Wang',y=403.2,h=96,size=34.67),box('Midcheckpoint presentation',y=537.6,h=57.6,size=29.33)]
slide('Predicting next-day menstrual pain','2. Background',35,
 'Menstrual pain varies across people and cycles. Our proposal asks whether sleep, stress, activity, physiology and menstrual history provide useful information. We made the task concrete: predict day-t pain using exact day t−1 data. The binary grouping follows observed labels and is a project convention, not a clinical cutoff. We combine Fitbit signals and diaries, then compare three classifiers with simple baselines for unseen participants.',
 ['Problem: menstrual pain varies across people and cycles.', 'Prediction: next-day no/low vs. moderate-or-higher pain.', 'Inputs: prior-day physiology, lifestyle and symptom history.', 'Goal: test whether these signals add value beyond pain history.'])
slide('Dataset and cohort','3. Dataset / sensing',35,
 'The existing mcPHASES download has 23 tables and 3.68 GB of files. We use 42 participants and 3,320 labeled days from 2022. Missing outcomes are excluded. Positive labels represent 15.6% of days. The later interval has only seven pain reports and is excluded from the headline results. We use nine Fitbit and diary tables for 21 predictors; source hardware is Fitbit Sense. No new pilot is part of this analysis.',
 ['42 participants • 23 tables • 3.68 GB of extracted files', '3,320 labeled 2022 days; 517 moderate-or-higher days (15.6%)', 'Fitbit Sense: sleep, activity, resting HR/HRV, temperature, breathing', 'Diary: pain, stress, mood, sleep difficulty and flow history', '2024 has only seven pain labels; not used in the primary analysis.'])
slide('Completed cleaning and features','4. Milestones / analysis',40,
 'We inspected the codebook and real schemas, mapped the ordered pain responses and prepared daily features. We excluded 378 missing outcomes, removed 3,601 duplicate stress records and rejected failed or in-progress scores. Broad prespecified bounds flag impossible measurements as missing, and HRV requires adequate coverage. Sleep is assigned to its end day. Exact lagging avoids bridging missing days or study rounds. We exclude retrospective hormone phase labels; imputation is learned inside training folds.',
 ['Verified outcome labels; excluded 378 missing pain outcomes.', 'Removed duplicates and invalid device scores; checked plausible ranges.', 'Prepared 21 prior-day predictors from nine source tables.', 'Used exact day t−1 joins and sleep-end-day alignment.', 'Kept imputation and missingness filtering inside training folds.'])
s=slide('Completed analysis milestones','4. Milestones / analysis',40,
 'Download and initial preparation were completed October 24 after the access delay. The three proposed classifiers are implemented, together with three baselines and two feature-ablation checks. We have five participant-held-out folds, confusion matrices, participant-cluster uncertainty, initial explainability and supported subgroup checks. Eight targeted tests pass and code is on GitHub. Initial interpretation is complete; remaining work is final checking and communication. The optional pilot was not collected and is outside the final deliverable scope.')
s['table']=[['Proposal work','Completed output'],['Data preparation','Audited daily dataset and 21 predictors'],['Model implementation','Logistic regression, decision tree, random forest'],['Validation','5 participant-held-out folds + baseline comparison'],['Interpretation and bias','Permutation importance, uncertainty and subgroup audit']]
s['table_widths']=[360,763.2];s['table_font_size']=27
s=slide('Pain history remains the strongest baseline','5. Initial results',50,
 'This chart shows macro F1 on the same out-of-fold target days. Persistence is 0.781; forest is 0.770, logistic is 0.716 and tree is 0.713. All beat majority class, but none beats previous-day pain. Forest and persistence balanced accuracies both round to 0.773. Forest and logistic AUCs are around 0.83, but a higher AUC does not establish better decisions than a hard-prediction baseline. Two thousand participant-cluster resamples support a small F1 disadvantage for forest, conditional on fixed predictions.')
keys=['majority','flow_timing_proxy','decision_tree','logistic_regression','random_forest','previous_pain']
s['chart']={'categories':[labels[k] for k in keys],'values':[round(float(m.loc[k,'macro_f1']),6) for k in keys], 'series_name':'Macro F1','axis_max':1,'format':'0.000','position':{'left':76.8,'top':155,'width':1123.2,'height':448}}
s['boxes'].append(box('Forest 0.770 vs. persistence 0.781; balanced accuracy ≈ 0.773 for both.',y=625,h=37,size=23,color=ACCENT))
s=slide('Previous pain dominates feature importance','5. Initial results',40,
 'Held-out permutation importance asks how much balanced accuracy decreases when a feature is shuffled. Previous pain causes a mean decrease of 0.241, much larger than the other predictors. Wearable-only forest has F1 of 0.569; a logistic model without previous pain has F1 of 0.581. These comparisons suggest that symptom history explains much of the current performance. Importance is a predictive association, not evidence of a cause; correlated features and missingness affect interpretation.')
features=importance.head(5).iloc[::-1]
pretty={'previous_pain':'Previous-day pain','stress_lag1':'Prior-day stress','respiratory_rate_lag1':'Respiratory rate','vigorous_activity_minutes_lag1':'Vigorous activity','resting_hr_lag1':'Resting heart rate'}
s['chart']={'categories':[pretty.get(c,c) for c in features.index],'values':[round(float(v),6) for v in features.values], 'series_name':'Decrease in balanced accuracy','axis_max':.3,'format':'0.000','position':{'left':76.8,'top':155,'width':1123.2,'height':448}}
s['boxes'].append(box('Wearables-only forest F1 = 0.569; importance does not imply causation.',y=625,h=37,size=23,color=ACCENT))
s=slide('Errors and subgroup limitations','5. Initial results',35,
 'Forest finds 320 of 517 moderate-or-higher days but misses 197. Compared with persistence it finds seven extra positive days at the cost of 39 more false alarms. In supported ethnicity groups, missed-pain rates vary approximately 26% to 59%, but the groups are small and comparisons are exploratory. Only one gender category meets our minimum group threshold. There is no independent final test cohort or clinical validation.')
s['table']=[['Random forest','Predicted no/low','Predicted moderate+'],['Actual no/low','2,596','207'],['Actual moderate+','197','320']]
s['table_widths']=[400,340,383.2];s['table_font_size']=27;s['table_position']={'left':76.8,'top':165,'width':1123.2,'height':252}
s['boxes'].append(box(['61.9% sensitivity: 320 of 517 positive days detected.', 'Small cohort and exploratory subgroup gaps constrain generalization.'],y=460,h=140,size=28))
slide('Core analysis complete; final refinements remain','6. Next steps / discussion',30,
 'Our completed work answers the initial feasibility question under a defined retrospective task. The extra features do not beat pain history on macro F1. We will preserve that finding and its caveats. Only final reviews, figure improvements, clear explanations and submission preparation remain. A new model, a new pilot and independent external validation are not requirements for this final scope; the absence of external validation is documented as a limit.',
 ['Completed: processing, model comparison, uncertainty and interpretation.', 'Finding: additional features have not improved macro F1 over pain history.', 'Remaining: final checks, clearer figures and the written presentation of results.', 'Limits stay explicit: selected cohort, missing data and no independent test.'])
s=slide('October complete; final tasks due November 30','6. Next steps / discussion',40,
 'These are proposed owners for final delivery, not new major research milestones. The October data audit, processing, model evaluation and count checks are complete. All remaining tasks are due November 30, 2026: finalize figures and explanations, finish the report, check consistency, rehearse and submit. The analysis pipeline and initial results already exist. No new sensing cohort or model rebuild is needed to complete this scope. Thank the audience and leave two minutes for questions.')
s['table']=final_rows;s['table_widths']=[210,600,313.2];s['table_font_size']=23.5
assert sum(s['seconds'] for s in slides)==360
(ROOT/'scripts/midpoint_richer.json').write_text(json.dumps(slides,indent=2)+'\n')
(ROOT/'output/presentation/midpoint_richer_notes.md').write_text('# Six-minute presentation — expanded structure\n\n'+'\n\n'.join(f'## Slide {i}: {s["boxes"][0]["paragraphs"][0]}\n\n{s["notes"]}' for i,s in enumerate(slides,1))+'\n\nAllow two minutes for questions.\n')
print(f'Prepared {len(slides)} slides and {len(blocks)} document blocks.')
