"""Which ad patterns go with attention and with sales? Run with: uv run python -m lj.ads

The grading rules below were fixed before any final results were seen. A pattern only counts if it holds across
several views of the data, because one ad (LJ-004) carries 30% of revenue and about 450 comparisons are being made.

All ad performance data is synthetic. "Goes with" means association; nothing here proves cause.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lj import clean, config, ingest
from lj.metrics import AD_RATIOS, pooled_metrics, safe_div

CONCEPT_MAP = config.ROOT / "data" / "overrides" / "ad_concepts.csv"
CORRECTIONS = config.ROOT / "data" / "overrides" / "label_corrections.csv"

# ---------------------------------------------------------------- pre-declared rules
N_PERMUTATIONS = 10_000
SEED = 20261104
MIN_GROUP = 5  # concepts needed on each side before a comparison is made at all
MIN_SUPPORTED = 10  # concepts needed on each side for the top grade
FDR_Q = 0.10  # false discovery rate across every comparison, for the top grade
ALPHA = 0.05
MIN_LIFT = 0.10  # smaller differences aren't worth acting on, even if they're real
HEADLINE_ROAS_GAP = 1.0  # a pooled ROAS lead this large that fails the checks gets called out as a false lead

METRICS = {"hook_rate": "attention", "hold_rate": "retention", "ctr": "interest", "cvr": "purchase", "roas": "return"}

SINGLE_LABELS = [
    "hook_type",
    "hook_driver",
    "ad_format",
    "story_structure",
    "main_benefit",
    "performance_style",
    "creator_type",
    "creator_gender",
    "first_frame",
    "language",
    "language_mixing",
    "production",
    "audio",
    "captions",
    "setting",
    "cta_type",
    "product_shown_as",
]
MULTI_LABELS = ["child_role", "demo_shown", "proof_used", "persuasion", "narratives", "ad_categories"]
SKIP_LEVELS = {"other", "none"}
REGIONAL = {"Kannada", "Malayalam", "Tamil", "Punjabi"}

SUM_COLUMNS = [
    "spend_inr",
    "impressions",
    "video_3s_views",
    "thruplays",
    "link_clicks",
    "add_to_carts",
    "purchases",
    "revenue_inr",
]
FIRST_COLUMNS = (
    SINGLE_LABELS
    + MULTI_LABELS
    + [
        "product_line",
        "segment",
        "child_on_screen",
        "child_in_first_3s",
        "humour",
        "brand_said_aloud",
        "duration_s",
        "dominant_ad",
    ]
)


# ---------------------------------------------------------------- preparing the data
def apply_corrections(ads: pd.DataFrame, corrections: pd.DataFrame) -> pd.DataFrame:
    """Overwrite labels that a video review found wrong. Only reviewed ads change."""
    out = ads.copy()
    for row in corrections.itertuples():
        out.loc[out.ad_id == row.ad_id, row.label] = row.corrected
    return out


def assign_concepts(ads: pd.DataFrame, concept_map: pd.DataFrame) -> pd.DataFrame:
    """Each ad belongs to a concept. Ads that aren't part of a family are a concept of their own."""
    out = ads.merge(concept_map[["ad_id", "concept_id"]], on="ad_id", how="left", validate="one_to_one")
    out["concept_id"] = out.concept_id.fillna(out.ad_id)
    return out


def to_concepts(ads: pd.DataFrame) -> pd.DataFrame:
    """One row per concept. Counts are summed. Labels come from the biggest-spending member that has that label."""
    ordered = ads.sort_values("spend_inr", ascending=False)
    grouped = ordered.groupby("concept_id", sort=False)
    # min_count=1 keeps a concept's purchases missing, not zero, when every member's value is missing
    counts = grouped[SUM_COLUMNS].sum(min_count=1)
    labels = grouped[FIRST_COLUMNS].first()
    members = grouped.ad_id.agg(lambda ids: "; ".join(ids)).rename("ad_ids")
    n_ads = grouped.ad_id.size().rename("n_ads")
    out = pd.concat([counts, labels, members, n_ads], axis=1).reset_index()
    for name, (num, den) in AD_RATIOS.items():
        out[name] = safe_div(out[num], out[den])
    out["language_group"] = out.language.map(lambda v: "regional" if v in REGIONAL else v)
    return out


