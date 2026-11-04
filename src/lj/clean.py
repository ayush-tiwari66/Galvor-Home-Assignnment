"""Cleaning rules. Each row-level change goes into the cleaning log, so it can be traced and challenged."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from lj import config
from lj.ingest import RawData
from lj.metrics import add_ad_metrics

LANGUAGE_NAME = re.compile(r"^([A-Za-z ]+?)\s*\(")
COMMENT_BAIT = re.compile(
    r"""\bcomment\b.{0,40}(?:\blink\b|\bbelow\b|\bfor\b|["“”'‘’])"""
    r"""|\bgiveaway\b|\bdm\b.{0,25}\blink\b|\btag\b.{0,25}\b(?:friend|mom|mum)""",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class CleanData:
    ads: pd.DataFrame
    creators: pd.DataFrame
    posts: pd.DataFrame
    audience: pd.DataFrame
    log: pd.DataFrame = field(default_factory=pd.DataFrame)


def _entry(table, row, column, old, new, rule) -> dict:
    return {"table": table, "row": row, "column": column, "old": old, "new": new, "rule": rule}


# ---------------------------------------------------------------- ads
def tracking_failures(ads: pd.DataFrame, max_prob: float = config.TRACKING_FAILURE_MAX_PROB) -> pd.Series:
    """Flag zero-purchase ads whose add-to-carts make a true zero essentially impossible.

    Uses the median purchases-per-add-to-cart of the ads that did record purchases.
    """
    with_sales = ads[ads.purchases > 0]
    rate = (with_sales.purchases / with_sales.add_to_carts).median()
    prob_of_zero = (1 - rate) ** ads.add_to_carts
    return (ads.purchases == 0) & (prob_of_zero < max_prob)


def clean_ads(ads: pd.DataFrame, product_map: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    out = ads.copy()
    log: list[dict] = []

    unmapped = set(out.ad_id) ^ set(product_map.ad_id)
    if unmapped:
        raise ValueError(f"Product map and ads.csv disagree on: {sorted(unmapped)}")
    out = out.merge(product_map[["ad_id", "product", "product_line", "segment"]], on="ad_id", how="left", validate="one_to_one")

    out["launch_date"] = pd.to_datetime(out.launch_date)
    out["stopped_date"] = pd.to_datetime(out.stopped_date)

    # Keep the export's values, then blank the ones we do not believe.
    out["purchases_raw"] = out.purchases
    out["revenue_inr_raw"] = out.revenue_inr
    out["purchases"] = out.purchases.astype(float)
    out["revenue_inr"] = out.revenue_inr.astype(float)
    out["tracking_suspect"] = tracking_failures(ads).to_numpy()
    for _, row in out[out.tracking_suspect].iterrows():
        rule = f"zero purchases on {row.add_to_carts} add-to-carts: treated as a tracking failure"
        log.append(_entry("ads", row.ad_id, "purchases", 0, "missing", rule))
        log.append(_entry("ads", row.ad_id, "revenue_inr", 0, "missing", rule))
    out.loc[out.tracking_suspect, ["purchases", "revenue_inr"]] = np.nan

    share = out.purchases / out.purchases.sum()
    out["dominant_ad"] = share >= config.DOMINANT_AD_PURCHASE_SHARE
    out["low_evidence"] = out.purchases_raw < config.LOW_EVIDENCE_PURCHASES

    # Ads that reuse a video are one creative in pattern analysis, not independent observations.
    out["creative_id"] = out.groupby("video_url").ad_id.transform("min")
    out["creative_n_ads"] = out.groupby("video_url").ad_id.transform("size")
    return add_ad_metrics(out), log


# ---------------------------------------------------------------- posts
def repair_transcript_language(posts: pd.DataFrame) -> pd.Series:
    """Spoken language per post. Blank without a transcript; pasted text reduced to its leading language name."""
    def repair(value):
        if pd.isna(value) or len(value) <= 25:
            return value
        match = LANGUAGE_NAME.match(value)
        return match.group(1) if match else np.nan

    return posts.transcript_language.map(repair).where(posts.transcript.notna())


def clean_posts(posts: pd.DataFrame, as_of: pd.Timestamp = config.POSTS_AS_OF) -> tuple[pd.DataFrame, list[dict]]:
    out = posts.copy()
    log: list[dict] = []
    out["posted_on"] = pd.to_datetime(out.posted_on)
    out["age_days"] = (as_of - out.posted_on).dt.days
    out["recent"] = out.age_days <= config.RECENT_WINDOW_DAYS
    out["sponsored"] = out.is_sponsored.map({"yes": True, "no": False})  # "unclear" stays missing

    hidden = out.likes <= config.HIDDEN_LIKES_MAX
    out["likes_hidden"] = hidden
    out["likes_clean"] = out.likes.astype(float).where(~hidden)

    # A zero at scale, or on a post with no play count to judge by, is unavailable rather than a real zero.
    not_real_zero = out.plays.isna() | (out.plays >= config.IMPLAUSIBLE_ZERO_MIN_PLAYS)
    out["reshares_clean"] = out.reshares.astype(float).where(~((out.reshares == 0) & not_real_zero))
    out["comments_clean"] = out.comments.astype(float).where(~((out.comments == 0) & not_real_zero))

    out["comment_bait"] = out.caption.fillna("").map(lambda text: bool(COMMENT_BAIT.search(text)))
    out["spoken_language"] = repair_transcript_language(out)
    out["child_age_bands"] = out.child_ages.fillna("").map(lambda s: [b.strip() for b in s.split(";") if b.strip()])

    for _, row in out[hidden].iterrows():
        log.append(_entry("posts", row.post_url, "likes", row.likes, "missing", "very low like count: hidden by the account"))
    for column in ("reshares", "comments"):
        for _, row in out[out[column].eq(0) & out[f"{column}_clean"].isna()].iterrows():
            log.append(_entry("posts", row.post_url, column, 0, "missing", "zero at scale or without play count: treated as unavailable"))
    for _, row in out[out.transcript_language.notna() & (out.transcript_language != out.spoken_language)].iterrows():
        log.append(_entry("posts", row.post_url, "transcript_language", str(row.transcript_language)[:40], row.spoken_language, "repaired language value"))
    return out, log


# ---------------------------------------------------------------- audience
def parse_shares(text) -> dict[str, float]:
    """Turn '25-34 48.3%; 35-44 40.1%' into {'25-34': 48.3, '35-44': 40.1}."""
    shares: dict[str, float] = {}
    if pd.isna(text):
        return shares
    for part in str(text).split(";"):
        match = re.match(r"^\s*(.+?)\s+([\d.]+)%\s*$", part)
        if match:
            shares[match.group(1)] = float(match.group(2))
    return shares


def clean_audience(audience: pd.DataFrame) -> pd.DataFrame:
    out = audience.copy()
    out["comparable_platform"] = out.platform == "instagram"
    out["age_shares"] = out.age_split.map(parse_shares)
    out["country_shares"] = out.top_countries.map(parse_shares)
    out["india_pct"] = out.country_shares.map(lambda shares: shares.get("India", np.nan))
    return out


# ---------------------------------------------------------------- everything
def clean_all(raw: RawData, product_map_path: Path = config.PRODUCT_MAP) -> CleanData:
    ads, ads_log = clean_ads(raw.ads, pd.read_csv(product_map_path))
    posts, posts_log = clean_posts(raw.posts)
    creators = raw.creators.drop(columns=["audience_read"])  # comment_evidence is "none" for all 20
    return CleanData(ads, creators, posts, clean_audience(raw.audience), pd.DataFrame(ads_log + posts_log))
