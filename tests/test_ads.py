import math

import numpy as np
import pandas as pd
import pytest

from lj import ads as A
from lj.metrics import pooled_metrics


@pytest.fixture(scope="module")
def corrected(data):
    fixed = A.apply_corrections(data.ads, pd.read_csv(A.CORRECTIONS))
    return A.assign_concepts(fixed, pd.read_csv(A.CONCEPT_MAP))


@pytest.fixture(scope="module")
def concepts(corrected):
    return A.to_concepts(corrected[corrected.segment == "kids"])


def good_row(**overrides):
    row = dict(
        gap_without_lj004=0.2,
        adjusted_gap=0.2,
        median_gap=0.1,
        gap_without_largest=0.1,
        controlled_lift=0.3,
        p=0.001,
        q=0.05,
        controlled_p=0.01,
        n_in=12,
        n_out=60,
    )
    return row | overrides


# ---------------------------------------------------------------- concepts
def test_every_ad_in_a_concept_family_exists(corrected, data):
    assert set(pd.read_csv(A.CONCEPT_MAP).ad_id) <= set(data.ads.ad_id)


def test_each_family_has_at_least_two_ads():
    assert (pd.read_csv(A.CONCEPT_MAP).groupby("concept_id").size() >= 2).all()


def test_exact_duplicate_videos_always_share_a_concept(corrected):
    assert (corrected.groupby("creative_id").concept_id.nunique() == 1).all()


def test_concept_counts_are_summed_exactly(corrected, concepts):
    family = corrected[corrected.ad_id.isin(["LJ-050", "LJ-081"])]
    row = concepts.set_index("concept_id").loc["nutrimix_batman_boy_protein"]
    assert row.spend_inr == family.spend_inr.sum() and row.purchases == family.purchases.sum()
    assert row.roas == pytest.approx(family.revenue_inr.sum() / family.spend_inr.sum())
    assert row.n_ads == 2


def test_no_kids_ad_is_lost_or_double_counted(corrected, concepts):
    kids = corrected[corrected.segment == "kids"]
    assert concepts.n_ads.sum() == len(kids)
    assert concepts.spend_inr.sum() == kids.spend_inr.sum()


def test_moms_and_teen_ads_are_excluded(concepts):
    assert set(concepts.segment) == {"kids"}
    assert not concepts.ad_ids.str.contains("LJ-046").any()  # 13+ product
    assert not concepts.ad_ids.str.contains("LJ-015").any()  # moms' gummies


def test_blank_label_filled_from_other_family_member(concepts):
    row = concepts.set_index("concept_id").loc["nutrimix_kids_milkshake_voxpop"]
    assert row.child_role == "speaks; consumes_product; reacts_to_taste"  # LJ-035 is blank; LJ-055 has it


def test_missing_purchases_stay_missing_in_concepts(concepts):
    lj089 = concepts[concepts.ad_ids == "LJ-089"].iloc[0]
    assert math.isnan(lj089.purchases) and math.isnan(lj089.cvr) and lj089.hook_rate > 0


def test_concept_pooling_matches_ad_pooling(corrected, concepts):
    kids = corrected[corrected.segment == "kids"]
    for metric in ("cvr", "roas", "hook_rate"):
        assert pooled_metrics(concepts)[metric] == pytest.approx(pooled_metrics(kids)[metric])


# ---------------------------------------------------------------- corrections
def test_corrections_record_what_they_replace(data):
    source = data.ads.set_index("ad_id")
    for row in pd.read_csv(A.CORRECTIONS).itertuples():
        assert source.loc[row.ad_id, row.label] == row.system_value


def test_corrections_are_applied_and_nothing_else_changes(data, corrected):
    fixed = corrected.set_index("ad_id")
    assert fixed.ad_format["LJ-060"] == "silent_brand_film"
    assert fixed.ad_format["LJ-097"] == "child_led"
    assert (fixed.ad_format == "child_led").sum() == 7


