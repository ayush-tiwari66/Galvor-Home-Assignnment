import math

import numpy as np
import pandas as pd
import pytest

from lj.metrics import add_ad_metrics, pooled_metrics, safe_div


def ad(**overrides):
    row = dict(spend_inr=1000.0, impressions=10000.0, video_3s_views=3000.0, thruplays=750.0, link_clicks=100.0,
               add_to_carts=10.0, purchases=4.0, revenue_inr=2600.0)
    return row | overrides


def test_safe_div_scalar():
    assert safe_div(1, 4) == 0.25


@pytest.mark.parametrize("n,d", [(1, 0), (0, 0), (np.nan, 2), (2, np.nan)])
def test_safe_div_unavailable_is_nan(n, d):
    assert math.isnan(safe_div(n, d))


def test_safe_div_series_keeps_index():
    result = safe_div(pd.Series([1.0, 2.0], index=["a", "b"]), pd.Series([2.0, 0.0], index=["a", "b"]))
    assert result["a"] == 0.5 and math.isnan(result["b"])


def test_formulas_use_the_right_denominators():
    m = add_ad_metrics(pd.DataFrame([ad()])).iloc[0]
    assert m.hook_rate == pytest.approx(0.30)
    assert m.thruplay_rate == pytest.approx(0.075)
    assert m.hold_rate == pytest.approx(0.25)
    assert m.ctr == pytest.approx(0.01)
    assert m.atc_rate == pytest.approx(0.10)
    assert m.cvr == pytest.approx(0.04)
    assert m.roas == pytest.approx(2.6)
    assert m.cpa == pytest.approx(250.0)
    assert m.aov == pytest.approx(650.0)


def test_zero_purchases_give_undefined_cpa_not_zero_or_infinity():
    m = add_ad_metrics(pd.DataFrame([ad(purchases=0.0, revenue_inr=0.0)])).iloc[0]
    assert math.isnan(m.cpa) and math.isnan(m.aov)
    assert m.cvr == 0 and m.roas == 0


def test_pooled_is_sum_over_sum_not_mean_of_ratios():
    df = pd.DataFrame([ad(spend_inr=100.0, revenue_inr=500.0), ad(spend_inr=900.0, revenue_inr=900.0)])
    assert pooled_metrics(df)["roas"] == pytest.approx(1.4)  # the mean of the two ad ROAS values would be 3.0


def test_pooled_drops_a_missing_row_from_both_sides():
    good = ad(link_clicks=100.0, purchases=5.0, spend_inr=100.0, revenue_inr=300.0)
    missing = ad(link_clicks=900.0, purchases=np.nan, spend_inr=900.0, revenue_inr=np.nan)
    result = pooled_metrics(pd.DataFrame([good, missing]))
    assert result["cvr"] == pytest.approx(0.05)  # 0.005 if the missing ad's clicks stayed in
    assert result["roas"] == pytest.approx(3.0)
    assert result["ctr"] == pytest.approx(1000 / 20000)  # its clicks still count where they are real


def test_pooled_of_empty_group_is_nan_not_an_error():
    assert math.isnan(pooled_metrics(pd.DataFrame([ad()]).iloc[0:0])["roas"])


def test_pooled_matches_a_hand_sum_on_real_data(data):
    ads = data.ads
    usable = ads.purchases.notna()
    assert pooled_metrics(ads)["cvr"] == pytest.approx(ads.purchases[usable].sum() / ads.link_clicks[usable].sum())
