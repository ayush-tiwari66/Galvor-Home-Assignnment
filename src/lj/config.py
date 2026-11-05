"""Paths, reference dates and rule thresholds. Every threshold used in cleaning lives here."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ZIP = ROOT / "data" / "raw" / "little-joys-data.zip"
PRODUCT_MAP = ROOT / "data" / "overrides" / "ad_products.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUTS_DIR = ROOT / "outputs"
AUDIT_DIR = ROOT / "data" / "audit"

# SHA-256 of the little-joys-data.zip supplied by Galvor. Results are only reproducible against this file.
EXPECTED_ZIP_SHA256 = "03b29e7c7a09f28bac17f96c5d354ee8083039f7e519fdb26eace37272086217"

ADS_AS_OF = pd.Timestamp("2026-10-26")  # README: ad performance runs up to this date
POSTS_AS_OF = pd.Timestamp("2026-10-27")  # newest post in creator_posts.csv
RECENT_WINDOW_DAYS = 365

# A zero-purchase ad is treated as a tracking failure when zero is this unlikely given its add-to-carts.
TRACKING_FAILURE_MAX_PROB = 1e-6
# An ad with at least this share of all purchases is reported separately, never pooled silently.
DOMINANT_AD_PURCHASE_SHARE = 0.20
# Below this many purchases an ad's conversion and ROAS are too noisy to read alone (relative SE of about 18%).
LOW_EVIDENCE_PURCHASES = 30

# README: hidden like counts show as 0 or a very low number. Exactly 3 recurs, on posts with up to 1.35M plays.
HIDDEN_LIKES_MAX = 5
# A zero reshare or comment count at or above this many plays is treated as unavailable, not as zero.
IMPLAUSIBLE_ZERO_MIN_PLAYS = 50_000


# ---------------------------------------------------------------- creator gates and scoring (M4)
# Main answer: creators with direct kids' nutrition competitor work in the last 90 days are left out, because we
# can't see their contracts and their audience has just heard them recommend a rival. Every rule is always reported:
#   exclude          any paid post for a direct kids' nutrition rival in the last 90 days rules a creator out
#   challengers_only only challenger brands rule a creator out; long-established mass brands are flagged
#   flag             nobody is ruled out; competitor work is shown as a risk
COMPETITOR_RULES = ("exclude", "challengers_only", "flag")
COMPETITOR_RULE = "exclude"
COMPETITOR_WINDOW_DAYS = 90
# Mixed-age feeds pass the age gate when at least this share of child posts show a child aged 3 to 12.
MIXED_AGE_MIN_3_TO_12 = 0.5
# A feed with no children on camera still reaches buyers if at least this share of posts is about food.
FOOD_FEED_MIN_SHARE = 0.3
# Measured audience: above this share of men, the viewers aren't evidence of parents who buy.
MAX_MEN_SHARE = 50.0
# Fewer organic videos than this and the organic median is one or two posts, so the all-video median is used.
MIN_ORGANIC_VIDEOS = 5
# Reach score runs from 10k plays (0) to about 3.2M plays (1) on a log scale.
REACH_LOG10_FLOOR, REACH_LOG10_SPAN = 4.0, 2.5
# Feeds with more sponsored posts than this lose readiness points, down to zero at 100% sponsored.
SPONSORED_COMFORT_SHARE = 0.35
SCORE_WEIGHTS = {"creative_fit": 0.30, "product_fit": 0.25, "reach": 0.20, "paid_readiness": 0.15, "authenticity": 0.10}
SENSITIVITY_DRAWS = 5000
SENSITIVITY_SEED = 0


def zip_path() -> Path:
    """Location of the data zip. Override with the LJ_DATA_ZIP environment variable."""
    return Path(os.environ.get("LJ_DATA_ZIP", DEFAULT_ZIP))