# ---------------------------------------------------------------- features
def test_features_cover_both_label_kinds(concepts):
    features = A.build_features(concepts)
    assert "ad_format = skit" in features
    assert "narratives = recipe" in features  # from a multi-label column
    assert "child_on_screen = any" in features


def test_small_groups_are_left_out(concepts):
    features = A.build_features(concepts)
    assert all(A.MIN_GROUP <= mask.sum() <= len(concepts) - A.MIN_GROUP for mask in features.values())


def test_other_and_none_levels_are_not_tested(concepts):
    assert not [name for name in A.build_features(concepts) if name.endswith(("= other", "= none"))]


def test_unreliable_labels_are_never_tested(concepts):
    names = " ".join(A.build_features(concepts))
    for label in ("product_form", "people_on_screen", "brand_first_said"):
        assert label not in names


# ---------------------------------------------------------------- statistics
def test_stratified_permutation_stays_within_strata():
    strata = np.array(["a", "a", "a", "b", "b", "c", "c", "c", "c"])
    indices = A.stratified_permutations(strata, 200, np.random.default_rng(0))
    assert (strata[indices] == strata).all()
    assert len({tuple(row) for row in indices}) > 50


def test_pooled_gap_by_hand():
    mask = np.array([True, True, False, False])
    gap = A.pooled_gap(mask, np.array([1.0, 3.0, 1.0, 1.0]), np.array([10.0, 10.0, 10.0, 10.0]))
    assert gap == pytest.approx(0.2 - 0.1)


def test_permutation_finds_a_planted_effect():
    rng = np.random.default_rng(1)
    denominator = np.full(60, 1000.0)
    mask = np.arange(60) < 20
    numerator = rng.normal(100, 5, 60) + mask * 40
    indices = A.stratified_permutations(np.zeros(60, dtype=int), 2000, rng)
    _, _, p = A.permutation_test(mask, numerator, denominator, indices)
    assert p < 0.005


def test_permutation_does_not_find_an_effect_in_noise():
    rng = np.random.default_rng(2)
    p_values = []
    for _ in range(200):
        numerator = rng.normal(100, 10, 40)
        mask = rng.permutation(np.arange(40) < 15)
        indices = A.stratified_permutations(np.zeros(40, dtype=int), 300, rng)
        p_values.append(A.permutation_test(mask, numerator, np.full(40, 1000.0), indices)[2])
    assert 0.02 <= np.mean(np.array(p_values) < 0.05) <= 0.09  # about 5% by chance


def test_adjustment_removes_a_pure_product_effect():
    # The group looks better only because it holds more of the better product line.
    strata = np.array([0] * 30 + [1] * 30)
    numerator = np.where(strata == 0, 100.0, 200.0)
    mask = np.array([False] * 25 + [True] * 5 + [False] * 5 + [True] * 25)
    indices = A.stratified_permutations(strata, 500, np.random.default_rng(3))
    observed, adjusted, p = A.permutation_test(mask, numerator, np.full(60, 1000.0), indices)
    assert observed > 0.05 and abs(adjusted) < 1e-9 and p > 0.5


def test_benjamini_hochberg_by_hand():
    q = A.benjamini_hochberg(pd.Series([0.01, 0.04, 0.03, 0.20]))
    assert q.tolist() == pytest.approx([0.04, 0.16 / 3, 0.16 / 3, 0.20])


def test_controlled_effect_recovers_a_planted_lift():
    rng = np.random.default_rng(4)
    n = 80
    feature = pd.Series(np.arange(n) < 30)
    clicks = rng.integers(2000, 8000, n)
    purchases = rng.binomial(clicks, np.where(feature, 0.04, 0.02))
    frame = pd.DataFrame(
        {
            "purchases": purchases.astype(float),
            "link_clicks": clicks.astype(float),
            "product_line": rng.choice(["a", "b"], n),
            "language_group": rng.choice(["x", "y"], n),
        }
    )
    lift, p = A.controlled_effect(frame, feature, "cvr", control_language=True)
    assert 0.7 < lift < 1.4 and p < 0.001  # the true odds ratio is about 2


