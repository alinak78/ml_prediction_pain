import numpy as np
import pandas as pd
from pandas.testing import assert_series_equal

from src.literature_analysis import (CLINICAL_CATEGORICAL, CLINICAL_NUMERIC,
                                     clinical_features, confirmed_onset_clock)
from src.mpis import BASE_COLUMNS


def test_onset_clock_requires_observed_transition_and_ignores_spotting():
    daily = pd.DataFrame({'id': ['a'] * 6, 'day': [1, 2, 3, 4, 5, 6],
                          'flow': [2., 0., 1., 2., 3., 0.]})
    clock = confirmed_onset_clock(daily)
    assert clock.iloc[:3].isna().all()
    assert clock.iloc[3:].tolist() == [0., 1., 2.]


def test_onset_clock_resets_on_gaps_missing_flow_and_participant_changes():
    daily = pd.DataFrame({'id': ['a'] * 8 + ['b'],
                          'day': [1, 2, 3, 5, 6, 7, 8, 9, 9],
                          'flow': [0., 2., 3., 3., np.nan, 3., 0., 2., 3.]})
    clock = confirmed_onset_clock(daily)
    assert clock.iloc[1:3].tolist() == [0., 1.]
    assert clock.iloc[3:7].isna().all()
    assert clock.iloc[7] == 0
    assert np.isnan(clock.iloc[8])


def test_future_observations_do_not_rewrite_past_clock_and_sorting_is_local():
    daily = pd.DataFrame({'id': ['a'] * 5, 'day': [1, 2, 3, 4, 5],
                          'flow': [0., 2., 0., 2., 3.]})
    assert_series_equal(confirmed_onset_clock(daily.iloc[:3]),
                        confirmed_onset_clock(daily).iloc[:3])
    shuffled = daily.sample(frac=1, random_state=8)
    assert_series_equal(confirmed_onset_clock(shuffled).sort_index(),
                        confirmed_onset_clock(daily))


def test_clinical_missing_codes_are_not_disease_categories_or_numeric_births():
    data = {'unique_id': ['a', 'b', 'c', 'd'],
            'Height': [170.] * 4, 'Weight': [60.] * 4}
    data.update({col: ['yes'] * 4 for col in BASE_COLUMNS.values()})
    data.update({col: [12, -997, -998, -999] for col in CLINICAL_NUMERIC.values()})
    data.update({col: ['1 = Yes, suspected', '2 = Yes, diagnosed',
                       '-999.0', '-998 = not answered']
                 for col in CLINICAL_CATEGORICAL.values()})
    clean = clinical_features(pd.DataFrame(data))
    assert clean[list(CLINICAL_NUMERIC)].iloc[1:].isna().all().all()
    for col in CLINICAL_CATEGORICAL:
        assert clean[col].tolist() == ['1 = Yes, suspected', '2 = Yes, diagnosed',
                                      'Missing', 'Missing']
