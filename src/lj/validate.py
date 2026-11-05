"""Data validation. Errors stop the pipeline; warnings are known issues the analysis must handle."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from lj import config
from lj.ingest import RawData

REQUIRED_COLUMNS = {
    "ads": [
        "ad_id",
        "meta_ad_library_id",
        "video_url",
        "launch_date",
        "stopped_date",
        "days_live",
        "duration_s",
        "language",
        "ad_copy",
        "transcript",
        "hook_line",
        "on_screen_text",
        "claims_made",
        "hook_type",
        "hook_driver",
        "hook_delivered_by",
        "hook_text_on_screen",
        "ad_format",
        "story_structure",
        "main_benefit",
        "performance_style",
        "humour",
        "creator_type",
        "creator_gender",
        "creator_age",
        "people_on_screen",
        "child_on_screen",
        "child_age",
        "child_role",
        "child_in_first_3s",
        "brand_first_said",
        "brand_said_aloud",
        "product_form",
        "product_shown_as",
        "demo_shown",
        "proof_used",
        "persuasion",
        "production",
        "audio",
        "music",
        "captions",
        "language_mixing",
        "first_frame",
        "setting",
        "cta_type",
        "offer",
        "narratives",
        "ad_categories",
        "spend_inr",
        "impressions",
        "video_3s_views",
        "thruplays",
        "link_clicks",
        "add_to_carts",
        "purchases",
        "revenue_inr",
    ],
    "creators": [
        "creator_id",
        "handle",
        "name",
        "profile_url",
        "bio",
        "followers",
        "following",
        "total_posts",
        "verified",
        "posts_in_file",
        "persona",
        "persona_description",
        "feed_story",
        "voice",
        "language_use",
        "catchphrases",
        "themes",
        "format_habits",
        "what_feels_native",
        "what_would_feel_foreign",
        "audience_read",
    ],
    "posts": [
        "creator_id",
        "handle",
        "post_url",
        "posted_on",
        "type",
        "duration_s",
        "caption",
        "plays",
        "likes",
        "comments",
        "reshares",
        "content_type",
        "content_form",
        "topic",
        "hook_style",
        "creator_on_camera",
        "children_on_camera",
        "child_ages",
        "presenter_age",
        "presenter_gender",
        "language",
        "setting",
        "tone",
        "product_shown",
        "is_sponsored",
        "brands_visible",
        "production_quality_1to5",
        "audience_signal",
        "on_screen_text",
        "what_stands_out",
        "transcript",
        "transcript_language",
    ],
    "audience": [
        "creator_id",
        "handle",
        "platform",
        "as_of",
        "women_pct",
        "men_pct",
        "age_split",
        "top_cities",
        "top_countries",
        "brands_in_past_year",
    ],
}
EXPECTED_ROWS = {"ads": 100, "creators": 20, "posts": 392, "audience": 3}
KEYS = {
    "ads": ["ad_id", "meta_ad_library_id"],
    "creators": ["handle", "creator_id"],
    "posts": ["post_url"],
    "audience": ["handle"],
}
AD_COUNTS = [
    "spend_inr",
    "impressions",
    "video_3s_views",
    "thruplays",
    "link_clicks",
    "add_to_carts",
    "purchases",
    "revenue_inr",
]
FUNNEL_ORDER = [
    ("video_3s_views", "impressions"),
    ("thruplays", "video_3s_views"),
    ("link_clicks", "impressions"),
    ("add_to_carts", "link_clicks"),
    ("purchases", "add_to_carts"),
]


@dataclass
class Check:
    name: str
    dataset: str
    severity: str  # "error" stops the pipeline when failed; "warning" must be handled downstream
    passed: bool
    detail: str = ""
    rows: list | None = None

    def __post_init__(self):
        self.passed = bool(self.passed)  # checks often produce numpy booleans, which JSON rejects


def _ids(series: pd.Series, limit: int = 12) -> list:
    return [str(v) for v in series.head(limit)]


def check_structure(raw: RawData, expected_rows: dict[str, int] | None = EXPECTED_ROWS) -> list[Check]:
    checks: list[Check] = []
    for table, columns in REQUIRED_COLUMNS.items():
        df = getattr(raw, table)
        missing = sorted(set(columns) - set(df.columns))
        checks.append(
            Check(
                "required columns present",
                table,
                "error",
                not missing,
                f"missing: {missing}" if missing else f"{len(columns)} columns",
            )
        )
        if expected_rows:
            checks.append(
                Check(
                    "row count",
                    table,
                    "error",
                    len(df) == expected_rows[table],
                    f"{len(df)} rows, expected {expected_rows[table]}",
                )
            )
        dups = int(df.duplicated().sum())
        checks.append(Check("no fully duplicated rows", table, "error", dups == 0, f"{dups} duplicates"))
        for key in KEYS[table]:
            if key in df.columns:
                n = int(df[key].duplicated().sum())
                checks.append(
                    Check(
                        f"{key} unique",
                        table,
                        "error",
                        n == 0,
                        f"{n} repeats",
                        _ids(df.loc[df[key].duplicated(), key]) or None,
                    )
                )
    return checks


def check_ads(ads: pd.DataFrame) -> list[Check]:
    checks: list[Check] = []
    nulls = ads[AD_COUNTS].isna().sum().sum()
    checks.append(Check("performance columns complete", "ads", "error", nulls == 0, f"{nulls} missing values"))
    negative = ads[(ads[AD_COUNTS] < 0).any(axis=1)]
    checks.append(
        Check(
            "no negative performance values",
            "ads",
            "error",
            negative.empty,
            f"{len(negative)} rows",
            _ids(negative.ad_id) or None,
        )
    )
    for low, high in FUNNEL_ORDER:
        bad = ads[ads[low] > ads[high]]
        checks.append(Check(f"{low} <= {high}", "ads", "error", bad.empty, f"{len(bad)} rows", _ids(bad.ad_id) or None))
    bad = ads[(ads.spend_inr <= 0) | (ads.impressions <= 0)]
    checks.append(
        Check(
            "spend and impressions above zero", "ads", "error", bad.empty, f"{len(bad)} rows", _ids(bad.ad_id) or None
        )
    )
    bad = ads[(ads.purchases == 0) != (ads.revenue_inr == 0)]
    checks.append(
        Check(
            "revenue is zero exactly when purchases are zero",
            "ads",
            "error",
            bad.empty,
            f"{len(bad)} rows",
            _ids(bad.ad_id) or None,
        )
    )

    launch = pd.to_datetime(ads.launch_date, errors="coerce")
    stop = pd.to_datetime(ads.stopped_date, errors="coerce")
    checks.append(
        Check("launch dates parse", "ads", "error", launch.notna().all(), f"{int(launch.isna().sum())} unparsed")
    )
    bad = ads[stop < launch]
    checks.append(
        Check("stop is not before launch", "ads", "error", bad.empty, f"{len(bad)} rows", _ids(bad.ad_id) or None)
    )
    bad = ads[stop > config.ADS_AS_OF]
    checks.append(
        Check(
            "stop is not after the as-of date", "ads", "error", bad.empty, f"{len(bad)} rows", _ids(bad.ad_id) or None
        )
    )

    # Known issues: reported, then handled in analysis.
    blanks = int(ads.stopped_date.isna().sum())
    checks.append(
        Check(
            "some ads still live (README: blank stopped_date)",
            "ads",
            "warning",
            blanks > 0,
            f"{blanks} blanks; {ads.stopped_date.nunique()} distinct stop dates, latest {ads.stopped_date.max()}. Likely snapshot dates, so days_live is weak evidence.",
        )
    )
    span = (stop.fillna(config.ADS_AS_OF) - launch).dt.days
    off = int((span != ads.days_live).sum())
    checks.append(
        Check(
            "days_live equals stop minus launch",
            "ads",
            "warning",
            off == 0,
            f"{off} rows differ, by at most {int((span - ads.days_live).abs().max())} day",
        )
    )
    repeats = ads[ads.video_url.duplicated(keep=False)].sort_values("video_url")
    checks.append(
        Check(
            "each ad is a distinct video",
            "ads",
            "warning",
            repeats.empty,
            f"{ads.video_url.nunique()} distinct videos in {len(ads)} ads",
            _ids(repeats.ad_id) or None,
        )
    )
    bad = ads[(ads.purchases == 0) & (ads.add_to_carts > 0)]
    checks.append(
        Check(
            "no zero-purchase ads with add-to-carts",
            "ads",
            "warning",
            bad.empty,
            "reviewed by the tracking-failure rule in clean.py",
            _ids(bad.ad_id) or None,
        )
    )
    bad = ads[(ads.brand_said_aloud == "no") & ads.brand_first_said.notna()]
    checks.append(
        Check(
            "brand timing absent when brand not said aloud",
            "ads",
            "warning",
            bad.empty,
            f"{len(bad)} ads have both, so the two labels contradict",
        )
    )
    bad = ads[(ads.people_on_screen == "none") & (ads.child_on_screen != "none")]
    checks.append(
        Check(
            "no child on screen when no people on screen",
            "ads",
            "warning",
            bad.empty,
            f"{len(bad)} contradictions",
            _ids(bad.ad_id) or None,
        )
    )
    bad = ads[(ads.people_on_screen == "none") & (ads.creator_type != "none_visible")]
    checks.append(
        Check(
            "no named creator type when no people on screen",
            "ads",
            "warning",
            bad.empty,
            f"{len(bad)} contradictions",
            _ids(bad.ad_id) or None,
        )
    )
    label_cols = ["hook_type", "ad_format", "story_structure", "child_role", "brand_first_said", "creator_age"]
    gaps = {c: int(ads[c].isna().sum()) for c in label_cols if ads[c].isna().any()}
    checks.append(Check("labels complete", "ads", "warning", not gaps, f"blanks: {gaps}"))
    return checks


def check_creators_and_posts(raw: RawData) -> list[Check]:
    creators, posts, audience = raw.creators, raw.posts, raw.audience
    checks: list[Check] = []
    orphans = set(posts.handle) - set(creators.handle)
    checks.append(
        Check(
            "every post belongs to a known creator",
            "posts",
            "error",
            not orphans,
            f"{len(orphans)} unknown handles",
            sorted(orphans)[:12] or None,
        )
    )
    no_posts = set(creators.handle) - set(posts.handle)
    checks.append(
        Check(
            "every creator has posts",
            "creators",
            "error",
            not no_posts,
            f"{len(no_posts)} without posts",
            sorted(no_posts)[:12] or None,
        )
    )
    merged = posts.merge(creators[["handle", "creator_id"]], on="handle", how="left", suffixes=("", "_c"))
    bad = merged[merged.creator_id != merged.creator_id_c]
    checks.append(Check("post creator_id matches creators.csv", "posts", "error", bad.empty, f"{len(bad)} mismatches"))
    orphans = set(audience.handle) - set(creators.handle)
    checks.append(
        Check(
            "every audience row belongs to a known creator",
            "audience",
            "error",
            not orphans,
            f"{len(orphans)} unknown handles",
        )
    )
    counts = posts.groupby("handle").size()
    declared = creators.set_index("handle").posts_in_file
    bad = declared[declared != counts.reindex(declared.index)]
    checks.append(
        Check(
            "posts_in_file matches actual count",
            "creators",
            "error",
            bad.empty,
            f"{len(bad)} mismatches",
            _ids(bad.index.to_series()) or None,
        )
    )
    negative = posts[(posts[["likes", "comments", "reshares"]] < 0).any(axis=1) | (posts.plays < 0)]
    checks.append(Check("no negative engagement", "posts", "error", negative.empty, f"{len(negative)} rows"))
    bad = posts[posts.likes > posts.plays]
    checks.append(Check("likes do not exceed plays", "posts", "error", bad.empty, f"{len(bad)} rows"))
    dated = pd.to_datetime(posts.posted_on, errors="coerce")
    checks.append(
        Check("post dates parse", "posts", "error", dated.notna().all(), f"{int(dated.isna().sum())} unparsed")
    )
    is_video = posts.type == "video"
    checks.append(
        Check(
            "plays exist for all videos",
            "posts",
            "error",
            posts.loc[is_video, "plays"].notna().all(),
            f"{int(posts.loc[is_video, 'plays'].isna().sum())} videos without plays",
        )
    )
    shares = audience.women_pct + audience.men_pct
    bad = audience[(shares - 100).abs() > 1]
    checks.append(Check("audience gender shares sum to 100", "audience", "error", bad.empty, f"{len(bad)} rows"))

    # Known issues.
    nonvideo = int((~is_video).sum())
    checks.append(
        Check(
            "plays exist for all posts",
            "posts",
            "warning",
            nonvideo == 0,
            f"{nonvideo} non-video posts have no plays: unavailable, not zero",
        )
    )
    few = declared[declared < 20]
    checks.append(
        Check(
            "each creator has about 20 posts",
            "creators",
            "warning",
            few.empty,
            f"{ {handle: int(n) for handle, n in few.items()} }",
        )
    )
    old = posts[(config.POSTS_AS_OF - dated).dt.days > config.RECENT_WINDOW_DAYS]
    checks.append(
        Check(
            f"all posts within {config.RECENT_WINDOW_DAYS} days",
            "posts",
            "warning",
            old.empty,
            f"{len(old)} older posts, the oldest from {dated.min().date()}",
        )
    )
    bad = audience[audience.platform != "instagram"]
    checks.append(
        Check(
            "audience measured on Instagram",
            "audience",
            "warning",
            bad.empty,
            f"{list(bad.handle)} use another platform and cannot be compared directly",
        )
    )
    has_lang = posts.transcript_language.notna()
    bad = posts[has_lang & (posts.transcript_language.str.len() > 25)]
    checks.append(
        Check(
            "transcript_language holds a language name",
            "posts",
            "warning",
            bad.empty,
            f"{len(bad)} rows contain pasted text",
        )
    )
    bad = posts[has_lang & posts.transcript.isna()]
    checks.append(
        Check("transcript_language only where a transcript exists", "posts", "warning", bad.empty, f"{len(bad)} rows")
    )
    empty_read = creators.audience_read.str.contains('"comment_evidence": "none"', regex=False).sum()
    checks.append(
        Check(
            "audience_read has comment evidence",
            "creators",
            "warning",
            empty_read == 0,
            f"{int(empty_read)} of {len(creators)} report comment_evidence none, so the field is not used",
        )
    )
    return checks


def run_all(raw: RawData, expected_rows: dict[str, int] | None = EXPECTED_ROWS) -> list[Check]:
    return check_structure(raw, expected_rows) + check_ads(raw.ads) + check_creators_and_posts(raw)


def failed_errors(checks: list[Check]) -> list[Check]:
    return [c for c in checks if c.severity == "error" and not c.passed]


def write_report(checks: list[Check], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "data_validation.json").write_text(json.dumps([asdict(c) for c in checks], indent=2), encoding="utf-8")
    passed = sum(c.passed for c in checks)
    errors = failed_errors(checks)
    warnings = [c for c in checks if c.severity == "warning" and not c.passed]
    lines = [
        "# Data validation report",
        "",
        f"**{passed} of {len(checks)} checks passed.** Blocking failures: {len(errors)}. Known issues handled downstream: {len(warnings)}.",
        "",
        "All ad performance figures are made up for this exercise and are not Little Joys' real results.",
        "",
        "## Known issues",
        "",
        "| Dataset | Check | Result | Example rows |",
        "|---|---|---|---|",
    ]
    lines += [f"| {c.dataset} | {c.name} | {c.detail} | {', '.join(c.rows) if c.rows else ''} |" for c in warnings]
    if errors:
        lines += ["", "## Blocking failures", ""] + [f"- {c.dataset}: {c.name}: {c.detail}" for c in errors]
    lines += ["", "## Passed checks", "", "| Dataset | Check | Result |", "|---|---|---|"]
    lines += [f"| {c.dataset} | {c.name} | {c.detail} |" for c in checks if c.passed]
    (folder / "data_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
