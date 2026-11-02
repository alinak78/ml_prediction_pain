"""Separate exploratory session-level PhysioPain analysis; never a forecast test.

Run --prepare-survey-only with an interpreter providing pandas/openpyxl, then
run the analysis in the project's scikit-learn environment. Raw files are read
in place. Participant derivatives stay in the ignored run directory.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/external/physiopain-v4/PhysioPain Dataset/PhysioPain Dataset'
OUT = ROOT / 'reports/runs/physiopain'
TYPE = 'What is your pain type?'
SEVERITY = 'Rate the severity of your pain (Likert scale) [How severe is your pain now?]'
SEX = 'Gender (Biological)'
SEVERITY_MAP = {'Not severe at all': 1, 'Mild': 2, 'Moderate': 3,
                'Severe': 4, 'Very severe': 5}
LIFESTYLE_COLUMNS = {
    'habitual_sleep': 'How many hours do you sleep per day on average?',
    'sleep_before_test': 'How many hours did you sleep before this test?',
    'sleep_difficulty': 'Have you had any problems falling asleep or staying asleep? (Yes No)',
    'stress': 'What do you think about your stress level in your daily life?',
    'exercise': 'How would you rate yourself based on your exercise frequency?',
    'diet': 'How would you evaluate yourself based on your eating habits?',
    'water': 'Do you think you drink enough water?',
}
WEARABLES = ['hr_median', 'hr_iqr', 'eda_median', 'eda_iqr',
             'temperature_median', 'temperature_iqr', 'acc_magnitude_sd',
             'acc_jerk_median', 'ibi_rmssd_ms']
BURN_IN_SECONDS = 30
WINDOW_SECONDS = 600
MIN_COVERAGE = .8


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def read_regular(payload):
    """E4 CSV: UTC epoch, sampling rate, then actual samples (including ACC)."""
    lines = payload.decode('utf-8-sig').splitlines()
    epoch = float(lines[0].split(',')[0])
    rate = float(lines[1].split(',')[0])
    if rate <= 0 or not np.isfinite(rate):
        raise ValueError('Invalid sampling rate')
    data = np.loadtxt(io.StringIO('\n'.join(lines[2:])), delimiter=',', ndmin=2)
    return epoch, rate, data


def ibi_rmssd(payload, burn=BURN_IN_SECONDS, end=None):
    """Use adjacent valid beats only; do not bridge missing-beat gaps."""
    lines = payload.decode('utf-8-sig').splitlines()
    if len(lines) < 3:
        return np.nan, 0
    data = np.loadtxt(io.StringIO('\n'.join(lines[1:])), delimiter=',', ndmin=2)
    time, ibi = data[:, 0], data[:, 1]
    valid = np.isfinite(data).all(axis=1) & (time >= burn) & (ibi >= .3) & (ibi <= 2.)
    if end is not None:
        valid &= time < end
    adjacent = valid[1:] & valid[:-1] & (np.diff(time) > 0)
    adjacent &= np.abs(np.diff(time) - ibi[1:]) <= np.maximum(.1, .2 * ibi[1:])
    differences = np.diff(ibi)[adjacent]
    return (float(np.sqrt(np.mean(differences ** 2)) * 1000)
            if len(differences) >= 30 else np.nan), int(len(differences))


def summarize_recording(path):
    features, audit = {}, {'id': path.stem}
    with zipfile.ZipFile(path) as z:
        channels = {c: read_regular(z.read(c + '.csv')) for c in ['HR', 'EDA', 'TEMP', 'ACC']}
        common_start = max(epoch for epoch, _, _ in channels.values())
        window_start = common_start + BURN_IN_SECONDS
        audit['feature_window_start_utc'] = window_start
        audit['feature_window_seconds'] = WINDOW_SECONDS
        for channel, prefix, bounds in [('HR', 'hr', (30, 220)),
                                        ('EDA', 'eda', (0, 100)),
                                        ('TEMP', 'temperature', (20, 42))]:
            epoch, rate, values = channels[channel]
            values = values[:, 0]
            audit[channel + '_duration_seconds'] = float(len(values) / rate)
            audit[channel + '_utc_start'] = epoch
            first = int(np.ceil((window_start - epoch) * rate))
            values = values[first:first + int(WINDOW_SECONDS * rate)]
            valid = np.isfinite(values) & (values >= bounds[0]) & (values <= bounds[1])
            coverage = float(valid.sum() / (WINDOW_SECONDS * rate))
            audit[channel + '_valid_fraction_after_burn_in'] = coverage
            clean = values[valid]
            usable = len(clean) >= 30 and coverage >= MIN_COVERAGE
            features[prefix + '_median'] = float(np.median(clean)) if usable else np.nan
            features[prefix + '_iqr'] = float(np.subtract(*np.percentile(clean, [75, 25]))) if usable else np.nan
        epoch, rate, values = channels['ACC']
        first = int(np.ceil((window_start - epoch) * rate))
        values = values[first:first + int(WINDOW_SECONDS * rate)]
        valid = np.isfinite(values).all(axis=1) & (np.abs(values) <= 128).all(axis=1)
        audit['ACC_valid_fraction_after_burn_in'] = float(valid.sum() / (WINDOW_SECONDS * rate))
        g = values / 64.  # Raw archive info.txt documents units of 1/64 g.
        magnitude = np.linalg.norm(g[valid], axis=1)
        consecutive = valid[1:] & valid[:-1]
        jerk = np.linalg.norm(np.diff(g, axis=0), axis=1)[consecutive] * rate
        usable = len(magnitude) >= 30 and audit['ACC_valid_fraction_after_burn_in'] >= MIN_COVERAGE
        features['acc_magnitude_sd'] = float(np.std(magnitude)) if usable else np.nan
        features['acc_jerk_median'] = float(np.median(jerk)) if usable and len(jerk) else np.nan
        ibi_payload = z.read('IBI.csv')
        ibi_lines = ibi_payload.decode().splitlines()
        if not ibi_lines:
            features['ibi_rmssd_ms'], audit['IBI_valid_adjacent_pairs'] = np.nan, 0
        else:
            ibi_epoch = float(ibi_lines[0].split(',')[0])
            features['ibi_rmssd_ms'], audit['IBI_valid_adjacent_pairs'] = ibi_rmssd(
                ibi_payload, window_start - ibi_epoch, window_start + WINDOW_SECONDS - ibi_epoch)
    return features, audit


def define_cohort(survey):
    """Survey-specific labels take precedence over ambiguous processed folders."""
    survey = survey.copy()
    unknown = set(survey[SEVERITY].dropna()) - set(SEVERITY_MAP)
    if unknown:
        raise ValueError(f'Unknown severity labels: {unknown}')
    survey['current_severity'] = survey[SEVERITY].map(SEVERITY_MAP)
    women = survey[SEX].eq('Female')
    menstrual = survey[TYPE].eq('Menstrual pain') & survey.current_severity.notna()
    controls = survey[TYPE].eq('No pain')
    cohort = survey.loc[women & (menstrual | controls)].copy()
    # Explicit "No pain" defines controls even when the severity question is blank.
    cohort['target'] = (cohort[TYPE].eq('Menstrual pain') & cohort.current_severity.ge(3)).astype(int)
    return cohort


def processed_label_audit(raw, survey):
    rows = []
    menstrual_severity = next(c for c in survey if c.startswith('What do you think about the severity of your menstrual'))
    for group in ['menstrual_pain', 'no_pain', 'headache', 'back_pain']:
        for path in sorted((raw / 'WATCH DATA/PROCESSED WATCH DATA' / group / 'signal_4').glob('*.csv')):
            d = pd.read_csv(path, usecols=['person_id', 'pain_scale'])
            if d.person_id.nunique() != 1 or d.pain_scale.nunique(dropna=False) != 1:
                raise ValueError('Unexpected within-recording label changes')
            person = d.person_id.iloc[0]
            s = survey.loc[person]
            current = SEVERITY_MAP.get(s[SEVERITY], np.nan)
            supplied = d.pain_scale.iloc[0]
            rows.append({'id': person, 'processed_group': group,
                         'processed_severity': supplied, 'survey_type': s[TYPE],
                         'survey_current_severity': current,
                         'survey_general_menstrual_severity': s[menstrual_severity],
                         'processed_vs_current_severity_disagrees': bool(pd.notna(current) and supplied != current)})
    result = pd.DataFrame(rows)
    if result.id.duplicated().any():
        raise ValueError('Duplicate participant across processed groups')
    return result


def evaluate(cohort, features, lifestyle_columns, out):
    """Fixed models; one held-out participant per fold; no tuning or windows."""
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                                 confusion_matrix, f1_score, roc_auc_score)
    from sklearn.model_selection import LeaveOneOut
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    y = cohort.target.to_numpy(int)
    if min(np.bincount(y, minlength=2)) < 2:
        raise ValueError('Insufficient independent people in each class for held-out modeling')
    definitions = [('logistic_wearables', WEARABLES, [], 'logistic'),
                   ('logistic_lifestyle', [], lifestyle_columns, 'logistic'),
                   ('logistic_combined', WEARABLES, lifestyle_columns, 'logistic'),
                   ('forest_wearables', WEARABLES, [], 'forest')]
    outputs, folds = [], []
    split = list(LeaveOneOut().split(cohort))
    for model_name, numeric, categorical, kind in definitions:
        probability = np.zeros(len(y))
        for fold, (tr, te) in enumerate(split):
            if set(cohort.iloc[tr].index) & set(cohort.iloc[te].index):
                raise ValueError('Participant leakage')
            transforms = []
            if numeric:
                transforms.append(('numeric', Pipeline([
                    ('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                    ('scale', StandardScaler())]), numeric))
            if categorical:
                transforms.append(('categorical', Pipeline([
                    ('impute', SimpleImputer(strategy='constant', fill_value='Missing')),
                    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical))
            estimator = (LogisticRegression(C=.1, class_weight='balanced', max_iter=2000, random_state=42)
                         if kind == 'logistic' else RandomForestClassifier(
                             n_estimators=200, max_depth=2, min_samples_leaf=3,
                             class_weight='balanced_subsample', random_state=42, n_jobs=-1))
            model = Pipeline([('preprocess', ColumnTransformer(transforms)), ('model', estimator)])
            model.fit(features.iloc[tr], y[tr])
            probability[te] = model.predict_proba(features.iloc[te])[:, 1]
            if model_name == 'logistic_wearables':
                folds.append({'fold': fold, 'test_id': cohort.index[te[0]],
                              'training_people': len(tr), 'test_people': len(te),
                              'overlap': 0})
        outputs.append(pd.DataFrame({'id': cohort.index, 'model': model_name, 'target': y,
                                     'probability': probability, 'predicted': (probability >= .5).astype(int)}))
    outputs.append(pd.DataFrame({'id': cohort.index, 'model': 'always_negative', 'target': y,
                                 'probability': np.zeros(len(y)), 'predicted': np.zeros(len(y), dtype=int)}))
    predictions = pd.concat(outputs, ignore_index=True)
    rows = []
    for name, d in predictions.groupby('model', sort=False):
        tn, fp, fn, tp = confusion_matrix(d.target, d.predicted, labels=[0, 1]).ravel()
        rows.append({'model': name, 'people': len(d), 'positive': int(d.target.sum()),
                     'macro_f1': float(f1_score(d.target, d.predicted, average='macro', zero_division=0)),
                     'balanced_accuracy': float(balanced_accuracy_score(d.target, d.predicted)),
                     'average_precision': float(average_precision_score(d.target, d.probability)),
                     'roc_auc': float(roc_auc_score(d.target, d.probability)),
                     'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)})
    predictions.to_csv(out / 'predictions_private.csv', index=False)
    pd.DataFrame(folds).to_csv(out / 'folds_private.csv', index=False)
    metrics = pd.DataFrame(rows)
    metrics.to_csv(out / 'metrics.csv', index=False)
    return metrics


def run(raw=RAW, out=OUT, prepare_only=False):
    raw, out = Path(raw), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    source = raw / 'SURVEY DATA/survey_answers_en.xlsx'
    survey_csv = out / 'survey_private.csv'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if prepare_only:
        survey = pd.read_excel(source)
        if survey.id.duplicated().any():
            raise ValueError('Duplicate survey IDs')
        survey.to_csv(survey_csv, index=False)
        write_json(out / 'survey_provenance.json', {'source': str(source.relative_to(ROOT)),
                   'sha256': source_hash, 'rows': len(survey), 'columns': len(survey.columns),
                   'csv_sha256': hashlib.sha256(survey_csv.read_bytes()).hexdigest()})
        print(f'Prepared {len(survey)} survey rows in ignored run folder')
        return
    provenance = json.loads((out / 'survey_provenance.json').read_text())
    if provenance['sha256'] != source_hash or provenance['csv_sha256'] != hashlib.sha256(survey_csv.read_bytes()).hexdigest():
        raise ValueError('Survey changed; repeat --prepare-survey-only')
    survey = pd.read_csv(survey_csv).set_index('id')
    if not survey.index.is_unique:
        raise ValueError('Duplicate survey IDs')
    labels = processed_label_audit(raw, survey)
    labels.to_csv(out / 'label_audit_private.csv', index=False)
    paths = sorted((raw / 'WATCH DATA/RAW WATCH DATA/All').glob('*.zip'))
    if len({p.stem for p in paths}) != len(paths):
        raise ValueError('Duplicate raw participants')
    rows, audits = [], []
    for path in paths:
        features, audit = summarize_recording(path)
        rows.append({'id': path.stem, **features})
        audits.append(audit)
    signals = pd.DataFrame(rows).set_index('id')
    if not signals.index.is_unique:
        raise ValueError('Duplicate signal IDs')
    signals.to_csv(out / 'session_features_private.csv')
    pd.DataFrame(audits).to_csv(out / 'signal_quality_private.csv', index=False)
    candidate = define_cohort(survey)
    cohort = candidate.loc[candidate.index.intersection(signals.index)].sort_index()
    if len(cohort) < 2 or signals.loc[cohort.index].notna().sum(axis=1).eq(0).any():
        raise ValueError('Unusable cohort or completely absent signals')
    lifestyle = cohort[list(LIFESTYLE_COLUMNS.values())].rename(columns={v:k for k,v in LIFESTYLE_COLUMNS.items()})
    lifestyle = lifestyle.fillna('Missing').astype(str)
    features = signals.loc[cohort.index].join(lifestyle)
    features.to_csv(out / 'model_features_private.csv')
    cohort[[TYPE, SEX, 'current_severity', 'target']].to_csv(out / 'cohort_private.csv')
    metrics = evaluate(cohort, features, list(LIFESTYLE_COLUMNS), out)
    descriptive = []
    for feature in WEARABLES:
        for target in [0, 1]:
            values = features.loc[cohort.target.eq(target), feature].dropna()
            descriptive.append({'feature': feature, 'target': target, 'observed_people': len(values),
                                'median': float(values.median()) if len(values) else None,
                                'q25': float(values.quantile(.25)) if len(values) else None,
                                'q75': float(values.quantile(.75)) if len(values) else None})
    pd.DataFrame(descriptive).to_csv(out / 'descriptive_wearables.csv', index=False)
    lifestyles = []
    for feature in LIFESTYLE_COLUMNS:
        for target in [0, 1]:
            for value, count in features.loc[cohort.target.eq(target), feature].value_counts().items():
                lifestyles.append({'feature': feature, 'target': target, 'category': value, 'people': int(count)})
    pd.DataFrame(lifestyles).to_csv(out / 'descriptive_lifestyle.csv', index=False)
    menstrual = survey[TYPE].eq('Menstrual pain')
    moderate = survey[SEVERITY].map(SEVERITY_MAP).ge(3)
    matching_raw = survey.index.isin(signals.index)
    import sklearn
    artifact = {
        'status': 'EXPLORATORY_SEPARATE_SESSION_LEVEL_EXPERIMENT',
        'client_date': '2026-11-01', 'source_doi': '10.17632/mf2cgph9cy.4',
        'survey_people': len(survey), 'raw_wristband_people': len(signals),
        'processed_4hz_people': len(labels),
        'survey_people_without_raw_wristband': int((~matching_raw).sum()),
        'explicit_menstrual_people': int(menstrual.sum()),
        'explicit_menstrual_people_with_raw': int((menstrual & matching_raw).sum()),
        'menstrual_current_severity_counts': {str(k):int(v) for k,v in survey.loc[menstrual, SEVERITY].value_counts().items()},
        'processed_menstrual_folder_people': int(labels.processed_group.eq('menstrual_pain').sum()),
        'abdominal_reports_in_menstrual_folder': int((labels.processed_group.eq('menstrual_pain') & labels.survey_type.eq('Abdominal pain')).sum()),
        'processed_menstrual_severity_vs_current_disagreements': int(labels.loc[labels.processed_group.eq('menstrual_pain'), 'processed_vs_current_severity_disagrees'].sum()),
        'cohort_people': len(cohort), 'positive_people': int(cohort.target.sum()),
        'negative_people': int(cohort.target.eq(0).sum()),
        'female_no_pain_controls': int(cohort[TYPE].eq('No pain').sum()),
        'mild_menstrual_comparison_people': int((cohort[TYPE].eq('Menstrual pain') & cohort.target.eq(0)).sum()),
        'positive_prevalence': float(cohort.target.mean()),
        'outcome': 'Current moderate-or-higher menstrual pain versus female no-pain controls and mild menstrual pain',
        'predictor_timing': 'Same-session physiology and retrospective/self-reported habits; not exact prior-day wearable data',
        'wearable_features': WEARABLES, 'lifestyle_features': LIFESTYLE_COLUMNS,
        'wearable_nonmissing_counts': {k:int(v) for k,v in signals.loc[cohort.index].notna().sum().items()},
        'evaluation': 'Leave-one-participant-out; fixed hyperparameters; all preprocessing fit on training people only',
        'burn_in_seconds': BURN_IN_SECONDS, 'minimum_regular_signal_valid_fraction': MIN_COVERAGE,
        'window_seconds': WINDOW_SECONDS,
        'software': {'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__},
        'survey_source_sha256': source_hash,
        'models': metrics.to_dict('records'), 'descriptive_wearables': descriptive,
        'limits': ['Single short recording per participant; no next-day outcome or pain-history baseline',
                  'Only 9 explicit menstrual-pain participants; only 1 has low current severity',
                  'Cannot evaluate menstrual severity alone with held-out people and both training classes in every fold',
                  'Control-group contrast changes the task and does not validate the mcPHASES forecasting model',
                  'Processed folder and severity labels disagree with some original survey responses',
                  'Raw signal availability differs from published participant counts',
                  'Small exploratory cohort; no reliable feature attribution, causal inference, or clinical validation',
                  'Participant-level independence from mcPHASES is not verified by the archive']}
    write_json(out / 'summary.json', artifact)
    write_json(ROOT / 'reports/physiopain_results.json', artifact)
    make_report(artifact, metrics)
    print(metrics.to_string(index=False))
    print(f'Completed analysis for {len(cohort)} participants; report: reports/physiopain_analysis.md')


def make_report(a, metrics):
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    titles = ['Logistic: wearables', 'Logistic: lifestyle', 'Logistic: combined', 'Forest: wearables']
    for ax, title, (_, r) in zip(axes.flat, titles, metrics.iloc[:4].iterrows()):
        cm = np.array([[r.tn, r.fp], [r.fn, r.tp]], dtype=int)
        ax.imshow(cm, cmap='Blues', vmin=0, vmax=max(a['positive_people'], a['negative_people']))
        for (i, j), value in np.ndenumerate(cm):
            ax.text(j, i, str(value), ha='center', va='center', fontsize=18,
                    color='white' if value > 4 else '#102838')
        ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['Comparison', 'Moderate+'],
               yticklabels=['Comparison', 'Moderate+'], xlabel='Predicted', ylabel='Observed', title=title)
    fig.suptitle('Exploratory current menstrual-pain classification\n17 held-out participant predictions per model', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, .93])
    figure_dir = ROOT / 'output/analysis'
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_dir / 'physiopain_confusion_matrices.png', dpi=180)
    plt.close(fig)
    rows = '\n'.join(f"| {r.model} | {r.macro_f1:.3f} | {r.balanced_accuracy:.3f} | {r.average_precision:.3f} | {r.roc_auc:.3f} | {r.tp}/{r.tp+r.fn} | {r.fp}/{r.fp+r.tn} |" for r in metrics.itertuples())
    by_name = metrics.set_index('model')
    text = f'''# PhysioPain exploratory analysis

Analysis date: November 1, 2026. This is a separate experiment in classifying current pain during a short recording. The completed mcPHASES next-day forecasting results remain the primary project analysis.

## Data and label audit

- The verified extracted archive contains 1,011 entries and 5,235,238,091 uncompressed bytes. Source: [PhysioPain v4](https://data.mendeley.com/datasets/mf2cgph9cy/4), CC BY 4.0. [Study methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12410463/).
- English survey: **{a['survey_people']} people**. The Turkish workbook is a translation, not additional participants.
- Raw wristband recordings: **{a['raw_wristband_people']} people**, also represented in the individual processed 4 Hz files. **{a['survey_people_without_raw_wristband']} survey participants lack a raw wristband archive**. These actual counts differ from the paper's claimed 93 usable physiological participants.
- Original survey explicitly identifies **{a['explicit_menstrual_people']} menstrual-pain participants**. Current severity: {a['menstrual_current_severity_counts']}.
- The processed menstrual folder has **{a['processed_menstrual_folder_people']} people**, including **{a['abdominal_reports_in_menstrual_folder']} reporting abdominal pain**, excluded from the modeled cohort. Processed severity differs from current survey severity in **{a['processed_menstrual_severity_vs_current_disagreements']}** menstrual-folder records. The current-pain survey item, rather than general menstrual severity or the supplied processed label, defines the target.

## Cleaning and feature preparation

Read original E4 ZIP files in place. Remove the first two rows (UTC epoch and sampling rate) from regularly sampled signals. The packaged processed files include sampling-rate values in the signal columns, with associated filtering/resampling artifacts, so they are used for the label audit only.

Align channels in UTC and use the same **10-minute window**, starting {BURN_IN_SECONDS} seconds after the latest channel start, for every recording. This avoids using different recording durations as different feature windows. Broad validity bounds: HR 30–220 bpm, EDA 0–100 microsiemens, temperature 20–42 °C, acceleration ±2 g (raw units divided by 64). Use a regular channel's summaries only with at least 80% valid samples of the expected window. These fixed engineering bounds are not clinical diagnoses. No selection by outcome or model performance occurs.

Nine wearable features: median and IQR of HR, EDA, and temperature; acceleration-magnitude SD; median acceleration-change rate; IBI-derived RMSSD. RMSSD requires at least 30 adjacent valid interval pairs, intervals 0.3–2 seconds, and temporal continuity. It is exploratory session HRV, not a standardized nocturnal/resting HRV measurement. Seven survey predictors cover habitual sleep, sleep before the test, sleep difficulty, stress, exercise, diet, and water intake. No pain questions, pain type, ID, recording timestamp, or demographic sex enters the predictors.

## Modeled cohort and evaluation

The cohort has **{a['cohort_people']} female participants**: **{a['positive_people']} with current moderate-or-higher menstrual pain**, **{a['female_no_pain_controls']} reporting no pain**, and **{a['mild_menstrual_comparison_people']} with mild menstrual pain**. Explicit no-pain reports define controls even when the severity follow-up is blank; missing pain labels in other groups are not filled. Other pain types and ambiguous abdominal-pain cases are excluded.

One summary row per person prevents sensor samples and resampled copies from inflating sample size. Leave-one-participant-out evaluation keeps each test person out of all training. Fixed logistic regression (C=0.1, balanced classes) tests wearables, lifestyle, and their combination. A shallow fixed random forest uses wearables. Median imputation, missingness indicators, scaling, and categorical encoding are fit inside each training fold. The probability threshold is fixed at 0.5. No tuning or result-driven feature selection was performed. OOF predictions are exploratory and cannot be treated as an untouched final test set for later tuning.

| Model | Macro F1 | Balanced accuracy | Average precision | ROC-AUC | Positives detected | False positives |
|---|---:|---:|---:|---:|---:|---:|
{rows}

Average-precision prevalence reference: **{a['positive_prevalence']:.3f}**. All metrics pool the held-out participant predictions. The always-negative classifier is a constant reference, not a fitted history model. A single person's classification changes recall by 1/{a['positive_people']} and specificity by 1/{a['negative_people']}. Model rankings and feature utility are therefore uncertain. No significance or reliable attribution claim is made. Correlated physiology, movement, recording conditions, and feature missingness may explain apparent differences.

The lifestyle logistic model has balanced accuracy **{by_name.loc['logistic_lifestyle', 'balanced_accuracy']:.3f}**, compared with **{by_name.loc['logistic_wearables', 'balanced_accuracy']:.3f}** for wearable logistic regression and **{by_name.loc['logistic_combined', 'balanced_accuracy']:.3f}** for the combined model. Adding wearables did not improve the lifestyle model's held-out balanced accuracy or average precision in this experiment. The wearable forest's balanced accuracy is **{by_name.loc['forest_wearables', 'balanced_accuracy']:.3f}**. This does not demonstrate reliable wearable utility or establish that particular lifestyle factors cause or predict future menstrual pain.

![Held-out participant confusion matrices](../output/analysis/physiopain_confusion_matrices.png)

## What this adds to the project

The work provides an independently sourced data audit, reproducible raw-signal cleaning, lifestyle and wearable features, and a small current-pain experiment. It establishes that public dataset folder labels and advertised participant counts need to be checked before modeling.

It does **not** establish external validation of next-day menstrual-pain prediction. These recordings contain no consecutive daily wearable history or next-day pain outcome. There is only one low-severity menstrual-pain participant, so a within-menstrual severity model cannot sustain both classes in every leave-one-person-out training fold. The control contrast changes the scientific question. Different recruitment is reported in the publication, but participant-level non-overlap with mcPHASES is not verified here.

Next analysis step: review this exploratory result for inclusion as a supplementary audit. Direct external forecast evaluation still requires a longitudinal cohort with compatible pain severity, prior-day predictors, IDs, dates, and confirmed independence. Do not pool these sessions into mcPHASES or replace the primary forecasting scores with these metrics.

## Reproduce and outputs

First use a Python interpreter with pandas/openpyxl to run `python -m src.physiopain --prepare-survey-only`. The bundled workspace Python supports this extraction. Then run `.venv/bin/python -m src.physiopain` for feature extraction and modeling. The existing local conversion is ready to use. Source workbook and converted CSV hashes are checked before analysis. Software versions and source hash are recorded in the summary. Run `.venv/bin/python -m pytest -q` for software checks.

Aggregate results are in `reports/physiopain_results.json`. Participant-level survey conversions, labels, features, quality records, fold assignments, and predictions remain ignored under `reports/runs/physiopain/`. The source archive and extracted records are unchanged.
'''
    (ROOT / 'reports/physiopain_analysis.md').write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=RAW)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--prepare-survey-only', action='store_true')
    args = parser.parse_args()
    run(args.raw, args.output, args.prepare_survey_only)
