# Data validation report

**40 of 55 checks passed.** Blocking failures: 0. Known issues handled downstream: 15.

All ad performance figures are made up for this exercise and are not Little Joys' real results.

## Known issues

| Dataset | Check | Result | Example rows |
|---|---|---|---|
| ads | some ads still live (README: blank stopped_date) | 0 blanks; 8 distinct stop dates, latest 2026-10-23. Likely snapshot dates, so days_live is weak evidence. |  |
| ads | days_live equals stop minus launch | 74 rows differ, by at most 1 day |  |
| ads | each ad is a distinct video | 97 distinct videos in 100 ads | LJ-073, LJ-093, LJ-036, LJ-056, LJ-003, LJ-059 |
| ads | no zero-purchase ads with add-to-carts | reviewed by the tracking-failure rule in clean.py | LJ-054, LJ-089 |
| ads | brand timing absent when brand not said aloud | 30 ads have both, so the two labels contradict |  |
| ads | no child on screen when no people on screen | 5 contradictions | LJ-002, LJ-011, LJ-019, LJ-037, LJ-040 |
| ads | no named creator type when no people on screen | 10 contradictions | LJ-010, LJ-017, LJ-022, LJ-043, LJ-054, LJ-063, LJ-083, LJ-087, LJ-090, LJ-099 |
| ads | labels complete | blanks: {'hook_type': 2, 'ad_format': 2, 'story_structure': 2, 'child_role': 2, 'brand_first_said': 2, 'creator_age': 1} |  |
| posts | plays exist for all posts | 39 non-video posts have no plays: unavailable, not zero |  |
| creators | each creator has about 20 posts | {'foodies_by_neha': 12} |  |
| posts | all posts within 365 days | 18 older posts, the oldest from 2022-03-03 |  |
| audience | audience measured on Instagram | ['parentingtips_surat'] use another platform and cannot be compared directly |  |
| posts | transcript_language holds a language name | 1 rows contain pasted text |  |
| posts | transcript_language only where a transcript exists | 1 rows |  |
| creators | audience_read has comment evidence | 20 of 20 report comment_evidence none, so the field is not used |  |

## Passed checks

| Dataset | Check | Result |
|---|---|---|
| ads | required columns present | 56 columns |
| ads | row count | 100 rows, expected 100 |
| ads | no fully duplicated rows | 0 duplicates |
| ads | ad_id unique | 0 repeats |
| ads | meta_ad_library_id unique | 0 repeats |
| creators | required columns present | 21 columns |
| creators | row count | 20 rows, expected 20 |
| creators | no fully duplicated rows | 0 duplicates |
| creators | handle unique | 0 repeats |
| creators | creator_id unique | 0 repeats |
| posts | required columns present | 32 columns |
| posts | row count | 392 rows, expected 392 |
| posts | no fully duplicated rows | 0 duplicates |
| posts | post_url unique | 0 repeats |
| audience | required columns present | 10 columns |
| audience | row count | 3 rows, expected 3 |
| audience | no fully duplicated rows | 0 duplicates |
| audience | handle unique | 0 repeats |
| ads | performance columns complete | 0 missing values |
| ads | no negative performance values | 0 rows |
| ads | video_3s_views <= impressions | 0 rows |
| ads | thruplays <= video_3s_views | 0 rows |
| ads | link_clicks <= impressions | 0 rows |
| ads | add_to_carts <= link_clicks | 0 rows |
| ads | purchases <= add_to_carts | 0 rows |
| ads | spend and impressions above zero | 0 rows |
| ads | revenue is zero exactly when purchases are zero | 0 rows |
| ads | launch dates parse | 0 unparsed |
| ads | stop is not before launch | 0 rows |
| ads | stop is not after the as-of date | 0 rows |
| posts | every post belongs to a known creator | 0 unknown handles |
| creators | every creator has posts | 0 without posts |
| posts | post creator_id matches creators.csv | 0 mismatches |
| audience | every audience row belongs to a known creator | 0 unknown handles |
| creators | posts_in_file matches actual count | 0 mismatches |
| posts | no negative engagement | 0 rows |
| posts | likes do not exceed plays | 0 rows |
| posts | post dates parse | 0 unparsed |
| posts | plays exist for all videos | 0 videos without plays |
| audience | audience gender shares sum to 100 | 0 rows |