@pytest.mark.parametrize("metric", ["hook_rate", "ctr", "cvr", "roas"])
def test_controlled_p_values_are_honest_when_there_is_no_real_effect(concepts, metric):
    """Shuffling a real label within products removes any true effect, so about 5% of tests should come up p < .05."""
    rng = np.random.default_rng(7)
    frame = concepts[~concepts.dominant_ad].reset_index(drop=True)
    label = (frame.child_in_first_3s == "yes").to_numpy()
    products = frame.product_line.to_numpy()
    hits = []
    for _ in range(120):
        order = np.arange(len(frame))
        for line in np.unique(products):
            positions = np.flatnonzero(products == line)
            order[positions] = rng.permutation(positions)
        _, p = A.controlled_effect(frame, pd.Series(label[order]), metric, control_language=True)
        hits.append(p < 0.05)
    assert np.mean(hits) <= 0.13


def test_pattern_identical_to_a_control_drops_that_control():
    rng = np.random.default_rng(5)
    n = 60
    language = pd.Series(np.where(np.arange(n) < 20, "x", "y"))
    clicks = rng.integers(2000, 8000, n)
    purchases = rng.binomial(clicks, np.where(language == "x", 0.04, 0.02))
    frame = pd.DataFrame(
        {
            "purchases": purchases.astype(float),
            "link_clicks": clicks.astype(float),
            "product_line": rng.choice(["a", "b"], n),
            "language_group": language,
        }
    )
    lift, p = A.controlled_effect(frame, language == "x", "cvr", control_language=True)
    assert 0.7 < lift < 1.4 and p < 0.001  # a meaningless split between pattern and control would halve this


def test_pattern_identical_to_a_product_cannot_be_separated():
    rng = np.random.default_rng(6)
    n = 40
    product = pd.Series(np.where(np.arange(n) < 15, "a", "b"))
    clicks = rng.integers(2000, 8000, n)
    frame = pd.DataFrame(
        {
            "purchases": rng.binomial(clicks, 0.03).astype(float),
            "link_clicks": clicks.astype(float),
            "product_line": product,
            "language_group": "x",
        }
    )
    lift, p = A.controlled_effect(frame, product == "a", "cvr", control_language=True)
    assert math.isnan(lift) and math.isnan(p)


# ---------------------------------------------------------------- grading
def test_grade_top_tier():
    assert A.grade(good_row()) == "Supported"


@pytest.mark.parametrize("change", [dict(q=0.3), dict(controlled_p=0.2), dict(controlled_lift=0.05), dict(n_in=8)])
def test_grade_falls_to_directional_when_a_strong_condition_fails(change):
    assert A.grade(good_row(**change)) == "Directional"


@pytest.mark.parametrize(
    "field", ["gap_without_lj004", "adjusted_gap", "median_gap", "gap_without_largest", "controlled_lift"]
)
def test_any_view_disagreeing_means_inconclusive(field):
    assert A.grade(good_row(**{field: -0.1})) == "Inconclusive"


def test_weak_p_or_missing_view_means_inconclusive():
    assert A.grade(good_row(p=0.2)) == "Inconclusive"
    assert A.grade(good_row(controlled_lift=float("nan"))) == "Inconclusive"


# ---------------------------------------------------------------- the real results
@pytest.fixture(scope="module")
def table(corrected):
    return A.analyse(corrected, n_permutations=500)


def test_every_theme_points_at_a_real_result(table):
    tested = set(zip(table.pattern, table.metric, strict=True))
    for theme in A.THEMES:
        for key in theme["evidence"]:
            assert key in tested, key


def test_theme_readings_carry_no_hand_typed_figures():
    """Numbers come from the analysis, so a reading can't go stale. '3 seconds' and similar are descriptions, not results."""
    for theme in A.THEMES:
        assert "%" not in theme["reading"] and "₹" not in theme["reading"]
        assert "ROAS" not in theme["reading"]


