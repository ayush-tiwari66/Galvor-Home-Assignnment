# Little Joys creator selection

Answers one question for Little Joys' marketing manager: which 5 of 20 creators to work with next, and what each should say. The plan is in [PROJECT_UNDERSTANDING.md](PROJECT_UNDERSTANDING.md), and status is in [docs/PROGRESS.md](docs/PROGRESS.md).

## Commands
- `uv sync --all-groups`: install
- `uv run pytest -q`: run tests
- `uv run python -m lj.pipeline`: validate and clean the data, analyse ads, profile creators, write reports to `outputs/`
- `uv run python -m lj.audit`: rebuild the label audit summary

Keep all work on the `main` branch.

## Rules
- **Work in milestones.** Finish one, show real outputs and test results, then stop for the user's review. The user makes the final decisions.
- **Python decides, the LLM drafts.** Metrics, scores and rankings are deterministic code. An LLM only drafts briefs from checked evidence, and a validator must pass the result.
- **Never invent anything.** No made-up metrics, demographics, product benefits or citations. Missing data stays missing (NaN), never 0.
- **Keep three things apart:** observed facts, interpretations, recommendations.
- **Ad performance is synthetic.** Never describe it as Little Joys' real results.
- **`claims_made` is what ads said, not what's approved.** Every product claim in a brief needs brand approval. Health, immunity, growth and comparison claims get extra scrutiny.
- **Correlation isn't causation,** and no recommendation guarantees results.

## Data handling
- Read from `little-joys-data.zip`; the checksum is enforced. Never commit raw data or `data/processed/` (see `.gitignore`).
- Don't use these columns: post `language` (83% wrong in our check), `audience_read` (no evidence behind it), `product_form` (use the product map), `people_on_screen` (contradictory), `audience_signal` as a stand-in for demographics.
- LJ-089's purchases and revenue are treated as missing. LJ-004 is always reported with and without.
- Group metrics come from `metrics.pooled_metrics`, so rows with missing values drop out of both sides of a ratio.
- Near-copies of an ad count once: analyse by `concept_id` (`data/overrides/ad_concepts.csv`), not by ad.
- Thresholds live in `src/lj/config.py`. Row-level changes go in the cleaning log.

## Code
- Business logic goes in `src/lj/`. The app only reads `outputs/` and holds no business logic.
- Write a failing test for each bug before fixing it. Never weaken a test to make it pass.
- Log AI mistakes and key decisions in [docs/AI_LOG.md](docs/AI_LOG.md); it's part of the submission.
- Use they/them for creators; don't infer pronouns from names.
