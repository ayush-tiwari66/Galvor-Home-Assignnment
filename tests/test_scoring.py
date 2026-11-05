import numpy as np
import pandas as pd
import pytest

from lj import config, scoring


def creator(handle, **overrides):
    row = dict(
        handle=handle,
        followers=100_000,
        posts_last_90_days=10,
        organic_videos=12,
        organic_median_plays=300_000.0,
        all_video_median_plays=300_000.0,
        top_post_share=0.3,
        transcripts=6,
        sponsored_share=0.1,
        direct_competitor_last_90_days=False,
        child_post_share=0.7,
        age_3_to_12_share=1.0,
        food_topic_share=0.3,
        age_status="eligible",
        enjoy_status="proven",
        persona_check="Matches: x",
        women_pct=np.nan,
        men_pct=np.nan,
    )
    row.update(overrides)
    return row


def frame(*rows):
    return pd.DataFrame(list(rows))


def test_infant_feed_fails_age_gate_with_reason():
    g = scoring.gate_table(frame(creator("a", age_status="infant_led")))
    assert not g.passes_gates[0]
    assert "under the product's starting age" in g.gate_reason[0]


def test_mixed_feed_passes_only_with_enough_3_to_12_posts():
    g = scoring.gate_table(
        frame(
            creator("a", age_status="mixed", age_3_to_12_share=0.64),
            creator("b", age_status="mixed", age_3_to_12_share=0.40),
        )
    )
    assert g.gate_age.tolist() == [True, False]


def test_food_feed_without_children_passes_viewers_gate_but_comedy_does_not():
    g = scoring.gate_table(
        frame(
            creator("food", child_post_share=0.0, food_topic_share=0.78, age_status="school_age_not_shown"),
            creator("comedy", child_post_share=0.0, food_topic_share=0.0, age_status="no_child"),
        )
    )
    assert g.gate_viewers.tolist() == [True, False]
    assert g.passes_gates.tolist() == [True, False]


def test_majority_men_audience_fails_but_missing_audience_does_not():
    g = scoring.gate_table(frame(creator("men", women_pct=29.9, men_pct=70.1), creator("unknown")))
    assert g.gate_viewers.tolist() == [False, True]
    assert "70% men" in g.gate_reason[0]


def test_inactive_creator_fails():
    g = scoring.gate_table(frame(creator("a", posts_last_90_days=0)))
    assert not g.passes_gates[0]


def test_competitor_rule_changes_eligibility_only_in_exclude():
    g = scoring.gate_table(frame(creator("rival", direct_competitor_last_90_days=True), creator("clean")))
    assert scoring.eligible(g, "exclude").tolist() == [False, True]
    assert scoring.eligible(g, "flag").tolist() == [True, True]
    with pytest.raises(ValueError):
        scoring.eligible(g, "maybe")


def test_reach_uses_all_videos_when_few_organic_and_caps_when_none():
    f = frame(
        creator("few", organic_videos=1, organic_median_plays=5_000_000.0, all_video_median_plays=200_000.0),
        creator("none", organic_videos=0, organic_median_plays=np.nan, all_video_median_plays=3_200_000.0),
        creator("ok"),
    )
    c = scoring.components(f)
    assert c.reach_plays.tolist() == [200_000.0, 3_200_000.0, 300_000.0]
    assert c.reach[1] == pytest.approx(0.5)  # would be 1.0 without the cap
    assert c.reach_source.tolist() == ["all videos (few organic)", "all videos (no organic)", "organic"]


def test_reach_scale_end_points():
    c = scoring.components(
        frame(
            creator("lo", organic_median_plays=10_000.0),
            creator("hi", organic_median_plays=10**6.5),
            creator("tiny", organic_median_plays=500.0),
        )
    )
    assert c.reach.tolist() == pytest.approx([0.0, 1.0, 0.0])


def test_paid_readiness_falls_only_above_comfort_share():
    c = scoring.components(
        frame(
            creator("a", sponsored_share=0.35), creator("b", sponsored_share=1.0), creator("c", sponsored_share=0.675)
        )
    )
    assert c.paid_readiness.tolist() == pytest.approx([1.0, 0.0, 0.5])


def test_unknown_enjoy_status_is_an_error_not_a_zero():
    with pytest.raises(ValueError, match="Missing criterion"):
        scoring.components(frame(creator("a", enjoy_status="typo")))


def test_score_is_bounded_and_rejects_bad_weights():
    c = scoring.components(frame(creator("best", sponsored_share=0.0, organic_median_plays=1e7)))
    assert scoring.score(c, config.SCORE_WEIGHTS)[0] == pytest.approx(100.0)
    with pytest.raises(ValueError):
        scoring.score(c, dict.fromkeys(scoring.CRITERIA, 0.5))


def test_default_weights_sum_to_one():
    assert sum(config.SCORE_WEIGHTS.values()) == pytest.approx(1.0)
    for w in scoring.NAMED_WEIGHTS.values():
        assert sum(w.values()) == pytest.approx(1.0)


