import numpy as np
import pandas as pd
import pytest

from src.mpis import (BASE_COLUMNS, baseline_features, exact_pairs,
                      observed_daily)


def trial():
    return pd.DataFrame({
        'unique_id': ['a'] * 4 + ['b'] * 2,
        'invite_code': ['a'] * 4 + ['b'] * 2,
        'inferred_day_of_study': [1, 2, 3, 4, 1, 2],
        'imputed': [False, True, False, False, False, False],
        'pain': [0., 9., 5., 3., 7., 4.],
        'survey1_question2_response': [0., 9., 5., 3., 7., 4.],
        'measurement_time': ['2025-01-01 18:00Z', '2025-01-02 18:00Z',
                             '2025-01-03 18:00Z', '2025-01-04 18:00Z',
                             '2025-01-01 18:00Z', '2025-01-02 18:00Z'],
        'phase': ['A1', 'A1', 'A1', 'B', 'A1', 'A1'],
        'tablets': [0.] * 6, 'mood': [0.] * 6,
        'symptoms_count': [0.] * 6, 'menstruating': [False] * 6,
    })


def test_imputed_prior_and_missing_day_never_create_a_forecast_pair():
    daily = observed_daily(trial())
    assert len(daily) == 5
    pairs = exact_pairs(daily).set_index(['id', 'day'])
    assert pairs.index.tolist() == [('a', 4), ('b', 2)]
    assert pairs.loc[('a', 4), 'previous_nrs'] == 5
    assert pairs.loc[('b', 2), 'previous_nrs'] == 7
    assert pairs.loc[('a', 4), 'target'] == 0
    assert pairs.loc[('b', 2), 'target'] == 1


def test_imputed_target_is_excluded_even_if_it_has_a_filled_pain_value():
    d = trial()
    d.loc[5, 'imputed'] = True
    pairs = exact_pairs(observed_daily(d))
    assert pairs.id.tolist() == ['a']


def test_control_phase_scope_requires_both_days_and_a1_sensitivity_is_stricter():
    d = trial()
    d.loc[2:3, 'phase'] = 'A2'
    pairs = exact_pairs(observed_daily(d)).set_index('id')
    assert pairs.loc['a', 'control_only']
    assert not pairs.loc['a', 'preintervention_only']
    assert pairs.loc['b', 'preintervention_only']
    transition = exact_pairs(observed_daily(trial())).set_index('id')
    assert not transition.loc['a', 'control_only']


def test_adjacent_relative_days_with_nonadjacent_dates_fail():
    d = trial()
    d.loc[5, 'measurement_time'] = '2025-01-04 18:00Z'
    with pytest.raises(ValueError, match='timestamps'):
        exact_pairs(observed_daily(d))


def test_duplicate_keys_or_inconsistent_original_pain_fail():
    d = trial()
    with pytest.raises(ValueError, match='Duplicate'):
        observed_daily(pd.concat([d, d.iloc[[0]]]))
    d.loc[0, 'survey1_question2_response'] = 4
    with pytest.raises(ValueError, match='original survey'):
        observed_daily(d)


def test_unknown_imputation_flags_are_rejected():
    d = trial().astype({'imputed': object})
    d.loc[0, 'imputed'] = 'False'
    with pytest.raises(ValueError, match='imputation flag'):
        observed_daily(d)


def test_complete_unique_id_key_overrides_the_partial_source_id_column():
    d = trial()
    d['id'] = ['partial'] * len(d)
    observed = observed_daily(d)
    assert observed.columns.tolist().count('id') == 1
    assert set(observed.id) == {'a', 'b'}


def test_baseline_sentinels_are_missing_and_bmi_has_correct_units():
    data = {'unique_id': ['a', 'b'], 'Height': [200, -999], 'Weight': [80, 60]}
    data.update({column: ['yes', '-999 = not answered'] for column in BASE_COLUMNS.values()})
    clean = baseline_features(pd.DataFrame(data)).set_index('id')
    assert clean.loc['a', 'bmi'] == 20
    assert np.isnan(clean.loc['b', 'bmi'])
    assert clean.loc['b', 'smoking'] == 'Missing'
    assert not any('Pain' in column or 'pain' in column for column in clean)
