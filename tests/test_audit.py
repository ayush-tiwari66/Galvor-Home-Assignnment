import pandas as pd
import pytest

from lj import audit, config


@pytest.fixture(scope="module")
def records():
    return audit.load_audit()


def test_every_sampled_ad_is_audited_on_every_label(records):
    sample = pd.read_csv(config.AUDIT_DIR / "audit_sample.csv")
    assert set(records.ad_id) == set(sample.ad_id) and len(sample) == 20
    assert (records.groupby("ad_id").label.nunique() == len(audit.USE_DECISION)).all()


def test_verdicts_are_valid_and_disagreements_are_explained(records):
    assert set(records.verdict) <= {"agree", "disagree", "cannot_tell"}
    assert (records.loc[records.verdict != "agree", "note"] != "").all()


def test_system_values_were_copied_correctly(records, raw):
    """Guards against typos in the hand-recorded audit: each value must match the source file."""
    ads = raw.ads.set_index("ad_id")
    system = records[records.label != "product"]
    for row in system.itertuples():
        actual = ads.loc[row.ad_id, row.label]
        assert ("" if pd.isna(actual) else actual) == row.system_value, (row.ad_id, row.label)


def test_product_audit_matches_the_map_except_corrected_rows(records, data):
    products = data.ads.set_index("ad_id")["product"]
    rows = records[(records.label == "product") & (records.verdict != "disagree")]
    for row in rows.itertuples():
        assert products[row.ad_id] == row.system_value, row.ad_id


def test_spot_check_matches_the_recorded_verdicts(records):
    recorded = records.set_index(["ad_id", "label"]).verdict
    for key, verdict in audit.HUMAN_SPOT_CHECK.items():
        assert recorded[key] == verdict, key


def test_report_states_the_limits_of_the_spot_check(records, tmp_path):
    audit.write_report(records, tmp_path)
    report = (tmp_path / "label_audit.md").read_text(encoding="utf-8")
    assert "reviewed 6 of the verdicts" in report
    assert "not an independent error rate" in report


def test_correction_from_audit_is_applied(data):
    assert data.ads.set_index("ad_id")["product"]["LJ-038"] == "nutrimix_2plus"


def test_wilson_interval_behaves_at_the_edges():
    assert audit.wilson_interval(20, 20)[1] == pytest.approx(1.0)
    low, high = audit.wilson_interval(20, 20)
    assert 0.8 < low < 1.0
    low, high = audit.wilson_interval(0, 10)
    assert low == pytest.approx(0.0, abs=1e-9) and high < 0.35


def test_summary_excludes_cannot_tell_from_agreement():
    frame = pd.DataFrame(
        {
            "ad_id": ["a", "b", "c"],
            "label": ["setting"] * 3,
            "system_value": ["x"] * 3,
            "verdict": ["agree", "disagree", "cannot_tell"],
            "note": ["", "n", "n"],
        }
    )
    row = audit.summarise(frame).iloc[0]
    assert row.agreement == pytest.approx(0.5) and row.cannot_tell == 1
