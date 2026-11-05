"""One consistent profile per creator, built from their posts. Run with: uv run python -m lj.creators

Everything here is description. Gates and scores come in the next step. Unavailable values stay missing, so a creator
with hidden likes or no organic posts isn't treated as having zero.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lj import clean, config, ingest

BRANDS_FILE = config.ROOT / "data" / "overrides" / "brand_relationships.csv"
REVIEW_FILE = config.ROOT / "data" / "overrides" / "creator_review.csv"
SPONSORSHIP_AUDIT = config.AUDIT_DIR / "sponsorship_audit.csv"

MIN_FOR_SPONSOR_COMPARISON = 3  # below this, a sponsored-vs-organic ratio is one or two posts talking
SATURATED_SHARE = 0.5
RECENT_BRAND_DAYS = 90
CHILD_FOOD = re.compile(
    r"\b(?:eat|eats|eating|ate|tast\w+|drink\w*|sip\w*|milk|snack\w*|lunch\w*|tiffin|breakfast|meal\w*|feed\w*|food|recipe|cook\w*|chew\w*|bite|gumm\w+)\b",
    re.I,
)
FOOD_TOPIC = re.compile(
    r"\b(?:food\w*|meal\w*|recipe\w*|lunch\w*|tiffin|breakfast|snack\w*|nutrition\w*|protein|milk\w*|eat\w*|picky|fussy|diet|cook\w*|vitamin\w*|supplement\w*|immunity|dinner|supermilk)\b",
    re.I,
)
PARENT_AUDIENCE = re.compile(r"\b(?:parent\w*|mom\w*|mum\w*|mother\w*|famil\w*|caregiver\w*)\b", re.I)


# ---------------------------------------------------------------- reviewed inputs
def load_brands(posts: pd.DataFrame, path: Path = BRANDS_FILE) -> pd.DataFrame:
    """Reviewed brand relationships. Post-based rows must match a real post carrying that brand label."""
    brands = pd.read_csv(path)
    brands["posted_on"] = pd.to_datetime(brands.posted_on)
    urls = []
    for row in brands.itertuples():
        if row.source != "post":
            urls.append(None)
            continue
        found = posts[
            (posts.handle == row.handle)
            & (posts.posted_on == row.posted_on)
            & posts.brands_visible.fillna("").str.contains(re.escape(row.brand), case=False)
        ]
        if len(found) != 1:
            raise ValueError(
                f"{row.handle} {row.posted_on.date()} {row.brand}: expected 1 matching post, found {len(found)}"
            )
        urls.append(found.post_url.iloc[0])
    brands["post_url"] = urls
    return brands


def load_review(creators: pd.DataFrame, posts: pd.DataFrame, path: Path = REVIEW_FILE) -> pd.DataFrame:
    """Reviewed judgments per creator. Evidence dates must point at real posts by that creator."""
    review = pd.read_csv(path, keep_default_na=False)
    if set(review.handle) != set(creators.handle):
        raise ValueError(
            f"Review doesn't cover the creators exactly: {sorted(set(review.handle) ^ set(creators.handle))}"
        )
    urls = []
    for row in review.itertuples():
        found = []
        for date in filter(None, (d.strip() for d in row.enjoy_evidence_dates.split(";"))):
            matches = posts[
                (posts.handle == row.handle)
                & (posts.posted_on == pd.Timestamp(date))
                & (posts.children_on_camera == "yes")
            ]
            if matches.empty:
                raise ValueError(f"{row.handle}: no post with a child on camera on {date}")
            found.append(matches.post_url.iloc[0])
        urls.append("; ".join(found))
    review["enjoy_evidence_urls"] = urls
    return review


# ---------------------------------------------------------------- features
def median_per_thousand(values: pd.Series, plays: pd.Series) -> float:
    """Median per-post rate per 1,000 plays, using only posts where both values exist."""
    usable = values.notna() & plays.notna() & (plays > 0)
    return float((values[usable] / plays[usable] * 1000).median()) if usable.any() else np.nan


def age_shares(child_posts: pd.DataFrame) -> dict[str, float]:
    """How child-on-camera posts split: only under-3s, any child aged 3 to 12, only teens."""
    if child_posts.empty:
        return {"infant_only_share": np.nan, "age_3_to_12_share": np.nan, "teen_only_share": np.nan}
    bands = child_posts.child_age_bands.map(set)
    return {
        "infant_only_share": float(bands.map(lambda s: s == {"0-2"}).mean()),
        "age_3_to_12_share": float(bands.map(lambda s: bool(s & {"3-7", "8-12"})).mean()),
        "teen_only_share": float(bands.map(lambda s: s == {"13-17"}).mean()),
    }


def creator_row(creator: pd.Series, posts: pd.DataFrame, brands: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    recent = posts[posts.recent]
    videos = recent[recent.plays.notna()]
    organic = videos[videos.sponsored == False]  # noqa: E712  (missing means "unclear", which is excluded)
    sponsored = videos[videos.sponsored == True]  # noqa: E712
    child_posts = recent[recent.children_on_camera == "yes"]
    non_bait = videos[~videos.comment_bait]
    direct = brands[brands.category == "direct_kids_nutrition"]
    food_text = child_posts.topic.fillna("") + " " + child_posts.what_stands_out.fillna("")
    languages = recent.spoken_language.dropna().value_counts()
    organic_median = float(organic.plays.median()) if len(organic) else np.nan
    enough = len(organic) >= MIN_FOR_SPONSOR_COMPARISON and len(sponsored) >= MIN_FOR_SPONSOR_COMPARISON
    return {
        "handle": creator.handle,
        "creator_id": creator.creator_id,
        "persona": creator.persona,
        "followers": int(creator.followers),
        "posts_in_file": len(posts),
        "recent_posts": len(recent),
        "recent_videos": len(videos),
        "transcripts": int(recent.transcript.notna().sum()),
        "days_covered": int((recent.posted_on.max() - recent.posted_on.min()).days),
        "days_since_last_post": int((as_of - posts.posted_on.max()).days),
        "posts_last_90_days": int((posts.age_days <= 90).sum()),
        # reach
        "organic_videos": len(organic),
        "organic_median_plays": organic_median,
        "all_video_median_plays": float(videos.plays.median()) if len(videos) else np.nan,
        "plays_p25": float(videos.plays.quantile(0.25)) if len(videos) else np.nan,
        "plays_p75": float(videos.plays.quantile(0.75)) if len(videos) else np.nan,
        "top_post_share": float(videos.plays.max() / videos.plays.sum()) if len(videos) else np.nan,
        "median_plays_per_follower": float(videos.plays.median() / creator.followers) if len(videos) else np.nan,
        # engagement (each rate leaves out posts where the count is unavailable)
        "reshares_per_1k": median_per_thousand(videos.reshares_clean, videos.plays),
        "comments_per_1k_non_bait": median_per_thousand(non_bait.comments_clean, non_bait.plays),
        "likes_per_1k": median_per_thousand(videos.likes_clean, videos.plays),
        "hidden_likes_share": float(recent.likes_hidden.mean()),
        "comment_bait_share": float(recent.comment_bait.mean()),
        "unavailable_reshares_share": float(recent.reshares_clean.isna().mean()),
        # sponsorship
        "sponsored_posts": int(recent.sponsored.eq(True).sum()),
        "sponsored_share": float(recent.sponsored.eq(True).mean()),
        "sponsored_videos": len(sponsored),
        "sponsored_median_plays": float(sponsored.plays.median()) if len(sponsored) else np.nan,
        "sponsored_vs_organic_plays": float(sponsored.plays.median() / organic_median) if enough else np.nan,
        "saturated": bool((recent.sponsored == True).mean() > SATURATED_SHARE),  # noqa: E712
        "direct_competitor_posts": len(direct),
        "direct_competitor_brands": "; ".join(sorted(set(direct.brand))),
        "direct_competitor_latest": direct.posted_on.max().date().isoformat() if len(direct) else "",
        "direct_competitor_last_90_days": bool(
            (direct.posted_on >= as_of - pd.Timedelta(days=RECENT_BRAND_DAYS)).any()
        ),
        "adjacent_brands": "; ".join(sorted(set(brands[brands.category == "adjacent_food"].brand))),
        "little_joys_relationship": "; ".join(brands[brands.category == "little_joys"].source),
        # children and content
        "child_post_share": float((recent.children_on_camera == "yes").mean()),
        **age_shares(child_posts),
        "child_presenter_share": float(recent.presenter_age.isin(["3-7", "8-12"]).mean()),
        "child_food_share": float(food_text.str.contains(CHILD_FOOD).mean()) if len(child_posts) else 0.0,
        "food_topic_share": float(recent.topic.fillna("").str.contains(FOOD_TOPIC).mean()),
        "parent_audience_signal_share": float(recent.audience_signal.fillna("").str.contains(PARENT_AUDIENCE).mean()),
        "product_shown_share": float((recent.product_shown == "yes").mean()),
        "skit_share": float((recent.content_form == "skit").mean()),
        "demo_share": float((recent.content_form == "demo_or_haul").mean()),
        "montage_share": float((recent.content_form == "voiceover_montage").mean()),
        "to_camera_share": float((recent.content_form == "piece_to_camera").mean()),
        "main_spoken_language": languages.index[0] if len(languages) else "",
        "spoken_language_mix": "; ".join(f"{k} {v}" for k, v in languages.items()),
        "themes": creator.themes,
    }


def build_features(data: clean.CleanData) -> pd.DataFrame:
    brands = load_brands(data.posts)
    review = load_review(data.creators, data.posts)
    rows = [
        creator_row(c, data.posts[data.posts.handle == c.handle], brands[brands.handle == c.handle], config.POSTS_AS_OF)
        for _, c in data.creators.iterrows()
    ]
    table = pd.DataFrame(rows).merge(
        review.drop(columns=["enjoy_evidence_dates"]), on="handle", how="left", validate="one_to_one"
    )
    audience = data.audience[
        ["handle", "platform", "women_pct", "men_pct", "india_pct", "age_split", "comparable_platform"]
    ].rename(columns={"platform": "audience_platform", "age_split": "audience_age_split"})
    return table.merge(audience, on="handle", how="left", validate="one_to_one")


def data_gaps(row: pd.Series) -> list[str]:
    """Plain statements of what we can't know about this creator."""
    gaps = []
    if pd.isna(row.women_pct):
        gaps.append("No audience data, so who watches is unknown")
    elif not row.comparable_platform:
        gaps.append(f"Audience data comes from {row.audience_platform.title()}, not Instagram")
    if row.organic_videos < 5:
        gaps.append(f"Only {row.organic_videos} organic videos, so typical reach is uncertain")
    if pd.isna(row.sponsored_vs_organic_plays):
        gaps.append("Too few posts to compare sponsored and organic plays")
    if row.hidden_likes_share > 0:
        gaps.append(f"Likes hidden on {row.hidden_likes_share:.0%} of recent posts")
    if row.unavailable_reshares_share >= 0.25:
        gaps.append(f"Reshares unavailable on {row.unavailable_reshares_share:.0%} of recent posts")
    if row.recent_posts < 15:
        gaps.append(f"Only {row.recent_posts} posts within the last year")
    if row.transcripts < 5:
        gaps.append(f"Only {row.transcripts} transcripts, so spoken style is less certain")
    if row.days_covered < 45:
        gaps.append(f"Recent posts cover only {row.days_covered} days")
    return gaps


