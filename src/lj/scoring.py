"""Gates, fit score and sensitivity for all 20 creators. Run with: uv run python -m lj.scoring

Reads outputs/creator_features.csv (written by lj.creators). The score measures fit with what the brand's ads
suggest sells. It does not predict sales: nothing in the data links a creator to a purchase.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

CRITERIA = list(config.SCORE_WEIGHTS)
ENJOY_POINTS = {"proven": 1.0, "plausible": 0.6, "unlikely": 0.1}
AGE_POINTS = {"eligible": 1.0, "eligible_unconfirmed": 0.8, "mixed": 0.5, "school_age_not_shown": 0.5}
ELIGIBLE_AGES = {"eligible", "eligible_unconfirmed", "school_age_not_shown"}
CRITERION_WORDS = {
    "creative_fit": "Can show a child enjoying the product",
    "product_fit": "Children the right age, food in the feed",
    "reach": "Typical organic plays",
    "paid_readiness": "Feed not saturated with ads",
    "authenticity": "Profile matches the posts",
}
# The question each criterion answers, in plain words. Shared by the reports and the app.
CRITERION_PLAIN = {
    "creative_fit": "Has this creator filmed, or could they naturally film, their own child happily eating or drinking something?",
    "product_fit": "Are their children old enough for the product, and is food already part of what they post?",
    "reach": "How many people usually watch their normal, unpaid videos?",
    "paid_readiness": "Is the feed still mostly their own content, rather than one paid post after another?",
    "authenticity": "Does what the profile claims match what they actually post?",
}
CRITERION_MEASURE = {
    "creative_fit": "Already seen on camera = full marks, plausible = 0.6, unlikely without a new format = 0.1",
    "product_fit": "60% from child age fit, 40% from the share of posts about food (30% or more = full marks)",
    "reach": f"Median plays on unpaid videos, on a log scale from 10k (0) to 3.2M (full marks). Under {config.MIN_ORGANIC_VIDEOS} unpaid videos uses all videos; none at all caps it at half",
    "paid_readiness": f"Full marks up to {config.SPONSORED_COMFORT_SHARE:.0%} paid posts, falling to zero at 100%",
    "authenticity": "Matches = full marks, partly = half",
}
# Named weightings beside the default. Each is a plausible view a marketing manager might hold.
NAMED_WEIGHTS = {
    "Default": config.SCORE_WEIGHTS,
    "Equal weights": dict.fromkeys(CRITERIA, 0.2),
    "Reach first": {"creative_fit": 0.2, "product_fit": 0.2, "reach": 0.4, "paid_readiness": 0.1, "authenticity": 0.1},
    "Fit first": {"creative_fit": 0.4, "product_fit": 0.35, "reach": 0.1, "paid_readiness": 0.1, "authenticity": 0.05},
    "Ignore reach": {
        "creative_fit": 0.35,
        "product_fit": 0.3,
        "reach": 0.0,
        "paid_readiness": 0.2,
        "authenticity": 0.15,
    },
    "Trust first": {
        "creative_fit": 0.25,
        "product_fit": 0.2,
        "reach": 0.15,
        "paid_readiness": 0.2,
        "authenticity": 0.2,
    },
}


# ---------------------------------------------------------------- gates
def gate_table(f: pd.DataFrame) -> pd.DataFrame:
    """Yes/no checks for every creator, with the reason in words when one fails."""
    out = pd.DataFrame({"handle": f.handle})
    mixed_ok = (f.age_status == "mixed") & (f.age_3_to_12_share >= config.MIXED_AGE_MIN_3_TO_12)
    out["gate_age"] = f.age_status.isin(ELIGIBLE_AGES) | mixed_ok
    family_or_food = (f.child_post_share > 0) | (f.food_topic_share >= config.FOOD_FEED_MIN_SHARE)
    men_majority = f.men_pct.notna() & (f.men_pct > config.MAX_MEN_SHARE)  # missing audience never fails this
    out["gate_viewers"] = family_or_food & ~men_majority
    out["gate_active"] = f.posts_last_90_days >= 1
    out["competitor_recent"] = f.direct_competitor_last_90_days.astype(bool)

    reasons = []
    for i, r in f.iterrows():
        why = []
        if not out.at[i, "gate_age"]:
            why.append(
                {
                    "infant_led": "children shown are mostly under the product's starting age",
                    "teen_only": "only teenagers on camera",
                    "no_child": "no children on camera",
                    "mixed": "most children shown are under the product's starting age",
                }.get(r.age_status, "age doesn't fit")
            )
        if not family_or_food.at[i]:
            why.append("feed isn't about family or food")
        if men_majority.at[i]:
            why.append(f"measured audience is {r.men_pct:.0f}% men")
        if not out.at[i, "gate_active"]:
            why.append("no posts in the last 90 days")
        reasons.append("; ".join(why))
    out["gate_reason"] = reasons
    out["passes_gates"] = out.gate_age & out.gate_viewers & out.gate_active
    return out


COMPETITOR_TYPES = config.ROOT / "data" / "overrides" / "competitor_brands.csv"
RULE_WORDS = {
    "exclude": "Strict: any recent rival rules a creator out",
    "challengers_only": "Challenger rivals rule out; mass brands only flagged",
    "flag": "Nobody ruled out; competitor work flagged",
}


def competitor_table(
    handles: pd.Series, brands: pd.DataFrame, types: pd.DataFrame, as_of: pd.Timestamp = config.POSTS_AS_OF
) -> pd.DataFrame:
    """Per creator: recent paid rival posts, split by the rival's type. Unknown rival brands are an error."""
    direct = brands[brands.category == "direct_kids_nutrition"].copy()
    direct["posted_on"] = pd.to_datetime(direct.posted_on)
    unknown = set(direct.brand) - set(types.brand)
    if unknown:
        raise ValueError(f"Competitor brands without a type: {sorted(unknown)}")
    recent = direct[direct.posted_on >= as_of - pd.Timedelta(days=config.COMPETITOR_WINDOW_DAYS)].merge(
        types, on="brand"
    )
    out = pd.DataFrame({"handle": handles})
    out["competitor_recent_challenger"] = out.handle.isin(recent.loc[recent.brand_type == "challenger", "handle"])
    out["competitor_recent_mass"] = out.handle.isin(recent.loc[recent.brand_type == "mass", "handle"])
    by = recent.sort_values("posted_on").groupby("handle")
    out["competitor_detail"] = out.handle.map(
        by.apply(lambda g: "; ".join(f"{r.brand} ({r.posted_on:%d %b})" for r in g.itertuples()))
    ).fillna("")
    return out


