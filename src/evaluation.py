"""Participant-cluster uncertainty, coverage sensitivity and exploratory subgroup audit."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from src.pipeline import score, write_json


def metrics_from_counts(counts):
    tn, fp, fn, tp = np.moveaxis(np.asarray(counts, dtype=float), -1, 0)
    with np.errstate(invalid='ignore', divide='ignore'):
        f1 = .5 * (2*tp/(2*tp+fp+fn) + 2*tn/(2*tn+fp+fn))
        ba = .5 * (tp/(tp+fn) + tn/(tn+fp))
    return f1, ba


def evaluate(run_dir, raw, reps=2000):
    run_dir = Path(run_dir)
    predictions = pd.read_csv(run_dir / 'predictions_private.csv', dtype={'id':'string'})
    forecast = pd.read_csv(run_dir / 'forecast_private.csv', dtype={'id':'string'})
    people = sorted(predictions.id.unique())
    if predictions.groupby('id').fold.nunique().max() != 1:
        raise ValueError('A participant appears in multiple test folds')
    counts = {}
    for model, df in predictions.groupby('model'):
        if df.duplicated(['id','day']).any() or len(df) != len(forecast):
            raise ValueError('Invalid out-of-fold prediction coverage')
        counts[model] = np.array([confusion_matrix(g.target, g.predicted, labels=[0,1]).ravel()
                                 for _, g in df.groupby('id', sort=True)])
    rng = np.random.default_rng(42)
    weights = rng.multinomial(len(people), np.ones(len(people))/len(people), size=reps)
    boot, intervals = {}, []
    for model, cm in counts.items():
        f1, ba = metrics_from_counts(weights @ cm)
        boot[model] = {'macro_f1': f1, 'balanced_accuracy': ba}
        for metric, values in boot[model].items():
            low, high = np.nanpercentile(values, [2.5,97.5])
            intervals.append({'model':model,'metric':metric,'ci_low':float(low),'ci_high':float(high)})
    pd.DataFrame(intervals).to_csv(run_dir / 'confidence_intervals.csv', index=False)
    paired = []
    for model in ['random_forest','logistic_regression','random_forest_wearables_only']:
        for metric in ['macro_f1','balanced_accuracy']:
            d = boot[model][metric]-boot['previous_pain'][metric]
            low, high = np.nanpercentile(d,[2.5,97.5])
            paired.append({'model':model,'baseline':'previous_pain','metric':metric,
                           'delta_ci_low':float(low),'delta_ci_high':float(high)})
    pd.DataFrame(paired).to_csv(run_dir / 'paired_baseline_differences.csv', index=False)
    # Coverage sensitivity uses the existing fixed OOF predictions; no new training or tuning.
    covered = predictions.merge(forecast[['id','day','previous_pain']],on=['id','day'],validate='many_to_one')
    coverage = []
    for model, g in covered[covered.previous_pain.notna()].groupby('model'):
        coverage.append({'model':model,'labeled_days':len(g),'participants':g.id.nunique(),
                         **score(g.target,g.predicted,g.probability)})
    pd.DataFrame(coverage).to_csv(run_dir / 'sensitivity_prior_pain_available.csv',index=False)
    subjects = pd.read_csv(Path(raw)/'subject-info.csv',dtype={'id':'string'})
    predictions = predictions.merge(subjects,on='id',validate='many_to_one')
    subgroup = []
    suppressed = {}
    for field in ['gender','ethnicity','education']:
        supported = set(subjects.groupby(field).id.nunique().loc[lambda x:x>=5].index)
        suppressed[field] = int(subjects[field].nunique()-len(supported))
        for model in ['random_forest','previous_pain']:
            for group,g in predictions[(predictions.model==model)&predictions[field].isin(supported)].groupby(field):
                tn,fp,fn,tp = confusion_matrix(g.target,g.predicted,labels=[0,1]).ravel()
                if min(tn+fp,fn+tp)<10:
                    continue
                subgroup.append({'field':field,'group':group,'model':model,'participants':int(g.id.nunique()),
                                 'labeled_days':len(g),'positive_days':int(g.target.sum()),
                                 'false_positive_rate':float(fp/(tn+fp)), 'false_negative_rate':float(fn/(fn+tp)),
                                 **score(g.target,g.predicted,g.probability)})
    pd.DataFrame(subgroup).to_csv(run_dir / 'subgroup_metrics.csv',index=False)
    info={'bootstrap_replicates':reps,'resampling_unit':'participant, paired across models',
          'intervals':'percentile 95% intervals conditional on fixed OOF predictions; does not refit models',
          'subgroup_min_participants':5,'subgroup_min_each_outcome_days':10,
          'suppressed_small_group_counts':suppressed,
          'limitations':['Subgroups are exploratory; repeated days are not independent participants.',
                         'Only one gender category has >=5 participants; a reliable gender comparison is unavailable.',
                         'Income is described in README but absent from the supplied subject-info columns.',
                         'No independent final test cohort; no causal interpretation.']}
    write_json(run_dir / 'evaluation_notes.json',info)
    return info


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--run',default='reports/runs/mcphases_2022')
    p.add_argument('--raw',help='Defaults to raw_directory recorded in the run summary')
    args=p.parse_args()
    if args.raw is None:
        args.raw=json.loads((Path(args.run)/'summary.json').read_text())['raw_directory']
    print(json.dumps(evaluate(args.run,args.raw),indent=2))