# ---------------------------------------------------------------- reporting
AGE_WORDS = {
    "eligible": "Eligible",
    "eligible_unconfirmed": "Probably eligible, to confirm",
    "mixed": "Mixed ages",
    "infant_led": "Mostly under the product's starting age",
    "teen_only": "Teens only",
    "no_child": "No children shown",
    "school_age_not_shown": "School-age child, not shown",
}
ENJOY_WORDS = {"proven": "Done on camera", "plausible": "Plausible", "unlikely": "Unlikely without a format change"}


def number(value, style: str = "int") -> str:
    if pd.isna(value):
        return "n/a"
    return {"int": f"{value:,.0f}", "pct": f"{value:.0%}", "x": f"{value:.2f}x", "rate": f"{value:.1f}"}[style]


def write_report(features: pd.DataFrame, brands: pd.DataFrame, sponsorship: pd.DataFrame, folder: Path) -> None:
    table = features.sort_values("creator_id")
    agree = int((sponsorship.verdict == "agree").sum())
    unclear = int((sponsorship.verdict == "cannot_tell").sum())
    lines = [
        "# Creator profiles",
        "",
        "All 20 creators, built from their posts within the last 365 days. This is a description of each creator, not a ranking. Gates and scores come next.",
        "",
        "Medians are used because one viral post can dominate. Missing values stay `n/a`: hidden likes, photo posts without play counts and unavailable reshares don't count as zero. "
        "Follower counts are shown but don't drive anything here.",
        "",
        f"**Label checks, read from captions and transcripts by Claude (no video, since the posts are on Instagram):** of 28 randomly chosen sponsorship labels, {agree} look right and {unclear} can't be told from text. "
        f"Every kids' food or nutrition brand below was read against its post, which added brands the earlier list missed, such as Good Monk. Child ages were checked wherever text states them, but many posts give no age, so these remain partly unconfirmed. "
        "The post `language` label isn't used, because it was wrong on 83% of the English-labelled posts checked.",
        "",
        "## At a glance",
        "",
        "| Creator | Followers | Organic median plays (videos) | Top post share | Sponsored share | Child on camera | Age fit | Child enjoying product | Direct competitor work |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for r in table.itertuples():
        rival = (
            f"{r.direct_competitor_brands} ({r.direct_competitor_latest})" if r.direct_competitor_posts else "None seen"
        )
        lines.append(
            f"| `{r.handle}` | {r.followers:,} | {number(r.organic_median_plays)} ({r.organic_videos}) | {number(r.top_post_share, 'pct')} | {number(r.sponsored_share, 'pct')} | "
            f"{number(r.child_post_share, 'pct')} | {AGE_WORDS[r.age_status]} | {ENJOY_WORDS[r.enjoy_status]} | {rival} |"
        )
    lines += [
        "",
        '"None seen" covers only the posts in this sample. Exclusivity terms and rates are unknown for everyone.',
        "",
    ]
    for _, r in table.iterrows():
        audience = (
            f"{r.audience_platform.title()}: {r.women_pct:.0f}% women, {r.men_pct:.0f}% men, {r.india_pct:.0f}% India; {r.audience_age_split}"
            if pd.notna(r.women_pct)
            else "No data"
        )
        evidence = r.enjoy_evidence_urls.replace("; ", ", ") if r.enjoy_evidence_urls else "None"
        relationship = brands[(brands.handle == r.handle) & (brands.category == "little_joys")]
        lines += [
            f"## `{r.handle}` ({r.creator_id})",
            "",
            f"**Persona:** {r.persona}. **Themes:** {r.themes}.",
            "",
            f"- **Strengths:** {r.strengths}.",
            f"- **Weaknesses:** {r.weaknesses}.",
            f"- **Risks:** {r.risks}.",
            "",
            "| Area | What we see |",
            "|---|---|",
            f"| Reach | {r.followers:,} followers. Organic median {number(r.organic_median_plays)} plays over {r.organic_videos} videos. Middle half of all videos: {number(r.plays_p25)} to {number(r.plays_p75)}. Top post is {number(r.top_post_share, 'pct')} of plays. |",
            f"| Engagement | Per 1,000 plays: {number(r.reshares_per_1k, 'rate')} reshares, {number(r.comments_per_1k_non_bait, 'rate')} comments (excluding comment-for-link posts), {number(r.likes_per_1k, 'rate')} likes. Comment-for-link captions on {number(r.comment_bait_share, 'pct')} of posts. |",
            f"| Sponsorship | {r.sponsored_posts} of {r.recent_posts} recent posts sponsored. Sponsored vs organic plays: {number(r.sponsored_vs_organic_plays, 'x')}. Direct competitor work: {r.direct_competitor_brands or 'none seen'}. Adjacent food brands: {r.adjacent_brands or 'none seen'}. Little Joys: {'yes, per ' + ', '.join(relationship.source) if len(relationship) else 'none seen'}. |",
            f"| Children | On camera in {number(r.child_post_share, 'pct')} of posts; child presents in {number(r.child_presenter_share, 'pct')}. {AGE_WORDS[r.age_status]}: {r.age_evidence}. |",
            f"| Content | Food topics {number(r.food_topic_share, 'pct')}. Skits {number(r.skit_share, 'pct')}, demos {number(r.demo_share, 'pct')}, montage {number(r.montage_share, 'pct')}, to camera {number(r.to_camera_share, 'pct')}. Spoken: {r.spoken_language_mix or 'no transcripts'}. |",
            f"| Fit with what sells | Child enjoying a product: {ENJOY_WORDS[r.enjoy_status]}. Evidence: {evidence}. |",
            f"| Profile vs posts | {r.persona_check}. |",
            f"| Audience | {audience}. |",
            "",
            "**Data gaps:** " + ("; ".join(data_gaps(r)) + "." if data_gaps(r) else "None beyond the general limits."),
            "",
        ]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "creator_profiles.md").write_text("\n".join(lines), encoding="utf-8")


def main(data: clean.CleanData | None = None) -> int:
    data = data or clean.clean_all(ingest.load_raw())
    features = build_features(data)
    brands = load_brands(data.posts)
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    features.to_csv(config.OUTPUTS_DIR / "creator_features.csv", index=False)
    brands.to_csv(config.OUTPUTS_DIR / "brand_relationships.csv", index=False)
    write_report(features, brands, pd.read_csv(SPONSORSHIP_AUDIT), config.OUTPUTS_DIR)
    print(f"Creator profiles written for {len(features)} creators.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
