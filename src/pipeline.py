"""Manifest-driven mcPHASES preparation and participant-held-out binary forecasting.
Raw schemas/labels must be verified before use. No inferred pain label mappings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import os

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (balanced_accuracy_score, confusion_matrix, f1_score,
                             roc_auc_score, ConfusionMatrixDisplay)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

KEY = ['id', 'day']


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def inventory(root, output):
    """Headers/counts only: does not expose participant values in inventory."""
    records = []
    for p in sorted(Path(root).rglob('*')):
        if not p.is_file():
            continue
        item = {'file': str(p.relative_to(root)), 'bytes': p.stat().st_size}
        if p.suffix.lower() in {'.csv', '.tsv'}:
            sep = '\t' if p.suffix.lower() == '.tsv' else ','
            header = pd.read_csv(p, sep=sep, nrows=0)
            item['columns'] = list(header.columns)
            item['rows'] = sum(len(c) for c in pd.read_csv(p, sep=sep, usecols=[0], chunksize=100000))
        records.append(item)
    write_json(output, records)
    return records


def load_table(root, spec, cols):
    p = (Path(root) / spec['file']).resolve()
    if not p.is_relative_to(Path(root).resolve()):
        raise ValueError('Manifest file must remain inside the raw-data directory')
    df = pd.read_csv(p, sep='\t' if p.suffix.lower() == '.tsv' else ',',
                     usecols=list(dict.fromkeys([spec['id'], spec['day']] + cols)),
                     dtype={spec['id']: 'string'})
    df = df.rename(columns={spec['id']: 'id', spec['day']: 'day'})
    day = pd.to_numeric(df.day, errors='raise')
    if df.id.isna().any() or day.isna().any() or (day % 1 != 0).any():
        raise ValueError('Participant IDs and integer study days must be complete')
    df['day'] = day.astype(int)
    return df


def prepare(root, manifest):
    spec = manifest['outcomes']
    outcomes = load_table(root, spec, [spec['pain']])
    if outcomes.duplicated(KEY).any():
        raise ValueError('Duplicate participant-day outcomes; resolve diary conflicts explicitly')
    raw = outcomes[spec['pain']].astype('string').str.strip().str.lower()
    mapping = {str(k).strip().lower(): int(v) for k, v in manifest['label_map'].items()}
    if set(mapping.values()) != {0, 1}:
        raise ValueError('Binary label map must define classes 0 and 1')
    unknown = set(raw.dropna().unique()) - set(mapping)
    if unknown:
        raise ValueError(f'Unmapped pain labels: {sorted(unknown)}. Verify codebook; never guess.')
    outcomes = outcomes[KEY].assign(pain=raw.map(mapping))
    daily = outcomes.copy()
    feature_names = set()
    for spec in manifest['tables']:
        df = load_table(root, spec, list(spec['features']))
        named = {}
        for col, config in spec['features'].items():
            name, agg = config['name'], config['agg']
            if name in feature_names or name in {'id', 'day', 'pain', 'previous_pain'}:
                raise ValueError(f'Reserved or duplicate feature name: {name}')
            if agg not in {'mean', 'sum', 'min', 'max', 'median'}:
                raise ValueError(f'Unsupported aggregation: {agg}')
            df[col] = pd.to_numeric(df[col], errors='raise')
            named[name] = (col, (lambda x: x.sum(min_count=1)) if agg == 'sum' else agg)
            feature_names.add(name)
        grouped = df.groupby(KEY).agg(**named).reset_index()
        daily = daily.merge(grouped, on=KEY, how='outer', validate='one_to_one')
    daily = daily.sort_values(KEY).reset_index(drop=True)
    return daily


def make_forecast(daily):
    if daily.duplicated(KEY).any():
        raise ValueError('Daily input must have one row per participant and day')
    features = [c for c in daily if c not in KEY + ['pain']]
    # Join exact day t-1; do not forward-fill across missing days or study rounds.
    prior = daily[KEY + features + ['pain']].copy()
    prior['day'] += 1
    prior = prior.rename(columns={c: c + '_lag1' for c in features} | {'pain': 'previous_pain'})
    result = daily[KEY + ['pain']].merge(prior, on=KEY, how='left', validate='one_to_one')
    return result.dropna(subset=['pain']).reset_index(drop=True)


class MissingnessFilter(BaseEstimator, TransformerMixin):
    """Choose usable features using only the training fold."""
    def __init__(self, threshold=0.6):
        self.threshold = threshold

    def fit(self, X, y=None):
        self.keep_ = np.asarray(pd.isna(X).mean(axis=0) <= self.threshold)
        if not self.keep_.any():
            raise ValueError('No features pass the training-fold missingness threshold')
        return self

    def transform(self, X):
        return np.asarray(X)[:, self.keep_]


def model_pipeline(model):
    return Pipeline([('missingness', MissingnessFilter()),
                     ('impute', SimpleImputer(strategy='median', add_indicator=True)),
                     ('scale', StandardScaler()), ('model', model)])


def score(y, pred, prob):
    return {'macro_f1': float(f1_score(y, pred, labels=[0, 1], average='macro', zero_division=0)),
            'balanced_accuracy': float(balanced_accuracy_score(y, pred)),
            'roc_auc': float(roc_auc_score(y, prob)) if len(np.unique(y)) == 2 else None}


def run(daily, out, synthetic=False, folds=5, extended=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    forecast = make_forecast(daily)
    if forecast.pain.nunique() != 2:
        raise ValueError('Both target classes are required')
    X = forecast.drop(columns=KEY + ['pain']).replace([np.inf, -np.inf], np.nan)
    if X.shape[1] == 0:
        raise ValueError('No predictors supplied')
    y = forecast.pain.astype(int).to_numpy()
    groups = forecast.id.to_numpy()
    n_folds = min(folds, forecast.id.nunique())
    if n_folds < 2:
        raise ValueError('At least two participants are required')
    splits = list(GroupKFold(n_splits=n_folds).split(X, y, groups))
    for tr, te in splits:
        assert not set(groups[tr]) & set(groups[te])
        if len(np.unique(y[tr])) < 2:
            raise ValueError('A training fold has only one class; revise splits/sample eligibility')
    models = {
        'majority': DummyClassifier(strategy='most_frequent'),
        'logistic_regression': LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42),
        'decision_tree': DecisionTreeClassifier(max_depth=4, min_samples_leaf=10, class_weight='balanced', random_state=42),
        'random_forest': RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_leaf=5,
                                               class_weight='balanced_subsample', random_state=42, n_jobs=-1)}
    feature_sets = {name: list(X.columns) for name in models}
    feature_sets['majority'] = []
    if extended:
        models['flow_timing_proxy'] = LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42)
        feature_sets['flow_timing_proxy'] = ['days_since_observed_flow_lag1', 'flow_lag1']
        models['logistic_without_previous_pain'] = sklearn.base.clone(models['logistic_regression'])
        feature_sets['logistic_without_previous_pain'] = [c for c in X if c != 'previous_pain']
        models['random_forest_wearables_only'] = sklearn.base.clone(models['random_forest'])
        excluded = {'previous_pain', 'stress_lag1', 'moodswing_lag1', 'sleepissue_lag1',
                    'flow_lag1', 'days_since_observed_flow_lag1'}
        feature_sets['random_forest_wearables_only'] = [c for c in X if c not in excluded]
    metrics, predictions, importances, fold_metrics, retained, coefficients = [], [], [], [], [], []
    fold_assignment = np.zeros(len(y), dtype=int)
    for name, model in models.items():
        Xm = X[feature_sets[name]]
        pred, prob = np.zeros(len(y), dtype=int), np.zeros(len(y))
        for fold, (tr, te) in enumerate(splits):
            fold_assignment[te] = fold
            if name == 'majority':
                fitted = model.fit(np.zeros((len(tr), 1)), y[tr])
                xt = np.zeros((len(te), 1))
            else:
                fitted = model_pipeline(sklearn.base.clone(model)).fit(Xm.iloc[tr], y[tr])
                xt = Xm.iloc[te]
                kept = np.asarray(Xm.columns)[fitted['missingness'].keep_]
                retained.extend({'model': name, 'fold': fold, 'feature': col} for col in kept)
                if name == 'logistic_regression':
                    names = fitted['impute'].get_feature_names_out(kept)
                    coefficients.extend({'fold': fold, 'feature': col, 'coefficient': float(value)}
                                        for col, value in zip(names, fitted['model'].coef_[0]))
            pred[te] = fitted.predict(xt)
            prob[te] = fitted.predict_proba(xt)[:, 1]
            fold_metrics.append({'model': name, 'fold': fold, 'test_participants': len(set(groups[te])),
                                 **score(y[te], pred[te], prob[te])})
            if name == 'random_forest':
                imp = permutation_importance(fitted, xt, y[te], scoring='balanced_accuracy',
                                             n_repeats=5, random_state=42, n_jobs=1)
                importances.extend({'fold': fold, 'feature': c, 'importance': float(v)}
                                   for c, v in zip(Xm.columns, imp.importances_mean))
        metrics.append({'model': name, **score(y, pred, prob)})
        predictions.append(forecast[KEY].assign(fold=fold_assignment, model=name, target=y, predicted=pred, probability=prob))
        fig, ax = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay(confusion_matrix(y, pred, labels=[0, 1]),
                               display_labels=['No/low', 'Moderate+']).plot(ax=ax, colorbar=False)
        ax.set_title(('SYNTHETIC CHECK: ' if synthetic else '') + name.replace('_', ' '))
        fig.tight_layout()
        fig.savefig(out / f'{name}_confusion.png', dpi=160)
        plt.close(fig)
    # Persistence uses only the exact prior day's known label; training majority fills missing prior labels.
    previous = forecast.previous_pain.to_numpy(dtype=float)
    prob = np.zeros(len(y))
    for tr, te in splits:
        majority = int(np.bincount(y[tr], minlength=2).argmax())
        prob[te] = np.where(np.isnan(previous[te]), majority, previous[te])
    metrics.append({'model': 'previous_pain', **score(y, prob.astype(int), prob)})
    predictions.append(forecast[KEY].assign(fold=fold_assignment, model='previous_pain', target=y, predicted=prob.astype(int), probability=prob))
    for fold, (_, te) in enumerate(splits):
        fold_metrics.append({'model': 'previous_pain', 'fold': fold, 'test_participants': len(set(groups[te])),
                             **score(y[te], prob[te].astype(int), prob[te])})
    pd.DataFrame(retained).to_csv(out / 'retained_features.csv', index=False)
    pd.DataFrame(coefficients).to_csv(out / 'logistic_coefficients.csv', index=False)
    pd.DataFrame(metrics).to_csv(out / 'metrics.csv', index=False)
    pd.DataFrame(fold_metrics).to_csv(out / 'fold_metrics.csv', index=False)
    prediction_frame = pd.concat(predictions)
    prediction_frame.to_csv(out / 'predictions_private.csv', index=False)
    pd.DataFrame(importances).to_csv(out / 'permutation_importance.csv', index=False)
    X.isna().mean().rename('missing_fraction').to_csv(out / 'missingness.csv')
    forecast.to_csv(out / 'forecast_private.csv', index=False)
    summary = {'status': 'SYNTHETIC_SOFTWARE_CHECK_ONLY' if synthetic else 'REAL_DATA_EXPLORATORY_CV',
               'participants': int(forecast.id.nunique()), 'labeled_days': len(forecast),
               'daily_rows': len(daily), 'features': list(X.columns),
               'class_counts': {str(k): int(v) for k, v in pd.Series(y).value_counts().items()},
               'folds': n_folds, 'prediction': 'day t pain from exact day t-1 data',
               'python': platform.python_version(), 'sklearn': sklearn.__version__,
               'limitations': ['Fixed hyperparameters; no independent final test set.',
                               'Flow-history proxy is not a verified true cycle-day measurement.',
                               'Subgroup estimates require sufficient participants and remain exploratory.',
                               'Permutation importance is exploratory; correlated predictors may share importance.']}
    feature_sets['previous_pain'] = ['previous_pain']
    summary['feature_sets'] = feature_sets
    summary['model_parameters'] = {name: model.get_params() for name, model in models.items()}
    write_json(out / 'summary.json', summary)
    fig, ax = plt.subplots(figsize=(8, 4))
    frame = pd.DataFrame(metrics).set_index('model')
    frame[['macro_f1', 'balanced_accuracy']].plot.barh(ax=ax)
    ax.set_xlim(0, 1)
    ax.set_title('SYNTHETIC SOFTWARE CHECK ONLY' if synthetic else 'Participant-held-out cross-validation')
    fig.tight_layout()
    fig.savefig(out / 'model_comparison.png', dpi=160)
    plt.close(fig)
    return summary


def synthetic_daily():
    rng = np.random.default_rng(42)
    rows = []
    for person in range(12):
        previous = 0
        for day in list(range(1, 31)) + list(range(905, 920)):
            sleep = rng.normal(7, 1)
            stress = rng.uniform(0, 4)
            pain = int(rng.random() < 1 / (1 + np.exp(-(-1.5 + .5 * stress + .8 * previous))))
            rows.append([f'SYNTHETIC_{person}', day, pain, sleep, stress, rng.normal(65, 5)])
            previous = pain
    df = pd.DataFrame(rows, columns=KEY + ['pain', 'sleep', 'stress', 'resting_hr'])
    df.loc[rng.choice(len(df), 30, replace=False), 'sleep'] = np.nan
    return df


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inventory')
    p.add_argument('--raw', default='data/raw')
    p.add_argument('--output', default='reports/data_inventory.json')
    p = sub.add_parser('run')
    p.add_argument('--raw', default='data/raw')
    p.add_argument('--manifest', required=True)
    p.add_argument('--output', default='reports/runs/real')
    p = sub.add_parser('smoke')
    p.add_argument('--output', default='reports/runs/synthetic')
    args = parser.parse_args()
    if args.command == 'inventory':
        inventory(args.raw, args.output)
    elif args.command == 'smoke':
        print(json.dumps(run(synthetic_daily(), args.output, synthetic=True), indent=2))
    else:
        manifest = json.loads(Path(args.manifest).read_text())
        daily = prepare(args.raw, manifest)
        summary = run(daily, args.output)
        summary['manifest_sha256'] = hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest()
        write_json(Path(args.output) / 'summary.json', summary)


if __name__ == '__main__':
    main()
