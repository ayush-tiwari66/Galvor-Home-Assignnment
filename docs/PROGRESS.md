# Progress

| Milestone | Status |
|---|---|
| M1 Foundation: repo, ingest, validation, cleaning, label audit | Done, awaiting review |
| M2 Ad intelligence | Not started |
| M3 Creator features | Not started |
| M4 Gates, scoring, sensitivity | Not started |
| M5 Briefs and validator | Not started |
| M6 Report and app | Not started |
| M7 Review and packaging | Not started |

## M1 results (4 Nov 2026)

- **Tests:** 64 pass.
- **Validation:** 40 of 55 checks pass, none blocking. The other 15 are known issues handled downstream ([report](../outputs/data_validation.md)).
- **Cleaning:** 63 logged changes ([log](../outputs/cleaning_log.csv)). LJ-089 is the only ad treated as a tracking failure and LJ-004 the only dominant ad, both found by rules, not picked by hand.
- **Label audit:** 20 videos ([results](../outputs/label_audit.md)). The child and first-frame labels held up. `ad_format` and `product_form` were the weakest.

| Blended ROAS | Value |
|---|---:|
| Export as supplied | 1.50 |
| LJ-089 treated as missing | 1.59 |
| LJ-089 and LJ-004 both left out | 1.23 |

## Carried into M2

- **Re-read all 8 ads labelled `child_led` against the videos.** One of the 4 audited was wrong (LJ-060 is a silent film), and child-led is one of the most promising sales signals.
- Analyse by `creative_id`, so repeated videos aren't counted as independent.
- Keep moms' and teen ads out of the kids' patterns, and show product mix beside each finding.
- 32 ads, with 9.7% of spend, have fewer than 30 purchases. Don't read them alone.

## Carried into M3

- Audit creator post labels against captions and transcripts, especially `child_ages`, `is_sponsored` and `brands_visible`.
- The `0-2` child age band can't separate under-2s from 2-year-olds. Check before applying the product-age gate.

## Open decisions (defaults in use)

See section 10 of [PROJECT_UNDERSTANDING.md](../PROJECT_UNDERSTANDING.md). Decided: briefs will be drafted with Gemini, and the key goes in a local `.env`. Still needed: a human spot-check of the AI-recorded label audit.
