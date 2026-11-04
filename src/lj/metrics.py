"""Ad performance metrics. Unavailable is always NaN, never 0 or infinity."""
from __future__ import annotations

import numpy as np
import pandas as pd

# name -> (numerator column, denominator column)
AD_RATIOS = {
    "hook_rate": ("video_3s_views", "impressions"),
    "thruplay_rate": ("thruplays", "impressions"),
    "hold_rate": ("thruplays", "video_3s_views"),
    "ctr": ("link_clicks", "impressions"),
    "atc_rate": ("add_to_carts", "link_clicks"),
    "cvr": ("purchases", "link_clicks"),
    "purchase_per_atc": ("purchases", "add_to_carts"),
    "roas": ("revenue_inr", "spend_inr"),
    "cpa": ("spend_inr", "purchases"),
    "aov": ("revenue_inr", "purchases"),
}


def safe_div(numerator, denominator):
    """Divide, returning NaN wherever the denominator is zero or either side is missing."""
    n = np.asarray(numerator, dtype=float)
    d = np.asarray(denominator, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(d == 0, np.nan, n / d)
    if isinstance(numerator, pd.Series):
        return pd.Series(result, index=numerator.index)
    if isinstance(denominator, pd.Series):
        return pd.Series(result, index=denominator.index)
    return float(result)


def add_ad_metrics(ads: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with one column per metric in AD_RATIOS."""
    out = ads.copy()
    for name, (num, den) in AD_RATIOS.items():
        out[name] = safe_div(out[num], out[den])
    return out


def pooled_metrics(ads: pd.DataFrame) -> dict[str, float]:
    """Group-level metrics from summed numerators and denominators.

    Rows missing either side of a ratio drop out of that ratio entirely. Otherwise an ad with missing
    purchases would still add its clicks to the denominator and understate conversion for its group.
    """
    out: dict[str, float] = {}
    for name, (num, den) in AD_RATIOS.items():
        usable = ads[num].notna() & ads[den].notna()
        out[name] = safe_div(float(ads.loc[usable, num].sum()), float(ads.loc[usable, den].sum()))
    return out
