import numpy as np
import pandas as pd
import pytest
import zipfile

from src.physiopain import (SEVERITY, SEX, TYPE, define_cohort,
                           ibi_rmssd, read_regular, summarize_recording)


def test_e4_metadata_rows_are_not_signal_samples():
    epoch, hz, samples = read_regular(b'1702992722.00\n4.000000\n35.79\n35.81\n')
    assert epoch == 1702992722.
    assert hz == 4
    assert samples[:, 0].tolist() == [35.79, 35.81]
    _, rate, acc = read_regular(b'1702992722,1702992722,1702992722\n32,32,32\n-27,17,57\n')
    assert rate == 32 and acc.tolist() == [[-27., 17., 57.]]


def test_hrv_does_not_bridge_missing_beats():
    # Consecutive 1-second intervals, with an isolated .5-second interval after
    # a long recording gap. Treating that pair as adjacent would inflate RMSSD.
    lines = ['1702992722, IBI']
    lines += [f'{i},1' for i in range(40, 80)]
    lines += ['120,.5']
    value, pairs = ibi_rmssd(('\n'.join(lines)).encode())
    assert pairs == 39
    assert value == pytest.approx(0.)


def test_insufficient_ibi_pairs_stay_missing():
    value, pairs = ibi_rmssd(b'1702992722, IBI\n40,1\n41,1\n42,1')
    assert pairs == 2 and np.isnan(value)
    assert np.isnan(ibi_rmssd(b'')[0])


def test_features_align_clocks_use_fixed_window_and_allow_empty_ibi(tmp_path):
    path = tmp_path / 'person.zip'
    def scalar(epoch, before, stable, after, count):
        samples = [before] * count + [stable] * 600 + [after] * 50
        return f'{epoch}\n1\n' + '\n'.join(map(str, samples))
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('HR.csv', scalar(1000, 200, 70, 210, 40))
        z.writestr('EDA.csv', scalar(1010, 90, .7, 95, 30))
        z.writestr('TEMP.csv', scalar(1000, 22, 34, 40, 40))
        z.writestr('ACC.csv', '1000,1000,1000\n1,1,1\n' + '\n'.join(['64,0,0'] * 690))
        z.writestr('IBI.csv', '')
    features, audit = summarize_recording(path)
    assert audit['feature_window_start_utc'] == 1040
    assert audit['feature_window_seconds'] == 600
    assert features['hr_median'] == 70 and features['hr_iqr'] == 0
    assert features['eda_median'] == pytest.approx(.7)
    assert features['temperature_median'] == 34
    assert features['acc_magnitude_sd'] == 0
    assert np.isnan(features['ibi_rmssd_ms'])


def test_cohort_uses_original_current_labels_and_explicit_no_pain():
    frame = pd.DataFrame({
        TYPE: ['Menstrual pain', 'Menstrual pain', 'Abdominal pain', 'No pain',
               'Menstrual pain', 'No pain', 'Headache'],
        SEVERITY: ['Moderate', 'Mild', 'Severe', None, None, None, 'Moderate'],
        SEX: ['Female', 'Female', 'Female', 'Female', 'Female', 'Male', 'Female'],
    }, index=['a', 'b', 'c', 'd', 'e', 'f', 'g'])
    result = define_cohort(frame)
    assert result.index.tolist() == ['a', 'b', 'd']
    assert result.target.tolist() == [1, 0, 0]
    assert result.loc['b', 'current_severity'] == 2
    assert np.isnan(result.loc['d', 'current_severity'])


def test_unrecognized_severity_fails_instead_of_silent_imputation():
    frame = pd.DataFrame({TYPE: ['Menstrual pain'], SEVERITY: ['unknown'], SEX: ['Female']})
    with pytest.raises(ValueError, match='Unknown severity'):
        define_cohort(frame)
