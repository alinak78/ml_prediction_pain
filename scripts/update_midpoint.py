"""Update the editable presentation content from the aggregate real-data metrics."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
metrics=pd.read_csv(ROOT/'reports/runs/mcphases_2022/metrics.csv').set_index('model')
content=json.loads((ROOT/'scripts/midpoint_content.json').read_text())
for i, slide in enumerate(content,1):
 for b in slide['boxes']:
  b['paragraphs']=[v.replace('October 22, 2026','October 24, 2026') for v in b['paragraphs']]
 # Drop slide-number spaces from text footer; split into separate aligned text for clarity.
 for b in slide['boxes']:
  if b['y']==672:
   b['paragraphs']=['Midpoint • October 24, 2026']
   b['w']=650
 slide['boxes'].append({'x':1180,'y':672,'w':40,'h':24,'paragraphs':[str(i)],'size':14.67,'bold':False,'color':'#29695B'})

def replace_slide(index,title,lines,notes,seconds):
 slide=content[index]
 slide['boxes'][0]['paragraphs']=[title]
 # Keep title/footer and replace body box.
 slide['boxes']=[b for b in slide['boxes'] if b['y']<100 or b['y']>=660]
 if lines:
  slide['boxes'].insert(1,{'x':76.8,'y':172.8,'w':1123.2,'h':450,'paragraphs':lines,'size':32,'bold':False,'color':'#24342E'})
 slide['notes']=f'Target time: {seconds} seconds.\n{notes}\nSource: reports/midpoint_checkpoint.md; reports/runs/mcphases_2022/metrics.csv; downloaded mcPHASES v1.0.0 README. Dataset: https://physionet.org/content/mcphases/1.0.0/'
 slide['table']=None

# Title keeps the established cover composition.
for b in content[0]['boxes']:
 b['paragraphs']=[v.replace('Implementation checkpoint • Real-data evaluation pending','Real-data checkpoint • Participant-held-out evaluation') for v in b['paragraphs']]
content[0]['notes']='Target time: 20 seconds.\nIntroduce Alina Kapanova, Fiona Wang and Vicky Wang. We have processed mcPHASES and run the first real models. The main finding is that previous pain is a strong baseline and the extra features have not yet improved macro F1. Source: reports/midpoint_checkpoint.md.'

replace_slide(1,'Problem and approach',[
 'Can prior-day signals predict next-day menstrual cramp severity?',
 'Target: no/low versus moderate-or-higher pain.',
 'Combine Fitbit measurements with diary and flow history.',
 'Compare three classifiers with simple baselines on unseen participants.'
], 'Pain varies across people and cycles. We predict day t from exact day t−1 information. Not at all, Very Low/Little and Low are class zero; Moderate, High and Very High are class one. This mapping is a project convention, not a clinical threshold. The task is retrospective and assumes prior-day data were available; deployment latency is not established. This is feasibility research, not a diagnostic system.',45)

replace_slide(2,'mcPHASES: dataset and sensing',[
 '23 CSV tables; 3.68 GB uncompressed; Fitbit Sense and daily diaries.',
 '42 participants; 5,659 diary days across two study intervals.',
 'Primary analysis: 3,320 labeled days from 2022.',
 '517 moderate-or-higher days (15.6%); 2024 has only 7 labeled days.',
 'Small Toronto-area cohort limits generalization.'
], 'The full source study also used Mira hormone measurements and Dexcom G6 in interval one. We use nine source tables for 21 prior-day predictors: activity, sleep, physiology and diary history. There are 110.1 million records across all tables, mostly repeated sensor samples, not independent participants. Of 3,698 first-round diary days, 378 lack pain labels and are excluded. Only seven second-round days have cramp responses, so we exclude 2024 from the primary analysis. No new sensor pilot has been collected. Recent hormonal contraception and diabetes were exclusion criteria.',60)

replace_slide(3,'Completed processing and analysis',[
 'Verified labels and daily keys; excluded missing pain outcomes.',
 'Filtered failed sensor values and duplicate stress-score records.',
 'Built 21 exact prior-day predictors; excluded retrospective phase labels.',
 'Ran five folds grouped by participant; preprocessing fitted within folds.',
 'Added baseline checks, feature ablations, uncertainty and bias audits.'
], 'Main milestones are now complete through initial evaluation. We read the actual files and codebook. Main sleep uses its end day; distinct repeated daily summaries use median values. We removed 3,601 exact duplicate first-round Fitbit stress records and invalid zero/failed scores. Broad prespecified bounds set 782 resting heart-rate values, 53 respiratory measurements and 7 HRV records to missing. HRV requires coverage at least 0.8. Feature missingness is 1.2 to 44.0 percent. Exact day joins avoid crossing gaps. We never impute pain, and imputation/filtering use training folds only. Eight tests pass. Hyperparameters were fixed; no independent final test set exists.',60)

replace_slide(4,'Pain history remains the strongest baseline',[],
 'These are pooled out-of-fold scores from five participant-grouped folds. Persistence macro F1 is 0.781; forest is 0.770, so the added features have not beaten the simple baseline. Forest and persistence balanced accuracies both round to 0.773. Logistic and forest AUCs are about 0.83, but persistence uses hard predictions rather than a full probability ranking. A forest restricted to wearables reaches only 0.569 F1; a logistic model without previous pain reaches 0.581. Previous pain dominates held-out permutation importance. Two thousand participant-cluster bootstrap resamples give F1 intervals 0.716–0.826 for persistence and 0.699–0.821 for forest; the paired difference is about −0.010 with interval −0.022 to −0.002. These intervals condition on fixed OOF predictions. Forest catches 320 of 517 moderate-or-higher days and misses 197. Do not claim wearable value, clinical validity or causality.',80)
rows=[['Model / baseline','Macro F1','Balanced acc.','ROC-AUC']]
for key,label in [('majority','Majority class'),('flow_timing_proxy','Prior flow timing'),('previous_pain','Previous-day pain'),('logistic_regression','Logistic regression'),('decision_tree','Decision tree'),('random_forest','Random forest')]:
 r=metrics.loc[key];rows.append([label,f'{r.macro_f1:.3f}',f'{r.balanced_accuracy:.3f}',f'{r.roc_auc:.3f}'])
content[4]['table']=rows
content[4]['table_widths']=[480,205,235,203.2]
content[4]['table_font_size']=24
content[4]['boxes'].append({'x':76.8,'y':628,'w':1123.2,'h':36,'paragraphs':['Wearables-only forest: F1 0.569. No improvement over pain history yet.'],'size':23,'bold':False,'color':'#29695B'})

replace_slide(5,'Revised milestone timeline',[],
 'These are proposed team allocations and dates in 2026. Data processing and initial grouped evaluation are complete on October 24. Next inspect missingness and errors, review prospective feature timing, and use nested grouped validation for any tuning. The optional pilot remains outside the core path until a feasible protocol and devices exist. All team members review the final output.',55)
content[5]['table']=[['Target','Deliverable','Proposed owner'],
 ['Oct 24 ✓','Data processing + first models complete','Team'],
 ['Oct 30','Error and missingness sensitivity','Vicky + Alina'],
 ['Nov 6–13','Timing review; nested grouped validation','Alina + Vicky'],
 ['Nov 24','Robustness and subgroup follow-up','Alina + Fiona'],
 ['Dec 2','Explainability and frozen final rerun','Alina + Vicky'],
 ['Dec 4','Final report and presentation','All']]

replace_slide(6,'Discussion and next steps',[
 'No model has beaten previous-day pain on macro F1.',
 'Check forecast timing, missingness and failure cases before tuning.',
 'Subgroup error gaps are exploratory; gender comparisons lack support.',
 'Use nested grouped evaluation; no independent final test cohort yet.',
 'Next goal: test whether additional signals offer useful improvement.'
], 'Among supported ethnicity groups, forest false-negative rates range roughly 26 to 59 percent. Minimum group size is five participants and ten days of each class; these estimates are exploratory. Only Woman has at least five participants, so gender comparisons are unsupported. Income is absent in the downloaded demographic table despite the README mentioning it. The 2024 interval has only seven labels and cannot serve as a useful external test here. The full cohort has now been inspected; further work cannot call it an untouched final holdout. A limited or null wearable benefit is a valid finding. Stop at six minutes and allow two minutes for questions.',40)

(ROOT/'scripts/midpoint_content.json').write_text(json.dumps(content,indent=2)+'\n')
(ROOT/'output/presentation/speaker_notes.md').write_text('# Six-minute midpoint presentation — October 24, 2026\n\n'+'\n\n'.join(f'## Slide {i}\n\n{s["notes"]}' for i,s in enumerate(content,1))+'\n')
