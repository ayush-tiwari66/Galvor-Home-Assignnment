"""Little Joys creator explorer. Run with: uv run --group app streamlit run app.py

Reads only outputs/ (written by `uv run python -m lj.pipeline`). It holds no business logic: gates, eligibility and
criterion values come from the pipeline, and scores and points use the same functions in lj.scoring.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lj import config, scoring

OUT = config.OUTPUTS_DIR
RULES = list(config.COMPETITOR_RULES)
CRITERIA = scoring.CRITERIA
NAMES = scoring.CRITERION_WORDS

# Keep only the light/dark/system theme choice in the top-right menu. Deploy, rerun and clear cache are
# removed by `toolbarMode = "viewer"` in .streamlit/config.toml; this hides print, screencast, about and the version line.
MENU_CSS = """<style>
[data-testid^="stMainMenuItem-"]:not([data-testid^="stMainMenuItem-theme-"]),
[data-testid="stMainMenuDivider"],
[data-testid="stMainMenuList"] ~ * { display: none !important; }
</style>"""

# Drawn with currentColor so lines and words follow the light or dark theme.
IDEA_SVG = """
<svg viewBox="0 0 760 200" role="img" aria-label="Your ads show what sells; the posts show who can deliver it"
     style="width:100%;max-width:820px;height:auto;color:inherit;font-family:inherit" font-size="13">
  <defs><marker id="idea-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"
    orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor" fill-opacity="0.6"/></marker></defs>
  <g fill="none" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.25">
    <path d="M280 52H306V98H330" marker-end="url(#idea-arrow)"/>
    <path d="M280 148H306V122H330" marker-end="url(#idea-arrow)"/>
    <path d="M532 110H550" marker-end="url(#idea-arrow)"/>
  </g>
  <g stroke="currentColor" stroke-opacity="0.45" stroke-width="1.25" fill="none">
    <rect x="24" y="24" width="256" height="56" rx="8"/>
    <rect x="24" y="120" width="256" height="56" rx="8"/>
    <rect x="332" y="82" width="200" height="56" rx="8"/>
  </g>
  <rect x="552" y="82" width="184" height="56" rx="8" fill="#4C8BF5" fill-opacity="0.15" stroke="#4C8BF5" stroke-width="2"/>
  <g fill="currentColor" text-anchor="middle">
    <text x="152" y="48" font-weight="600">100 Little Joys ads</text>
    <text x="152" y="66" font-size="11.5" fill-opacity="0.7">what kind of message sells</text>
    <text x="152" y="144" font-weight="600">392 creator posts</text>
    <text x="152" y="162" font-size="11.5" fill-opacity="0.7">who can deliver it naturally</text>
    <text x="432" y="106" font-weight="600">Where they meet</text>
    <text x="432" y="124" font-size="11.5" fill-opacity="0.7">score and five briefs</text>
    <text x="644" y="106" font-weight="600">Paid test per creator</text>
    <text x="644" y="124" font-size="11.5" fill-opacity="0.7">stop or scale on results</text>
  </g>
