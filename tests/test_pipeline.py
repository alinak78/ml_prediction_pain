import json
import numpy as np
import pandas as pd
import pytest
from src.pipeline import make_forecast, prepare, MissingnessFilter


def test_lag_is_exact_day_and_never_crosses_people_or_rounds():
    daily = pd.DataFrame({'id': ['a', 'a', 'a', 'b', 'b'], 'day': [1, 2, 905, 1, 2],
                          'pain': [0, 1, 1, 1, 0], 'sleep': [7, 8, 9, 5, 6]})
    out = make_forecast(daily).set_index(['id', 'day'])
    assert out.loc[('a', 2), 'sleep_lag1'] == 7
    assert out.loc[('b', 2), 'previous_pain'] == 1
    assert pd.isna(out.loc[('a', 905), 'previous_pain'])
    assert pd.isna(out.loc[('a', 1), 'sleep_lag1'])
    assert 'sleep' not in out.columns


def test_missing_labels_excluded_but_prior_features_retained():
    daily = pd.DataFrame({'id': ['a'] * 3, 'day': [1, 2, 3],
                          'pain': [0, np.nan, 1], 'sleep': [7, 8, 9]})
    out = make_forecast(daily).set_index('day')
    assert list(out.index) == [1, 3]
    assert out.loc[3, 'sleep_lag1'] == 8
    assert pd.isna(out.loc[3, 'previous_pain'])


def test_missingness_filter_learns_on_train_only():
    train = pd.DataFrame({'x': [1, 2, 3], 'y': [np.nan] * 3})
    f = MissingnessFilter().fit(train)
    test = pd.DataFrame({'x': [np.nan], 'y': [8]})
    assert f.transform(test).shape == (1, 1)
    assert np.isnan(f.transform(test)[0, 0])


def manifest():
    return {'label_map': {'none': 0, 'severe': 1},
            'outcomes': {'file': 'diary.csv', 'id': 'person', 'day': 'study_day', 'pain': 'cramps'},
            'tables': [{'file': 'activity.csv', 'id': 'person', 'day': 'study_day',
                        'features': {'minutes': {'name': 'activity', 'agg': 'sum'}}}]}


def test_aggregation_preserves_all_missing_and_sensor_only_days(tmp_path):
    pd.DataFrame({'person': ['a', 'a'], 'study_day': [1, 3], 'cramps': ['none', 'severe']}).to_csv(tmp_path/'diary.csv', index=False)
    pd.DataFrame({'person': ['a', 'a', 'a'], 'study_day': [1, 1, 2],
                  'minutes': [np.nan, np.nan, 8]}).to_csv(tmp_path/'activity.csv', index=False)
    result = prepare(tmp_path, manifest()).set_index('day')
    assert pd.isna(result.loc[1, 'activity'])
    assert result.loc[2, 'activity'] == 8
    forecast = make_forecast(result.reset_index())
    assert forecast.loc[forecast.day == 3, 'activity_lag1'].iloc[0] == 8


def test_unknown_pain_and_duplicate_diaries_fail(tmp_path):
    pd.DataFrame({'person': ['a'], 'study_day': [1], 'cramps': ['unknown']}).to_csv(tmp_path/'diary.csv', index=False)
    with pytest.raises(ValueError, match='Unmapped pain'):
        prepare(tmp_path, manifest())
    pd.DataFrame({'person': ['a', 'a'], 'study_day': [1, 1], 'cramps': ['none', 'severe']}).to_csv(tmp_path/'diary.csv', index=False)
    with pytest.raises(ValueError, match='Duplicate'):
        prepare(tmp_path, manifest())


def test_flow_history_uses_only_past_and_resets_round_gap():
    from src.mcphases import previous_flow_distance
    frame = pd.DataFrame({'id': ['a'] * 5, 'day': [1, 2, 3, 4, 905], 'flow': [0, 1, np.nan, 0, 0]})
    distance = previous_flow_distance(frame)
    assert np.isnan(distance.iloc[0])
    assert distance.iloc[1:4].tolist() == [0, 1, 2]
    assert np.isnan(distance.iloc[4])


def test_likert_mapping_is_explicit_and_missing_stays_missing():
    from src.mcphases import ordinal, LIKERT
    result = ordinal(pd.Series(['Not at all', 'Low', 'Moderate', 'Very High', None]), LIKERT)
    assert result.iloc[:4].tolist() == [0, 2, 3, 5]
    assert np.isnan(result.iloc[4])
    with pytest.raises(ValueError, match='Unexpected'):
        ordinal(pd.Series(['moderately painful']), LIKERT)


def test_bootstrap_count_metrics_match_sklearn():
    from src.evaluation import metrics_from_counts
    from src.pipeline import score
    y = np.array([0,0,0,1,1,1])
    pred = np.array([0,0,1,0,1,1])
    f1, ba = metrics_from_counts(np.array([2,1,1,2]))
    expected = score(y, pred, pred)
    assert f1 == pytest.approx(expected['macro_f1'])
    assert ba == pytest.approx(expected['balanced_accuracy'])