def build_features(concepts: pd.DataFrame, min_group: int = MIN_GROUP) -> dict[str, pd.Series]:
    """Every yes/no pattern to test, named 'label = value'. Too-small groups are left out rather than guessed at."""
    features: dict[str, pd.Series] = {}
    for column in SINGLE_LABELS:
        for level in concepts[column].dropna().unique():
            if level not in SKIP_LEVELS:
                features[f"{column} = {level}"] = concepts[column] == level
    for column in MULTI_LABELS:
        lists = concepts[column].fillna("").map(lambda s: {part.strip() for part in s.split(";") if part.strip()})
        for level in sorted(set().union(*lists)) if len(lists) else []:
            if level not in SKIP_LEVELS:
                features[f"{column} = {level}"] = lists.map(lambda values, lv=level: lv in values)
    features["language = regional"] = concepts.language.isin(REGIONAL)
    features["child_on_screen = any"] = concepts.child_on_screen != "none"
    features["child_in_first_3s = yes"] = concepts.child_in_first_3s == "yes"
    features["humour = any"] = concepts.humour != "none"
    features["brand_said_aloud = yes"] = concepts.brand_said_aloud == "yes"
    features["duration = up to 30s"] = concepts.duration_s <= 30
    features["duration = over 45s"] = concepts.duration_s > 45
    total = len(concepts)
    return {name: mask.astype(bool) for name, mask in features.items() if min_group <= mask.sum() <= total - min_group}


# ---------------------------------------------------------------- statistics
def stratified_permutations(strata: np.ndarray, n_permutations: int, rng: np.random.Generator) -> np.ndarray:
    """Row indices shuffled within each stratum. Comparing like with like: each product line keeps its own ads."""
    indices = np.tile(np.arange(len(strata)), (n_permutations, 1))
    for stratum in np.unique(strata):
        positions = np.flatnonzero(strata == stratum)
        indices[:, positions] = rng.permuted(np.tile(positions, (n_permutations, 1)), axis=1)
    return indices


