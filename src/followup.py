"""Exploratory matched feature ablations and pain-onset evaluation.

Reuses the frozen October 24 cohort and participant folds. No feature search,
threshold tuning, or temporal features are introduced. Outputs remain separate.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (average_precision_score, confusion_matrix,
                             precision_recall_curve, roc_auc_score)
from sklearn.model_selection import GroupKFold

from src.pipeline import KEY, model_pipeline, write_json, plt
from src.evaluation import metrics_from_counts

WEARABLES = ['sedentary_minutes_lag1', 'light_activity_minutes_lag1',
 'moderate_activity_minutes_lag1', 'vigorous_activity_minutes_lag1',
 'resting_hr_lag1', 'sleep_minutes_lag1', 'sleep_awake_minutes_lag1',
 'sleep_efficiency_lag1', 'sleep_score_lag1', 'deep_sleep_minutes_lag1',
 'sleep_restlessness_lag1', 'nightly_temperature_lag1',
 'respiratory_rate_lag1', 'hrv_rmssd_lag1', 'fitbit_stress_score_lag1']
NAMES = {'persistence': 'Previous-day pain rule', 'majority': 'Majority class',
 'rf_history': 'RF: previous pain only', 'rf_wearables': 'RF: wearables only',
 'rf_history_wearables': 'RF: previous pain + wearables', 'rf_all': 'RF: all features'}


def onset_mask(frame):
    """Eligibility uses only observed previous-day information, never today's label."""
    return frame.previous_pain.notna() & frame.previous_pain.eq(0)


def operational_metrics(y, pred, probability):
    y, pred, probability = np.asarray(y), np.asarray(pred), np.asarray(probability)
    if len(y) == 0:
        raise ValueError('No evaluation observations')
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    f1, ba = metrics_from_counts([tn, fp, fn, tp])
    return {'labeled_days': int(len(y)), 'positive_days': int(y.sum()),
        'positive_prevalence': float(y.mean()), 'macro_f1': float(f1),
        'balanced_accuracy': float(ba) if np.isfinite(ba) else None,
        'precision': float(tp/(tp+fp)) if tp+fp else 0.,
        'recall': float(tp/(tp+fn)) if tp+fn else None,
        'average_precision': float(average_precision_score(y, probability)) if y.sum() else None,
        'roc_auc': float(roc_auc_score(y, probability)) if len(np.unique(y))==2 else None,
        'false_alarms_per_100_days': float(100*fp/len(y)),
        'false_positive_rate': float(fp/(tn+fp)) if tn+fp else None,
        'tn':int(tn), 'fp':int(fp), 'fn':int(fn), 'tp':int(tp)}


def weighted_average_precision(y, probability, sample_weights):
    """Vectorized weighted AP, including tied scores, for fixed OOF bootstrap draws."""
    y, probability = np.asarray(y), np.asarray(probability)
    order = np.argsort(-probability, kind='stable')
    ends = np.r_[np.flatnonzero(np.diff(probability[order])), len(y)-1]
    weights = np.atleast_2d(sample_weights)[:, order]
    true = np.cumsum(weights * y[order], axis=1)[:, ends]
    total = np.cumsum(weights, axis=1)[:, ends]
    increments = np.diff(np.c_[np.zeros(len(weights)), true], axis=1)
    precision = np.divide(true, total, out=np.zeros_like(true, dtype=float), where=total>0)
    positives = true[:, -1]
    result = np.divide((precision*increments).sum(axis=1), positives,
                       out=np.full(len(weights), np.nan), where=positives>0)
    return result


