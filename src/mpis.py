"""Observed-only MPIS next-day replication, separate from mcPHASES evaluation."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, roc_auc_score,
                             precision_recall_curve)
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.evaluation import metrics_from_counts
from src.followup import weighted_average_precision
from src.pipeline import plt, write_json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/external/mpis-21538147'
OUT = ROOT / 'reports/runs/mpis'
KEY = ['id', 'day']
THRESHOLD = 4  # Project definition on a different 0–10 scale; not a clinical claim.
DIARY = ['previous_nrs', 'tablets_lag1', 'mood_lag1', 'symptoms_count_lag1', 'menstruating_lag1']
BASE_COLUMNS = {
    'age_group': 'Age Group', 'work_while_studying': 'Work While Studying',
    'alcohol': 'Alcohol Consumption', 'smoking': 'Smoking Status',
    'vigorous_activity': 'Vigorous Activity (Outside Menstruation)',
    'moderate_activity': 'Moderate Activity (Outside Menstruation)',
}
CATEGORIES = list(BASE_COLUMNS)
NAMES = {'persistence': 'Previous-day pain rule', 'always_negative': 'Always low/no pain',
         'lr_history': 'Logistic: pain history', 'lr_diary': 'Logistic: pain + diary',
         'lr_lifestyle': 'Logistic: pain + baseline attributes',
         'lr_combined': 'Logistic: pain + diary + baseline',
         'rf_history': 'Forest: pain history', 'rf_diary': 'Forest: pain + diary'}
SCOPES = ['control_only', 'preintervention_only', 'all_phases']


def observed_daily(raw):
    required = ['unique_id', 'invite_code', 'inferred_day_of_study', 'imputed',
                'pain', 'survey1_question2_response', 'measurement_time', 'phase',
                'tablets', 'mood', 'symptoms_count', 'menstruating']
    missing = set(required) - set(raw)
    if missing:
        raise ValueError(f'Missing fields: {missing}')
    if raw.unique_id.isna().any() or raw.inferred_day_of_study.isna().any():
        raise ValueError('Missing participant or day key')
    if raw.duplicated(['unique_id', 'inferred_day_of_study']).any():
        raise ValueError('Duplicate participant-day rows')
    if not raw.invite_code.eq(raw.unique_id).all():
        raise ValueError('Published participant aliases disagree')
    if raw.imputed.isna().any() or not set(raw.imputed.unique()) <= {True, False}:
        raise ValueError('Unrecognized imputation flag')
    d = raw.loc[~raw.imputed].copy()
    if d.pain.isna().any() or not d.pain.between(0, 10).all():
        raise ValueError('Observed pain must be present and in 0–10')
    if not d.pain.eq(d.survey1_question2_response).all():
        raise ValueError('Observed pain disagrees with original survey question')
    if not set(d.phase) <= {'A1', 'A2', 'B'}:
        raise ValueError('Unknown observed phase')
    if (d.inferred_day_of_study % 1 != 0).any():
        raise ValueError('Study days must be integers')
    if d.menstruating.isna().any() or not set(d.menstruating.unique()) <= {True, False}:
        raise ValueError('Missing or unknown observed menstruation flag')
    # The release also has a partially populated "id" column; use the complete,
    # verified unique_id key rather than creating duplicate column names.
    d = d.drop(columns=['id'], errors='ignore')
    d = d.rename(columns={'unique_id': 'id', 'inferred_day_of_study': 'day'})
    d['day'] = d.day.astype(int)
    d['date'] = pd.to_datetime(d.measurement_time, utc=True, errors='raise').dt.floor('D')
    if d.duplicated(['id', 'date']).any():
        raise ValueError('Duplicate observed participant-date rows')
    if 'current_day_of_study' in d and not d.current_day_of_study.eq(d.day).all():
        raise ValueError('Observed day index disagrees with filled-grid day index')
    for field, maximum in [('tablets', 50), ('mood', 4), ('symptoms_count', 20)]:
        if d[field].isna().any() or not d[field].between(0, maximum).all():
            raise ValueError(f'Unexpected observed {field} values')
    d['menstruating'] = d.menstruating.astype(int)
    return d.sort_values(KEY).reset_index(drop=True)


def exact_pairs(daily):
    columns = KEY + ['date', 'pain', 'phase', 'tablets', 'mood', 'symptoms_count', 'menstruating']
    prior = daily[columns].copy()
    prior['day'] += 1
    prior = prior.rename(columns={'date': 'prior_date', 'pain': 'previous_nrs', 'phase': 'prior_phase',
                                  **{c: c + '_lag1' for c in ['tablets', 'mood', 'symptoms_count', 'menstruating']}})
    result = daily[KEY + ['date', 'pain', 'phase']].merge(prior, on=KEY, how='inner', validate='one_to_one')
    if not (result.date - result.prior_date).dt.days.eq(1).all():
        raise ValueError('Relative-day adjacency contradicts the published timestamps')
    result['target'] = result.pain.ge(THRESHOLD).astype(int)
    result['control_only'] = result.phase.isin(['A1', 'A2']) & result.prior_phase.isin(['A1', 'A2'])
    result['preintervention_only'] = result.phase.eq('A1') & result.prior_phase.eq('A1')
    result['all_phases'] = True
    return result.sort_values(KEY).reset_index(drop=True)


def baseline_features(raw):
    if raw.unique_id.isna().any() or raw.unique_id.duplicated().any():
        raise ValueError('Invalid baseline participant keys')
    b = pd.DataFrame({'id': raw.unique_id})
    for new, source in BASE_COLUMNS.items():
        values = raw[source].astype('string').str.strip()
        sentinel = values.str.match(r'^-99[789](?:\s*=|$)', na=False)
        b[new] = values.mask(sentinel).fillna('Missing').astype(str)
    height = pd.to_numeric(raw.Height, errors='raise').replace([-997, -998, -999], np.nan)
    weight = pd.to_numeric(raw.Weight, errors='raise').replace([-997, -998, -999], np.nan)
    if not height.dropna().between(100, 220).all() or not weight.dropna().between(30, 250).all():
        raise ValueError('Unexpected baseline height/weight units or range')
    b['bmi'] = weight / (height / 100) ** 2
    return b


def estimator(kind, numeric, categorical):
    transforms = [('numeric', Pipeline([
        ('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
        ('scale', StandardScaler())]), numeric)]
    if categorical:
        transforms.append(('categorical', Pipeline([
            ('impute', SimpleImputer(strategy='constant', fill_value='Missing')),
            ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical))
    model = (LogisticRegression(C=.1, class_weight='balanced', max_iter=2000, random_state=42)
             if kind == 'lr' else RandomForestClassifier(n_estimators=200, max_depth=3,
                 min_samples_leaf=5, class_weight='balanced_subsample', random_state=42, n_jobs=-1))
    return Pipeline([('preprocess', ColumnTransformer(transforms)), ('model', model)])


def calculate_metrics(y, predicted, score):
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    return {'macro_f1': float(f1_score(y, predicted, average='macro', zero_division=0)),
            'balanced_accuracy': float(balanced_accuracy_score(y, predicted)),
            'average_precision': float(average_precision_score(y, score)),
            'roc_auc': float(roc_auc_score(y, score)), 'tn': int(tn), 'fp': int(fp),
            'fn': int(fn), 'tp': int(tp), 'recall': float(tp / (tp + fn)),
            'precision': float(tp / (tp + fp)) if tp + fp else 0.,
            'false_alarms_per_100_days': float(100 * fp / len(y))}


def evaluate(cohort, scope):
    definitions = {'lr_history': ('lr', ['previous_nrs'], []),
                   'lr_diary': ('lr', DIARY, []),
                   'lr_lifestyle': ('lr', ['previous_nrs', 'bmi'], CATEGORIES),
                   'lr_combined': ('lr', DIARY + ['bmi'], CATEGORIES),
                   'rf_history': ('rf', ['previous_nrs'], []),
                   'rf_diary': ('rf', DIARY, [])}
    X = cohort[DIARY + ['bmi'] + CATEGORIES]
    y = cohort.target.to_numpy(int)
    groups = cohort.id.to_numpy()
    splits = list(LeaveOneGroupOut().split(X, y, groups))
    if len(splits) < 5 or len(np.unique(y)) != 2:
        raise ValueError('Insufficient participant groups or outcome classes')
    outputs, folds = [], []
    for fold, (tr, te) in enumerate(splits):
        if set(groups[tr]) & set(groups[te]):
            raise ValueError('Participant leakage')
        if len(np.unique(y[tr])) != 2:
            raise ValueError('Training fold lacks an outcome class')
        for person in np.unique(groups[te]):
            folds.append({'scope': scope, 'fold': fold, 'id': person, 'test_days': len(te),
                          'training_people': len(np.unique(groups[tr])), 'overlap': 0})
    for name, (kind, numeric, categorical) in definitions.items():
        score = np.zeros(len(cohort))
        assignment = np.zeros(len(cohort), dtype=int)
        for fold, (tr, te) in enumerate(splits):
            fitted = estimator(kind, numeric, categorical).fit(X.iloc[tr], y[tr])
            score[te] = fitted.predict_proba(X.iloc[te])[:, 1]
            assignment[te] = fold
        outputs.append(cohort[KEY].assign(scope=scope, model=name, target=y,
                       predicted=(score >= .5).astype(int), score=score, fold=assignment))
    outputs.append(cohort[KEY].assign(scope=scope, model='persistence', target=y,
                   predicted=cohort.previous_nrs.ge(THRESHOLD).astype(int),
                   score=cohort.previous_nrs / 10., fold=assignment))
    outputs.append(cohort[KEY].assign(scope=scope, model='always_negative', target=y,
                   predicted=np.zeros(len(y), dtype=int), score=np.zeros(len(y)), fold=assignment))
    predictions = pd.concat(outputs, ignore_index=True)
    rows = []
    for name, g in predictions.groupby('model', sort=False):
        person_weights = 1. / g.id.map(g.id.value_counts()).to_numpy()
        rows.append({'scope': scope, 'model': name, 'people': int(g.id.nunique()), 'days': len(g),
                     'positive_days': int(g.target.sum()), 'prevalence': float(g.target.mean()),
                     **calculate_metrics(g.target, g.predicted, g.score),
                     'equal_person_balanced_accuracy': float(balanced_accuracy_score(g.target, g.predicted, sample_weight=person_weights)),
                     'equal_person_average_precision': float(average_precision_score(g.target, g.score, sample_weight=person_weights))})
    return predictions, pd.DataFrame(rows), pd.DataFrame(folds)


def cluster_bootstrap(predictions, reps):
    intervals, comparisons = [], []
    for scope, data in predictions.groupby('scope', sort=False):
        people = sorted(data.id.unique())
        mapping = {p:i for i, p in enumerate(people)}
        weights = np.random.default_rng(42).multinomial(len(people), np.ones(len(people)) / len(people), size=reps)
        draws = {}
        for model, g in data.groupby('model', sort=False):
            code = g.id.map(mapping).to_numpy()
            cm = np.zeros((len(people), 4))
            np.add.at(cm, (code, 2*g.target.to_numpy(int) + g.predicted.to_numpy(int)), 1)
            f1, ba = metrics_from_counts(weights @ cm)
            ap = weighted_average_precision(g.target.to_numpy(), g.score.to_numpy(), weights[:, code])
            draws[model] = {'macro_f1': f1, 'balanced_accuracy': ba, 'average_precision': ap}
            for metric, values in draws[model].items():
                low, high = np.nanpercentile(values, [2.5, 97.5])
                intervals.append({'scope': scope, 'model': model, 'metric': metric,
                                  'ci_low': float(low), 'ci_high': float(high),
                                  'valid_resamples': int(np.isfinite(values).sum())})
        for model, baseline in [('lr_diary', 'lr_history'), ('lr_lifestyle', 'lr_history'),
                                ('lr_combined', 'lr_diary'), ('rf_diary', 'rf_history')]:
            for metric in ['macro_f1', 'balanced_accuracy', 'average_precision']:
                delta = draws[model][metric] - draws[baseline][metric]
                low, high = np.nanpercentile(delta, [2.5, 97.5])
                comparisons.append({'scope': scope, 'model': model, 'baseline': baseline,
                                    'metric': metric, 'ci_low': float(low), 'ci_high': float(high),
                                    'valid_resamples': int(np.isfinite(delta).sum())})
    return pd.DataFrame(intervals), pd.DataFrame(comparisons)


def plot_results(predictions, metrics, intervals):
    output = ROOT / 'output/analysis'
    output.mkdir(parents=True, exist_ok=True)
    primary = metrics[metrics.scope.eq('control_only')]
    selected = ['persistence', 'lr_history', 'lr_diary', 'lr_lifestyle', 'lr_combined', 'rf_history', 'rf_diary']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
    indexed = primary.set_index('model').loc[selected]
    positions = np.arange(len(selected))
    bounds = intervals[intervals.scope.eq('control_only') & intervals.metric.eq('balanced_accuracy')].set_index('model').loc[selected]
    axes[0].hlines(positions, bounds.ci_low, bounds.ci_high, color='#2f7198', linewidth=2)
    axes[0].scatter(indexed.balanced_accuracy, positions, color='#163d55', s=36, zorder=3)
    axes[0].set(yticks=positions, yticklabels=[NAMES[m] for m in selected], xlim=(0, 1), xlabel='Balanced accuracy')
    axes[0].set_title('95% participant-bootstrap intervals\nConditional on saved predictions', fontsize=10)
    axes[0].invert_yaxis()
    axes[0].axvline(.5, color='gray', ls='--', lw=1)
    for p, value in zip(positions, indexed.balanced_accuracy):
        axes[0].text(.99, p, f'{value:.3f}', va='center', ha='right', fontsize=9)
    for model in ['persistence', 'lr_history', 'lr_diary', 'lr_combined']:
        g = predictions[predictions.scope.eq('control_only') & predictions.model.eq(model)]
        precision, recall, _ = precision_recall_curve(g.target, g.score)
        ap = indexed.loc[model, 'average_precision']
        axes[1].step(recall, precision, where='post', label=f'{NAMES[model]} (AP {ap:.3f})')
    axes[1].axhline(primary.prevalence.iloc[0], ls='--', color='gray', label='Observed prevalence')
    axes[1].set(xlabel='Recall', ylabel='Precision', xlim=(0, 1), ylim=(0, 1))
    axes[1].set_title('Precision–recall ranking performance', fontsize=10)
    axes[1].legend(fontsize=8)
    fig.suptitle(f'MPIS observed-only control phases: {int(primary.days.iloc[0])} next-day pairs, '
                 f'{int(primary.people.iloc[0])} participants\nExploratory participant-held-out evaluation', fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, .9])
    fig.savefig(output / 'mpis_results.png', dpi=180)
    plt.close(fig)


def make_report(a):
    metrics = pd.DataFrame(a['models'])
    def table(scope):
        rows = metrics[metrics.scope.eq(scope)]
        return ('| Model | Macro F1 | Balanced accuracy | AP | Detected positives | False alarms |\n'
                '|---|---:|---:|---:|---:|---:|\n' + '\n'.join(
                    f'| {NAMES[r.model]} | {r.macro_f1:.3f} | {r.balanced_accuracy:.3f} | {r.average_precision:.3f} '
                    f'| {r.tp}/{r.positive_days} | {r.fp}/{r.tn+r.fp} |' for r in rows.itertuples()))
    primary = a['scopes']['control_only']
    point = metrics[metrics.scope.eq('control_only')].set_index('model')
    primary_ci = pd.DataFrame(a['confidence_intervals'])
    primary_ci = primary_ci[primary_ci.scope.eq('control_only') & primary_ci.metric.eq('balanced_accuracy')].set_index('model')
    contrasts = pd.DataFrame(a['paired_differences'])
    contrast = contrasts[contrasts.scope.eq('control_only') & contrasts.model.eq('lr_lifestyle') & contrasts.metric.eq('balanced_accuracy')].iloc[0]
    diary_ap = contrasts[contrasts.scope.eq('control_only') & contrasts.model.eq('lr_diary') & contrasts.metric.eq('average_precision')].iloc[0]
    text = f'''# MPIS observed-only next-day pain analysis

Analysis date: November 1, 2026. This is an exploratory replication of the forecasting question in a separate dataset. Models are trained and evaluated within MPIS with held-out participants. This is not external evaluation of the frozen mcPHASES model, and it cannot test wearable utility because MPIS has no wearable recordings.

## Source audit

[MPIS Study Data](https://zenodo.org/records/21538147), DOI 10.5281/zenodo.21538147, CC BY 4.0. All eight source files match their downloaded checksums. English and German tables describe the same participants; AI-extracted free-text outputs are not used as outcomes or predictors.

- Published grid: **{a['grid_rows']} rows, {a['enrolled_people']} participants**, nominally 60 days each.
- **{a['imputed_rows']} rows ({a['imputed_fraction']:.1%}) are imputed**, all excluded from both targets and prior-day inputs.
- Only **{a['observed_rows']} observed daily reports from {a['observed_people']} people** remain. **{a['people_without_observed_reports']} enrolled participants have no observed daily report** in this release.
- Observed original pain question and supplied `pain` column agree. Pain ranges from 0 to 9 in the observed data, despite a 0–10 instrument. The binary pain-present question has one yes response paired with a severity of zero; the numeric severity remains authoritative.
- Exact adjacent observed pairs: **{a['scopes']['all_phases']['days']} days from {a['scopes']['all_phases']['people']} people**. All retained study-day pairs also have a one-day difference in the published UTC calendar dates. No forward-fill or previous-observation join is used across missing days.
- Baseline questionnaire linkage is one-to-one by the published pseudonymous participant ID. Negative sentinel codes −997/−998/−999 are missing, not numeric values. Six chosen baseline categorical attributes plus BMI form the baseline feature block.

The source states that timestamps were changed. Publication/creation metadata and the trial-registry reference also contain inconsistencies, and the linked analysis repository was unavailable during inspection. Absolute dates, season, weekday, source-generated future phase labels, and source-imputed features are excluded. Preserved relative ordering is checked against the published timestamp differences, but original timing and independent recruitment cannot be established from these files alone.

## Outcome, predictors and evaluation

The target is **next-day observed pain ≥{THRESHOLD}/10**, an explicit project threshold. It is not a clinical cutoff and is not an exact scale conversion of mcPHASES verbal categories. The outcome is not imputed. Both members of every pair must be observed.

Predictors available by the previous report: continuous previous-day pain, previous-day tablet count, pain-related negative mood impact, symptom count, and menstruation status. Baseline attributes: age group, working while studying, alcohol, smoking, vigorous and moderate activity outside menstruation, and BMI. These are baseline habits rather than measured daily activity. No baseline pain severity, current-day symptoms, current pain, imputation-generated fields, IDs, absolute dates, or free-text model labels enter any model. No daily stress, sleep, or wearable measurements are available in the chosen source tables. Conditional symptom reporting can make diary attributes redundant with pain history. This is a next-calendar-day retrospective task; varying report times, shifted dates and unconfirmed questionnaire lookback windows prevent a claim of an exact 24-hour operational forecast.

Primary scope is **both days in control phases A1/A2**, yielding **{primary['days']} pairs, {primary['people']} participants, and {primary['positive_days']} positive outcomes ({primary['prevalence']:.1%})**. A2 follows massage, so carry-over effects remain possible. The stricter A1-only analysis excludes post-intervention control days. An all-phase sensitivity includes treatment periods and six A1-to-B transitions; it estimates a different case mix.

Leave-one-participant-out evaluation prevents rows from the same person entering both train and test. Fixed logistic regression uses C=0.1 and balanced classes. Fixed random forests use 200 trees, maximum depth 3, minimum leaf size 5, balanced subsample classes and seed 42. All numeric imputation/scaling and categorical encoding are fitted within the training fold. No model/threshold search or post-result feature selection is performed. Learned models use a fixed 0.5 classification threshold.

The persistence classifier predicts the previous day's ≥{THRESHOLD}/10 class. Its ranking score is previous pain/10, not a calibrated probability. Always-negative is a constant reference. Within-family feature comparisons isolate the added diary or baseline block without changing model settings. The study has only a few independent participants, even though there are more daily rows.

## Primary results: observed control phases

{table('control_only')}

**Main finding:** the previous-day pain rule has the highest primary balanced accuracy (**{point.loc['persistence', 'balanced_accuracy']:.3f}**) and macro F1 (**{point.loc['persistence', 'macro_f1']:.3f}**). It detects **{int(point.loc['persistence', 'tp'])} of {primary['positive_days']}** moderate-or-higher pain days, with **{int(point.loc['persistence', 'fp'])} false alarms among {int(point.loc['persistence', 'tn']+point.loc['persistence', 'fp'])} negative days**. Its 95% conditional participant-bootstrap interval for balanced accuracy is **[{primary_ci.loc['persistence', 'ci_low']:.3f}, {primary_ci.loc['persistence', 'ci_high']:.3f}]**.

Additional diary fields do not improve classification over the matched pain-only model: logistic balanced accuracy changes from **{point.loc['lr_history', 'balanced_accuracy']:.3f} to {point.loc['lr_diary', 'balanced_accuracy']:.3f}**. Their AP point estimate increases slightly, but the paired AP-difference interval **[{diary_ap.ci_low:.3f}, {diary_ap.ci_high:.3f}]** crosses zero. Adding baseline attributes to pain-only logistic regression gives balanced accuracy **{point.loc['lr_lifestyle', 'balanced_accuracy']:.3f}**, with a paired difference interval **[{contrast.ci_low:.3f}, {contrast.ci_high:.3f}]**. The full diary-plus-baseline model falls to **{point.loc['lr_combined', 'balanced_accuracy']:.3f}**. These results show no consistent added predictive value from the attribute blocks in this small cohort; they do not establish that the attributes are irrelevant.

AP means average precision. The prevalence reference is **{primary['prevalence']:.3f}**. These are pooled held-out day scores; equal-person-weighted metrics are also retained in the aggregate JSON to show sensitivity to unequal reporting frequency. False alarms are counts among actual negative days, not a clinical alert-rate estimate.

![MPIS control-phase model results](../output/analysis/mpis_results.png)

## Sensitivity: pre-intervention A1 only

{table('preintervention_only')}

In this stricter scope, the pain-plus-baseline logistic model and persistence tie on balanced accuracy and macro F1, while their ranking scores differ. This does not establish superiority of either approach. The small sample and changes across scopes limit model-ranking conclusions.

## Sensitivity: all observed phases

{table('all_phases')}

## Uncertainty and interpretation

The report records **{a['bootstrap_reps']} paired participant-cluster bootstrap resamples** of fixed held-out predictions. These intervals do not refit models, account for hyperparameter search, or establish clinical validity. Participants with longer reporting histories contribute more rows to pooled metrics; equal-person-weighted sensitivity is included. A bootstrap sample lacking an outcome class cannot define balanced accuracy and is omitted for that metric; valid-resample counts are reported.

The aggregate JSON contains point estimates, intervals, and paired differences for diary additions and baseline additions. These prespecified comparisons are exploratory, with no multiple-testing correction. Apparent differences may reflect individual symptom patterns, reporting behavior, treatment phases or selective adherence. They do not establish that alcohol, activity, BMI or mood causes menstrual pain.

This dataset adds genuine observed consecutive-day reports, but its 86% imputed grid and small observed sample constrain the strength of any conclusion. Reporting only the 2,160 filled rows would substantially exaggerate the available evidence. The imputed values derived from baseline pain cannot be treated as independent targets for evaluating baseline attributes.

## Reproduce and saved outputs

Run `.venv/bin/python -m src.mpis`, then `.venv/bin/python -m pytest -q`. Original files are unchanged. Source hashes, software versions and complete analysis settings are recorded in `reports/mpis_results.json`.

Participant-level observed rows, consecutive-day pairs, baseline features, folds, predictions and source-audit details stay ignored under `reports/runs/mpis/`. Aggregate metrics and uncertainty appear in `reports/mpis_results.json`; the figure is in `output/analysis/mpis_results.png`. The mcPHASES and PhysioPain analyses are unchanged.
'''
    (ROOT / 'reports/mpis_analysis.md').write_text(text)


def run(raw=RAW, output=OUT, reps=2000):
    raw, output = Path(raw), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    verified = json.loads((raw / 'download_verification.json').read_text())
    hashes = {}
    for item in verified['files']:
        path = raw / item['name']
        content = path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        if sha != item['sha256']:
            raise ValueError('Downloaded file changed: ' + item['name'])
        hashes[item['name']] = sha
    source = pd.read_csv(raw / 'cleaned_studyu_data.csv')
    baseline = pd.read_csv(raw / 'final_upsurvey_data_labeled_mpisapp.csv')
    daily = observed_daily(source)
    daily.to_csv(output / 'observed_daily_private.csv', index=False)
    pairs = exact_pairs(daily)
    base = baseline_features(baseline)
    pairs = pairs.merge(base, on='id', how='left', validate='many_to_one', indicator=True)
    if not pairs._merge.eq('both').all():
        raise ValueError('Missing baseline linkage')
    pairs = pairs.drop(columns='_merge')
    pairs.to_csv(output / 'forecast_private.csv', index=False)
    all_predictions, all_metrics, all_folds, scopes = [], [], [], {}
    for scope in SCOPES:
        data = pairs[pairs[scope]].reset_index(drop=True)
        scopes[scope] = {'days': len(data), 'people': int(data.id.nunique()),
                         'positive_days': int(data.target.sum()), 'prevalence': float(data.target.mean()),
                         'positive_people': int(data.loc[data.target.eq(1), 'id'].nunique())}
        prediction, metrics, folds = evaluate(data, scope)
        all_predictions.append(prediction); all_metrics.append(metrics); all_folds.append(folds)
        print(f'Completed {scope}: {len(data)} pairs, {data.id.nunique()} participants', flush=True)
    predictions = pd.concat(all_predictions, ignore_index=True)
    metrics = pd.concat(all_metrics, ignore_index=True)
    folds = pd.concat(all_folds, ignore_index=True)
    predictions.to_csv(output / 'predictions_private.csv', index=False)
    metrics.to_csv(output / 'metrics.csv', index=False)
    folds.to_csv(output / 'folds_private.csv', index=False)
    intervals, paired = cluster_bootstrap(predictions, reps)
    intervals.to_csv(output / 'confidence_intervals.csv', index=False)
    paired.to_csv(output / 'paired_differences.csv', index=False)
    summary = {'status': 'EXPLORATORY_OBSERVED_ONLY_WITHIN_MPIS_PARTICIPANT_HELD_OUT_REPLICATION',
               'client_date': '2026-11-01', 'source_doi': '10.5281/zenodo.21538147',
               'grid_rows': len(source), 'enrolled_people': int(source.unique_id.nunique()),
               'imputed_rows': int(source.imputed.sum()), 'imputed_fraction': float(source.imputed.mean()),
               'observed_rows': len(daily), 'observed_people': int(daily.id.nunique()),
               'people_without_observed_reports': int(source.unique_id.nunique() - daily.id.nunique()),
               'observed_positive_days_threshold4': int(daily.pain.ge(THRESHOLD).sum()),
               'threshold': THRESHOLD, 'outcome': 'Next-day observed pain >=4 on 0–10 numeric scale; project threshold',
               'scopes': scopes, 'models': metrics.to_dict('records'),
               'confidence_intervals': intervals.to_dict('records'), 'paired_differences': paired.to_dict('records'),
               'bootstrap_reps': reps, 'daily_predictors': DIARY, 'baseline_predictors': CATEGORIES + ['bmi'],
               'source_sha256': hashes, 'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'software': {'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__},
               'limits': ['No wearable measurements; cannot evaluate wearable added value',
                          'Most filled-grid outcomes are imputed and excluded',
                          'Few participants and positive outcomes; selected reporting/adherence',
                          'Different numeric pain scale; threshold is a project choice',
                          'Timestamp shifting and inconsistent provenance metadata require author clarification',
                          'Control A2 may retain massage carry-over; treatment-phase sensitivity has different case mix',
                          'Within-dataset model training is not external validation of a frozen mcPHASES model',
                          'Participant-level non-overlap with mcPHASES is not verified',
                          'Bootstrap intervals condition on saved predictions and omit model-refitting uncertainty']}
    write_json(output / 'summary.json', summary)
    write_json(ROOT / 'reports/mpis_results.json', summary)
    plot_results(predictions, metrics, intervals)
    make_report(summary)
    print(metrics[metrics.scope.eq('control_only')][['model','macro_f1','balanced_accuracy','average_precision','tp','fp']].to_string(index=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', type=Path, default=RAW)
    p.add_argument('--output', type=Path, default=OUT)
    p.add_argument('--bootstrap-reps', type=int, default=2000)
    args = p.parse_args()
    run(args.raw, args.output, args.bootstrap_reps)
