# Little Joys: which creators next, and what should they say?

A take-home project for Galvor. It uses Little Joys' 100 ads and 20 candidate creators to recommend five creators and what each should say. The goal is an answer the brand's marketing manager can follow and check.

**Start here:** [REPORT.md](REPORT.md) is the answer for the marketing manager. [docs/NOTE.md](docs/NOTE.md) is the one-page note on key choices and next steps. [docs/AI_LOG.md](docs/AI_LOG.md) records how AI was used and the mistakes caught.

**The answer in one line:** `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu` and `foodies_by_neha`, each briefed to show a child visibly enjoying the product and to end with a clear ask. Each runs as a paid test with stop and scale rules. Call `sia_3vedi` and `raja_choudhary04` first: they fit best but posted for a competitor recently.

All ad performance figures in the data are made up for the exercise and are not Little Joys' real results.

## Setup

You need [uv](https://docs.astral.sh/uv/), which also installs the right Python (3.12) for you. If you don't have it:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, from the project folder:

```
uv sync --all-groups                                   # install everything
uv run --group app streamlit run app.py                # open the explorer in your browser
```

The report and the app work straight away: the generated results in `outputs/` are part of the repo, so you don't need the raw data to read or present them.

### Re-running the analysis

The raw data isn't in the repo. Download it once into `data/raw/` (or point the `LJ_DATA_ZIP` environment variable at a copy elsewhere):

```
mkdir -p data/raw
curl -L -o data/raw/little-joys-data.zip https://storage.googleapis.com/galvor-report-assets-cloud-galvor/intern-task-adc0f5e948c2/little-joys-data.zip
uv run python -m lj.pipeline                           # rebuilds everything in outputs/ (about 6 seconds)
uv run pytest -q                                       # about 200 tests (about 10 seconds)
```

The pipeline stops if the zip's checksum doesn't match the file Galvor supplied, or if a blocking data check fails. Without the zip, the tests that need raw data are skipped and the rest still run.

## How it works

```
zip (checksum checked) -> validate -> clean -> ad patterns ----+
                                          \-> creator profiles -+-> gates + score + sensitivity -> briefs (LLM-drafted, validated)
                                                                                                      |
                                                                              outputs/ -> REPORT.md and app.py
```

Python makes every decision: metrics, gates, scores and rankings. The briefs in `data/briefs/briefs.json` were drafted with Claude in the working session from the evidence in `outputs/`. `lj.briefs` refuses to render them unless every post and ad exists and belongs to the right creator, every claim traces to a real ad, and no number has been typed in by hand. No API key is needed.

The competitor rule is a business decision, so the ranking is always reported under three settings: strict (the main answer), challenger brands only, and flag only. To make another setting the main answer, set `COMPETITOR_RULE` in `src/lj/config.py` and re-run the pipeline. The briefs will then fail validation on purpose, because they were written for the main five.

## Outputs

| File | What it shows |
|---|---|
| [REPORT.md](REPORT.md) | The answer, for the marketing manager |
| [app.py](app.py) | A Streamlit explorer for the client: how the score works, the top five with each score split by parameter, a lookup for any creator, and the briefs. Switch the competitor rule or move the weights and the five update. Reads only `outputs/` |
| [outputs/briefs.md](outputs/briefs.md) | The five briefs, with sources, claims and the test plan |
| [outputs/creator_rankings.md](outputs/creator_rankings.md) | Gates, scores and stability for all 20 creators, under all three competitor rules |
| [outputs/creator_rankings.csv](outputs/creator_rankings.csv) | The same as a table |
| [outputs/data_validation.md](outputs/data_validation.md) | Every data check, and the known issues found |
| [outputs/cleaning_log.csv](outputs/cleaning_log.csv) | Every value changed during cleaning, and why |
| [outputs/label_audit.md](outputs/label_audit.md) | How the system's ad labels held up against the videos |
| [outputs/ad_patterns.md](outputs/ad_patterns.md) | Which ad patterns go with attention and sales, and how sure we are |
| [outputs/ad_patterns.csv](outputs/ad_patterns.csv) | All 553 comparisons behind that report |
| [outputs/ad_metrics.csv](outputs/ad_metrics.csv) | Cleaned performance metrics for each ad |
| [outputs/creator_profiles.md](outputs/creator_profiles.md) | Evidence, strengths, weaknesses, risks and data gaps for all 20 creators |
| [outputs/creator_features.csv](outputs/creator_features.csv) | The same creator metrics as a table |
| [outputs/brand_relationships.csv](outputs/brand_relationships.csv) | Reviewed competitor and Little Joys relationships, with source posts |

To repeat the label audit's frame extraction: `uv run --group audit python scripts/audit_prepare.py`. To repeat the near-copy search: `uv run --group audit python scripts/find_concepts.py`.

## Layout

```
REPORT.md        the answer, for the marketing manager
app.py           Streamlit explorer (reads outputs/ only); .streamlit/ holds its settings
src/lj/          ingest, validate, metrics, clean, audit, ads, creators, scoring, briefs, pipeline
tests/           pytest suite
scripts/         one-off audit helpers (frame extraction, near-copy search)
data/briefs/     the five drafted briefs (validated before rendering)
data/overrides/  reviewed product map, near-copy families, label corrections, brand relationships,
                 creator review, claims library, competitor brand types
data/audit/      label audit sample, verdicts, re-checks, frame fingerprints
outputs/         generated reports and tables
docs/            NOTE.md (one-page note), AI_LOG.md (AI use and mistakes caught), PROGRESS.md
CLAUDE.md        instructions and guardrails given to the AI assistant
PROJECT_UNDERSTANDING.md  the original plan, kept as written
```

## Development

```
uv run ruff check . && uv run ruff format .            # lint and format
```

Business logic lives in `src/lj/`; the app only displays what the pipeline wrote. Rules for working on the code are in [CLAUDE.md](CLAUDE.md).
