import math

import numpy as np
import pandas as pd
import pytest

from lj import creators as C


@pytest.fixture(scope="module")
def features(data):
    return C.build_features(data).set_index("handle")


@pytest.fixture(scope="module")
def brands(data):
    return C.load_brands(data.posts)


def recent_videos(data, handle):
    posts = data.posts
    return posts[(posts.handle == handle) & posts.recent & posts.plays.notna()]


# ---------------------------------------------------------------- reach
def test_every_creator_gets_exactly_one_row(features):
    assert len(features) == 20 and features.index.is_unique


def test_organic_median_by_hand(features, data):
    videos = recent_videos(data, "hello_ps8")
    expected = videos[videos.is_sponsored == "no"].plays.median()
    assert features.organic_median_plays["hello_ps8"] == expected == 731154


def test_no_organic_posts_means_missing_not_zero(features):
    assert features.organic_videos["radhikabansal0908"] == 0
    assert math.isnan(features.organic_median_plays["radhikabansal0908"])
    assert features.all_video_median_plays["radhikabansal0908"] > 0


def test_unclear_sponsorship_is_neither_organic_nor_sponsored(features, data):
    videos = recent_videos(data, "tej.lil.diary")
    assert features.organic_videos["tej.lil.diary"] == (videos.is_sponsored == "no").sum()
    assert features.sponsored_videos["tej.lil.diary"] == (videos.is_sponsored == "yes").sum()
    assert (videos.is_sponsored == "unclear").sum() > 0


def test_old_posts_are_left_out(features, data):
    # sia_3vedi's two posts from 2025 are much bigger than recent ones
    videos = recent_videos(data, "sia_3vedi")
    assert features.recent_videos["sia_3vedi"] == len(videos) == 16
    assert features.plays_p75["sia_3vedi"] == videos.plays.quantile(0.75)


def test_viral_spike_is_visible(features):
    assert features.top_post_share["mumma_and_ridhu"] > 0.9
    assert features.organic_median_plays["mumma_and_ridhu"] < 200_000  # the 48.8M post doesn't inflate it


def test_photo_posts_do_not_count_as_zero_plays(features, data):
    assert features.recent_videos["hello_ps8"] < features.recent_posts["hello_ps8"]
    assert recent_videos(data, "hello_ps8").plays.min() > 0


# ---------------------------------------------------------------- engagement
def test_hidden_likes_are_left_out_of_the_rate(data):
    posts = data.posts
    videos = recent_videos(data, "radhikabansal0908")
    with_hidden = (videos.likes / videos.plays * 1000).median()
    without = C.median_per_thousand(videos.likes_clean, videos.plays)
    assert videos.likes_hidden.sum() == 6 and without > with_hidden
    assert posts[posts.handle == "radhikabansal0908"].likes_hidden.sum() == 6


def test_median_per_thousand_by_hand():
    values = pd.Series([1.0, np.nan, 3.0])
    plays = pd.Series([1000.0, 1000.0, 1000.0])
    assert C.median_per_thousand(values, plays) == 2.0
    assert math.isnan(C.median_per_thousand(pd.Series([np.nan]), pd.Series([100.0])))


def test_comment_bait_posts_are_left_out_of_the_comment_rate(features, data):
    videos = recent_videos(data, "tej.lil.diary")
    all_posts = C.median_per_thousand(videos.comments_clean, videos.plays)
    assert features.comments_per_1k_non_bait["tej.lil.diary"] < all_posts


def test_followers_do_not_drive_any_derived_field(features):
    # Followers are context only; the sole derived use is an explicit ratio
    assert features.median_plays_per_follower["livesimply_withkripa"] == pytest.approx(
        features.all_video_median_plays["livesimply_withkripa"] / features.followers["livesimply_withkripa"])


# ---------------------------------------------------------------- sponsorship
def test_sponsored_ratio_needs_enough_posts(features):
    assert math.isnan(features.sponsored_vs_organic_plays["drgarima_mehta"])  # only 2 sponsored posts
    assert not math.isnan(features.sponsored_vs_organic_plays["raja_choudhary04"])


def test_saturation(features):
    assert features.saturated["radhikabansal0908"] and features.saturated["doc_mama_and_babies"]
    assert not features.saturated["hello_ps8"]


# ---------------------------------------------------------------- brands
def test_each_brand_row_points_at_a_real_post(brands, data):
    rows = brands[brands.source == "post"]
    assert rows.post_url.notna().all() and set(rows.post_url) <= set(data.posts.post_url)


def test_a_brand_row_without_a_matching_post_is_rejected(data, tmp_path):
    path = tmp_path / "brands.csv"
    pd.DataFrame([dict(handle="hello_ps8", posted_on="2026-10-01", brand="Gritzo", category="direct_kids_nutrition", source="post", note="")]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="expected 1 matching post"):
        C.load_brands(data.posts, path)


