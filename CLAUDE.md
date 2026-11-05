# Little Joys creator selection

Answers one question for Little Joys' marketing manager: which 5 of 20 creators to work with next, and what each should say. The answer is [REPORT.md](REPORT.md). The original plan is in [PROJECT_UNDERSTANDING.md](PROJECT_UNDERSTANDING.md), and status is in [docs/PROGRESS.md](docs/PROGRESS.md).

## Commands
- `uv sync --all-groups`: install
- `uv run pytest -q`: run tests
- `uv run python -m lj.pipeline`: validate and clean the data, analyse ads, profile, score and rank creators, validate and render the briefs, write reports to `outputs/`
- `uv run python -m lj.audit`: rebuild the label audit summary
- `uv run --group app streamlit run app.py`: open the explorer (reads `outputs/` only)
- `uv run ruff check . && uv run ruff format .`: lint and format (config in `pyproject.toml`)

Keep all work on the `main` branch.

## Rules
- **Work in milestones.** Finish one, show real outputs and test results, then stop for the user's review. The user makes the final decisions.
- **Python decides, the LLM drafts.** Metrics, scores and rankings are deterministic code. An LLM only drafts briefs from checked evidence, and a validator must pass the result.
- **Never invent anything.** No made-up metrics, demographics, product benefits or citations. Missing data stays missing (NaN), never 0.
- **Keep three things apart:** observed facts, interpretations, recommendations.
- **Ad performance is synthetic.** Never describe it as Little Joys' real results.
- **`claims_made` is what ads said, not what's approved.** Every product claim in a brief needs brand approval. Health, immunity, growth and comparison claims get extra scrutiny.
- **Correlation isn't causation,** and no recommendation guarantees results.
- **The score measures fit, not sales.** No ad names its creator, so never describe a score as a sales forecast.
- **The competitor rule is the brand's decision.** Always report all three settings (`COMPETITOR_RULES` in `config.py`); `COMPETITOR_RULE` only picks the main answer. Brand types in `data/overrides/competitor_brands.csv` are general knowledge, not data, and must stay marked that way.

## Data handling
- Read from `little-joys-data.zip`; the checksum is enforced. Never commit raw data or `data/processed/` (see `.gitignore`).
- Don't use these columns: post `language` (83% wrong in our check), `audience_read` (no evidence behind it), `product_form` (use the product map), `people_on_screen` (contradictory), `audience_signal` as a stand-in for demographics.
- LJ-089's purchases and revenue are treated as missing. LJ-004 is always reported with and without.
- Group metrics come from `metrics.pooled_metrics`, so rows with missing values drop out of both sides of a ratio.
- Near-copies of an ad count once: analyse by `concept_id` (`data/overrides/ad_concepts.csv`), not by ad.
- Thresholds and score weights live in `src/lj/config.py`. Row-level changes go in the cleaning log.
- Don't score likes or comments: likes are hidden on some accounts and comments are inflated or switched off. Use median organic plays.
- Pipeline steps take the cleaned data (`main(data)`), so the zip is read and checked once per run.
- Re-running on another machine can change the last digits of `outputs/ad_patterns.*`. Grades don't change; don't commit that drift on its own.

## Briefs
- Briefs live in `data/briefs/briefs.json`, drafted by an LLM from evidence in `outputs/`. `lj.briefs` must pass every brief before it is rendered.
- Cite posts by Instagram shortcode and ads by ID; the validator checks they exist and belong to the right creator.
- Never type a number into brief text. Use a `{placeholder}` filled from `creator_features.csv`.
- Claims come only from `data/overrides/claims_library.csv`, and each must match an ad's `claims_made`.

## Code
- Business logic goes in `src/lj/`. The app only reads `outputs/` and reuses `lj.scoring` (`score`, `points`, the criterion wording), so it can never disagree with the report.
- Write a failing test for each bug before fixing it. Never weaken a test to make it pass.
- Log AI mistakes and key decisions in [docs/AI_LOG.md](docs/AI_LOG.md); it's part of the submission.
- Use they/them for creators; don't infer pronouns from names.
