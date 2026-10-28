"""Six slides matching the class midpoint requirements, using verified saved results."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
INK,ACCENT='#24342E','#29695B'

def box(text,x=76.8,y=172.8,w=1123.2,h=450,size=32,bold=False,color=INK):
 return {'x':x,'y':y,'w':w,'h':h,'paragraphs':text if isinstance(text,list) else [text], 'size':size,'bold':bold,'color':color}

def slide(title,number,seconds,talk,body=None):
 s={'boxes':[box(title,x=67.2,y=48,w=1152,h=96,size=45.33,bold=True),
             box('Midpoint • October 28, 2026',y=672,w=700,h=24,size=14.67,color=ACCENT),
             box(str(number),x=1180,y=672,w=40,h=24,size=14.67,color=ACCENT)],
    'table':None,'notes':f'Target time: {seconds} seconds.\n{talk}', 'seconds':seconds}
 if body:s['boxes'].insert(1,box(body))
 return s

source='Sources: Original proposal (slides 2, 4–8); reports/runs/mcphases_2022/metrics.csv and cleaning_audit.json; reports/midpoint_checkpoint.md. Dataset: https://physionet.org/content/mcphases/1.0.0/.'
slides=[]
s=slide('Predicting menstrual pain',1,20,
 'We are Alina Kapanova, Fiona Wang and Vicky Wang. Our project asks whether health and lifestyle information can anticipate menstrual pain. This checkpoint covers our dataset, completed analysis, initial results and remaining work. We now have real participant-held-out results. '+source)
s['boxes'] += [box('Using health and lifestyle factors',y=201.6,h=124.8,size=45.33,color=ACCENT),
                 box('Alina Kapanova · Fiona Wang · Vicky Wang',y=403.2,h=96,size=34.67),
                 box('Midcheckpoint presentation',y=537.6,h=57.6,size=29.33)]
slides.append(s)
slides.append(slide('Background',2,50,
 'Menstrual pain varies across people and cycles and can interfere with daily activities. Our original proposal asks whether sleep, stress, physical activity, physiology and menstrual history can predict severity. We made this concrete as a retrospective one-day-ahead task: predict day t from information recorded on exact day t−1. We map Not at all, Very Low/Little and Low to class zero, and Moderate, High and Very High to class one. This is a project threshold, not a clinical cutoff. We compare logistic regression, decision tree and random forest against simple baselines and hold out complete people to assess generalization. '+source,
 ['Problem: menstrual pain varies across people and cycles.',
  'Goal: anticipate moderate-or-higher pain one day ahead.',
  'Approach: combine prior-day Fitbit signals and symptom history.',
  'Models: logistic regression, decision tree and random forest.']))
slides.append(slide('Dataset / sensing',3,65,
 'We use the existing mcPHASES v1.0.0 dataset, so our core project requires no new sensor collection. The download contains 23 CSV tables and 3.68 GB of files. The source study used Fitbit Sense, Mira hormone measurements and Dexcom G6 in the first interval. Our selected features come from Fitbit and daily diaries: sleep duration and quality, activity minutes, resting heart rate, HRV, breathing rate, nightly temperature, device stress and diary history. We processed nine tables into 21 prior-day predictors. The primary cohort includes 42 people and 3,320 labeled 2022 days. We excluded 378 first-round days without pain labels and never imputed outcomes. Only seven 2024 days have pain reports, so that interval cannot support a useful external test. The small Toronto cohort, missing sensor data and 15.6% positive prevalence limit generalization. '+source,
 ['mcPHASES: 42 participants, 23 tables, 3.68 GB uncompressed.',
  'Analysis: 3,320 labeled days from 2022; 15.6% positive.',
  'Fitbit Sense: sleep, activity, heart rate/HRV, temperature, breathing.',
  'Diary: pain, stress, mood, sleep difficulty and flow history.',
  'Bias: small Toronto cohort; only seven pain labels from 2024.']))
s=slide('Milestones / analysis',4,85,
 'This table ties our completed work to the proposal. Download and exploration were planned for October 9 but completed on October 24 after the access delay. Initial cleaning and feature construction, planned for October 23, were also completed on October 24; further sensitivity work remains. We verified labels and day keys, removed 3,601 duplicate stress records, filtered failed device scores and set measurements outside broad prespecified bounds to missing. Sleep is assigned to its end day, and all features are lagged by exactly one day. We never bridge missing days or the gap between study rounds, and we exclude retrospective phase labels. Median imputation and missingness filtering are learned inside each training fold. We have already implemented the three proposed models and evaluated them in five participant-held-out folds, ahead of the November model/evaluation milestones. Initial permutation importance, participant-cluster intervals and supported subgroup checks are complete, but final validation and interpretation are not. The optional pilot has not been collected or compared; we have deferred it. '+source)
s['table']=[['Proposal milestone','Completed by Oct 24','Issue / decision'],
 ['Download & explore\nOct 9','Inventory and schema check\nfor all 23 tables','Access delay; finished Oct 24'],
 ['Clean & engineer\nOct 23','21 prior-day predictors;\nfold-only imputation','Missing labels; duplicate\nand failed sensor records'],
 ['Implement models\nNov 13','Logistic regression, tree,\nforest + baselines','Class imbalance;\nfixed model settings'],
 ['Evaluate models\nNov 24','5 participant-held-out folds;\nparticipant-cluster intervals','Avoid sharing people\nbetween train and test'],
 ['Interpret & audit bias\nDec 2','Initial feature importance\nand supported subgroup audit','Small groups;\nexploratory findings']]
s['table_widths']=[280,480,363.2];s['table_font_size']=23
s['boxes'].append(box('Optional wearable pilot and pilot comparison: not completed; deferred.',y=628,h=35,size=23,color=ACCENT))
slides.append(s)
metrics=pd.read_csv(ROOT/'reports/runs/mcphases_2022/metrics.csv').set_index('model')
s=slide('Initial results',5,70,
 'These are pooled out-of-fold results from five participant-grouped folds. The previous-day pain baseline has the highest macro F1 at 0.781. Random forest is the strongest of the three full classifiers at 0.770, and logistic regression is 0.716. The forest and persistence have nearly equal balanced accuracy, about 0.773. Forest detects 320 of 517 moderate-or-higher days, but gives more false positives than persistence: 207 compared with 168. All three classifiers beat the majority baseline, but none beats pain history on macro F1. Wearable-only forest reaches 0.569, and previous pain dominates permutation importance. Two thousand paired participant-cluster bootstrap resamples give a forest-minus-persistence F1 interval of about −0.022 to −0.002, conditional on fixed predictions. The higher AUC of the full models is not proof of better decisions; persistence uses hard predictions. These results do not establish clinical validity or causality. '+source)
s['table']=[['Model / baseline','Macro F1','Balanced acc.','ROC-AUC']]
for model,label in [('majority','Majority class'),('flow_timing_proxy','Prior flow timing'),('previous_pain','Previous-day pain'),('logistic_regression','Logistic regression'),('decision_tree','Decision tree'),('random_forest','Random forest')]:
 r=metrics.loc[model];s['table'].append([label,f'{r.macro_f1:.3f}',f'{r.balanced_accuracy:.3f}',f'{r.roc_auc:.3f}'])
s['table_widths']=[480,205,235,203.2];s['table_font_size']=24
s['boxes'].append(box('Added features have not beaten pain history on macro F1; wearables-only F1 = 0.569.',y=628,h=36,size=22.8,color=ACCENT))
slides.append(s)
s=slide('Next steps / discussion',6,70,
 'Our main challenge is demonstrating useful improvement beyond pain history. We also need to check missingness mechanisms, actual report availability and error differences across people. Supported ethnicity groups show different missed-pain rates, but the samples are too small for a fairness conclusion. Only one gender category meets our minimum participant count, and income is absent. Next we will inspect failures and imputation sensitivity by October 30, then review feature timing and use nested participant-grouped validation for any tuning by November 13. We will refine robustness and subgroup comparisons by November 24, freeze explainability and a reproducible rerun by December 2, and finish the report and presentation by December 4. These are proposed work allocations. The optional pilot remains outside the critical path. Because we have already inspected this cohort, it cannot later be called an untouched independent final test. We will report any limited or null benefit honestly. Thank you; we have two minutes for questions. '+source)
s['boxes'].insert(1,box(['Problems: missing data, uncertain timing and no gain over pain history.',
                       'Next: inspect errors and sensitivity; validate any new features with grouped CV.'],y=152,h=100,size=26))
s['table']=[['Target in 2026','Next milestone','Proposed owner'],
 ['Oct 30','Error and missingness sensitivity','Vicky + Alina'],
 ['Nov 13','Timing review; nested grouped evaluation','Alina + Vicky'],
 ['Nov 24','Robustness and subgroup follow-up','Alina + Fiona'],
 ['Dec 2–4','Explainability, final rerun, report and slides','All']]
s['table_position']={'left':76.8,'top':292,'width':1123.2,'height':304}
s['table_widths']=[170,640,313.2];s['table_font_size']=23.5
s['boxes'].append(box('Pilot deferred; no independent final test cohort yet. Final deadline: Dec 4.',y=623,h=40,size=23,color=ACCENT))
slides.append(s)
assert len(slides)==6 and sum(s['seconds'] for s in slides)==360
(ROOT/'scripts/midpoint_six_sections.json').write_text(json.dumps(slides,indent=2)+'\n')
notes='# Midcheckpoint speaker notes — October 28, 2026\n\nSix slides, six minutes, followed by two minutes of questions. Model results are from the October 24 real-data run.\n\n'
notes+='\n\n'.join(f'## {i}. {s["boxes"][0]["paragraphs"][0]}\n\n{s["notes"]}' for i,s in enumerate(slides,1))
notes+='''\n\n## Two-minute Q&A prompts\n\n- Why split by person? Daily records from the same person in train and test would overstate generalization.\n- Why exclude 2024? It has only seven observed pain outcomes.\n- Do wearables improve the prediction? The current models do not beat previous-day pain on macro F1.\n- What has changed from the proposal? The target is binary, 2022 is the primary cohort, retrospective phase labels are excluded, and the optional pilot is deferred.\n- Is this clinically validated? No. This is retrospective exploratory evaluation, with no independent final test cohort.\n'''
(ROOT/'output/presentation/midpoint_six_sections_notes.md').write_text(notes)
print('Prepared six sections; total speaking time 360 seconds.')
