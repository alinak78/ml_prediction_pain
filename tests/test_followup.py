import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score
from src.followup import onset_mask, operational_metrics, weighted_average_precision


def test_onset_eligibility_uses_observed_previous_pain_only():
    df=pd.DataFrame({'previous_pain':[0,0,1,np.nan], 'target':[0,1,0,1]})
    assert onset_mask(df).tolist()==[True,True,False,False]
    df['target']=1-df.target
    assert onset_mask(df).tolist()==[True,True,False,False]


def test_operational_counts_and_false_alarm_denominator():
    r=operational_metrics([0,0,1,1],[1,0,1,0],[.8,.1,.7,.2])
    assert (r['tn'],r['fp'],r['fn'],r['tp'])==(1,1,1,1)
    assert r['false_alarms_per_100_days']==25
    assert r['false_positive_rate']==.5
    assert r['precision']==r['recall']==.5


def test_no_alert_baseline_has_zero_precision_and_recall_but_valid_ap():
    r=operational_metrics([0,0,0,1],[0,0,0,0],[0,0,0,0])
    assert r['precision']==r['recall']==0
    assert r['average_precision']==.25
    assert r['false_alarms_per_100_days']==0


def test_weighted_ap_matches_sklearn_with_ties_and_zero_weights():
    y=np.array([0,1,1,0,1]);prob=np.array([.2,.2,.8,.8,.5])
    weights=np.array([[1,2,1,0,3],[0,1,2,3,1],[1,0,0,1,0]])
    observed=weighted_average_precision(y,prob,weights)
    for i in range(2):
        assert observed[i]==pytest.approx(average_precision_score(y,prob,sample_weight=weights[i]))
    assert np.isnan(observed[2])