def test_top5_frequency_is_one_for_dominant_and_zero_for_dominated():
    rows = [creator(f"c{i}", enjoy_status="plausible") for i in range(6)]
    rows[0] = creator("star", sponsored_share=0.0, organic_median_plays=1e7)
    rows[5] = creator(
        "weak",
        enjoy_status="unlikely",
        age_status="mixed",
        food_topic_share=0.0,
        organic_median_plays=10_000.0,
        sponsored_share=1.0,
        persona_check="Partly: x",
    )
    f = frame(*rows)
    comp = scoring.components(f)
    share = scoring.top5_frequency(comp, pd.Series(True, index=f.index), scoring.random_weights(500, 1))
    assert share[0] == 1.0
    assert share[5] == 0.0


def test_ineligible_creators_never_enter_top5():
    f = frame(
        creator("rival", direct_competitor_last_90_days=True, sponsored_share=0.0, organic_median_plays=1e7),
        *[creator(f"c{i}") for i in range(5)],
    )
    table, detail = scoring.build(f)
    assert 0 not in detail["top5"]["exclude"]
    assert detail["top5"]["flag"][0] == 0
    assert pd.isna(table.top5_share_exclude[0])


def test_confidence_drops_when_age_is_unconfirmed():
    conf = scoring.confidence(frame(creator("a"), creator("b", age_status="eligible_unconfirmed")))
    assert conf.confidence_points.tolist() == [5, 4]
    assert conf.confidence.tolist() == ["High", "Medium"]
    assert "child's age confirmed" in conf.confidence_missing[1]


def test_sensitivity_is_repeatable():
    a = scoring.random_weights(10, config.SENSITIVITY_SEED)
    b = scoring.random_weights(10, config.SENSITIVITY_SEED)
    assert np.array_equal(a, b)


@pytest.mark.skipif(not (config.OUTPUTS_DIR / "creator_features.csv").exists(), reason="needs pipeline outputs")
def test_real_rankings_cover_all_20_and_main_five_are_eligible():
    table, detail = scoring.build(pd.read_csv(config.OUTPUTS_DIR / "creator_features.csv"))
    assert len(table) == 20
    for rule in ("exclude", "flag"):
        assert len(detail["top5"][rule]) == 5
        assert table.loc[detail["top5"][rule], f"eligible_{rule}"].all()


# ---------------------------------------------------------------- competitor tiers
TYPES = pd.DataFrame({"brand": ["Gritzo", "Complan"], "brand_type": ["challenger", "mass"]})


def brand_rows(*rows):
    return pd.DataFrame(
        [{"handle": h, "posted_on": d, "brand": b, "category": "direct_kids_nutrition"} for h, d, b in rows]
    )


def test_competitor_table_splits_types_and_ignores_old_posts():
    brands = brand_rows(("a", "2026-10-01", "Gritzo"), ("b", "2026-10-06", "Complan"), ("c", "2026-03-01", "Gritzo"))
    t = scoring.competitor_table(pd.Series(["a", "b", "c", "d"]), brands, TYPES)
    assert t.competitor_recent_challenger.tolist() == [True, False, False, False]
    assert t.competitor_recent_mass.tolist() == [False, True, False, False]
    assert t.competitor_detail[1] == "Complan (06 Oct)"


def test_competitor_brand_without_a_type_is_an_error():
    with pytest.raises(ValueError, match="without a type"):
        scoring.competitor_table(pd.Series(["a"]), brand_rows(("a", "2026-10-01", "Mystery")), TYPES)


def test_challengers_only_rule_keeps_mass_brand_creators():
    f = frame(
        creator("challenger", direct_competitor_last_90_days=True),
        creator("mass", direct_competitor_last_90_days=True),
        *[creator(f"c{i}") for i in range(4)],
    )
    comp = scoring.competitor_table(
        f.handle, brand_rows(("challenger", "2026-10-01", "Gritzo"), ("mass", "2026-10-06", "Complan")), TYPES
    )
    table, _ = scoring.build(f, comp)
    assert table.eligible_exclude.tolist()[:2] == [False, False]
    assert table.eligible_challengers_only.tolist()[:2] == [False, True]
    assert table.eligible_flag.tolist()[:2] == [True, True]


def test_build_rejects_brand_file_that_disagrees_with_features():
    f = frame(creator("a", direct_competitor_last_90_days=False))
    comp = scoring.competitor_table(f.handle, brand_rows(("a", "2026-10-01", "Gritzo")), TYPES)
    with pytest.raises(ValueError, match="disagree"):
        scoring.build(f, comp)


@pytest.mark.skipif(not (config.OUTPUTS_DIR / "brand_relationships.csv").exists(), reason="needs pipeline outputs")
def test_every_real_rival_brand_has_a_type():
    brands = pd.read_csv(config.OUTPUTS_DIR / "brand_relationships.csv")
    types = pd.read_csv(scoring.COMPETITOR_TYPES)
    assert set(brands.loc[brands.category == "direct_kids_nutrition", "brand"]) <= set(types.brand)
