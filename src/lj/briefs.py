"""Validate and render the creator briefs. Run with: uv run python -m lj.briefs

The briefs in data/briefs/briefs.json were drafted with an LLM from the evidence in outputs/. Nothing is rendered
unless every brief passes these checks, because a brief that cites a post that doesn't exist, or a claim no ad has
made, would mislead the person using it.
"""

from __future__ import annotations

import json
import re
import string
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lj import clean, config, ingest

BRIEFS_FILE = config.ROOT / "data" / "briefs" / "briefs.json"
CLAIMS_FILE = config.ROOT / "data" / "overrides" / "claims_library.csv"
PRODUCT_NAMES = {"nutrimix_2plus": "Nutrimix 2+", "nutrimix_7plus": "Nutrimix 7+", "proteinmix": "Proteinmix"}
REQUIRED = [
    "handle",
    "product",
    "idea",
    "why",
    "hook",
    "beats",
    "child_moment",
    "reason_to_care",
    "ask",
    "tone",
    "avoid",
    "claims",
    "ads",
    "check_before_signing",
]
FREE_TEXT = ["idea", "hook", "child_moment", "reason_to_care", "ask", "tone"]
LIST_TEXT = ["beats", "avoid", "check_before_signing"]
# Phrases a brief must never put in a creator's mouth. "avoid" lists may name them, so they're checked elsewhere.
BANNED = re.compile(
    r"guarantee|clinically|doctor[- ]recommended|best in india|india'?s (only|no\.? ?1|#1)|cures?\b|"
    r"\bincreases? height|\bgrow taller|boosts? immunity|\bproven to\b",
    re.I,
)
PLACEHOLDER_FORMAT = {
    "child_post_share": "pct",
    "sponsored_share": "pct",
    "top_post_share": "pct",
    "sponsored_vs_organic_plays": "times",
    "reach_plays": "count",
    "recent_posts": "count",
}
ENJOY_PATTERN = re.compile(r"reacts_to_taste|taste_test")


