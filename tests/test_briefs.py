import copy

import pandas as pd
import pytest

from lj import briefs, config

POSTS = pd.DataFrame(
    {
        "handle": ["mum", "mum", "other"],
        "post_url": [
            "https://www.instagram.com/p/AAA/",
            "https://www.instagram.com/p/OLD/",
            "https://www.instagram.com/p/BBB/",
        ],
        "recent": [True, False, True],
        "child_ages": ["3-7", "3-7", "8-12"],
    }
)
ADS = pd.DataFrame(
    {
        "ad_id": ["LJ-001", "LJ-002", "LJ-003"],
        "segment": ["kids", "kids", "moms"],
        "product": ["nutrimix_2plus", "proteinmix", "proteinmix"],
        "product_line": ["nutrimix_kids", "proteinmix", "proteinmix"],
        "child_role": ["reacts_to_taste", "none", "none"],
        "demo_shown": ["child_consuming", "live_use", "live_use"],
        "claims_made": ["Sweetened with jaggery and dates", "12g protein per scoop", "12g protein"],
    }
)
CLAIMS = pd.DataFrame(
    {
        "claim_id": ["NM_SWEET", "PM_PROTEIN"],
        "products": ["nutrimix_2plus;nutrimix_7plus", "proteinmix"],
        "text": ["Sweetened with jaggery and dates", "12g protein"],
        "tier": ["label_check", "needs_approval"],
        "match": ["jaggery and dates", "12g"],
        "note": ["", ""],
    }
)
FEATURES = pd.DataFrame({"handle": ["mum"], "age_status": ["eligible_unconfirmed"]})
GOOD = {
    "handle": "mum",
    "product": "nutrimix_2plus",
    "idea": "A skit.",
    "hook": "Child first.",
    "why": [{"text": "Shows the child in {child_post_share} of posts.", "posts": ["AAA"]}],
    "beats": ["Child asks.", "Child tastes."],
    "child_moment": "Child enjoys it.",
    "reason_to_care": "Picky",
    "ask": "Buy now",
    "tone": "Warm.",
    "avoid": ["Boosts immunity"],
    "claims": ["NM_SWEET"],
    "ads": ["LJ-001"],
    "check_before_signing": ["Confirm the child's age."],
}


def run(brief, selected=frozenset({"mum"})):
    return briefs.validate(brief, posts=POSTS, ads=ADS, claims=CLAIMS, features=FEATURES, selected=set(selected))


def with_(**changes):
    b = copy.deepcopy(GOOD)
    b.update(changes)
    return b


def test_good_brief_passes():
    assert run(GOOD) == []


def test_avoid_list_may_name_banned_phrases():
    assert run(with_(avoid=["Boosts immunity", "Guaranteed results"])) == []


@pytest.mark.parametrize(
    "changes, expected",
    [
        ({"why": [{"text": "Reason.", "posts": ["ZZZ"]}]}, "doesn't exist"),
        ({"why": [{"text": "Reason.", "posts": ["BBB"]}]}, "belongs to another creator"),
        ({"why": [{"text": "Reason.", "posts": ["OLD"]}]}, "older than a year"),
        ({"why": [{"text": "Reason.", "posts": []}]}, "without a source post"),
        ({"ads": ["LJ-999", "LJ-001"]}, "ad LJ-999 doesn't exist"),
        ({"ads": ["LJ-002"]}, "no cited ad shows a child enjoying"),
        ({"ads": ["LJ-001", "LJ-003"]}, "non-kids ads"),
        ({"claims": ["MADE_UP"]}, "isn't in the claims library"),
        ({"claims": ["PM_PROTEIN"]}, "isn't for nutrimix_2plus"),
        ({"product": "nutrimix_7plus"}, "no child aged 8 to 12"),
        ({"product": "magic_powder"}, "unknown product"),
        ({"hook": "Kids grew 3 cm taller."}, "typed number"),
        ({"idea": "Mention ad LJ-555 as proof."}, "LJ-555, which doesn't exist"),
        ({"beats": ["It boosts immunity."]}, "banned phrase"),
        ({"ask": "Guaranteed results, buy now"}, "banned phrase"),
        ({"why": [{"text": "Reach of {follower_magic}.", "posts": ["AAA"]}]}, "unknown placeholder"),
        ({"check_before_signing": ["Confirm the fee."]}, "age is unconfirmed"),
        ({"child_moment": ""}, "missing field: child_moment"),
    ],
)
def test_bad_briefs_are_rejected(changes, expected):
    errors = run(with_(**changes))
    assert any(expected in e for e in errors), errors


def test_unselected_creator_is_rejected():
    assert any("isn't one of the selected" in e for e in run(GOOD, selected={"someone_else"}))


def test_product_names_and_real_ad_ids_are_allowed_in_text():
    assert run(with_(idea="Nutrimix 2+ in milk, as in ad LJ-001.")) == []


def test_duplicate_creator_briefs_rejected():
    out = briefs.validate_all([GOOD, GOOD], posts=POSTS, ads=ADS, claims=CLAIMS, features=FEATURES, selected={"mum"})
    assert out["_all"]


def test_claim_no_ad_made_is_an_error():
    bad = CLAIMS.assign(match=["never said anywhere", "12g"])
    path = config.ROOT / "data" / "processed" / "_claims_test.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    bad.drop(columns=[]).to_csv(path, index=False)
    try:
        with pytest.raises(ValueError, match="isn't made by any ad"):
            briefs.load_claims(ADS, path)
    finally:
        path.unlink()


def test_fill_formats_and_keeps_missing_as_na():
    values = pd.Series({"child_post_share": 0.736, "sponsored_vs_organic_plays": float("nan"), "reach_plays": 37857.0})
    assert (
        briefs.fill("{child_post_share} / {sponsored_vs_organic_plays} / {reach_plays}", values) == "74% / n/a / 37,857"
    )


def test_test_plan_budget_reaches_readable_purchases():
    b = {m: {"q1": 1.0, "median": 2.0, "q3": 3.0} for m in ("hook_rate", "ctr", "cvr", "roas")}
    b["cpa"] = {"q1": 400.0, "median": 543.0, "q3": 767.0}
    plan = "\n".join(briefs.test_plan(b))
    assert "₹24,000" in plan  # 30 purchases x ₹767, rounded up to the next thousand
    assert "made up for this exercise" in plan


# ---------------------------------------------------------------- real data
@pytest.mark.skipif(not (config.OUTPUTS_DIR / "creator_rankings.csv").exists(), reason="needs pipeline outputs")
def test_committed_briefs_pass_and_cover_the_selected_five(data):
    features = pd.read_csv(config.OUTPUTS_DIR / "creator_features.csv")
    rankings = pd.read_csv(config.OUTPUTS_DIR / "creator_rankings.csv")
    selected = set(rankings.loc[rankings[f"rank_{config.COMPETITOR_RULE}"] <= 5, "handle"])
    claims = briefs.load_claims(data.ads)
    loaded = briefs.load_briefs()
    results = briefs.validate_all(
        loaded, posts=data.posts, ads=data.ads, claims=claims, features=features, selected=selected
    )
    assert all(not e for e in results.values()), results
    assert {b["handle"] for b in loaded} == selected


def test_claims_library_traces_to_real_ads(data):
    claims = briefs.load_claims(data.ads)
    assert claims.source_ads.str.len().gt(0).all()