def test_direct_competitors_match_the_reviewed_list(features):
    flagged = set(features.index[features.direct_competitor_posts > 0])
    assert flagged == {"couple_adishiv", "doc_mama_and_babies", "ekamichildcare", "instamommy_suchi", "raja_choudhary04", "sia_3vedi"}
    assert features.direct_competitor_posts["raja_choudhary04"] == 3


def test_every_sponsored_nutrition_label_is_reviewed(data, brands):
    """No kids' nutrition brand can slip through unreviewed: known rival names must all have a row."""
    posts = data.posts
    names = r"gritzo|complan|bournvita|horlicks|pediasure|troovy|good monk|manna"
    tagged = posts[posts.brands_visible.fillna("").str.contains(names, case=False)]
    reviewed = set(zip(brands.handle, brands.posted_on))
    assert all((row.handle, row.posted_on) in reviewed for row in tagged.itertuples())


def test_existing_little_joys_relationships_are_all_found(features):
    related = set(features.index[features.little_joys_relationship != ""])
    assert related == {"doc_mama_and_babies", "foodies_by_neha", "storiesbyvihaa"}


# ---------------------------------------------------------------- children and age
def test_age_shares_by_hand():
    posts = pd.DataFrame({"child_age_bands": [["0-2"], ["0-2", "3-7"], ["13-17"], ["8-12"]]})
    shares = C.age_shares(posts)
    assert shares == {"infant_only_share": 0.25, "age_3_to_12_share": 0.5, "teen_only_share": 0.25}


def test_no_child_posts_gives_missing_age_shares(features):
    assert features.child_post_share["thatkushalmistry"] == 0
    assert math.isnan(features.infant_only_share["thatkushalmistry"])
    assert math.isnan(features.age_3_to_12_share["foodies_by_neha"])


def test_review_uses_only_known_statuses(features):
    assert set(features.age_status) <= set(C.AGE_WORDS) and set(features.enjoy_status) <= set(C.ENJOY_WORDS)


def test_review_covering_the_wrong_creators_is_rejected(data, tmp_path):
    path = tmp_path / "review.csv"
    pd.read_csv(C.REVIEW_FILE, keep_default_na=False).iloc[:-1].to_csv(path, index=False)
    with pytest.raises(ValueError, match="doesn't cover"):
        C.load_review(data.creators, data.posts, path)


def test_proven_enjoyment_always_cites_a_post(features, data):
    proven = features[features.enjoy_status == "proven"]
    assert (proven.enjoy_evidence_urls != "").all()
    for urls in features.enjoy_evidence_urls:
        for url in filter(None, urls.split("; ")):
            assert url in set(data.posts.post_url)


def test_review_text_carries_no_hand_typed_metrics():
    review = pd.read_csv(C.REVIEW_FILE, keep_default_na=False)
    for column in ("strengths", "weaknesses", "risks", "persona_check"):
        assert not review[column].str.contains("%").any(), column


# ---------------------------------------------------------------- audience and gaps
def test_only_three_creators_have_audience_data(features):
    assert features.women_pct.notna().sum() == 3
    assert features.men_pct["storiesbyvihaa"] == pytest.approx(70.1)
    assert not features.comparable_platform["parentingtips_surat"]


def test_data_gaps_state_missing_audience_and_platform(features):
    assert any("No audience data" in gap for gap in C.data_gaps(features.loc["hello_ps8"].rename("hello_ps8")))
    assert any("Facebook" in gap for gap in C.data_gaps(features.loc["parentingtips_surat"]))
    assert not any("No audience data" in gap for gap in C.data_gaps(features.loc["tej.lil.diary"]))


# ---------------------------------------------------------------- audit and report
def test_sponsorship_audit_matches_its_fixed_sample(data):
    posts = data.posts
    sample = pd.concat([posts[posts.is_sponsored == "yes"].sample(14, random_state=20261104), posts[posts.is_sponsored == "no"].sample(14, random_state=20261104)])
    ids = sample.post_url.str.rstrip("/").str.rsplit("/", n=1).str[-1]
    assert set(ids) == set(pd.read_csv(C.SPONSORSHIP_AUDIT).post_id)


def test_report_covers_everyone_and_shows_gaps(features, brands, tmp_path):
    table = features.reset_index()
    C.write_report(table, brands, pd.read_csv(C.SPONSORSHIP_AUDIT), tmp_path)
    report = (tmp_path / "creator_profiles.md").read_text(encoding="utf-8")
    assert all(f"## `{handle}`" in report for handle in table.handle)
    assert "**Data gaps:**" in report and "n/a" in report