# ---------------------------------------------------------------- inputs
def load_briefs(path: Path = BRIEFS_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["briefs"]


def load_claims(ads: pd.DataFrame, path: Path = CLAIMS_FILE) -> pd.DataFrame:
    """Claims library, with the ads whose claims_made back each claim. A claim no ad has made is an error."""
    claims = pd.read_csv(path)
    sources = []
    for row in claims.itertuples():
        said = ads.claims_made.fillna("").str.contains(row.match, case=False, regex=True)
        hits = ads[ads["product"].isin(row.products.split(";")) & said]
        if hits.empty:
            raise ValueError(f"Claim {row.claim_id} isn't made by any ad for {row.products}")
        sources.append("; ".join(hits.ad_id))
    claims["source_ads"] = sources
    return claims


def benchmarks(ads: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Quartiles of per-ad metrics for kids' ads, without LJ-004. LJ-089's missing purchases drop out of CVR and ROAS."""
    k = ads[(ads.segment == "kids") & ~ads.dominant_ad].copy()
    k["hook_rate"] = k.video_3s_views / k.impressions
    k["ctr"] = k.link_clicks / k.impressions
    k["cvr"] = k.purchases / k.link_clicks
    k["roas"] = k.revenue_inr / k.spend_inr
    k["cpa"] = k.spend_inr / k.purchases.where(k.purchases > 0)
    return {
        m: {q: float(k[m].quantile(v)) for q, v in (("q1", 0.25), ("median", 0.5), ("q3", 0.75))}
        for m in ("hook_rate", "ctr", "cvr", "roas", "cpa")
    }


# ---------------------------------------------------------------- validation
def placeholders(text: str) -> list[str]:
    return [name for _, name, _, _ in string.Formatter().parse(text) if name]


def texts(brief: dict) -> list[str]:
    out = [brief.get(k, "") for k in FREE_TEXT] + [w["text"] for w in brief.get("why", [])]
    return out + [t for k in LIST_TEXT if k != "avoid" for t in brief.get(k, [])]


def validate(
    brief: dict,
    *,
    posts: pd.DataFrame,
    ads: pd.DataFrame,
    claims: pd.DataFrame,
    features: pd.DataFrame,
    selected: set[str],
) -> list[str]:
    """Every problem with one brief, in words. An empty list means it passes."""
    errors = [f"missing field: {k}" for k in REQUIRED if not brief.get(k)]
    if errors:
        return errors
    handle, product = brief["handle"], brief["product"]
    if handle not in selected:
        errors.append(f"{handle} isn't one of the selected creators")
    if product not in PRODUCT_NAMES:
        errors.append(f"unknown product {product}")

    # Posts: exist, belong to this creator, recent.
    mine = posts[posts.handle == handle]
    codes = {u.rstrip("/").split("/")[-1]: u for u in posts.post_url}
    for why in brief["why"]:
        if not why.get("posts"):
            errors.append(f"reason without a source post: {why['text'][:50]}")
        for code in why.get("posts", []):
            if code not in codes:
                errors.append(f"post {code} doesn't exist")
            elif codes[code] not in set(mine.post_url):
                errors.append(f"post {code} belongs to another creator")
            elif not mine.loc[mine.post_url == codes[code], "recent"].iloc[0]:
                errors.append(f"post {code} is older than a year")

    # Ads: exist, are kids' ads, and at least one shows a child enjoying the same product line.
    cited = ads[ads.ad_id.isin(brief["ads"])]
    for missing in sorted(set(brief["ads"]) - set(cited.ad_id)):
        errors.append(f"ad {missing} doesn't exist")
    if (cited.segment != "kids").any():
        errors.append(f"cites non-kids ads: {', '.join(cited[cited.segment != 'kids'].ad_id)}")
    line = ads.loc[ads["product"] == product, "product_line"]
    enjoy = cited.child_role.fillna("").str.contains(ENJOY_PATTERN) | cited.demo_shown.fillna("").str.contains(
        ENJOY_PATTERN
    )
    if line.empty or not (enjoy & (cited.product_line == line.iloc[0])).any():
        errors.append("no cited ad shows a child enjoying this product line")

    # Claims: from the library and for this product.
    for cid in brief["claims"]:
        row = claims[claims.claim_id == cid]
        if row.empty:
            errors.append(f"claim {cid} isn't in the claims library")
        elif product not in row.products.iloc[0].split(";"):
            errors.append(f"claim {cid} isn't for {product}")

    # Product age against the creator's children.
    f = features[features.handle == handle]
    if not f.empty:
        f = f.iloc[0]
        if product == "nutrimix_7plus" and not mine.child_ages.fillna("").str.contains("8-12").any():
            errors.append("Nutrimix 7+ but no child aged 8 to 12 appears in the creator's posts")
        if product.startswith("nutrimix") and f.age_status in {"infant_led", "teen_only", "no_child"}:
            errors.append(f"{PRODUCT_NAMES[product]} doesn't fit a feed that is {f.age_status}")
        if f.age_status == "eligible_unconfirmed" and not any(
            "age" in c.lower() for c in brief["check_before_signing"]
        ):
            errors.append("child's age is unconfirmed but the checks don't ask for it")

    # Text: no typed numbers, valid placeholders, no banned phrases.
    for t in texts(brief):
        for ad_id in re.findall(r"LJ-\d{3}", t):
            if ad_id not in set(ads.ad_id):
                errors.append(f"text mentions ad {ad_id}, which doesn't exist")
        stripped = re.sub(r"\{[a-z_]+\}|LJ-\d{3}|" + "|".join(re.escape(n) for n in PRODUCT_NAMES.values()), "", t)
        if re.search(r"\d", stripped):
            errors.append(f"typed number in text (use a placeholder): {t[:60]}")
        for name in placeholders(t):
            if name not in PLACEHOLDER_FORMAT:
                errors.append(f"unknown placeholder {{{name}}}")
        if BANNED.search(t):
            errors.append(f"banned phrase: {BANNED.search(t).group(0)}")
    return errors


def validate_all(briefs: list[dict], **kwargs) -> dict[str, list[str]]:
    result = {b.get("handle", f"brief {i}"): validate(b, **kwargs) for i, b in enumerate(briefs)}
    handles = [b.get("handle") for b in briefs]
    if len(set(handles)) != len(handles):
        result["_all"] = ["a creator has more than one brief"]
    return result


# ---------------------------------------------------------------- rendering
def fill(text: str, values: pd.Series) -> str:
    def fmt(name: str) -> str:
        v, kind = values[name], PLACEHOLDER_FORMAT[name]
        if pd.isna(v):
            return "n/a"
        return {"pct": f"{v:.0%}", "times": f"{v:.1f} times", "count": f"{v:,.0f}"}[kind]

    return string.Formatter().vformat(text, (), {n: fmt(n) for n in placeholders(text)})


def test_plan(b: dict[str, dict[str, float]]) -> list[str]:
    """Spend and stop/scale rules computed from the brand's own kids' ads."""
    cpa = b["cpa"]["median"]
    budget = int(np.ceil(config.LOW_EVIDENCE_PURCHASES * b["cpa"]["q3"] / 1000) * 1000)
    check = int(np.ceil(budget / 2 / 1000) * 1000)
    pct = lambda m, q: f"{b[m][q]:.1%}"  # noqa: E731
    return [
        f"- **Paid test budget:** about ₹{budget:,} per creator in partnership-ad spend, on top of the creator's fee. "
        f"At the brand's median cost per purchase in kids' ads (₹{cpa:,.0f}) that buys roughly {budget / cpa:.0f} purchases, "
        f"and even at the upper-quartile cost it reaches {config.LOW_EVIDENCE_PURCHASES}, the point where this project treats a result as readable.",
        f"- **Early check at ₹{check:,}:** stop if both hook rate is below {pct('hook_rate', 'q1')} and click-through is below {pct('ctr', 'q1')} "
        "(the bottom quarter of the brand's kids' ads on both). Fix the opening before spending more.",
        f"- **At ₹{budget:,}:** scale if ROAS is at or above {b['roas']['median']:.2f} and conversion at or above {pct('cvr', 'median')} (the brand's medians). "
        f"Stop if ROAS is below {b['roas']['q1']:.2f} (bottom quarter). In between, try a second cut before deciding.",
        "- **Compare like with like:** run one version with the child-enjoying moment and, where the creator agrees, one without it. "
        "That tells the brand whether the pattern in its old ads holds for creators.",
        "- These benchmarks come from the brand's ad export, whose numbers are made up for this exercise. Replace them with real account benchmarks before use.",
    ]


def render(briefs: list[dict], claims: pd.DataFrame, features: pd.DataFrame, plan: list[str], folder: Path) -> None:
    lines = [
        "# Creator briefs",
        "",
        "One brief per selected creator. Each was drafted with an LLM from checked evidence and passed the validator in `lj.briefs`: "
        "every post exists and belongs to that creator, every ad exists, a cited ad shows a child enjoying the same product line, "
        "claims come only from the claims library, and every number is filled in by code.",
        "",
        "**Every product claim needs brand and legal approval before use.** The library holds only what past ads have said, not what is approved.",
        "",
    ]
    for brief in briefs:
        f = features[features.handle == brief["handle"]].iloc[0].copy()
        f["reach_plays"] = (
            f.organic_median_plays if f.organic_videos >= config.MIN_ORGANIC_VIDEOS else f.all_video_median_plays
        )
        lines += [
            f"## `{brief['handle']}`: {PRODUCT_NAMES[brief['product']]}",
            "",
            f"**The idea:** {fill(brief['idea'], f)}",
            "",
            "**Why this creator**",
            "",
        ]
        for w in brief["why"]:
            links = ", ".join(f"[post](https://www.instagram.com/p/{c}/)" for c in w["posts"])
            lines.append(f"- {fill(w['text'], f)} ({links})")
        lines += [
            "",
            "**What to say**",
            "",
            f"- **Opening:** {brief['hook']}",
            f"- **Reason to care:** {brief['reason_to_care']}",
            f"- **The proof moment:** {brief['child_moment']}",
            f"- **The ask:** {brief['ask']}",
            f"- **Tone:** {brief['tone']}",
            "",
            "**Running order**",
            "",
        ]
        lines += [f"{i}. {beat}" for i, beat in enumerate(brief["beats"], 1)]
        lines += ["", "**Claims they may use, once approved**", "", "| Claim | Check | Said in ads |", "|---|---|---|"]
        for cid in brief["claims"]:
            c = claims[claims.claim_id == cid].iloc[0]
            tier = "Check against the pack" if c.tier == "label_check" else "Needs legal sign-off"
            lines.append(f"| {c.text} | {tier}. {c.note} | {c.source_ads} |")
        lines += [
            "",
            f"**Avoid:** {'; '.join(brief['avoid'])}.",
            "",
            f"**Brand's own ads behind this brief:** {', '.join(brief['ads'])}. Each shows a child enjoying the product or is the closest match in format.",
            "",
            "**Check before signing**",
            "",
        ]
        lines += [f"- {fill(c, f)}" for c in brief["check_before_signing"]]
        lines.append("")
    lines += ["## How to test each brief", ""] + plan + [""]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "briefs.md").write_text("\n".join(lines), encoding="utf-8")


def main(data: clean.CleanData | None = None) -> int:
    data = data or clean.clean_all(ingest.load_raw())
    features = pd.read_csv(config.OUTPUTS_DIR / "creator_features.csv")
    features["reach_plays"] = features.organic_median_plays.where(
        features.organic_videos >= config.MIN_ORGANIC_VIDEOS, features.all_video_median_plays
    )
    rankings = pd.read_csv(config.OUTPUTS_DIR / "creator_rankings.csv")
    selected = set(rankings.loc[rankings[f"rank_{config.COMPETITOR_RULE}"] <= 5, "handle"])
    claims = load_claims(data.ads)
    briefs = load_briefs()
    results = validate_all(briefs, posts=data.posts, ads=data.ads, claims=claims, features=features, selected=selected)
    failed = {h: e for h, e in results.items() if e}
    if failed:
        for handle, errors in failed.items():
            for e in errors:
                print(f"  REJECTED {handle}: {e}")
        return 1
    if {b["handle"] for b in briefs} != selected:
        print(f"  Briefs don't match the selected five: {sorted(selected ^ {b['handle'] for b in briefs})}")
        return 1
    render(briefs, claims, features, test_plan(benchmarks(data.ads)), config.OUTPUTS_DIR)
    print(f"Briefs: {len(briefs)} passed validation and were written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
