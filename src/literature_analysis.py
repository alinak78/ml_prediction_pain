"""Literature-motivated exploratory feature blocks on already inspected cohorts.

Preserves original labels/folds and fits preprocessing within training folds.
Never combines records from different studies or creates unmeasured constructs.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

from src.pipeline import KEY, model_pipeline, write_json
from src.mcphases import LIKERT, ordinal
from src.followup import operational_metrics, weighted_average_precision
from src.evaluation import metrics_from_counts
from src.mpis import baseline_features, estimator

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/runs/literature_factors'
SOMATIC = ['headaches', 'fatigue', 'bloating', 'indigestion', 'sorebreasts']
MC_BLOCKS = {
    'somatic': [c + '_lag1' for c in SOMATIC],
    'stress_mood': ['stress_lag1', 'moodswing_lag1'],
    'sleep': ['sleepissue_lag1', 'sleep_minutes_lag1', 'sleep_awake_minutes_lag1',
              'sleep_efficiency_lag1', 'sleep_score_lag1', 'deep_sleep_minutes_lag1', 'sleep_restlessness_lag1'],
    'activity': ['sedentary_minutes_lag1', 'light_activity_minutes_lag1',
                 'moderate_activity_minutes_lag1', 'vigorous_activity_minutes_lag1'],
    'bleeding': ['flow_lag1', 'days_since_observed_flow_lag1', 'days_since_confirmed_flow_onset_lag1'],
    'background': ['age_approx_2022', 'age_at_menarche'],
    'physiology': ['resting_hr_lag1', 'nightly_temperature_lag1', 'respiratory_rate_lag1',
                   'hrv_rmssd_lag1', 'fitbit_stress_score_lag1'],
}
CLINICAL_NUMERIC = {'menarche_age': 'Age at Menarche', 'cycle_length': 'Cycle Length',
                    'period_duration': 'Period Duration', 'live_births': 'Live Births'}
CLINICAL_CATEGORICAL = {'endometriosis_status': 'Endometriosis', 'adenomyosis_status': 'Adenomyosis',
                        'nonmenstrual_pain_frequency': 'Non-Menstrual Cycle Pain'}


def confirmed_onset_clock(daily):
    """Past-only clock since a transition to light-or-heavier flow on adjacent days.

    Spotting alone is not onset. Missing days/flow reset the clock because onset
    could have occurred in that gap. This is observed bleeding history, not phase.
    """
    clock = pd.Series(np.nan, index=daily.index, dtype=float)
    for _, group in daily.groupby('id', sort=False):
        previous_day = previous_flow = onset = None
        for i, row in group.sort_values('day').iterrows():
            if previous_day is None or row.day != previous_day + 1 or pd.isna(row.flow):
                onset = None
            if (previous_day is not None and row.day == previous_day + 1
                    and pd.notna(row.flow) and previous_flow is not None
                    and pd.notna(previous_flow) and previous_flow < 2 <= row.flow):
                onset = row.day
            if onset is not None:
                clock.at[i] = row.day - onset
            previous_day, previous_flow = row.day, row.flow
    return clock


def add_mc_features():
    source = ROOT / 'reports/runs/mcphases_2022'
    raw = Path(json.loads((source / 'summary.json').read_text())['raw_directory'])
    base = pd.read_csv(source / 'forecast_private.csv', dtype={'id': str})
    daily = pd.read_csv(source / 'daily_private.csv', dtype={'id': str})
    diary = pd.read_csv(raw / 'hormones_and_selfreport.csv', dtype={'id': str})
    diary = diary[diary.study_interval.eq(2022)].rename(columns={'day_in_study': 'day'})
    if diary.duplicated(KEY).any():
        raise ValueError('Duplicate original diary keys')
    additions = diary[KEY].copy()
    additions['previous_cramp_severity'] = ordinal(diary.cramps, LIKERT)
    for c in SOMATIC:
        additions[c + '_lag1'] = ordinal(diary[c], LIKERT)
    additions['day'] += 1
    clock = daily[KEY].assign(days_since_confirmed_flow_onset_lag1=confirmed_onset_clock(daily))
    clock['day'] += 1
    frame = base.merge(additions, on=KEY, how='left', validate='one_to_one').merge(clock, on=KEY, how='left', validate='one_to_one')
    subject = pd.read_csv(raw / 'subject-info.csv', dtype={'id': str})
    subject = subject[['id', 'birth_year', 'age_of_first_menarche']].rename(columns={'age_of_first_menarche': 'age_at_menarche'})
    if subject.id.duplicated().any():
        raise ValueError('Duplicate subject baseline key')
    subject['age_approx_2022'] = 2022 - subject.birth_year
    frame = frame.merge(subject.drop(columns='birth_year'), on='id', how='left', validate='many_to_one')
    known = frame.previous_cramp_severity.notna()
    if not np.array_equal(frame.loc[known, 'previous_pain'].to_numpy(), frame.loc[known, 'previous_cramp_severity'].ge(3).astype(int).to_numpy()):
        raise ValueError('Previous pain and original ordinal severity disagree')
    cols = [c for c in base if c not in KEY + ['pain']]
    full = ['previous_cramp_severity'] + [c for block in MC_BLOCKS.values() for c in block]
    assert len(set(full)) == len(full)
    specs = {'rf_history_binary': ['previous_pain'], 'rf_original21': cols,
             'rf_history_severity': ['previous_cramp_severity']}
    specs.update({f'rf_history_plus_{name}': ['previous_cramp_severity'] + block for name, block in MC_BLOCKS.items()})
    specs['rf_full'] = full
    specs.update({f'rf_full_without_{name}': [c for c in full if c not in block]
                  for name, block in MC_BLOCKS.items()})
    specs['rf_no_pain_history'] = full[1:]
    specs['lr_history_severity'] = ['previous_cramp_severity']
    specs['lr_full'] = full
    specs['lr_no_pain_history'] = full[1:]
    reference = pd.read_csv(source / 'predictions_private.csv', dtype={'id': str})
    reference = reference[reference.model.eq('random_forest')].set_index(KEY).loc[pd.MultiIndex.from_frame(frame[KEY])]
    splits = list(GroupKFold(n_splits=5).split(frame, frame.pain, frame.id))
    assignments = np.empty(len(frame), dtype=int)
    for fold, (_, test) in enumerate(splits):
        assignments[test] = fold
    if not np.array_equal(assignments, reference.fold.to_numpy()):
        raise ValueError('Original participant folds changed')
    source_hashes = {f: hashlib.sha256((raw / f).read_bytes()).hexdigest()
                     for f in ['hormones_and_selfreport.csv', 'subject-info.csv', 'height_and_weight.csv']}
    audit = {'participants': int(frame.id.nunique()), 'target_days': len(frame), 'positive_days': int(frame.pain.sum()),
             'feature_blocks': MC_BLOCKS, 'model_features': specs, 'source_sha256': source_hashes,
             'feature_nonmissing_days': {c:int(frame[c].notna().sum()) for c in full},
             'new_features': ['previous_cramp_severity'] + [c+'_lag1' for c in SOMATIC] +
                              ['days_since_confirmed_flow_onset_lag1', 'age_approx_2022', 'age_at_menarche'],
             'bmi_policy': '2022 height/weight lack collection timestamps and are incomplete; excluded from primary forecasting. MPIS baseline BMI remains available.',
             'timing_policy': 'All diary, sensor and bleeding clocks use exact t-1 joins; age and menarche age are historical fixed attributes.'}
    return frame, specs, splits, reference, audit


def run_mc():
    frame, specs, splits, reference, audit = add_mc_features()
    y = frame.pain.to_numpy(int)
    outputs, retained = [], []
    for name, columns in specs.items():
        template = (RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_leaf=5,
                        class_weight='balanced_subsample', random_state=42, n_jobs=-1)
                    if name.startswith('rf_') else LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42))
        scores, predictions, assignments = np.zeros(len(y)), np.zeros(len(y), dtype=int), np.zeros(len(y), dtype=int)
        for fold, (train, test) in enumerate(splits):
            if set(frame.id.iloc[train]) & set(frame.id.iloc[test]):
                raise ValueError('Participant overlap')
            fitted = model_pipeline(clone(template)).fit(frame.iloc[train][columns], y[train])
            kept = np.asarray(columns)[fitted['missingness'].keep_]
            retained.extend({'model': name, 'fold': fold, 'feature': c} for c in kept)
            scores[test] = fitted.predict_proba(frame.iloc[test][columns])[:, 1]
            predictions[test] = fitted.predict(frame.iloc[test][columns])
            assignments[test] = fold
        if name == 'rf_original21':
            if not np.allclose(scores, reference.probability, rtol=0, atol=1e-12) or not np.array_equal(predictions, reference.predicted):
                raise ValueError('Original full forest not reproduced')
        outputs.append(frame[KEY].assign(dataset='mcphases', model=name, target=y, predicted=predictions,
                                          score=scores, fold=assignments))
        print('Completed mcPHASES', name, flush=True)
    pred = pd.concat(outputs, ignore_index=True)
    frame.to_csv(OUT / 'mcphases_features_private.csv', index=False)
    pd.DataFrame(retained).to_csv(OUT / 'retained_features.csv', index=False)
    audit['retained_feature_folds'] = {name: group.groupby('feature').size().to_dict()
                                     for name, group in pd.DataFrame(retained).groupby('model')}
    return pred, audit


def clinical_features(baseline):
    result = baseline_features(baseline)
    for name, col in CLINICAL_NUMERIC.items():
        result[name] = pd.to_numeric(baseline[col], errors='raise').replace([-997, -998, -999], np.nan)
    for name, col in CLINICAL_CATEGORICAL.items():
        values = baseline[col].astype('string').str.strip()
        result[name] = values.mask(values.str.match(r'^-99[789](?:\.0+)?(?:\s*=|$)', na=False)).fillna('Missing').astype(str)
    return result


def run_mpis():
    from src.mpis import DIARY, CATEGORIES
    pairs = pd.read_csv(ROOT / 'reports/runs/mpis/forecast_private.csv', dtype={'id': str})
    base = pd.read_csv(ROOT / 'data/raw/external/mpis-21538147/final_upsurvey_data_labeled_mpisapp.csv', dtype={'unique_id': str})
    new = clinical_features(base)
    cols = ['id'] + list(CLINICAL_NUMERIC) + list(CLINICAL_CATEGORICAL)
    pairs = pairs.merge(new[cols], on='id', how='left', validate='many_to_one')
    outputs, specs = [], {}
    reference = pd.read_csv(ROOT / 'reports/runs/mpis/predictions_private.csv', dtype={'id': str})
    cn, cc = list(CLINICAL_NUMERIC), list(CLINICAL_CATEGORICAL)
    specs['lr_history'] = (['previous_nrs'], [])
    specs['lr_history_clinical'] = (['previous_nrs']+cn, cc)
    specs['lr_history_background_clinical'] = (['previous_nrs', 'bmi']+cn, CATEGORIES+cc)
    specs['lr_full_literature'] = (DIARY+['bmi']+cn, CATEGORIES+cc)
    specs['lr_no_pain_history'] = (DIARY[1:]+['bmi']+cn, CATEGORIES+cc)
    cohorts = {}
    for scope in ['control_only', 'preintervention_only']:
        data = pairs.loc[pairs[scope]].reset_index(drop=True)
        X = data[DIARY + ['bmi'] + CATEGORIES + cn + cc]
        y = data.target.to_numpy(int)
        cohorts[scope] = {'people': int(data.id.nunique()), 'days': len(data), 'positive': int(data.target.sum())}
        for name, (numeric, categorical) in specs.items():
            scores, predictions, fold_id = np.zeros(len(data)), np.zeros(len(data), dtype=int), np.zeros(len(data), dtype=int)
            for fold, (tr, te) in enumerate(LeaveOneGroupOut().split(X, y, data.id)):
                if set(data.id.iloc[tr]) & set(data.id.iloc[te]):
                    raise ValueError('Participant overlap')
                fitted = estimator('lr', numeric, categorical).fit(X.iloc[tr], y[tr])
                scores[te] = fitted.predict_proba(X.iloc[te])[:, 1]
                predictions[te] = fitted.predict(X.iloc[te])
                fold_id[te] = fold
            if name == 'lr_history':
                old = reference.loc[reference.scope.eq(scope) & reference.model.eq(name)].set_index(KEY).loc[pd.MultiIndex.from_frame(data[KEY])]
                if (not np.array_equal(y, old.target) or not np.array_equal(fold_id, old.fold)
                        or not np.array_equal(predictions, old.predicted)
                        or not np.allclose(scores, old.score, rtol=0, atol=1e-12)):
                    raise ValueError('Original MPIS history model not reproduced')
            outputs.append(data[KEY].assign(dataset='mpis_'+scope, model=name, target=y,
                           predicted=predictions, score=scores, fold=fold_id))
        print('Completed MPIS literature models', scope, flush=True)
    pairs.to_csv(OUT / 'mpis_features_private.csv', index=False)
    audit = {'cohorts': cohorts, 'clinical_numeric': CLINICAL_NUMERIC,
             'baseline_source_sha256': hashlib.sha256((ROOT / 'data/raw/external/mpis-21538147/final_upsurvey_data_labeled_mpisapp.csv').read_bytes()).hexdigest(),
             'clinical_categorical': CLINICAL_CATEGORICAL,
             'models': {k:{'numeric':v[0], 'categorical':v[1]} for k,v in specs.items()},
             'new_baseline_nonmissing_people': {k:int(new[k].notna().sum()) if k in cn else int(new[k].ne('Missing').sum()) for k in cn+cc},
             'policy': 'Original observed-only pairs, original threshold 4/10, training-only preprocessing; baseline pain ratings and treatment-derived imputation excluded.'}
    return pd.concat(outputs, ignore_index=True), audit


def summarize(predictions, reps=2000):
    metrics, intervals, comparisons = [], [], []
    for dataset, data in predictions.groupby('dataset', sort=False):
        people = sorted(data.id.unique()); lookup = {p:i for i,p in enumerate(people)}
        weights = np.random.default_rng(42).multinomial(len(people), np.ones(len(people))/len(people), size=reps)
        draws = {}
        for name, g in data.groupby('model', sort=False):
            m = operational_metrics(g.target, g.predicted, g.score)
            metrics.append({'dataset': dataset, 'model': name, 'people': len(people), **m})
            codes = g.id.map(lookup).to_numpy()
            cm = np.zeros((len(people),4))
            np.add.at(cm, (codes, 2*g.target.to_numpy(int)+g.predicted.to_numpy(int)), 1)
            f1, ba = metrics_from_counts(weights@cm)
            ap = weighted_average_precision(g.target.to_numpy(),g.score.to_numpy(),weights[:,codes])
            draws[name] = {'macro_f1':f1, 'balanced_accuracy':ba, 'average_precision':ap}
            for metric, vals in draws[name].items():
                low, high = np.nanpercentile(vals,[2.5,97.5])
                intervals.append({'dataset':dataset,'model':name,'metric':metric,'ci_low':float(low),'ci_high':float(high)})
        if dataset == 'mcphases':
            pairs = [(m,'rf_history_severity') for m in draws if m.startswith('rf_history_plus_') or m=='rf_full']
            pairs += [('rf_history_severity','rf_history_binary'),('rf_full','rf_original21'),
                      ('lr_full','lr_history_severity')]
            pairs += [('rf_full', m) for m in draws if m.startswith('rf_full_without_')]
        else:
            pairs = [(m,'lr_history') for m in draws if m not in ['lr_history','lr_no_pain_history']]
        for model, reference in pairs:
            for metric in ['macro_f1','balanced_accuracy','average_precision']:
                delta = draws[model][metric]-draws[reference][metric]
                low, high = np.nanpercentile(delta,[2.5,97.5])
                comparisons.append({'dataset':dataset,'model':model,'reference':reference,'metric':metric,
                                    'delta_ci_low':float(low),'delta_ci_high':float(high)})
    return pd.DataFrame(metrics),pd.DataFrame(intervals),pd.DataFrame(comparisons)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    mc, mc_audit = run_mc()
    mpis, mpis_audit = run_mpis()
    predictions = pd.concat([mc,mpis],ignore_index=True)
    predictions.to_csv(OUT/'predictions_private.csv',index=False)
    metrics,ci,paired = summarize(predictions)
    for name,frame in [('metrics',metrics),('confidence_intervals',ci),('paired_differences',paired)]:
        frame.to_csv(OUT/(name+'.csv'),index=False)
    audit = {'status':'EXPLORATORY_LITERATURE_MOTIVATED_EXTENSION_OF_PREVIOUSLY_INSPECTED_COHORTS',
             'client_date':'2026-11-01','mcphases':mc_audit,'mpis':mpis_audit,
             'metrics':metrics.to_dict('records'),'confidence_intervals':ci.to_dict('records'),
             'paired_differences':paired.to_dict('records'),'bootstrap_reps':2000,
             'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'limitations':['Literature-motivated after inspecting prior cohort results; not confirmatory validation',
                'Somatic diaries are proxies, not BSI-18/CSSI-24; mood/stress do not measure PROMIS or catastrophizing',
                'No raw participant data from the four papers were obtained',
                'Conditional participant-bootstrap intervals do not refit models; many exploratory comparisons',
                'No clinical, causal, or treatment-effect claims; physiological association is not independent prediction']}
    write_json(OUT/'summary.json',audit)
    write_json(ROOT/'reports/literature_factor_results.json',audit)
    print(metrics[['dataset','model','macro_f1','balanced_accuracy','average_precision']].round(4).to_string(index=False))


if __name__=='__main__':
    run()
