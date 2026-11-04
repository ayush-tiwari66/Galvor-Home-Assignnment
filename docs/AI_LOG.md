# AI usage log

The project is built with Claude Code. This log records decisions made with AI and the mistakes caught along the way, including the AI's own. Full session logs and main prompts will be added at submission.

## Decisions

| Date | Decision | Who | Why |
|---|---|---|---|
| 4 Nov | Use gates plus a score, instead of the initial weighted sum | Claude proposed; defaults accepted, pending review | Reach shouldn't be able to cancel out a wrong audience |
| 4 Nov | Audience gets no scoring weight; it acts as an override and confidence input | Claude proposed; defaults accepted, pending review | Only 3 of 20 creators have data |
| 4 Nov | Report plus a 4-page app, not the 7 pages first suggested | Claude proposed; defaults accepted, pending review | Galvor values a plain, sound answer over polish |
| 4 Nov | No RAG or vector search | Claude proposed | 392 posts can be filtered directly, and citations stay checkable |
| 4 Nov | Reviewed product map instead of keyword rules | Claude, after finding the bug below | Keyword rules failed on a large ad |
| 4 Nov | Grades for ad patterns fixed in code before final results; not loosened when nothing reached the top grade | Claude proposed; pending review | Moving the bar afterwards would make the grades meaningless |
| 4 Nov | Use Gemini for briefs; keep all work on `main` | Project owner | Owner's decisions |
| 4 Nov | Don't drop parent stories or growth, immunity and picky eating angles; use them as the reason to care, with a child enjoying the product as proof | Project owner challenged Claude's draft; Claude tested it | Owner's category knowledge. The data rejected the weak-hook explanation but supported pairing, so the briefs changed |

## Mistakes caught

| What went wrong | How it was caught | Fix |
|---|---|---|
| Profiling script counted empty transcripts as junk values in the language check | Numbers looked impossible on review | Recounted only rows with transcripts: 83% mismatch stands, on the right base |
| Keyword tagging called LJ-035 a teen product because Hindi "teen-teen baar" means "three times" | Hand review of all 100 ads | Reviewed product map, with a test locking this case |
| Product map missed that LJ-038's end card shows the 2+ tub | Label audit | Map corrected, with a test |
| Pipeline crashed writing its report (numpy booleans), although 56 tests had passed | Running the real pipeline, not only the tests | Fixed, with a new test covering the report writer |
| The six-frame audit sheets missed children who appear late in 3 ads, wrongly suggesting a label error | Sampled those ads more densely before recording a verdict | Labels confirmed correct; the limit is noted in the audit report |
| The plan said "about 2 teen ads" | Rechecked once the map existed | Corrected to 1 |
| Duplicate check compared only video files, so re-cuts and translations counted as separate evidence | Noticed the same boy and script while re-checking child-led ads | Compared frame fingerprints and transcripts across all ads, and reviewed 12 families into a concept map |
| Controlled model flipped a true +100% lift to -57% when a pattern matched a control | Followed up a statsmodels warning instead of ignoring it | Failing test first, then dropped redundant controls |
| Controlled model reported significance on 98-100% of shuffled labels, where about 5% is correct | p-values of 0.0000 beside permutation p = 0.3 looked wrong, so ran a calibration check | Failing test first, then replaced with a weighted log regression that shows 3-6% |
| Earlier tests passed despite that bug, because they only checked that real effects were found | Same calibration check | Added a test that the model stays quiet when no effect exists |
| Interpretation said a pattern missed "only narrowly" and called a format "the weakest", beyond what the data shows | Checked other random seeds and the without-largest-concepts column | Reworded; removed fear appeal evidence that didn't hold up |

## How AI output is checked

- Metric formulas have hand-computed tests, including zero denominators and missing values.
- Statistical methods are tested both ways: they must find a planted effect and stay quiet when labels are shuffled.
- Results are rerun with other random seeds, and with the system's uncorrected labels, to see what changes.
- Hand-recorded audit values are tested against the source file, to catch copying errors.
- Figures quoted in documents are rechecked against the tested code.
- Limits are stated, e.g. the label audit was done by the AI from video frames. The project owner reviewed 6 of its verdicts, chosen by the AI, and agreed with all of them; the rest have had no human check.
