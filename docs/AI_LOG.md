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

## Mistakes caught

| What went wrong | How it was caught | Fix |
|---|---|---|
| Profiling script counted empty transcripts as junk values in the language check | Numbers looked impossible on review | Recounted only rows with transcripts: 83% mismatch stands, on the right base |
| Keyword tagging called LJ-035 a teen product because Hindi "teen-teen baar" means "three times" | Hand review of all 100 ads | Reviewed product map, with a test locking this case |
| Product map missed that LJ-038's end card shows the 2+ tub | Label audit | Map corrected, with a test |
| Pipeline crashed writing its report (numpy booleans), although 56 tests had passed | Running the real pipeline, not only the tests | Fixed, with a new test covering the report writer |
| The six-frame audit sheets missed children who appear late in 3 ads, wrongly suggesting a label error | Sampled those ads more densely before recording a verdict | Labels confirmed correct; the limit is noted in the audit report |
| The plan said "about 2 teen ads" | Rechecked once the map existed | Corrected to 1 |

## How AI output is checked

- Metric formulas have hand-computed tests, including zero denominators and missing values.
- Hand-recorded audit values are tested against the source file, to catch copying errors.
- Figures quoted in documents are rechecked against the tested code.
- Limits are stated, e.g. the label audit was done by the AI from video frames and hasn't had a human check yet.
