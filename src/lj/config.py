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


def zip_path() -> Path:
    """Location of the data zip. Override with the LJ_DATA_ZIP environment variable."""
    return Path(os.environ.get("LJ_DATA_ZIP", DEFAULT_ZIP))
