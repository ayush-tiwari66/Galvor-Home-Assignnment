# Little Joys: which creators next, and what should they say?

A take-home project for Galvor. It uses Little Joys' 100 ads and 20 candidate creators to recommend five creators and what each should say. The goal is an answer the brand's marketing manager can follow and check.

**Status:** in progress. Data validation, cleaning, the label audit and the ad analysis are done; see [docs/PROGRESS.md](docs/PROGRESS.md). The recommendation doesn't exist yet.

All ad performance figures in the data are made up for the exercise and are not Little Joys' real results.

## Setup

Requires [uv](https://docs.astral.sh/uv/). The raw data isn't in this repo.

1. Download `little-joys-data.zip` from the assignment and save it as `data/raw/little-joys-data.zip`, or point the `LJ_DATA_ZIP` environment variable at it.
2. Install and run:

```
uv sync --all-groups
uv run pytest -q
uv run python -m lj.pipeline
```

The pipeline stops if the zip's checksum doesn't match or a blocking data check fails. Tests that need the data skip when the zip is missing.

## Outputs so far

| File | What it shows |
|---|---|
| [outputs/data_validation.md](outputs/data_validation.md) | Every data check, and the known issues found |
| [outputs/cleaning_log.csv](outputs/cleaning_log.csv) | Every value changed during cleaning, and why |
| [outputs/label_audit.md](outputs/label_audit.md) | How the system's ad labels held up against the videos |
| [outputs/ad_patterns.md](outputs/ad_patterns.md) | Which ad patterns go with attention and sales, and how sure we are |
| [outputs/ad_patterns.csv](outputs/ad_patterns.csv) | All 553 comparisons behind that report |
| [outputs/ad_metrics.csv](outputs/ad_metrics.csv) | Cleaned performance metrics for each ad |

To repeat the label audit's frame extraction: `uv run --group audit python scripts/audit_prepare.py`. To repeat the near-copy search: `uv run --group audit python scripts/find_concepts.py`.

## Layout

```
src/lj/          ingest, validate, metrics, clean, audit, ads, pipeline
tests/           pytest suite
data/overrides/  reviewed product map, near-copy families, label corrections
data/audit/      label audit sample, verdicts, re-checks, frame fingerprints
outputs/         generated reports
docs/            progress and AI usage log
```