def cluster_intervals(predictions, reps=2000):
    people = sorted(predictions.id.unique())
    weights = np.random.default_rng(42).multinomial(len(people),
                    np.ones(len(people))/len(people), size=reps)
    index = {person:i for i,person in enumerate(people)}
    rows, paired, draws = [], [], {}
    for scope in ['all_days', 'new_onset']:
        for name,g in predictions.groupby('model', sort=False):
            if scope=='new_onset': g=g[onset_mask(g)]
            codes = g.id.map(index).to_numpy()
            cm = np.zeros((len(people),4))
            cell = 2*g.target.to_numpy(int) + g.predicted.to_numpy(int)
            np.add.at(cm, (codes,cell),1)
            f1, ba = metrics_from_counts(weights@cm)
            ap = weighted_average_precision(g.target.to_numpy(),g.probability.to_numpy(),weights[:,codes])
            draws[scope,name] = {'macro_f1':f1,'balanced_accuracy':ba,'average_precision':ap}
            for metric,values in draws[scope,name].items():
                lo,hi=np.nanpercentile(values,[2.5,97.5])
                rows.append({'scope':scope,'model':name,'metric':metric,'ci_low':float(lo),'ci_high':float(hi)})
        for comparison,baseline in [('rf_history_wearables','rf_history'),('rf_all','rf_history'),
                                     ('rf_history_wearables','persistence')]:
            for metric in ['macro_f1','balanced_accuracy','average_precision']:
                diff=draws[scope,comparison][metric]-draws[scope,baseline][metric]
                lo,hi=np.nanpercentile(diff,[2.5,97.5])
                paired.append({'scope':scope,'model':comparison,'baseline':baseline,'metric':metric,
                               'delta_ci_low':float(lo),'delta_ci_high':float(hi)})
    return pd.DataFrame(rows),pd.DataFrame(paired)


