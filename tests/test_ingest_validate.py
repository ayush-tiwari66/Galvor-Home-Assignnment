import json
import zipfile
from dataclasses import replace

import pytest

from lj import config, ingest, validate


def by_name(checks, name):
    return next(c for c in checks if c.name == name)


def test_real_data_has_no_blocking_failures(raw):
    assert validate.failed_errors(validate.run_all(raw)) == []


def test_real_data_shape(raw):
    assert (len(raw.ads), len(raw.creators), len(raw.posts), len(raw.audience)) == (100, 20, 392, 3)


def test_known_issues_are_reported_not_hidden(raw):
    checks = validate.run_all(raw)
    assert not by_name(checks, "each ad is a distinct video").passed
    assert not by_name(checks, "some ads still live (README: blank stopped_date)").passed
    assert not by_name(checks, "audience_read has comment evidence").passed


def test_missing_zip_gives_a_clear_error(tmp_path):
    with pytest.raises(ingest.DataFileError, match="not found"):
        ingest.load_raw(tmp_path / "nope.zip")


def test_altered_zip_is_rejected(tmp_path):
    path = tmp_path / "little-joys-data.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ads.csv", "ad_id\nLJ-001\n")
    with pytest.raises(ingest.DataFileError, match="checksum"):
        ingest.load_raw(path)


def test_incomplete_zip_is_rejected(tmp_path):
    path = tmp_path / "little-joys-data.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ads.csv", "ad_id\nLJ-001\n")
    with pytest.raises(ingest.DataFileError, match="missing"):
        ingest.load_raw(path, expected_sha256=None)


def test_missing_column_blocks(raw):
    broken = replace(raw, ads=raw.ads.drop(columns=["spend_inr"]))
    failed = validate.failed_errors(validate.check_structure(broken))
    assert any(c.name == "required columns present" and c.dataset == "ads" for c in failed)


def test_duplicate_key_blocks(raw):
    ads = raw.ads.copy()
    ads.loc[1, "ad_id"] = ads.loc[0, "ad_id"]
    failed = validate.failed_errors(validate.check_structure(replace(raw, ads=ads)))
    assert any(c.name == "ad_id unique" for c in failed)


def test_broken_funnel_blocks(raw):
    ads = raw.ads.copy()
    ads.loc[0, "purchases"] = ads.loc[0, "add_to_carts"] + 1
    failed = validate.failed_errors(validate.check_ads(ads))
    assert any(c.name == "purchases <= add_to_carts" for c in failed)


def test_revenue_without_purchases_blocks(raw):
    ads = raw.ads.copy()
    zero = ads.index[ads.purchases == 0][0]
    ads.loc[zero, "revenue_inr"] = 500
    failed = validate.failed_errors(validate.check_ads(ads))
    assert any(c.name == "revenue is zero exactly when purchases are zero" for c in failed)


def test_broken_join_blocks(raw):
    posts = raw.posts.copy()
    posts.loc[0, "handle"] = "not_a_creator"
    failed = validate.failed_errors(validate.check_creators_and_posts(replace(raw, posts=posts)))
    assert any(c.name == "every post belongs to a known creator" for c in failed)


def test_report_writes_valid_json_and_markdown(raw, tmp_path):
    checks = validate.run_all(raw)
    validate.write_report(checks, tmp_path)
    saved = json.loads((tmp_path / "data_validation.json").read_text(encoding="utf-8"))
    assert len(saved) == len(checks) and all(isinstance(c["passed"], bool) for c in saved)
    assert "Blocking failures: 0" in (tmp_path / "data_validation.md").read_text(encoding="utf-8")


def test_checksum_constant_is_lowercase_hex():
    assert config.EXPECTED_ZIP_SHA256.lower() == config.EXPECTED_ZIP_SHA256 and len(config.EXPECTED_ZIP_SHA256) == 64