def test_rate_without_top_by_hand():
    frame = pd.DataFrame(
        {
            "purchases": [100.0, 10.0, 1.0, 1.0],
            "link_clicks": [1000.0, 100.0, 100.0, 100.0],
            "spend_inr": [9.0, 8.0, 1.0, 2.0],
        }
    )
    mask = pd.Series([True, True, True, True])
    assert A.rate_without_top(frame, mask, "cvr", n=2) == pytest.approx(2 / 200)


def test_report_marks_data_as_synthetic_and_keeps_interpretation_apart(table, corrected, tmp_path):
    A.write_report(table, corrected, tmp_path)
    report = (tmp_path / "ad_patterns.md").read_text(encoding="utf-8")
    assert "not Little Joys' real results" in report
    assert "What this means (interpretation)" in report and "Too few concepts to grade" in report


def test_follow_up_checks_can_be_reproduced_by_hand(concepts):
    primary = concepts[~concepts.dominant_ad].reset_index(drop=True)
    hooks, angles, hook_corr, _ = A.follow_up_checks(primary)
    parent = primary[(primary.creator_type == "parent_or_caregiver") & primary.purchases.notna()]
    row = hooks.set_index("group").loc["Parent-led"]
    assert row.cvr == pytest.approx(parent.purchases.sum() / parent.link_clicks.sum())
    assert hook_corr == pytest.approx(parent.hook_rate.corr(parent.cvr, method="spearman"))
    picky = primary.narratives.fillna("").str.contains("fussy_eating")
    enjoying = primary.demo_shown.fillna("").str.contains("taste_test")
    assert angles.set_index("group").n["Picky eating, with a child enjoying"] == (picky & enjoying).sum()


def test_follow_up_groups_split_without_overlap(concepts):
    primary = concepts[~concepts.dominant_ad].reset_index(drop=True)
    hooks, angles, _, _ = A.follow_up_checks(primary)
    counts = hooks.set_index("group").n
    assert counts["Parent-led"] + counts["Not parent-led"] == len(primary)
    assert counts["Parent-led, stronger hook"] + counts["Parent-led, weaker hook"] == counts["Parent-led"]
    by_group = angles.set_index("group").n
    assert by_group["Parent-led, with a child enjoying"] + by_group["Parent-led, without"] == counts["Parent-led"]


def test_small_groups_are_reported_rather_than_vanishing(corrected):
    small = A.too_small_to_test(corrected).set_index("pattern")
    assert small.concepts["ad_format = child_led"] == 4
    assert small.concepts["main_benefit = taste"] == 4
    assert small.roas_with_lj004["ad_format = child_led"] > small.roas_without_lj004["ad_format = child_led"]


def test_false_leads_are_only_apparent_winners(table):
    assert (table.loc[table.false_lead, "gap_with_lj004"] >= A.HEADLINE_ROAS_GAP).all()
    assert (table.loc[table.false_lead, "grade"] == "Inconclusive").all()


def test_lj004_is_never_in_the_main_comparison(table):
    assert not table.supporting_ads.str.contains("LJ-004").any()


def test_a_result_is_reproducible(corrected):
    one = A.analyse(corrected, n_permutations=200, seed=9)
    two = A.analyse(corrected, n_permutations=200, seed=9)
    pd.testing.assert_series_equal(one.p, two.p)


def test_gap_can_be_reproduced_by_hand(table, concepts):
    row = table[(table.pattern == "ad_format = skit") & (table.metric == "cvr")].iloc[0]
    data = concepts[~concepts.dominant_ad & concepts.purchases.notna()]
    skit = data[data.ad_format == "skit"]
    rest = data[data.ad_format != "skit"]
    expected = skit.purchases.sum() / skit.link_clicks.sum() - rest.purchases.sum() / rest.link_clicks.sum()
    assert row.gap_without_lj004 == pytest.approx(expected)


def test_lj089_only_counts_in_attention_comparisons(table):
    skit = table[table.pattern == "ad_format = skit"].set_index("metric")
    assert skit.n_in["hook_rate"] == skit.n_in["cvr"] + 1
