# Progress

| Milestone | Status |
|---|---|
| M1 Foundation: repo, ingest, validation, cleaning, label audit | Done |
| M2 Ad intelligence | Done, awaiting review |
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

## M2 results (4 Nov 2026)

- **Tests:** 115 pass.
- **Scope:** 91 kids' ads grouped into 78 concepts, so that near-copies count once. 553 comparisons across 111 patterns ([report](../outputs/ad_patterns.md), [all results](../outputs/ad_patterns.csv)).
- **Grades:** 0 Supported, 53 Directional, 500 Inconclusive. The rules were fixed before results and weren't loosened. 57 comparisons fell below p = 0.05 where about 28 would be chance, so there is real signal, but nothing is firmly established.
- **Child-led:** the re-check confirmed 7 of 8 labels. With LJ-004 aside and near-copies grouped, only 4 concepts remain, too few to test.

| What the ads suggest | Evidence |
|---|---|
| Show a child visibly enjoying the product | Strongest sales signal; holds without the biggest concepts and after controls |
| A child in the first 3 seconds wins attention, not purchases | Closest to the top grade |
| End with a clear ask | Holds after controls; may be overstated |
| A parent's personal story alone may sell less well | Caution only; keep the parent's voice and pair it with a child enjoying the product |
| Picky eating, recipes and growth are the reason to care, not the proof | No evidence alone once LJ-004 is set aside; do better paired with a child enjoying the product (ungraded lead) |
| Immunity and science-led messages | Too few paired ads to tell; keep as supporting points, with claims approved |

These are associations in synthetic data, not proof of cause.

**Owner review (4 Nov):** the project owner agreed with most points and cautioned against changing briefs on two: parent stories (peer trust) and growth, immunity and picky eating (main buying triggers). Follow-up checks are in the report. Outcome: no format or angle gets removed, parent voice stays, and the first campaign tests pairing.

## Carried into M3

- Score creative fit on what the ads support: can this creator naturally show a child enjoying the product? Reward that, not recipes or routines alone.
- Don't mark creators down for being parents or making UGC, or for covering growth, immunity or picky eating.
- For M5: every brief uses a parent's voice or the creator's native format, with a category reason to care and a child enjoying the product as the proof. The test plan should compare a parent's story with and without that moment.
- Don't penalise Hinglish. Don't favour a creator for attention alone, or for doctor-style authority.
- `foodies_by_neha` was on the early contender list, but shows no children on camera and recipes aren't a proven sales argument. Let the scoring decide.
- Charts move to M6, when the report and app are built.

- Audit creator post labels against captions and transcripts, especially `child_ages`, `is_sponsored` and `brands_visible`.
- The `0-2` child age band can't separate under-2s from 2-year-olds. Check before applying the product-age gate.

## Open decisions (defaults in use)

See section 10 of [PROJECT_UNDERSTANDING.md](../PROJECT_UNDERSTANDING.md). Decided: briefs will be drafted with Gemini, and the key goes in a local `.env`. All work stays on `main`. The project owner spot-checked 6 audit verdicts on 4 Nov and agreed with all of them.
