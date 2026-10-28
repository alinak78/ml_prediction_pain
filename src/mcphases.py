"""Verified local mcPHASES 1.0.0 adapter. No restricted data are copied to source control."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from src.pipeline import KEY, run, write_json

LIKERT = {'Not at all': 0, 'Very Low/Little': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Very High': 5}
FLOW = {'Not at all': 0, 'Spotting / Very Light': 1, 'Light': 2, 'Somewhat Light': 3,
        'Moderate': 4, 'Somewhat Heavy': 5, 'Heavy': 6, 'Very Heavy': 7}


def ordinal(series, mapping, numeric=False):
    clean = series.astype('string').str.strip()
    lookup = dict(mapping)
    if numeric:
        lookup.update({str(i): i for i in range(6)})
    unknown = set(clean.dropna().unique()) - set(lookup)
    if unknown:
        raise ValueError(f'Unexpected ordinal labels: {unknown}')
    return clean.map(lookup).astype(float)


def previous_flow_distance(frame):
    """At end of day d, distance since last *observed* positive flow through d.
    This is a history proxy, not a true cycle phase or cycle-day ground truth.
    """
    result = pd.Series(np.nan, index=frame.index, dtype=float)
    for _, idx in frame.groupby('id', sort=False).groups.items():
        ordered = frame.loc[idx].sort_values('day')
        last_day = None
        last_observation = None
        for index, row in ordered.iterrows():
            if last_observation is not None and row.day - last_observation > 90:
                last_day = None
            if pd.notna(row.flow) and row.flow > 0:
                last_day = row.day
            if last_day is not None:
                result.at[index] = row.day - last_day
            last_observation = row.day
    return result


def prepare_mcphases(raw, out):
    raw, out = Path(raw), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    audit = {'primary_interval': 2022, 'tables': {}, 'excluded': {}, 'rules': [
        'Primary analysis uses 2022 only: 2024 contains just seven nonmissing cramp outcomes.',
        'Cramp labels 0/1/2 map to no-or-low pain; 3/4/5 map to moderate-or-higher pain.',
        'All model features are joined from exact prior study day; hormone/phase labels excluded.',
        'Exact duplicate records removed before aggregation; repeated distinct daily summaries use median.',
        'Sleep uses end-day availability; main sleeps only; multiple distinct sessions use median to avoid summing revisions.',
        'Fitbit stress score uses READY statuses only; failed and IN_PROGRESS/NO_DATA scores excluded.',
        'Prespecified broad plausible ranges set impossible predictor values to missing, not labels.',
        'Temperature uses absolute nightly temperature; proprietary personal-baseline deviations excluded.',
        'HRV uses coverage >=0.8; retrospective hormones and raw high-frequency heart rate/glucose excluded.',
        'Flow timing uses history of observed flow only, not retrospective hormone-derived cycle phases.'
    ]}

    def read(name):
        path = raw / (name + '.csv')
        df = pd.read_csv(path, dtype={'id': 'string'})
        all_rows = len(df)
        if 'study_interval' in df:
            df = df[df.study_interval == 2022].copy()
        before = len(df)
        df = df.drop_duplicates().copy()
        audit['tables'][name] = {'file_bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                 'all_rows': all_rows, 'primary_rows': before, 'exact_duplicates_removed': before-len(df)}
        return df

    diary = read('hormones_and_selfreport')
    if diary.duplicated(['id', 'day_in_study']).any():
        raise ValueError('Conflicting diary participant-day keys')
    daily = diary[['id', 'day_in_study']].rename(columns={'day_in_study': 'day'})
    cramp = ordinal(diary.cramps, LIKERT)
    daily['pain'] = (cramp >= 3).astype(float).where(cramp.notna())
    for col in ['stress', 'moodswing', 'sleepissue']:
        daily[col] = ordinal(diary[col], LIKERT, numeric=(col == 'stress'))
    daily['flow'] = ordinal(diary.flow_volume, FLOW)
    daily['days_since_observed_flow'] = previous_flow_distance(daily)
    audit['diary_rows'] = len(diary)
    audit['raw_cramp_counts'] = diary.cramps.value_counts(dropna=False).rename(index={np.nan: 'missing'}).to_dict()
    audit['missing_cramp_days'] = int(diary.cramps.isna().sum())

    def merge(name, mapping, day='day_in_study', filters=None, bounds=None):
        nonlocal daily
        df = read(name)
        if filters is not None:
            before = len(df)
            df = df.loc[filters(df)].copy()
            audit['tables'][name]['filtered_records'] = before - len(df)
        invalid = {}
        for col in mapping:
            df[col] = pd.to_numeric(df[col], errors='raise')
            lo, hi = (bounds or {}).get(col, (-np.inf, np.inf))
            mask = df[col].notna() & ~df[col].between(lo, hi)
            invalid[col] = int(mask.sum())
            df.loc[mask, col] = np.nan
        audit['tables'][name]['values_outside_bounds'] = invalid
        audit['tables'][name]['distinct_records_after_filters'] = len(df)
        aggregate = df.groupby(['id', day])[list(mapping)].median().reset_index().rename(columns={day: 'day', **mapping})
        if aggregate.duplicated(KEY).any():
            raise ValueError('Duplicate aggregated keys')
        daily = daily.merge(aggregate, on=KEY, how='left', validate='one_to_one')

    merge('active_minutes', {'sedentary': 'sedentary_minutes', 'lightly': 'light_activity_minutes',
                            'moderately': 'moderate_activity_minutes', 'very': 'vigorous_activity_minutes'},
          bounds={c: (0, 1440) for c in ['sedentary', 'lightly', 'moderately', 'very']})
    merge('resting_heart_rate', {'value': 'resting_hr'}, bounds={'value': (30, 220)})
    merge('sleep', {'minutesasleep': 'sleep_minutes', 'minutesawake': 'sleep_awake_minutes', 'efficiency': 'sleep_efficiency'},
          day='sleep_end_day_in_study', filters=lambda d: d.mainsleep.eq(True),
          bounds={'minutesasleep': (0, 1440), 'minutesawake': (0, 1440), 'efficiency': (0, 100)})
    merge('sleep_score', {'overall_score': 'sleep_score', 'deep_sleep_in_minutes': 'deep_sleep_minutes',
                          'restlessness': 'sleep_restlessness'},
          bounds={'overall_score': (0, 100), 'deep_sleep_in_minutes': (0, 1440), 'restlessness': (0, 1)})
    merge('computed_temperature', {'nightly_temperature': 'nightly_temperature'}, day='sleep_end_day_in_study',
          bounds={'nightly_temperature': (20, 45)})
    merge('respiratory_rate_summary', {'full_sleep_breathing_rate': 'respiratory_rate'},
          bounds={'full_sleep_breathing_rate': (4, 50)})
    merge('heart_rate_variability_details', {'rmssd': 'hrv_rmssd'},
          filters=lambda d: d.coverage.ge(.8), bounds={'rmssd': (0, 500)})
    merge('stress_score', {'stress_score': 'fitbit_stress_score'},
          filters=lambda d: d.status.isin(['READY', 'READY_NOT_PREMIUM']) & ~d.calculation_failed.eq(True),
          bounds={'stress_score': (1, 100)})
    # A single missing session/stage is not imputed here; learned imputation stays in CV folds.
    daily = daily.sort_values(KEY).reset_index(drop=True)
    daily.to_csv(out / 'daily_private.csv', index=False)
    daily.isna().mean().rename('missing_fraction').to_csv(out / 'daily_missingness.csv')
    write_json(out / 'cleaning_audit.json', audit)
    return daily, audit


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--raw', help='Authorized dataset folder; defaults to the single mcphases folder beside the project')
    p.add_argument('--output', default='reports/runs/mcphases_2022')
    args = p.parse_args()
    if args.raw is None:
        candidates = [d for d in Path(__file__).resolve().parents[2].glob('mcphases*')
                      if d.is_dir() and (d/'hormones_and_selfreport.csv').is_file()]
        if len(candidates) != 1:
            p.error('Pass --raw with the authorized dataset directory')
        args.raw = str(candidates[0])
    daily, audit = prepare_mcphases(args.raw, args.output)
    summary = run(daily, args.output, extended=True)
    summary['raw_directory'] = str(Path(args.raw).resolve())
    summary['primary_interval'] = 2022
    summary['analysis_code_sha256'] = {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                                       for name in ['mcphases.py', 'pipeline.py']}
    summary['cleaning_audit'] = 'cleaning_audit.json'
    summary['label_definition'] = 'Not at all/Very Low-Little/Low versus Moderate/High/Very High'
    write_json(Path(args.output) / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
