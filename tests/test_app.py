import pandas as pd
import pytest

from lj import config, scoring

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(config.ROOT / "app.py")
pytestmark = pytest.mark.skipif(
    not (config.OUTPUTS_DIR / "creator_rankings.csv").exists(), reason="needs pipeline outputs"
)


def recommended() -> list[str]:
    t = pd.read_csv(config.OUTPUTS_DIR / "creator_rankings.csv")
    col = f"rank_{config.COMPETITOR_RULE}"
    return t[t[col] <= 5].sort_values(col).handle.tolist()


def run_app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, at.exception
    return at


def top_five(at: AppTest) -> list[str]:
    frame = next(d.value for d in at.dataframe if "Rank" in d.value.columns)
    return frame["Creator"].tolist()


def test_defaults_reproduce_the_recommended_five():
    at = run_app()
    assert top_five(at) == recommended()
    assert any("recommended five" in s.value for s in at.success)


def test_app_shows_no_confidence():
    at = run_app()
    for d in at.dataframe:
        assert not any("onfidence" in c for c in d.value.columns)


def test_switching_competitor_rule_changes_the_five():
    at = run_app()
    at.radio[0].set_value("flag").run()
    assert not at.exception
    five = top_five(at)
    assert five != recommended()
    assert "sia_3vedi" in five
    assert any("Differs" in s.value for s in at.info)


def test_zero_weights_warn_instead_of_crashing():
    at = run_app()
    for s in at.slider:
        s.set_value(0)
    at.run()
    assert not at.exception
    assert any("at least one" in w.value for w in at.warning)


def test_creator_lookup_explains_an_excluded_creator():
    at = run_app()
    at.selectbox[0].set_value("sia_3vedi").run()
    assert any("competitor rule" in w.value for w in at.warning)
    at.selectbox[0].set_value("thatkushalmistry").run()
    assert any("basic checks" in e.value for e in at.error)


def test_how_it_works_and_briefs_render():
    at = run_app()
    text = " ".join(m.value for m in at.markdown)
    assert "Why the child moment weighs most" in text
    assert "Why this creator" in text
    assert "Paid test budget" in text
    assert [t.label for t in at.tabs] == ["How it works", "The answer", "Briefs"]


def test_client_view_has_no_disclaimers_or_data_proofs():
    at = run_app()
    shown = " ".join(e.value for e in [*at.markdown, *at.caption, *at.subheader, *at.title]).lower()
    for phrase in ("made up", "synthetic", "right data", "checksum", "confidence", "validator", "llm"):
        assert phrase not in shown, phrase


def test_points_add_up_to_the_score():
    t = pd.read_csv(config.OUTPUTS_DIR / "creator_rankings.csv")
    pts = scoring.points(t, config.SCORE_WEIGHTS)
    assert pts.sum(axis=1).round(1).tolist() == t.score.tolist()
