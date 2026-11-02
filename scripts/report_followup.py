"""Generate aggregate report and strengthened presentation content from frozen follow-up outputs."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'reports/runs/wearable_followup'
m=pd.read_csv(RUN/'metrics.csv')
ci=pd.read_csv(RUN/'paired_differences.csv')
summary=json.loads((RUN/'summary.json').read_text())
labels={'rf_history':'RF: previous pain only','rf_wearables':'RF: wearables only',
 'rf_history_wearables':'RF: previous pain + wearables','rf_all':'RF: all features',
 'persistence':'Previous-day pain rule','majority':'Majority class'}
order=list(labels)

def subset(scope):return m[m.scope==scope].set_index('model')
a=subset('all_days');o=subset('new_onset')
rows=[]
for k in order:
 r=a.loc[k];rows.append(f'| {labels[k]} | {r.macro_f1:.3f} | {r.average_precision:.3f} | {r.precision:.1%} | {r.recall:.1%} | {r.false_alarms_per_100_days:.2f} |')
onsets=[]
for k in order:
 r=o.loc[k];onsets.append(f'| {labels[k]} | {int(r.tp)} / 177 | {int(r.fp)} | {r.precision:.1%} | {r.recall:.1%} | {r.average_precision:.3f} | {r.false_alarms_per_100_days:.2f} |')
report=f'''# Wearable contribution and new-onset follow-up

Completed October 29, 2026. These are **exploratory follow-up analyses on an already inspected cohort**, not an independent confirmation. Original October 24 results are preserved.

## What was added

1. A matched feature-set comparison using the same random forest and participant folds.
2. A secondary analysis of pain onset after a day with observed no/low pain.
3. Precision, recall, average precision, precision–recall curves and false alarms per 100 evaluated days.
4. A descriptive coverage check using a prespecified threshold of at least 80% observed wearable predictors.

No temporal-trend features, new data collection, hyperparameter search or threshold optimization were introduced.

## Matched model design

All four forests use the same 42 participants, 3,320 labeled 2022 days, five participant-grouped folds, random seed, hyperparameters and training-fold preprocessing. The only intended change is the predictor set:

- Previous pain only: one predictor.
- Wearables only: 15 predictors.
- Previous pain + wearables: 16 predictors.
- All features: 21 predictors, adding diary stress, mood, sleep difficulty and flow history.

The 21-feature forest exactly reproduces the original out-of-fold probabilities, and fold assignments match the original evaluation. Filtering and imputation are fitted within training folds. Each forest uses 200 trees, maximum depth 6, minimum leaf size 5, balanced-subsample class weights and random state 42. All use the estimator's default decision rule. The fixed hyperparameter values are identical, including the default feature-subsampling rule; that rule naturally draws from different available predictor counts.

## All-day results

| Model / feature set | Macro F1 | Average precision | Precision | Recall | False alarms / 100 days |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

The positive prevalence is 0.156. Average precision (AP) summarizes the precision–recall ranking; it is not accuracy and does not establish calibrated clinical risk.

**Matched wearable contribution:** adding wearables to the previous-pain forest increases AP from **0.460 to 0.512** (difference +0.052). The paired participant-bootstrap 95% interval for this AP difference is approximately **[+0.007, +0.081]**, conditional on fixed OOF predictions. This provides exploratory evidence that the wearable feature package improves ranking. The package includes missingness indicators, so the result does not isolate physiological values from measurement-availability patterns.

At the default operating rule, macro F1 decreases from **0.781 to 0.760**, recall decreases from **60.5% to 59.2%**, and false alarms increase from **5.06 to 6.20 per 100 days**. Therefore, ranking improves while the current classification decisions do not improve overall. The all-feature forest reaches AP 0.555 and F1 0.770; its additional gain cannot be attributed exclusively to wearables because diary features are also included.

## New pain onset: a harder secondary question

Eligibility is determined only from **observed previous-day no/low pain**, not from today's outcome. There are **2,603 eligible days** across 42 participants and **177 positive onsets** (6.8%). These are day-level transitions, not counts of independent episodes or unique cycles. We evaluate the existing all-day-trained models on this subset; we do not retrain onset-specific classifiers.

| Model / feature set | Detected onsets | False alarms | Precision | Recall | Average precision | False alarms / 100 eligible days |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(onsets)}

The persistence rule predicts no/low pain throughout this subset, so it detects no onsets. The history-plus-wearables forest detects **10 of 177** with **44 false alarms**: **18.5% precision**, **5.6% recall**, and **1.69 false alarms per 100 eligible days**. Its AP is **0.102**, versus **0.068** for the matched history-only forest. The paired conditional 95% interval for the AP difference is approximately **[+0.006, +0.082]**.

The wearable-only forest detects more onsets (**38**) but produces many more false alarms (**302**), with **11.2% precision**. The all-feature forest detects **8** with **41** false alarms; its AP is **0.117**, including contributions from non-wearable diary predictors. The low onset recall and false-alarm burden prevent a claim of practical readiness.

The learned history-only forest produces slightly different scores across folds, so its pooled onset AP can differ slightly from the constant-rule prevalence reference. Neither historical pain model distinguishes onset days usefully at its current decision rule.

## Coverage sensitivity

There are 2,885 target days with at least 80% of the 15 wearable values observed and 435 with less coverage. Using the same fixed OOF predictions:

- At least 80% observed: history-plus-wearables AP **0.526**, history-only AP **0.469**; wearable-only AP **0.228**.
- Below 80% observed: history-plus-wearables AP **0.408**, history-only AP **0.391**; wearable-only AP **0.157**.

These are descriptive subcohort results. Different participants, outcome prevalence, data availability and adherence may explain some differences; they do not prove missingness causes poor predictions. No coverage threshold was selected to maximize performance.

## Uncertainty and validation boundaries

We resample participants with replacement 2,000 times, paired across models. Intervals condition on fixed OOF predictions and do not refit models. Code verifies that participants do not cross folds, the full forest reproduces the original run, and the matched models share the same target days. New tests check onset eligibility, metric denominators, no-alert baselines and weighted AP with tied scores. **Twelve tests pass.**

Because these comparisons were motivated after the original results were inspected, they are exploratory. They do not create a new untouched test cohort, establish a causal effect of physiology, or show calibrated clinical risk. A useful future operating threshold would require training-only selection; none was selected here.

## Updated conclusion

**Wearable features add modest ranking information beyond previous-day pain and detect a small number of new onsets in this exploratory evaluation. They do not improve overall macro F1 at the current decision rule, and onset detection remains limited.**

The completed work now answers both the broad prediction question and the more specific question of incremental wearable contribution. Finalization tasks remain limited to checking outputs, polishing figures and explanations, completing the written report, rehearsal and submission, all due November 30, 2026. No new major modeling or sensing milestone is introduced.

## Reproduce

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m src.followup
.venv/bin/python scripts/report_followup.py
```

Detailed and participant-level outputs are in ignored `reports/runs/wearable_followup/`. Aggregate scores and provenance are also saved in `reports/followup_results.json`. Precision–recall figures are `all_days_precision_recall.png` and `new_onset_precision_recall.png` in the run directory.
'''
(ROOT/'reports/wearable_followup.md').write_text(report)
(ROOT/'reports/followup_results.json').write_text(json.dumps({'date':'2026-10-29',
 'status':summary['status'],'all_days':a.reset_index().to_dict('records'),
 'new_onset':o.reset_index().to_dict('records'),'paired_differences':ci.to_dict('records'),
 'limitations':summary['limitations']},indent=2)+'\n')

# Update presentation copies without altering the October 24 comparison.
slides=json.loads((ROOT/'scripts/midpoint_richer.json').read_text())
for s in slides:
 for b in s['boxes']:b['paragraphs']=[t.replace('October 28, 2026','October 29, 2026') for t in b['paragraphs']]
 s['notes']=s['notes'].replace('Eight targeted tests pass','Twelve targeted tests pass')

s=slides[5]
s['boxes'][0]['paragraphs']=['Matched models show added ranking information']
s['chart']['categories']=['Wearables only','Previous pain only','Previous pain + wearables','All features']
s['chart']['values']=[round(a.loc[k,'average_precision'],6) for k in ['rf_wearables','rf_history','rf_history_wearables','rf_all']]
s['chart']['series_name']='Average precision'
for b in s['boxes']:
 if b['y']==625:b['paragraphs']=['AP improves 0.460 → 0.512 with wearables; macro F1 decreases 0.781 → 0.760.'];b['size']=22
s['notes']='Target time: 50 seconds.\nThis is the same random forest, preprocessing, participants and five folds, with feature sets changed. Adding wearables to previous pain increases average precision from 0.460 to 0.512, with a paired conditional bootstrap interval about +0.007 to +0.081. Macro F1 falls from 0.781 to 0.760 at the default rule, so ranking improves without better overall classifications. All features reach AP 0.555, but that also includes diary predictors. Missingness indicators are part of the feature package. These are exploratory follow-ups after inspecting the initial cohort. Source: reports/wearable_followup.md.'

s=slides[6]
s.pop('chart',None)
s['boxes']=[b for b in s['boxes'] if b['y']<100 or b['y']>=660]
s['boxes'][0]['paragraphs']=['Can wearables anticipate new pain onset?']
s['boxes'].insert(1,{'x':76.8,'y':150,'w':1123.2,'h':45,'paragraphs':['2,603 days after no/low pain • 177 new onsets (6.8%)'],'size':28,'bold':False,'color':'#24342E'})
s['table']=[['Same RF feature set','Detected / 177','False alarms'],
 ['Previous pain only','0','0'],['Previous pain + wearables','10','44'],['Wearables only','38','302'],['All features','8','41']]
s['table_widths']=[620,250,253.2];s['table_font_size']=26
s['table_position']={'left':76.8,'top':215,'width':1123.2,'height':375}
s['boxes'].append({'x':76.8,'y':625,'w':1123.2,'h':37,'paragraphs':['History + wearables: 18.5% precision, 5.6% recall; detection remains limited.'],'size':22.5,'bold':False,'color':'#29695B'})
s['notes']='Target time: 40 seconds.\nWe evaluated existing OOF predictions only on days preceded by observed no/low pain. There are 177 onsets among 2,603 eligible days. Persistence and the history-only forest detect none. Adding wearables catches 10 but generates 44 false alarms: precision 18.5 percent and recall 5.6 percent. Wearables alone find 38 at the cost of 302 false alarms. Thus there is some additional signal, but onset detection is weak and there is a trade-off. No onset-specific model or threshold was tuned. This is secondary exploratory analysis. Source: reports/wearable_followup.md.'

s=slides[8]
for b in s['boxes']:
 b['paragraphs']=[t.replace('Finding: additional features have not improved macro F1 over pain history.',
 'Finding: wearables improve ranking; overall macro F1 remains below pain history.') for t in b['paragraphs']]
s['notes']='Target time: 30 seconds.\nThe complete analysis now isolates wearable contribution with matched forests and tests new onset. Wearables provide a modest ranking benefit beyond history, but current overall macro F1 is lower and onset recall remains limited. All follow-ups reuse the previously inspected cohort and are exploratory. The completed comparisons strengthen the answer without claiming practical or clinical readiness. Remaining work stays final checks, figure explanations, report preparation and submission, due November 30. Source: reports/wearable_followup.md.'
(ROOT/'scripts/midpoint_strengthened.json').write_text(json.dumps(slides,indent=2)+'\n')
(ROOT/'output/presentation/midpoint_strengthened_notes.md').write_text('# Strengthened midpoint — six-minute speaker notes\n\n'+'\n\n'.join(f'## Slide {i}\n\n{s["notes"]}' for i,s in enumerate(slides,1))+'\n')
assert sum(s['seconds'] for s in slides)==360
print(ROOT/'reports/wearable_followup.md')