</svg>"""

st.set_page_config(page_title="Little Joys creator explorer", layout="wide")
st.html(MENU_CSS)


@st.cache_data
def load_rankings() -> pd.DataFrame:
    return pd.read_csv(OUT / "creator_rankings.csv")


@st.cache_data
def read(path: str) -> str:
    return (config.ROOT / path).read_text(encoding="utf-8")


if not (OUT / "creator_rankings.csv").exists():
    st.error("No outputs found. Run `uv run python -m lj.pipeline` first.")
    st.stop()

table = load_rankings()
recommended = set(table.loc[table[f"rank_{config.COMPETITOR_RULE}"] <= 5, "handle"])

# ---------------------------------------------------------------- settings (sidebar)
with st.sidebar:
    st.header("Your settings")
    rule = st.radio(
        "Creators who did paid work for a kids' nutrition rival in the last 90 days",
        RULES,
        index=RULES.index(config.COMPETITOR_RULE),
        format_func=lambda r: scoring.RULE_WORDS[r],
    )
    st.markdown("**How much each thing matters**")
    raw = {
        c: st.slider(
            NAMES[c], 0, 100, int(round(config.SCORE_WEIGHTS[c] * 100)), step=5, key=c, help=scoring.CRITERION_PLAIN[c]
        )
        for c in CRITERIA
    }
    st.caption("Weights are rescaled to add up to 100%. The starting values give the recommended five.")

total = sum(raw.values())
if total == 0:
    st.warning("Give at least one thing some weight.")
    st.stop()
weights = {c: v / total for c, v in raw.items()}
earned = scoring.points(table, weights)
scores = scoring.score(table, weights)
mask = table[f"eligible_{rule}"].astype(bool)
top = scoring.top_n(scores, mask)
chosen = set(table.handle[top])

st.title("Which creators should Little Joys work with next?")
st.caption("Each creator is scored on how well they fit what sells in your ads. Each pick then runs as a paid test.")

how_tab, answer_tab, briefs_tab = st.tabs(["How it works", "The answer", "Briefs"])

# ---------------------------------------------------------------- how it works
with how_tab:
    st.subheader("Your ads show what sells. The posts show who can deliver it.")
    st.markdown(IDEA_SVG, unsafe_allow_html=True)

    st.subheader("How a creator gets picked")
    st.markdown(
        "1. **Basic checks.** Children on camera are old enough for the product, the feed is about family or food, "
        "the audience isn't mostly men where we know it, and the creator posted in the last 90 days.\n"
        "2. **Competitor rule.** Chosen in the sidebar.\n"
        "3. **Score out of 100** from the five parameters below. The top five eligible creators are picked.\n"
        "4. **Paid test.** About ₹23,000 per creator, with clear rules for when to stop or scale."
    )

    st.subheader("The five parameters")
    params = pd.DataFrame(
        {
            "Parameter": [NAMES[c] for c in CRITERIA],
            "Weight": [f"{config.SCORE_WEIGHTS[c]:.0%}" for c in CRITERIA],
            "The question it answers": [scoring.CRITERION_PLAIN[c] for c in CRITERIA],
            "How it's measured": [scoring.CRITERION_MEASURE[c] for c in CRITERIA],
        }
    )
    st.table(params.set_index("Parameter"))
    st.markdown(
        "**Why the child moment weighs most.** In your ads, a child visibly enjoying the product brought back "
        "₹1.78 per ₹1 spent, against ₹0.93 for the rest. No other pattern came close."
    )

    st.subheader("Key terms")
    st.markdown(
        "- **Rival:** another kids' nutrition brand (Gritzo, Troovy, Good Monk, Manna, Bournvita, Complan).\n"
        "- **Organic plays:** views on a creator's own unpaid posts.\n"
        "- **Median:** the middle value, so one viral post can't distort it.\n"
        "- **ROAS:** revenue divided by ad spend. ₹1.78 per ₹1 means each rupee brought back ₹1.78.\n"
        "- **Score:** points out of 100 across the five parameters."
    )

# ---------------------------------------------------------------- the answer
with answer_tab:
    a, b, c, d = st.columns(4)
    a.metric("Creators reviewed", len(table))
    b.metric("Pass the basic checks", int(table.passes_gates.sum()))
    c.metric("Eligible under this rule", int(mask.sum()))
    d.metric("Picked", len(top))

    if chosen == recommended:
        st.success("These settings give the recommended five.")
    else:
        st.info(
            f"Differs from the recommendation. In: {', '.join(sorted(chosen - recommended))}. "
            f"Out: {', '.join(sorted(recommended - chosen))}."
        )

    st.subheader("The top five, and where their points come from")
    five = pd.DataFrame(
        {
            "Rank": range(1, len(top) + 1),
            "Creator": table.handle[top].values,
            "Score (out of 100)": scores[top].round(0).astype(int).values,
            "Recent rival work": table.competitor_detail[top].fillna("").replace("", "None").values,
        }
    )
    st.dataframe(five, hide_index=True, width="stretch")

    long = earned.loc[top].assign(Creator=table.handle[top]).melt("Creator", var_name="key", value_name="Points")
    long["Parameter"] = long.key.map(NAMES)
    long["order"] = long.key.map(CRITERIA.index)
    bars = (
        alt.Chart(long)
        .mark_bar()
        .encode(
            y=alt.Y(
                "Creator:N", sort=list(table.handle[top]), title=None, axis=alt.Axis(labelLimit=260, labelOverlap=False)
            ),
            x=alt.X("Points:Q", stack="zero", title="Points out of 100", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "Parameter:N",
                sort=[NAMES[c] for c in CRITERIA],
                legend=alt.Legend(orient="bottom", columns=2, title=None, labelLimit=360),
            ),
            order=alt.Order("order:Q"),
            tooltip=["Creator", "Parameter", alt.Tooltip("Points:Q", format=".1f")],
        )
        .properties(height=alt.Step(40))
    )
    st.altair_chart(bars, width="stretch")
    st.caption("Each bar shows where a creator's points come from.")

    st.subheader("Look at one creator")
    order = list(table.handle[top]) + sorted(set(table.handle) - chosen)
    who = st.selectbox("Creator", order)
    i = table.index[table.handle == who][0]
    r = table.loc[i]
    if who in chosen:
        st.success(f"Picked at #{top.index(i) + 1} with {scores[i]:.0f} points.")
    elif not r.passes_gates:
        st.error(f"Not picked: fails the basic checks ({r.gate_reason}).")
    elif not mask[i]:
        st.warning(
            f"Not picked: ruled out by the competitor rule ({r.competitor_detail}). Scores {scores[i]:.0f} points."
        )
    else:
        rank = int((scores[mask] > scores[i]).sum()) + 1
        st.info(f"Not picked: ranked #{rank} with {scores[i]:.0f} points.")
    detail = pd.DataFrame(
        {
            "Parameter": [NAMES[c] for c in CRITERIA],
            "The question": [scoring.CRITERION_PLAIN[c] for c in CRITERIA],
            "Points": [f"{earned.at[i, c]:.1f} of {weights[c] * 100:.0f}" for c in CRITERIA],
        }
    )
    st.dataframe(detail, hide_index=True, width="stretch")
    st.caption(f"Typical plays used for reach: {r.reach_plays:,.0f} per video.")

    with st.expander("All 20 creators"):
        everyone = pd.DataFrame(
            {
                "Creator": table.handle,
                "Basic checks": table.passes_gates.map({True: "Pass", False: "Fail"}),
                "Why it failed": table.gate_reason.fillna(""),
                "Recent rival work": table.competitor_detail.fillna(""),
                "Eligible under this rule": mask.map({True: "Yes", False: "No"}),
                "Score (out of 100)": scores.round(0).astype(int),
            }
        ).sort_values(["Eligible under this rule", "Score (out of 100)"], ascending=[False, False])
        st.dataframe(everyone, hide_index=True, width="stretch", height=560)

# ---------------------------------------------------------------- briefs
with briefs_tab:
    sections = read("outputs/briefs.md").split("\n## ")[1:]
    creator_sections = [s for s in sections if s.startswith("`")]
    test_section = next((s for s in sections if s.startswith("How to test")), "")
    st.markdown(
        "One brief per creator: why them, what to say, the scene order, the claims they may use, and what to check before signing."
    )
    pick = st.selectbox("Brief for", creator_sections, format_func=lambda s: s.split("\n", 1)[0].replace("`", ""))
    st.markdown("### " + pick)
    if test_section:
        # The export disclaimer is for the reviewers' report, not the client view.
        plan = "\n".join(line for line in test_section.splitlines() if "made up for this exercise" not in line)
        st.markdown("### " + plan)