def run_followup(source, output, reps=2000):
    source,output=Path(source),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    frame=pd.read_csv(source/'forecast_private.csv',dtype={'id':'string'})
    original=pd.read_csv(source/'predictions_private.csv',dtype={'id':'string'})
    if frame.duplicated(KEY).any(): raise ValueError('Duplicate forecast keys')
    features=[c for c in frame if c not in KEY+['pain']]
    sets={'rf_history':['previous_pain'], 'rf_wearables':WEARABLES,
          'rf_history_wearables':['previous_pain']+WEARABLES, 'rf_all':features}
    y=frame.pain.to_numpy(int)
    split=list(GroupKFold(n_splits=5).split(frame,y,frame.id))
    reference=original[original.model=='random_forest'].set_index(KEY).loc[pd.MultiIndex.from_frame(frame[KEY])]
    assignments=np.zeros(len(frame),dtype=int)
    template=RandomForestClassifier(n_estimators=200,max_depth=6,min_samples_leaf=5,
                  class_weight='balanced_subsample',random_state=42,n_jobs=-1)
    outputs=[]
    retained=[]
    for name,cols in sets.items():
        X=frame[cols].replace([np.inf,-np.inf],np.nan)
        pred,prob=np.zeros(len(y),dtype=int),np.zeros(len(y))
        for fold,(tr,te) in enumerate(split):
            if set(frame.id.iloc[tr])&set(frame.id.iloc[te]): raise ValueError('Participant leakage')
            assignments[te]=fold
            fitted=model_pipeline(clone(template)).fit(X.iloc[tr],y[tr])
            pred[te]=fitted.predict(X.iloc[te])
            prob[te]=fitted.predict_proba(X.iloc[te])[:,1]
            retained.extend({'model':name,'fold':fold,'feature':c}
                            for c in np.asarray(cols)[fitted['missingness'].keep_])
        outputs.append(frame[KEY+['previous_pain']].assign(fold=assignments,model=name,target=y,
                         predicted=pred,probability=prob,
                         wearable_observed_fraction=frame[WEARABLES].notna().mean(axis=1)))
    if not np.array_equal(assignments,reference.fold.to_numpy()):
        raise ValueError('Follow-up folds differ from original evaluation')
    for name,prior_name in [('majority','majority'),('persistence','previous_pain')]:
        g=original[original.model==prior_name].set_index(KEY).loc[pd.MultiIndex.from_frame(frame[KEY])]
        outputs.append(frame[KEY+['previous_pain']].assign(fold=assignments,model=name,target=y,
                 predicted=g.predicted.to_numpy(),probability=g.probability.to_numpy(),
                 wearable_observed_fraction=frame[WEARABLES].notna().mean(axis=1)))
    all_predictions=pd.concat(outputs,ignore_index=True)
    actual=all_predictions[all_predictions.model=='rf_all']
    if not np.allclose(actual.probability.to_numpy(),reference.probability.to_numpy(),rtol=0,atol=1e-12):
        raise ValueError('Full-feature model no longer reproduces the original forest')
    if not np.array_equal(actual.predicted.to_numpy(),reference.predicted.to_numpy()):
        raise ValueError('Full forest classifications differ from the original')
    if not np.array_equal(y,reference.target.to_numpy()):
        raise ValueError('Follow-up target labels differ from the original')
    all_predictions.to_csv(output/'predictions_private.csv',index=False)
    pd.DataFrame(retained).to_csv(output/'retained_features.csv',index=False)
    results=[]
    for name,g in all_predictions.groupby('model',sort=False):
        for scope,mask in [('all_days',np.ones(len(g),dtype=bool)),('new_onset',onset_mask(g)),
                           ('coverage_at_least_80pct',g.wearable_observed_fraction.ge(.8)),
                           ('coverage_below_80pct',g.wearable_observed_fraction.lt(.8))]:
            subset=g.loc[mask]
            if subset.empty:continue
            results.append({'scope':scope,'model':name,'participants':int(subset.id.nunique()),
                            **operational_metrics(subset.target,subset.predicted,subset.probability)})
    metrics=pd.DataFrame(results)
    metrics.to_csv(output/'metrics.csv',index=False)
    ci,paired=cluster_intervals(all_predictions,reps)
    ci.to_csv(output/'confidence_intervals.csv',index=False)
    paired.to_csv(output/'paired_differences.csv',index=False)
    for scope in ['all_days','new_onset']:
        fig,ax=plt.subplots(figsize=(8,5))
        for name,g in all_predictions.groupby('model',sort=False):
            if name=='majority':continue
            if scope=='new_onset':g=g[onset_mask(g)]
            p,r,_=precision_recall_curve(g.target,g.probability)
            row=metrics[(metrics.scope==scope)&(metrics.model==name)].iloc[0]
            ax.step(r,p,where='post',label=f'{NAMES[name]} (AP {row.average_precision:.3f})')
        baseline=metrics[metrics.scope==scope].positive_prevalence.iloc[0]
        ax.axhline(baseline,color='gray',ls='--',label=f'Prevalence {baseline:.3f}')
        ax.set(xlabel='Recall',ylabel='Precision',xlim=(0,1),ylim=(0,1),
               title='All labeled days' if scope=='all_days' else 'Secondary analysis: new pain onset')
        ax.legend(fontsize=8)
        fig.tight_layout();fig.savefig(output/f'{scope}_precision_recall.png',dpi=180);plt.close(fig)
    summary={'status':'EXPLORATORY_FOLLOWUP_ON_PREVIOUSLY_INSPECTED_COHORT',
     'source_run':str(source),'participants':int(frame.id.nunique()),'labeled_days':len(frame),
     'onset_eligible_days':int(onset_mask(frame).sum()),
     'onset_positive_days':int(frame.loc[onset_mask(frame),'pain'].sum()),
     'feature_sets':sets,'random_forest_parameters':template.get_params(),
     'folds_identical_to_original':True,'full_forest_reproduces_original':True,
     'bootstrap_replicates':reps,'decision_rule':'Each fitted estimator default predict; no threshold tuning.',
     'false_alarm_denominator':'100 evaluated days in each reported scope, not 100 negative days.',
     'onset_definition':'Observed previous-day no/low pain; today moderate-or-higher is a positive onset.',
     'average_precision':'Non-interpolated average precision; random-ranking reference is scope-specific prevalence.',
     'coverage_threshold':.8,'python_sklearn_version':sklearn.__version__,
     'input_sha256':hashlib.sha256((source/'forecast_private.csv').read_bytes()).hexdigest(),
     'original_predictions_sha256':hashlib.sha256((source/'predictions_private.csv').read_bytes()).hexdigest(),
     'analysis_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
     'limitations':['Secondary analyses defined after inspecting the original results; not confirmatory.',
       'Bootstrap resamples participants and conditions on fixed OOF predictions; models are not refitted.',
       'No independent test cohort or prospective validation; no causal interpretation.',
       'Coverage comparisons are descriptive and may reflect different participants or pain prevalence.',
       'Random-forest scores have not been calibrated as clinical probabilities.',
       'No temporal-trend features, model tuning or threshold optimization were added.']}
    write_json(output/'summary.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',default='reports/runs/mcphases_2022')
    p.add_argument('--output',default='reports/runs/wearable_followup')
    p.add_argument('--bootstrap-replicates',type=int,default=2000)
    args=p.parse_args()
    print(json.dumps(run_followup(args.source,args.output,args.bootstrap_replicates),indent=2))