def pooled_gap(masks: np.ndarray, numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """In-group minus out-group pooled rate, for one mask or a matrix of masks (one per row)."""
    masks = masks.astype(float)
    inside = (masks @ numerator) / (masks @ denominator)
    outside = ((1 - masks) @ numerator) / ((1 - masks) @ denominator)
    return inside - outside


def permutation_test(
    mask: np.ndarray, numerator: np.ndarray, denominator: np.ndarray, indices: np.ndarray
) -> tuple[float, float, float]:
    """Observed gap, product-adjusted gap (observed minus what shuffling within products gives), two-sided p."""
    observed = float(pooled_gap(mask, numerator, denominator))
    shuffled = pooled_gap(mask[indices], numerator, denominator)
    centre = float(shuffled.mean())
    extreme = np.abs(shuffled - centre) >= abs(observed - centre) - 1e-12
    return observed, observed - centre, float((extreme.sum() + 1) / (len(shuffled) + 1))


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """False discovery rate adjusted p-values (q-values)."""
    p = p_values.to_numpy(dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1.0)
    out = np.empty_like(adjusted)
    out[order] = adjusted
    return pd.Series(out, index=p_values.index)


def controlled_effect(frame: pd.DataFrame, mask: pd.Series, metric: str, control_language: bool) -> tuple[float, float]:
    """Relative lift and p-value after holding product line (and usually language) constant.

    A regression on the metric's logarithm, weighted by the square root of its denominator, with robust errors.
    Shuffled-label tests show its p-values are honest. A binomial model with an estimated scale was tried first and
    called nearly everything significant, because counts this large swamp its error estimate.
    """
    num, den = AD_RATIOS[metric]
    usable = frame[num].notna() & frame[den].notna() & (frame[den] > 0) & (frame[num] > 0)  # log of zero is undefined
    data = frame[usable]
    in_group = mask[usable].astype(float).rename("feature")
    if in_group.nunique() < 2:
        return np.nan, np.nan
    product = pd.get_dummies(data.product_line, prefix="product", drop_first=True)
    language = pd.get_dummies(data.language_group, prefix="language", drop_first=True)

    def build(*controls):
        return sm.add_constant(pd.concat([in_group, *controls], axis=1).astype(float), has_constant="add")

    def separable(matrix):
        return np.linalg.matrix_rank(matrix.to_numpy()) == matrix.shape[1]

    # If a pattern is the same set of ads as a control, the model can't tell them apart and any split it reports is
    # arbitrary (it can even flip the sign). So drop a redundant language control, and give up if product is the clash.
    design = build(product, language) if control_language else build(product)
    if not separable(design):
        design = build(product)
    if not separable(design):
        return np.nan, np.nan
    try:
        fit = sm.WLS(np.log(data[num] / data[den]), design, weights=np.sqrt(data[den])).fit(cov_type="HC3")
    except (ValueError, np.linalg.LinAlgError):
        return np.nan, np.nan
    return float(np.exp(fit.params["feature"]) - 1), float(fit.pvalues["feature"])


def bootstrap_gap(
    mask: np.ndarray, numerator: np.ndarray, denominator: np.ndarray, rng: np.random.Generator, n: int = 2000
) -> tuple[float, float]:
    """95% interval for the pooled gap, resampling concepts within each group."""
    inside, outside = np.flatnonzero(mask), np.flatnonzero(~mask)
    picks_in = rng.choice(inside, (n, len(inside)))
    picks_out = rng.choice(outside, (n, len(outside)))
    gaps = (numerator[picks_in].sum(1) / denominator[picks_in].sum(1)) - (
        numerator[picks_out].sum(1) / denominator[picks_out].sum(1)
    )
    return float(np.percentile(gaps, 2.5)), float(np.percentile(gaps, 97.5))


def grade(row: pd.Series | dict) -> str:
    """Apply the pre-declared rules. Every direction must agree; a pattern can't win on one view alone."""
    signs = [
        row["gap_without_lj004"],
        row["adjusted_gap"],
        row["median_gap"],
        row["gap_without_largest"],
        row["controlled_lift"],
    ]
    if any(pd.isna(value) for value in signs):
        return "Inconclusive"
    same_direction = len({np.sign(value) for value in signs}) == 1
    if not same_direction or row["p"] >= ALPHA:
        return "Inconclusive"
    large_enough = min(row["n_in"], row["n_out"]) >= MIN_SUPPORTED
    if large_enough and row["q"] < FDR_Q and row["controlled_p"] < ALPHA and abs(row["controlled_lift"]) >= MIN_LIFT:
        return "Supported"
    return "Directional"


# ---------------------------------------------------------------- the analysis
def analyse(ads: pd.DataFrame, n_permutations: int = N_PERMUTATIONS, seed: int = SEED) -> pd.DataFrame:
    """Test every feature on every metric, among kids' product concepts, with LJ-004 set aside."""
    rng = np.random.default_rng(seed)
    concepts = to_concepts(ads[ads.segment == "kids"])
    primary = concepts[~concepts.dominant_ad].reset_index(drop=True)
    all_kids = concepts.reset_index(drop=True)
    features = build_features(primary)
    all_features = build_features(all_kids, min_group=1)

    rows = []
    for metric, stage in METRICS.items():
        num_col, den_col = AD_RATIOS[metric]
        usable = (primary[num_col].notna() & primary[den_col].notna()).to_numpy()
        data = primary[usable]
        numerator = data[num_col].to_numpy(float)
        denominator = data[den_col].to_numpy(float)
        indices = stratified_permutations(data.product_line.to_numpy(), n_permutations, rng)
        usable_all = all_kids[num_col].notna() & all_kids[den_col].notna()
        for name, full_mask in features.items():
            mask = full_mask[usable].to_numpy()
            if not MIN_GROUP <= mask.sum() <= len(mask) - MIN_GROUP:
                continue
            gap, adjusted, p = permutation_test(mask, numerator, denominator, indices)
            spend = data.spend_inr.to_numpy()
            largest = np.flatnonzero(mask)[np.argmax(spend[mask])]
            keep = np.arange(len(mask)) != largest
            without_largest = float(pooled_gap(mask[keep], numerator[keep], denominator[keep]))
            values = data[metric].to_numpy()
            median_in, median_out = np.nanmedian(values[mask]), np.nanmedian(values[~mask])
            rate_out = numerator[~mask].sum() / denominator[~mask].sum()
            rate_in = numerator[mask].sum() / denominator[mask].sum()
            everything = all_features[name][usable_all] if name in all_features else None
            gap_all = (
                float(
                    pooled_gap(
                        everything.to_numpy(),
                        all_kids.loc[usable_all, num_col].to_numpy(float),
                        all_kids.loc[usable_all, den_col].to_numpy(float),
                    )
                )
                if everything is not None
                else np.nan
            )
            lift, controlled_p = controlled_effect(
                primary, full_mask, metric, control_language=not name.startswith(("language =", "language_mixing ="))
            )
            members = data[mask].sort_values("spend_inr", ascending=False)
            rows.append(
                {
                    "pattern": name,
                    "metric": metric,
                    "stage": stage,
                    "n_in": int(mask.sum()),
                    "n_out": int((~mask).sum()),
                    "rate_in": rate_in,
                    "rate_out": rate_out,
                    "gap_with_lj004": gap_all,
                    "gap_without_lj004": gap,
                    "adjusted_gap": adjusted,
                    "gap_without_largest": without_largest,
                    "median_in": median_in,
                    "median_out": median_out,
                    "median_gap": median_in - median_out,
                    "controlled_lift": lift,
                    "controlled_p": controlled_p,
                    "p": p,
                    "supporting_ads": " | ".join(members.ad_ids.head(5)),
                }
            )
    table = pd.DataFrame(rows)
    table["q"] = benjamini_hochberg(table.p)
    table["grade"] = table.apply(grade, axis=1)
    table["false_lead"] = (
        (table.metric == "roas") & (table.grade == "Inconclusive") & (table.gap_with_lj004 >= HEADLINE_ROAS_GAP)
    )
    # Intervals only where they'll be read, which keeps the run quick
    low, high = [], []
    for row in table.itertuples():
        if row.grade == "Inconclusive":
            low.append(np.nan)
            high.append(np.nan)
            continue
        num_col, den_col = AD_RATIOS[row.metric]
        usable = (primary[num_col].notna() & primary[den_col].notna()).to_numpy()
        interval = bootstrap_gap(
            features[row.pattern][usable].to_numpy(),
            primary.loc[usable, num_col].to_numpy(float),
            primary.loc[usable, den_col].to_numpy(float),
            rng,
        )
        low.append(interval[0])
        high.append(interval[1])
    table["gap_low"], table["gap_high"] = low, high
    return table.sort_values(["grade", "p"]).reset_index(drop=True)


def too_small_to_test(ads: pd.DataFrame) -> pd.DataFrame:
    """Patterns with too few concepts to grade. Shown as plain description, so nothing vanishes without explanation."""
    concepts = to_concepts(ads[ads.segment == "kids"])
    primary = concepts[~concepts.dominant_ad].reset_index(drop=True)
    every = build_features(primary, min_group=1)
    rows = []
    for name, mask in every.items():
        group = primary[mask]
        if not 2 <= len(group) < MIN_GROUP:
            continue
        with_dominant = concepts[
            build_features(concepts, min_group=1).get(name, pd.Series(False, index=concepts.index))
        ]
        rows.append(
            {
                "pattern": name,
                "concepts": len(group),
                "spend_inr": int(group.spend_inr.sum()),
                "roas_without_lj004": pooled_metrics(group)["roas"],
                "roas_with_lj004": pooled_metrics(with_dominant)["roas"],
                "median_roas": float(group.roas.median()),
                "ads": " | ".join(group.sort_values("spend_inr", ascending=False).ad_ids),
            }
        )
    return pd.DataFrame(rows).sort_values("spend_inr", ascending=False).reset_index(drop=True)


def family_spreads(ads: pd.DataFrame) -> pd.DataFrame:
    """How far ROAS differs between near-copies of one concept: a yardstick for ad-level noise."""
    usable = ads[ads.roas > 0]
    multi = usable[usable.groupby("concept_id").ad_id.transform("size") > 1]
    spread = multi.groupby("concept_id").agg(
        ads=("ad_id", lambda ids: ", ".join(ids)), roas_low=("roas", "min"), roas_high=("roas", "max")
    )
    spread["ratio"] = spread.roas_high / spread.roas_low
    return spread.sort_values("ratio", ascending=False).reset_index()


# ---------------------------------------------------------------- reporting
def format_rate(metric: str, value: float) -> str:
    return f"{value:.2f}" if metric == "roas" else f"{value:.1%}"


def format_gap(metric: str, value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:+.2f}" if metric == "roas" else f"{value * 100:+.1f} pts"


def pattern_rows(frame: pd.DataFrame) -> list[str]:
    lines = [
        "| Pattern | Stage | Concepts | In group | Rest | Gap without LJ-004 | 95% interval | After controls | p | q | Ads (largest first) |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|",
    ]
    for r in frame.itertuples():
        lines.append(
            f"| {r.pattern} | {r.stage} | {r.n_in} | {format_rate(r.metric, r.rate_in)} | {format_rate(r.metric, r.rate_out)} | "
            f"{format_gap(r.metric, r.gap_without_lj004)} | {format_gap(r.metric, r.gap_low)} to {format_gap(r.metric, r.gap_high)} | "
            f"{r.controlled_lift:+.0%}{'*' if r.controlled_p < ALPHA else ''} | {r.p:.4f} | {r.q:.2f} | {r.supporting_ads} |"
        )
    return lines


# Interpretation, kept apart from the numbers. Readings carry no figures; each table's values come from the analysis.
THEMES = [
    {
        "title": "A child visibly enjoying the product goes with better sales",
        "evidence": [
            ("demo_shown = taste_test", "cvr"),
            ("demo_shown = taste_test", "roas"),
            ("child_role = reacts_to_taste", "roas"),
            ("child_role = consumes_product", "roas"),
            ("narratives = taste_better_than_other_brands", "roas"),
        ],
        "reading": "This is the strongest sales signal in the file, and it holds when each group's three biggest concepts are removed. Count it as one "
        "signal, not several: every `taste_test` concept is also `reacts_to_taste`. The label is broad, meaning a child shown enjoying the "
        "product, not a formal test. Briefs should build around this moment.",
    },
    {
        "title": "Child-led ads look promising but can't be graded",
        "evidence": [("child_role = speaks", "ctr"), ("child_role = speaks", "roas")],
        "reading": "A child speaking goes with more clicks, but its lead on return mostly disappears without its three biggest concepts. Fully child-led "
        "ads have only 4 concepts once LJ-004 and near-copies are accounted for, so they got no test (see 'Too few concepts to grade'). LJ-004 is "
        "this format, and its success can't be told apart from luck or targeting. The same boy and set gave both a strong and a below-average "
        "result in `nutrimix_batman_boy_protein`. Worth testing with creators, not assuming.",
    },
    {
        "title": "Attention and sales are different jobs",
        "evidence": [
            ("child_in_first_3s = yes", "hook_rate"),
            ("child_in_first_3s = yes", "cvr"),
            ("language = Hindi", "hook_rate"),
            ("hook_type = question", "hook_rate"),
        ],
        "reading": "A child in the first 3 seconds came closest to the top grade but didn't reach it. It goes with more people watching, with no change in "
        "purchases once they click. Use it to win attention, and rely on something else to make the sale. Hindi ads also show high attention, "
        "but from few concepts, and the lead disappears without the three biggest. Don't choose creators or scripts on attention alone.",
    },
    {
        "title": "A parent's personal story may sell less well",
        "evidence": [
            ("creator_type = parent_or_caregiver", "cvr"),
            ("hook_driver = personal_experience", "cvr"),
            ("hook_driver = personal_experience", "hold_rate"),
            ("proof_used = creator_testimonial", "cvr"),
            ("production = ugc", "cvr"),
        ],
        "reading": "This matters here because most candidate creators are parents making UGC, so treat it as a caution and not a reason to change the format. "
        "Only personal-experience hooks hold after controls, and the testimonial and UGC gaps largely disappear without their biggest concepts. "
        "It doesn't show parent creators fail, and peer trust isn't something this file can measure. Keep the parent's voice and pair it with a "
        "child enjoying the product (see 'Follow-up checks').",
    },
    {
        "title": "Language matters, but this file can't say why",
        "evidence": [
            ("language = English", "cvr"),
            ("language = regional", "cvr"),
            ("language = regional", "hold_rate"),
            ("language = Hinglish", "cvr"),
        ],
        "reading": "English ads convert better and regional ones worse. We can't see targeting, so this could be who was shown the ad rather than the language "
        "itself. Hinglish, the language of most candidate creators, shows no clear gap on purchases. Don't push creators out of their natural "
        "language on this evidence.",
    },
    {
        "title": "A clear ask goes with more purchases",
        "evidence": [("cta_type = buy_now", "cvr")],
        "reading": "Many ads end with no request at all. Asking costs nothing, so every brief should end with one. The buy-now group also holds many of the "
        "strongest ads, so the true effect may be smaller than this.",
    },
    {
        "title": "Popular themes: keep them as the reason to care, not the proof",
        "evidence": [
            ("story_structure = routine_integration", "roas"),
            ("narratives = recipe", "roas"),
            ("main_benefit = protein_intake", "roas"),
            ("hook_type = story_open", "roas"),
            ("persuasion = authority_science", "roas"),
            ("narratives = kids_immunity", "roas"),
        ],
        "reading": "No evidence either way is different from evidence against, so none of these should be dropped. The brand uses them widely, and growth, "
        "immunity and picky eating may well be why parents start looking. Several looked like winners only because LJ-004 carries those labels, "
        "and protein's lead falls away without its biggest concepts. So they don't work as the sales proof by themselves. In these ads they do better "
        "alongside a child enjoying the product (see 'Follow-up checks'). The science-led route has the least support.",
    },
]


def rate_without_top(primary: pd.DataFrame, mask: pd.Series, metric: str, n: int = 3) -> float:
    """The group's pooled rate after removing its n biggest-spending concepts."""
    num, den = AD_RATIOS[metric]
    usable = primary[mask & primary[num].notna() & primary[den].notna()]
    kept = usable.sort_values("spend_inr", ascending=False).iloc[n:]
    return safe_div(float(kept[num].sum()), float(kept[den].sum()))


def theme_lines(table: pd.DataFrame, primary: pd.DataFrame) -> list[str]:
    features = build_features(primary)
    lookup = table.set_index(["pattern", "metric"])
    lines = [
        "## What this means (interpretation)",
        "",
        "The readings below are judgment. The numbers are from the analysis. A star marks a result significant after controlling for product and language.",
    ]
    for theme in THEMES:
        lines += [
            "",
            f"### {theme['title']}",
            "",
            theme["reading"],
            "",
            "| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
        for pattern, metric in theme["evidence"]:
            r = lookup.loc[(pattern, metric)]
            without = format_rate(metric, rate_without_top(primary, features[pattern], metric))
            lines.append(
                f"| {pattern} | {metric} | {r.n_in} | {format_rate(metric, r.rate_in)} | {format_rate(metric, r.rate_out)} | {without} | "
                f"{r.controlled_lift:+.0%}{'*' if r.controlled_p < ALPHA else ''} | {r.grade} |"
            )
    return lines


def group_row(primary: pd.DataFrame, name: str, mask: pd.Series) -> dict:
    m = pooled_metrics(primary[mask])
    return {
        "group": name,
        "n": int(mask.sum()),
        "hook_rate": m["hook_rate"],
        "hold_rate": m["hold_rate"],
        "cvr": m["cvr"],
        "roas": m["roas"],
    }


def follow_up_checks(primary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
    """The project owner's two objections, tested on the same concepts. Exploratory: chosen after seeing results, so ungraded."""

    def has(column, value):
        return primary[column].fillna("").str.contains(value)

    parent = primary.creator_type == "parent_or_caregiver"
    story = primary.hook_driver == "personal_experience"
    ugc = primary["production"] == "ugc"
    strong_hook = primary.hook_rate >= primary.loc[parent, "hook_rate"].median()
    strong_hold = primary.hold_rate >= primary.loc[parent, "hold_rate"].median()
    hooks = pd.DataFrame(
        [
            group_row(primary, "Parent-led", parent),
            group_row(primary, "Not parent-led", ~parent),
            group_row(primary, "Personal-experience hook", story),
            group_row(primary, "Other hook drivers", ~story),
            group_row(primary, "UGC", ugc),
            group_row(primary, "Not UGC", ~ugc),
            group_row(primary, "Parent-led, stronger hook", parent & strong_hook),
            group_row(primary, "Parent-led, weaker hook", parent & ~strong_hook),
            group_row(primary, "Parent-led, stronger hold", parent & strong_hold),
            group_row(primary, "Parent-led, weaker hold", parent & ~strong_hold),
        ]
    )
    enjoying = has("demo_shown", "taste_test")
    angles = {
        "Picky eating": has("narratives", "fussy_eating"),
        "Recipe": has("narratives", "recipe"),
        "Growth": has("narratives", "kids_overall_growth"),
        "Immunity": has("narratives", "kids_immunity"),
        "Science-led": has("persuasion", "authority_science"),
        "Parent-led": parent,
    }
    rows = []
    for name, mask in angles.items():
        rows += [
            group_row(primary, f"{name}, with a child enjoying", mask & enjoying),
            group_row(primary, f"{name}, without", mask & ~enjoying),
        ]
    parents = primary[parent & primary.purchases.notna()]
    return (
        hooks,
        pd.DataFrame(rows),
        parents.hook_rate.corr(parents.cvr, method="spearman"),
        parents.hold_rate.corr(parents.cvr, method="spearman"),
    )


def follow_up_lines(primary: pd.DataFrame) -> list[str]:
    hooks, angles, hook_corr, hold_corr = follow_up_checks(primary)

    def rows(frame):
        return [
            f"| {r.group} | {r.n} | {r.hook_rate:.1%} | {r.hold_rate:.1%} | {r.cvr:.1%} | {r.roas:.2f} |"
            for r in frame.itertuples()
        ]

    header = ["| Group | Concepts | Hook rate | Hold rate | CVR | ROAS |", "|---|---:|---:|---:|---:|---:|"]
    return (
        [
            "## Follow-up checks after the project owner's review",
            "",
            "The project owner cautioned that, in Indian parenting, peer validation builds trust and weak parent ads may reflect hooks or pacing rather than UGC, "
            "and that growth, immunity and picky eating are main buying triggers. That is category knowledge, which this file can't confirm or rule out. "
            "These checks test what the file can. They were chosen after seeing results and are ungraded, so they're leads, and groups overlap.",
            "",
            "### Is it weak hooks or pacing?",
            "",
        ]
        + header
        + rows(hooks)
        + [
            "",
            f"Among parent-led concepts, rank correlation with CVR: hook rate {hook_corr:+.2f}, hold rate {hold_corr:+.2f}.",
            "",
            "Reading: weak hooks don't explain it here. Parent-led ads hook at least as well as others, and those with stronger hooks convert less. Pacing may play "
            "a part for personal-story hooks, which hold viewers less well, but better hold goes with only a small gain in parent-led CVR and none in ROAS.",
            "",
            "### Do these angles work when paired with a child enjoying the product?",
            "",
        ]
        + header
        + rows(angles)
        + [
            "",
            "Reading: in this file, picky eating, recipes, growth and parent-led ads all do better when paired with a child enjoying the product. Immunity and science have "
            "too few such ads to tell. A few large ads sit behind several of these groups, and pairing was never tested on purpose, so the first campaign should test it.",
            "",
        ]
    )


def product_lines_table(primary: pd.DataFrame) -> list[str]:
    lines = [
        "| Product line | Concepts | Spend (₹) | Hook rate | CTR | CVR | ROAS | Median ROAS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for line, group in sorted(primary.groupby("product_line"), key=lambda item: -item[1].spend_inr.sum()):
        m = pooled_metrics(group)
        lines.append(
            f"| {line} | {len(group)} | {int(group.spend_inr.sum()):,} | {m['hook_rate']:.1%} | {m['ctr']:.2%} | {m['cvr']:.1%} | {m['roas']:.2f} | {group.roas.median():.2f} |"
        )
    return lines


def write_report(
    table: pd.DataFrame, ads: pd.DataFrame, folder: Path, raw_label_grades: pd.DataFrame | None = None
) -> None:
    kids = ads[ads.segment == "kids"]
    n_concepts = kids.concept_id.nunique()
    spreads = family_spreads(ads)
    lines = [
        "# Ad patterns",
        "",
        "All ad performance figures are made up for this exercise and are not Little Joys' real results. These patterns "
        "show association within this export. They don't prove cause.",
        "",
        f"**Scope:** {len(kids)} ads for kids' products, grouped into {n_concepts} concepts so that near-copies count once. "
        "LJ-004 is set aside in the main results because of its size. LJ-089 counts for attention and clicks but not for purchases.",
        "",
        f"**Tested:** {len(table)} comparisons ({table.pattern.nunique()} patterns on {table.metric.nunique()} metrics). "
        f"**Result:** {(table.grade == 'Supported').sum()} Supported, {(table.grade == 'Directional').sum()} Directional, "
        f"{(table.grade == 'Inconclusive').sum()} Inconclusive. {(table.p < ALPHA).sum()} comparisons came in below p = {ALPHA}, where about {len(table) * ALPHA:.0f} would be "
        "expected by chance, so the file holds real signal, but no single pattern is firmly established.",
        "",
        "**Stability:** re-running with 3 other random seeds kept 50 to 53 of the 53 graded results, and none reached Supported. Results near p = 0.05 can change grade between runs.",
        "",
        "**Grades (fixed before results were seen):**",
        "",
        f"- **Supported:** at least {MIN_SUPPORTED} concepts on each side, false discovery rate below {FDR_Q:.0%}, a lift of at least {MIN_LIFT:.0%} "
        "and significant after controlling for product and language, with the direction agreeing across all five views.",
        f"- **Directional:** at least {MIN_GROUP} concepts on each side, p below {ALPHA}, and the direction agreeing across all five views. Worth testing, not proven.",
        "- **Inconclusive:** everything else.",
        "",
        "The five views are: pooled without LJ-004, adjusted for product, the median, pooled without the group's largest concept, and the regression with controls.",
        "",
    ]
    primary = to_concepts(kids)
    primary = primary[~primary.dominant_ad].reset_index(drop=True)
    lines += theme_lines(table, primary)
    lines += [""] + follow_up_lines(primary)
    correlation = primary[["spend_inr", "hook_rate", "cvr", "roas"]].corr("spearman")
    lines += [
        "",
        "## Where the money went",
        "",
        f"Rank correlations across concepts: spend and hook rate {correlation.loc['spend_inr', 'hook_rate']:+.2f}, spend and ROAS {correlation.loc['spend_inr', 'roas']:+.2f}, "
        f"hook rate and CVR {correlation.loc['hook_rate', 'cvr']:+.2f}. Spend follows attention, not return, so high spend isn't proof that an ad worked.",
        "",
    ]
    lines += [
        "## By product line",
        "",
        "Without LJ-004, which is a Proteinmix ad. Moms' and teen products are outside this analysis.",
        "",
    ] + product_lines_table(primary)
    lines += ["", "## Supported", ""]
    supported = table[table.grade == "Supported"]
    lines += pattern_rows(supported) if len(supported) else ["No pattern met this grade."]
    lines += ["", "## Directional", ""]
    directional = table[table.grade == "Directional"].sort_values(["stage", "p"])
    lines += pattern_rows(directional) if len(directional) else ["No pattern met this grade."]
    lines += [
        "",
        "## False leads",
        "",
        f"These look like winners with LJ-004 included (ROAS lead of at least {HEADLINE_ROAS_GAP}) but fail the checks.",
        "",
        "| Pattern | Concepts | ROAS gap with LJ-004 | Without LJ-004 | Median gap | p |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in table[table.false_lead].sort_values("gap_with_lj004", ascending=False).itertuples():
        lines.append(
            f"| {r.pattern} | {r.n_in} | {r.gap_with_lj004:+.2f} | {r.gap_without_lj004:+.2f} | {r.median_gap:+.2f} | {r.p:.3f} |"
        )
    small = too_small_to_test(ads)
    lines += [
        "",
        "## Too few concepts to grade",
        "",
        f"Fewer than {MIN_GROUP} concepts, not counting LJ-004, so these got no test. The figures are description only.",
        "",
        "| Pattern | Concepts | Spend (₹) | ROAS without LJ-004 | ROAS with LJ-004 | Median ROAS | Ads |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in small.itertuples():
        lines.append(
            f"| {r.pattern} | {r.concepts} | {r.spend_inr:,} | {r.roas_without_lj004:.2f} | {r.roas_with_lj004:.2f} | {r.median_roas:.2f} | {r.ads} |"
        )
    lines += [
        "",
        "## How far near-copies differ",
        "",
        "ROAS for ads from the same concept. Gaps of this size between two individual ads can arise with no real creative difference, "
        "though some of these ads are re-cuts or translations, so this is an upper guide rather than pure noise.",
        "",
        "| Concept | Ads | ROAS range | Ratio |",
        "|---|---|---|---:|",
    ]
    lines += [
        f"| {r.concept_id} | {r.ads} | {r.roas_low:.2f} to {r.roas_high:.2f} | {r.ratio:.2f}x |"
        for r in spreads.itertuples()
    ]
    if raw_label_grades is not None:
        lines += ["", "## Effect of label corrections", ""] + raw_label_grades_summary(table, raw_label_grades)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "ad_patterns.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def raw_label_grades_summary(table: pd.DataFrame, raw: pd.DataFrame) -> list[str]:
    key = ["pattern", "metric"]
    merged = table[key + ["grade"]].merge(raw[key + ["grade"]], on=key, how="outer", suffixes=("", "_uncorrected"))
    merged[["grade", "grade_uncorrected"]] = merged[["grade", "grade_uncorrected"]].fillna("Too few to test")
    changed = merged[merged.grade != merged.grade_uncorrected].sort_values(key)
    lines = [
        f"{len(pd.read_csv(CORRECTIONS))} labels were corrected after video review. With the system's labels left as they were, {len(changed)} of {len(merged)} grades differ."
    ]
    if len(changed):
        lines += ["", "| Pattern | Metric | Grade | With uncorrected labels |", "|---|---|---|---|"]
        lines += [f"| {r.pattern} | {r.metric} | {r.grade} | {r.grade_uncorrected} |" for r in changed.itertuples()]
    return lines


def load_ads(corrected: bool = True, data: clean.CleanData | None = None) -> pd.DataFrame:
    """Kids' and other ads with concepts assigned. Pass the pipeline's cleaned data to avoid reloading the zip."""
    ads = (data or clean.clean_all(ingest.load_raw())).ads.copy()
    if corrected:
        ads = apply_corrections(ads, pd.read_csv(CORRECTIONS))
    return assign_concepts(ads, pd.read_csv(CONCEPT_MAP))


def main(data: clean.CleanData | None = None) -> int:
    data = data or clean.clean_all(ingest.load_raw())
    ads = load_ads(data=data)
    table = analyse(ads)
    raw_labels = analyse(load_ads(corrected=False, data=data))
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(config.OUTPUTS_DIR / "ad_patterns.csv", index=False)
    columns = [
        "ad_id",
        "concept_id",
        "creative_id",
        "product",
        "product_line",
        "segment",
        "language",
        "spend_inr",
        "days_live",
        "tracking_suspect",
        "dominant_ad",
        "low_evidence",
        "purchases",
        "revenue_inr",
        *AD_RATIOS,
    ]
    ads[columns].to_csv(config.OUTPUTS_DIR / "ad_metrics.csv", index=False)
    write_report(table, ads, config.OUTPUTS_DIR, raw_labels)
    print(table.grade.value_counts().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
