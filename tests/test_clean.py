import math

import numpy as np
import pandas as pd
import pytest

from lj import clean, config


def rows(frame, column="ad_id"):
    return sorted(frame[column])


# ---------------------------------------------------------------- ads
def test_only_lj089_is_a_tracking_failure(data):
    assert rows(data.ads[data.ads.tracking_suspect]) == ["LJ-089"]


def test_a_small_zero_purchase_ad_stays_a_real_zero(data):
    lj054 = data.ads.set_index("ad_id").loc["LJ-054"]
    assert lj054.purchases == 0 and lj054.roas == 0 and math.isnan(lj054.cpa)


def test_lj089_keeps_attention_metrics_but_loses_conversion(data):
    lj089 = data.ads.set_index("ad_id").loc["LJ-089"]
    assert math.isnan(lj089.cvr) and math.isnan(lj089.roas)
    assert lj089.hook_rate > 0 and lj089.ctr > 0 and lj089.atc_rate > 0
    assert lj089.purchases_raw == 0  # the original value stays available


def test_tracking_rule_on_synthetic_ads():
    ads = pd.DataFrame({"purchases": [33, 33, 33, 0, 0], "add_to_carts": [100, 100, 100, 200, 3]})
    assert clean.tracking_failures(ads).tolist() == [False, False, False, True, False]


def test_only_lj004_is_dominant(data):
    assert rows(data.ads[data.ads.dominant_ad]) == ["LJ-004"]


def test_small_sample_ads_are_flagged(data):
    flagged = data.ads.set_index("ad_id").low_evidence
    assert flagged["LJ-072"] and flagged["LJ-039"] and not flagged["LJ-004"]


def test_duplicate_videos_share_one_creative(data):
    ads = data.ads.set_index("ad_id")
    for a, b in [("LJ-073", "LJ-093"), ("LJ-036", "LJ-056"), ("LJ-003", "LJ-059")]:
        assert ads.creative_id[a] == ads.creative_id[b]
        assert ads.creative_n_ads[a] == 2
    assert data.ads.creative_id.nunique() == 97


def test_every_ad_has_a_product(data):
    assert data.ads[["product", "product_line", "segment"]].notna().all().all()


def test_product_map_fixes_known_mislabels(data):
    ads = data.ads.set_index("ad_id")
    assert ads.product_form["LJ-004"] == "milk_mix_powder" and ads["product"]["LJ-004"] == "proteinmix"
    assert ads["product"]["LJ-097"] == "proteinmix"
    assert ads.segment["LJ-035"] == "kids"  # "teen-teen baar" means three times


def test_segments_match_review(data):
    ads = data.ads
    assert rows(ads[ads.segment == "teens"]) == ["LJ-046"]
    assert len(ads[ads.segment == "moms"]) == 8


def test_product_map_mismatch_is_rejected(raw):
    bad_map = pd.read_csv(config.PRODUCT_MAP).iloc[:-1]
    with pytest.raises(ValueError, match="disagree"):
        clean.clean_ads(raw.ads, bad_map)


def test_raw_inputs_are_not_mutated(raw):
    assert raw.ads.purchases.dtype.kind == "i"
    assert raw.ads.purchases[raw.ads.ad_id == "LJ-089"].iloc[0] == 0


def test_lj004_share_matches_the_documented_figure(data):
    ads = data.ads
    lj004 = ads[ads.ad_id == "LJ-004"].iloc[0]
    assert lj004.purchases_raw / ads.purchases_raw.sum() == pytest.approx(0.289, abs=0.001)
    assert lj004.roas == pytest.approx(5.00, abs=0.01)


# ---------------------------------------------------------------- posts
def test_hidden_likes_become_missing_not_zero(data):
    posts = data.posts
    assert posts.likes_hidden.sum() == 10
    assert posts.loc[posts.likes_hidden, "likes_clean"].isna().all()
    assert posts.groupby("handle").likes_hidden.sum()["radhikabansal0908"] == 6


def test_plays_stay_missing_for_non_video(data):
    posts = data.posts
    assert posts.loc[posts.type != "video", "plays"].isna().all()
    assert not (posts.plays == 0).any()


def test_zero_engagement_rule():
    posts = pd.DataFrame({
        "plays": [100.0, 600_000.0, np.nan], "likes": [50, 50, 50], "comments": [0, 0, 0], "reshares": [0, 0, 0],
        "posted_on": ["2026-10-01"] * 3, "is_sponsored": ["no"] * 3, "caption": [""] * 3, "post_url": list("abc"),
        "transcript": [None] * 3, "transcript_language": [None] * 3, "child_ages": [None] * 3,
    })
    out, _ = clean.clean_posts(posts)
    assert out.comments_clean[0] == 0  # zero on a tiny post can be real
    assert math.isnan(out.comments_clean[1])  # zero on 600k plays is not
    assert math.isnan(out.reshares_clean[2])  # no play count to judge by


def test_comments_off_post_is_unavailable(data):
    viral = data.posts[(data.posts.handle == "ohmother.in") & (data.posts.plays > 10_000_000)].iloc[0]
    assert viral.comments == 0 and math.isnan(viral.comments_clean)


def test_recency_window(data):
    assert (~data.posts.recent).sum() == 18
    assert (~data.posts[data.posts.handle == "doc_mama_and_babies"].recent).sum() == 9


def test_unclear_sponsorship_stays_unknown(data):
    posts = data.posts
    assert posts.sponsored.isna().sum() == (posts.is_sponsored == "unclear").sum() == 9


def test_spoken_language_is_repaired(data):
    values = data.posts.spoken_language.dropna()
    assert (values.str.len() <= 25).all()
    assert data.posts.spoken_language.notna().sum() <= data.posts.transcript.notna().sum()


@pytest.mark.parametrize("caption,expected", [
    ("Comment “milk” for the link", True),
    ("comment LINK below to get it", True),
    ("Giveaway time!", True),
    ("Tag a mom who needs this", True),
    ("What a lovely day with my family", False),
    ("No comment on this one today", False),
])
def test_comment_bait_detection(caption, expected):
    assert bool(clean.COMMENT_BAIT.search(caption)) is expected


def test_child_age_bands_parse(data):
    bands = data.posts.child_age_bands
    assert all(isinstance(b, list) for b in bands)
    assert (bands.map(len) > 0).sum() == 250


# ---------------------------------------------------------------- audience and creators
def test_parse_shares():
    assert clean.parse_shares("25-34 48.3%; 35-44 40.1%") == {"25-34": 48.3, "35-44": 40.1}
    assert clean.parse_shares("United States 2.8%") == {"United States": 2.8}
    assert clean.parse_shares(np.nan) == {}


def test_facebook_audience_is_not_comparable(data):
    audience = data.audience.set_index("handle")
    assert not audience.comparable_platform["parentingtips_surat"]
    assert audience.comparable_platform["tej.lil.diary"]
    assert audience.india_pct["parentingtips_surat"] == 64.4


def test_empty_audience_read_is_dropped(data):
    assert "audience_read" not in data.creators.columns


def test_only_three_creators_have_audience_data(data):
    assert len(data.audience) == 3 and set(data.audience.handle) <= set(data.creators.handle)


def test_cleaning_log_traces_changes(data):
    log = data.log
    assert ((log["row"] == "LJ-089") & (log["column"] == "purchases")).sum() == 1
    assert (log["column"] == "likes").sum() == 10