def eligible(gates: pd.DataFrame, competitor_rule: str) -> pd.Series:
    if competitor_rule not in config.COMPETITOR_RULES:
        raise ValueError(f"competitor_rule must be one of {config.COMPETITOR_RULES}, not {competitor_rule!r}")
    if competitor_rule == "flag":
        return gates.passes_gates.copy()
    if competitor_rule == "challengers_only":
        return gates.passes_gates & ~gates.competitor_recent_challenger
    return gates.passes_gates & ~gates.competitor_recent


# ---------------------------------------------------------------- score
def reach_plays(f: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Plays used for reach, and which median they came from. Too few organic videos falls back to all videos."""
    use_organic = f.organic_median_plays.notna() & (f.organic_videos >= config.MIN_ORGANIC_VIDEOS)
    plays = f.organic_median_plays.where(use_organic, f.all_video_median_plays)
    source = pd.Series(
        np.where(
            use_organic,
            "organic",
            np.where(f.organic_videos > 0, "all videos (few organic)", "all videos (no organic)"),
        ),
        index=f.index,
    )
    return plays, source


def components(f: pd.DataFrame) -> pd.DataFrame:
    """Each criterion on a 0 to 1 scale. All inputs are in creator_features.csv."""
    c = pd.DataFrame({"handle": f.handle})
    c["creative_fit"] = f.enjoy_status.map(ENJOY_POINTS)
    food = (f.food_topic_share / config.FOOD_FEED_MIN_SHARE).clip(upper=1)
    c["product_fit"] = 0.6 * f.age_status.map(AGE_POINTS).fillna(0) + 0.4 * food
    plays, source = reach_plays(f)
    reach = ((np.log10(plays) - config.REACH_LOG10_FLOOR) / config.REACH_LOG10_SPAN).clip(0, 1)
    # With no organic posts at all, plays may be paid boosting, so reach counts for at most half.
    c["reach"] = reach.where(source != "all videos (no organic)", reach.clip(upper=0.5))
    c["reach_plays"], c["reach_source"] = plays, source
    over = ((f.sponsored_share - config.SPONSORED_COMFORT_SHARE) / (1 - config.SPONSORED_COMFORT_SHARE)).clip(0, 1)
    c["paid_readiness"] = 1 - over
    c["authenticity"] = np.where(f.persona_check.str.startswith("Matches"), 1.0, 0.5)
    if c[CRITERIA].isna().any().any():
        raise ValueError(f"Missing criterion values: {c[c[CRITERIA].isna().any(axis=1)].handle.tolist()}")
    return c


def score(comp: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Fit score from 0 to 100: the weighted sum of the five criteria."""
    return points(comp, weights).sum(axis=1)


def points(comp: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """The score split into the points each criterion earned. Each row adds up to that creator's score."""
    w = pd.Series(weights)[CRITERIA]
    if not np.isclose(w.sum(), 1) or (w < 0).any():
        raise ValueError(f"Weights must be non-negative and sum to 1: {weights}")
    return comp[CRITERIA] * w * 100


def top_n(scores: pd.Series, mask: pd.Series, n: int = 5) -> list[int]:
    """Indices of the n best eligible creators. Ties break by row order, so results are repeatable."""
    return scores[mask].sort_values(ascending=False, kind="stable").index[:n].tolist()


def confidence(f: pd.DataFrame) -> pd.DataFrame:
    """How much evidence sits behind a creator's row, separate from how well they fit."""
    checks = pd.DataFrame(
        {
            "enough organic videos": f.organic_videos >= 10,
            "transcripts to hear their voice": f.transcripts >= 5,
            "reach not one viral post": f.top_post_share < 0.6,
            "child enjoying food already seen": f.enjoy_status == "proven",
            "child's age confirmed": f.age_status != "eligible_unconfirmed",
            "real audience data": f.women_pct.notna(),
        }
    )
    points = checks.sum(axis=1)
    level = np.select([points >= 5, points == 4], ["High", "Medium"], "Low")
    missing = checks.apply(lambda r: "; ".join(k for k, v in r.items() if not v), axis=1)
    return pd.DataFrame({"confidence": level, "confidence_points": points, "confidence_missing": missing})


# ---------------------------------------------------------------- sensitivity
def random_weights(draws: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).dirichlet(np.ones(len(CRITERIA)), size=draws)


def top5_frequency(comp: pd.DataFrame, mask: pd.Series, weights: np.ndarray) -> pd.Series:
    """Share of weightings under which each creator makes the top 5."""
    values = comp[CRITERIA].to_numpy()
    counts = pd.Series(0, index=comp.index, dtype=float)
    idx = np.flatnonzero(mask.to_numpy())
    for w in weights:
        s = values[idx] @ w
        order = idx[np.argsort(-s, kind="stable")][:5]
        counts.iloc[order] += 1
    return counts / len(weights)


def leave_one_out(comp: pd.DataFrame, mask: pd.Series) -> dict[str, list[int]]:
    out = {}
    for drop in CRITERIA:
        w = {k: (0.0 if k == drop else v) for k, v in config.SCORE_WEIGHTS.items()}
        total = sum(w.values())
        out[drop] = top_n(score(comp, {k: v / total for k, v in w.items()}), mask)
    return out


# ---------------------------------------------------------------- build
def build(features: pd.DataFrame, competitors: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    """competitors comes from competitor_table. Without it, every recent rival counts as a challenger (the strict reading)."""
    f = features.reset_index(drop=True)
    gates = gate_table(f)
    if competitors is None:
        competitors = pd.DataFrame(
            {
                "handle": f.handle,
                "competitor_recent_challenger": gates.competitor_recent,
                "competitor_recent_mass": False,
                "competitor_detail": "",
            }
        )
    gates = gates.merge(competitors, on="handle", how="left", validate="one_to_one")
    if (gates.competitor_recent_challenger | gates.competitor_recent_mass).ne(gates.competitor_recent).any():
        raise ValueError("Competitor brand file and creator features disagree on who has recent rival work")
    comp = components(f)
    table = gates.merge(comp, on="handle").join(confidence(f))
    table.insert(1, "followers", f.followers)
    table["score"] = score(comp, config.SCORE_WEIGHTS).round(1)
    draws = random_weights(config.SENSITIVITY_DRAWS, config.SENSITIVITY_SEED)
    detail: dict = {"named": {}, "leave_one_out": {}, "top5": {}}
    for rule in config.COMPETITOR_RULES:
        mask = eligible(gates, rule)
        table[f"eligible_{rule}"] = mask
        ranks = table.score.where(mask).rank(ascending=False, method="first")
        table[f"rank_{rule}"] = ranks.astype("Int64")
        table[f"top5_share_{rule}"] = top5_frequency(comp, mask, draws).where(mask)
        detail["top5"][rule] = top_n(table.score, mask)
        detail["named"][rule] = {name: top_n(score(comp, w), mask) for name, w in NAMED_WEIGHTS.items()}
        detail["leave_one_out"][rule] = leave_one_out(comp, mask)
    ok = table.eligible_flag
    detail["followers_spearman"] = float(table.loc[ok, "score"].rank().corr(table.loc[ok, "followers"].rank()))
    return table, detail


def stability_words(share: float) -> str:
    if pd.isna(share):
        return "not eligible"
    return "Firm" if share >= 0.8 else "Likely" if share >= 0.5 else "Close call" if share >= 0.2 else "Rarely"


def rank_cell(row: pd.Series, rule: str) -> str:
    value = row[f"rank_{rule}"]
    return "" if pd.isna(value) else str(value)


def write_report(table: pd.DataFrame, detail: dict, folder: Path) -> None:
    main = config.COMPETITOR_RULE
    h = table.handle
    names = lambda idx: ", ".join(f"`{h[i]}`" for i in idx)  # noqa: E731
    lines = [
        "# Creator ranking",
        "",
        "The score measures how well each creator fits what the brand's own ads suggest sells. It does not predict sales: "
        "nothing in the data links a creator to a purchase. The weights are judgment, so the ranking is tested against "
        f"{config.SENSITIVITY_DRAWS:,} random weightings and six named ones.",
        "",
        "## Top five under each competitor rule",
        "",
        "Whether recent work for a rival rules a creator out is a business decision, so all three versions are shown. "
        "The main answer uses the first. Change `COMPETITOR_RULE` in `src/lj/config.py` to switch.",
        "",
        "| Competitor rule | Eligible | Top five |",
        "|---|---:|---|",
    ]
    for rule in config.COMPETITOR_RULES:
        marker = " **(main answer)**" if rule == main else ""
        lines.append(
            f"| {RULE_WORDS[rule]}{marker} | {int(table[f'eligible_{rule}'].sum())} | {names(detail['top5'][rule])} |"
        )
    lines += ["", "**Recent rival work (last 90 days, all paid partnerships):**", ""]
    for _, r in table[table.competitor_recent].iterrows():
        kind = "challenger" if r.competitor_recent_challenger else "mass brand only"
        lines.append(f"- `{r.handle}`: {r.competitor_detail} ({kind})")
    lines += [
        "",
        "## How it works",
        "",
        "1. **Gates (yes/no).** Children on camera are mostly at or above the product's starting age, or the feed speaks to parents of school-age children; "
        "the feed is about family or food, and measured audience (where we have it) isn't mostly men; and the creator posted in the last 90 days.",
        "2. **Competitor rule**, as above.",
        "3. **Score (0 to 100)** from five criteria, each on a 0 to 1 scale:",
        "",
        "| Criterion | Weight | How it's measured |",
        "|---|---:|---|",
        *[f"| {CRITERION_WORDS[c]} | {config.SCORE_WEIGHTS[c]:.0%} | {CRITERION_MEASURE[c]} |" for c in CRITERIA],
        "",
        "The child moment carries the most weight because it is the strongest sales signal in the brand's ads.",
        "",
        "**Not in the score, on purpose:** likes and comments. Likes are hidden on some accounts, comment-for-link captions inflate comments, "
        "and some creators switch comments off, so plays are the only engagement signal that holds up. Audience data exists for 3 of 20 creators, "
        "so it acts as a check (a measured audience that is mostly men fails the gates) and lowers confidence when missing, rather than scoring 17 creators on nothing.",
        "",
        "**Stability** is the share of random weightings under which a creator makes the top 5: Firm (80% or more), Likely (50 to 79%), Close call (20 to 49%), Rarely (under 20%). "
        "In a small pool most eligible creators make the top 5 by construction, so a high share there says little. The useful question is who drops out, and how far apart the scores are.",
        "",
        "## All 20 creators",
        "",
        "| Creator | Gates | Recent rival work | Score | Rank: strict | Rank: challengers only | Rank: flag only | Stability (main) | Confidence |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    order = table.sort_values([f"eligible_{main}", "score"], ascending=False)
    for _, r in order.iterrows():
        gate = "Pass" if r.passes_gates else f"Fail: {r.gate_reason}"
        share = r[f"top5_share_{main}"]
        stab = "" if pd.isna(share) else f"{stability_words(share)} ({share:.0%})"
        rival = r.competitor_detail or ("Yes" if r.competitor_recent else "No")
        ranks = " | ".join(rank_cell(r, rule) for rule in ("exclude", "challengers_only", "flag"))
        lines.append(f"| `{r.handle}` | {gate} | {rival} | {r.score:.0f} | {ranks} | {stab} | {r.confidence} |")
    lines += [
        "",
        "## Score breakdown for eligible creators",
        "",
        "| Creator | " + " | ".join(CRITERION_WORDS[c] for c in CRITERIA) + " | Plays used for reach |",
        "|---|" + "---:|" * len(CRITERIA) + "---|",
    ]
    for _, r in table[table.eligible_flag].sort_values("score", ascending=False).iterrows():
        lines.append(
            f"| `{r.handle}` | "
            + " | ".join(f"{r[c]:.2f}" for c in CRITERIA)
            + f" | {r.reach_plays:,.0f} ({r.reach_source}) |"
        )
    lines += [
        "",
        "## Named weightings",
        "",
        "| Weighting | " + " | ".join(RULE_WORDS[r] for r in config.COMPETITOR_RULES) + " |",
        "|---|" + "---|" * len(config.COMPETITOR_RULES),
    ]
    for name in NAMED_WEIGHTS:
        lines.append(
            f"| {name} | " + " | ".join(names(detail["named"][rule][name]) for rule in config.COMPETITOR_RULES) + " |"
        )
    lines += ["", "## Removing one criterion at a time (main answer)", "", "| Without | Top 5 |", "|---|---|"]
    for crit, idx in detail["leave_one_out"][main].items():
        lines.append(f"| {CRITERION_WORDS[crit]} | {names(idx)} |")
    lines += [
        "",
        "## Checks",
        "",
        f"- Rank correlation between score and followers among gate-passing creators: {detail['followers_spearman']:+.2f}. "
        "The score isn't just following audience size.",
        "- Confidence is separate from fit. It counts six kinds of evidence: enough organic videos, transcripts, reach that isn't one viral post, "
        "a child already seen enjoying food on camera, a confirmed child age, and real audience data. High is 5 or 6, Medium 4, Low 3 or fewer.",
        "",
        "## Confidence gaps for the main five",
        "",
        "| Creator | Confidence | What we don't have |",
        "|---|---|---|",
    ]
    for i in detail["top5"][main]:
        r = table.loc[i]
        lines.append(f"| `{r.handle}` | {r.confidence} | {r.confidence_missing or 'nothing on this list'} |")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "creator_rankings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    features = pd.read_csv(config.OUTPUTS_DIR / "creator_features.csv")
    competitors = competitor_table(
        features.handle, pd.read_csv(config.OUTPUTS_DIR / "brand_relationships.csv"), pd.read_csv(COMPETITOR_TYPES)
    )
    table, detail = build(features, competitors)
    table.to_csv(config.OUTPUTS_DIR / "creator_rankings.csv", index=False)
    write_report(table, detail, config.OUTPUTS_DIR)
    for rule in config.COMPETITOR_RULES:
        print(
            f"Top five ({rule}{', main' if rule == config.COMPETITOR_RULE else ''}): {', '.join(table.handle[detail['top5'][rule]])}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
