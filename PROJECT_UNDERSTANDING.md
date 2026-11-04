# Project Understanding: Little Joys Creator Selection

**Status:** Plan of record. Milestones 1 to 3 are finished, and M3 is awaiting review; see [docs/PROGRESS.md](docs/PROGRESS.md).
**Date:** 4 Nov 2026
**Data source:** `little-joys-data.zip`. Its five files are byte-identical to the `little-joys-data/` folder in this repo.

**How to read the numbers.** Everything labelled *Observed* comes from profiling the actual files. Data-quality figures have been rechecked with the tested code from Milestone 1. The pattern tests in section 4.1 are the exploratory first pass, replaced by Milestone 2's results. Anything labelled *Hypothesis* is untested. All ad performance figures are made up for this exercise and must never be described as Little Joys' real results.

---

## 0. The six findings that shaped this plan

1. **The data never links a creator to a sale, with one tiny exception.** `ads.csv` has no creator column. Only one ad could be tied to a listed creator from its text: LJ-039 shows "Foodies by Neha, Kid's School Tiffin Recipe Episode-194". It had ₹3,101 of spend and 7 purchases, which is too small to mean anything. So any creator score estimates *fit*. It does not predict sales, and the report must say so plainly.
2. **One ad dominates the totals and one looks broken.** LJ-004 has 9.1% of spend but 28.9% of purchases and 30.3% of revenue (ROAS 5.00). LJ-089 spent ₹4,26,568, got 29,449 clicks and 1,544 add-to-carts, and recorded **zero** purchases. Across the file about a third of add-to-carts become purchases, so that zero looks like a tracking failure. It does not look like real demand.
3. **Those two ads create or destroy most of the headline "winners".** `story_open` falls from ROAS 1.93 to 0.92 without them, `routine_integration` from 2.34 to 1.15, and `family_skit` rises from 0.46 to 0.93.
4. **Near-copies of one ad can differ by up to 3x in ROAS.** Three videos each run as two ads with identical labels, differing by up to 1.6x. M2 also found re-cuts and translations, and one such pair differs by 3.1x. Gaps of this size between individual ads may not reflect any real creative difference.
5. **What grabs attention is not what sells.** Hook rate and purchase conversion are slightly *negatively* related. A child in the first 3 seconds lifts hook rate by 8.5 points with no change in conversion. Meta's spend follows attention (spend vs hook rate +0.38) and not return (spend vs ROAS 0.00).
6. **The accounts with the most reach are risky picks.** The three largest by plays are a comedian with no children on camera (`thatkushalmistry`), a child account with a recent Gritzo post (`sia_3vedi`) and a child account whose audience is 70.1% men (`storiesbyvihaa`). Separately, six creators mostly show children under 2, younger than any age the ads claim (see section 3.4).

---

## 1. The business problem

**Question:** which 5 of these 20 creators should Little Joys work with next, and what should each one say?

**Who decides:** the brand's marketing manager, who will commit real budget and needs to defend the choice internally. They need:

- a clear answer (five names, and what each should say)
- reasoning they can follow without reading code
- an honest view of how sure we are
- to know what to check before signing anyone
- a way to find out quickly if we were wrong

**Point of view:** the 100 ads tell us which messages tend to work *for this brand*. The 392 posts tell us what each creator can deliver *believably*. The recommendation sits where the two overlap. Because no outcome data links them, the first campaign should be run as a measured test, with spend limits and stop/scale rules.

---

## 2. What Galvor expects

| Required | Our form |
|---|---|
| The answer, written for the marketing manager | A standalone report, plus an interactive app |
| Code in a public GitHub repo with a README | Repo with one command to reproduce all outputs |
| One-page note: key choices, and what we'd build next with a week | `docs/NOTE.md` |
| AI tool use: `CLAUDE.md` or `AGENTS.md`, session logs or main prompts | `CLAUDE.md`, `docs/AI_LOG.md`, exported logs |
| Optional 3-minute screen recording | At the end, if time allows |

**What they grade:** product thinking, use of AI as a partner with a human guardrail, and trustworthy results. Their own line is the design rule: *"A plain answer with sound reasoning beats a polished one we can't trust."* Also: *"Whatever you build should not mislead the person using it."*

**Practical constraint:** 10 to 12 hours of work over 2 days.

---

## 3. The four datasets

### 3.1 Inventory

| File | Shape | Key | Joins | Notes |
|---|---|---|---|---|
| `ads.csv` | 100 x 56 | `ad_id` (unique) | **None to creators** | 97 distinct videos |
| `creators.csv` | 20 x 21 | `handle`, `creator_id` (unique) | to posts, to audience | 3 blank bios |
| `creator_posts.csv` | 392 x 32 | `post_url` (unique) | `handle`: all match | 353 videos, 34 carousels, 5 photos |
| `creator_audience.csv` | 3 x 10 | `handle` | all match | Only CR-14, CR-15, CR-20 |

There are no fully duplicated rows, and all creator joins are intact. `foodies_by_neha` has 12 posts; the other 19 have 20. Transcripts exist for 113 of 392 posts.

### 3.2 Data dictionary: columns that matter

**Purpose:** S = creator selection, P = ad performance, C = creative strategy, V = validation.

**ads.csv**

| Columns | Purpose | Trust and handling |
|---|---|---|
| `ad_id`, `meta_ad_library_id`, `video_url` | V | Reliable. Videos are reachable (LJ-004 and LJ-089 checked), so labels can be audited against them |
| `spend_inr`, `impressions`, `video_3s_views`, `thruplays`, `link_clicks`, `add_to_carts`, `purchases`, `revenue_inr` | P | Synthetic. Funnel order holds on all 100 rows. LJ-089 purchases treated as missing |
| `launch_date`, `stopped_date`, `days_live` | P | Weak, see 3.3. Use spend and impressions as the measure of exposure |
| `transcript`, `hook_line`, `on_screen_text` | C, V | Primary evidence for what an ad says |
| `claims_made` | C, V | Observed claims, **not** approved claims |
| `ad_copy` | C | Only 17 distinct texts plus 12 blanks. It describes the product, not the creative, so we don't test it for effect |
| `hook_type`, `hook_driver`, `ad_format`, `story_structure`, `main_benefit`, `performance_style` | P, C | AI labels. Used after audit |
| `creator_type`, `child_on_screen`, `child_role`, `child_in_first_3s`, `child_age` | P, C | AI labels. Consistent with each other, except some `people_on_screen` values |
| `brand_first_said`, `brand_said_aloud` | P | **Contradictory**, see 3.3 |
| `product_form` | P | **Wrong or too coarse**, see 3.3. We will build our own product column |
| `proof_used`, `persuasion`, `demo_shown`, `narratives` | P, C | Multi-label, so an ad counts in several groups. Compare only with care |

**Derived ad metrics**

| Metric | Formula |
|---|---|
| Hook rate | 3-second views / impressions |
| ThruPlay rate | ThruPlays / impressions |
| Hold rate | ThruPlays / 3-second views |
| CTR | clicks / impressions |
| Add-to-cart rate | add-to-carts / clicks |
| Conversion rate (CVR) | purchases / clicks |
| ROAS | revenue / spend |
| CPA | spend / purchases, undefined at 0 purchases (never ₹0 or infinity) |

Group figures sum numerators and denominators. They are always shown beside the median and a version without LJ-004 and LJ-089.

**creators.csv**

| Columns | Purpose | Trust and handling |
|---|---|---|
| `followers`, `following`, `total_posts`, `verified` | S | Facts. Followers track typical plays fairly closely (rank correlation 0.73) but say nothing about whether viewers are parents. `verified` is not used in scoring |
| `persona`, `voice`, `themes`, `format_habits`, `catchphrases` | S, C | AI read of the feed. Used for brief tone, and checked against actual posts |
| `language_use` | S, C | Sometimes contradicted by transcripts |
| `what_feels_native`, `what_would_feel_foreign` | C | Useful for briefs, but partly boilerplate: 15 of 20 "foreign" fields mention studio production |
| `audience_read` | none | **Excluded.** `comment_evidence` is `none` for all 20, so "None observed" means nobody looked |

**creator_posts.csv**

| Columns | Purpose | Trust and handling |
|---|---|---|
| `posted_on`, `type`, `duration_s` | S | Reliable. Restrict to the last 365 days |
| `plays` | S | Blank on all 39 non-video posts, which means unavailable and not zero |
| `likes` | S | Exactly 3 on 10 posts, with up to 1.35M plays: a hidden-likes placeholder |
| `comments` | S | Inflated by "comment X for the link" captions and sometimes switched off |
| `reshares` | S | 0 on 49 posts, some with over 500k plays, so a 0 may mean unavailable |
| `is_sponsored`, `brands_visible`, `product_shown` | S | AI labels. Needed for sponsorship and competitor checks; spot-check before use |
| `children_on_camera`, `child_ages`, `presenter_age` | S | AI labels. Needed for the age check; audit against captions and transcripts |
| `content_type`, `content_form`, `topic`, `hook_style`, `tone` | S, C | AI labels, mostly coherent |
| `language` | none | **Do not use.** See 3.3. Use `transcript_language` |
| `transcript`, `caption`, `on_screen_text`, `what_stands_out` | C, V | Primary evidence for voice and for brief citations |
| `audience_signal` | none | Free text. Failed the one direct test we can run, see 3.3 |

**creator_audience.csv:** `platform`, `women_pct`, `men_pct`, `age_split`, `top_countries`, `top_cities`, `brands_in_past_year`. These are facts for 3 creators only, and one of the three is measured on Facebook, not Instagram.

### 3.3 Data quality issues found (Observed)

**Ads**

| Issue | Evidence | Handling |
|---|---|---|
| Dominant outlier | LJ-004: ROAS 5.00, add-to-cart rate 24.0% (median ad about 9%). Blended ROAS is 1.50 with it, 1.15 without | Report every result with and without it. Treat it as a lead to test, not a pattern |
| Probable tracking failure | LJ-089: zero purchases on 1,544 add-to-carts | Set purchases and revenue to missing. Keep its attention metrics |
| Tiny-sample "winners" | LJ-072: ROAS 3.00 on ₹4,117 and 18 purchases. LJ-054: 1 day, 0 purchases | Apply minimum-evidence rules, show spend beside every rate |
| Same video counted twice | LJ-073/093 (ROAS 0.78, 1.27), LJ-036/056 (1.42, 2.30), LJ-003/059 (0.78, 0.58) | Treat each as one creative for pattern analysis. Use the spread as a noise reference |
| `stopped_date` doesn't match the README | No blanks, though blank should mean "still live". 98 of 100 dates fall on 6 dates; none is after 23 Oct. `days_live` matches stop minus launch on 26 rows and is 1 less on 74 | Likely snapshot dates. Don't read duration as evidence of success |
| `product_form` unreliable | LJ-004 is labelled milk mix, but its transcript sells Proteinmix mixed into roti dough. "Other" (26 ads) hides Proteinmix, pancake mix, spreads and more | Replaced by a reviewed product map for all 100 ads (`data/overrides/ad_products.csv`), because keyword matching proved unreliable |
| Non-kids products mixed in | 8 ads aimed at moms (e.g. LJ-001 postpartum weight loss, LJ-015) and 1 for teens (LJ-046, Nutrimix 13+) | Separate them from the kids' pattern analysis |
| Brand-timing labels contradict | All 30 ads with `brand_said_aloud=no` still have a `brand_first_said` timing (18 say under 3s). 12 ads marked "yes" don't contain the name in our transcript search (which may miss spellings) | Don't use these labels unless the audit shows what they mean |
| On-screen labels contradict | 5 ads say `people_on_screen=none` but a child is on screen; 10 more say none but name a person as `creator_type` | Don't use `people_on_screen` |
| Gaps in the data | No margins, no audience or targeting data, no daily data. Average order value barely varies between ads (10th to 90th percentile: ₹560 to ₹687) | ROAS below 1 means revenue under spend. It doesn't tell us profit. We can't study targeting or fatigue over time, and ROAS differences come almost entirely from CTR and CVR |

**Creators and posts**

| Issue | Evidence | Handling |
|---|---|---|
| Hidden likes | 10 posts have exactly 3 likes (`radhikabansal0908` 6, `doc_mama_and_babies` 3, `livesimply_withkripa` 1). Likes are below comments on 45% of `tej.lil.diary` posts | Score no one on likes. Show hidden-metric share in confidence |
| Viral spikes distort averages | One post is 96% of `mumma_and_ridhu`'s recent plays (a 48.8M sponsored sofa-stain video; mean 3.18M vs median 132k). `ohmother.in` 81%, `tej.lil.diary` 75% | Use medians and report top-post share |
| "Recent" isn't always recent | 18 posts are over a year old, back to Mar 2022, including 9 of 20 for `doc_mama_and_babies`. Older posts look like pinned hits (`sia_3vedi`: 24.4M vs 4.2M) | Use a 365-day window |
| Comments are inflated | Comment-for-link captions on 55% of `tej.lil.diary` and `raising_zohran` posts and 50% of `couple_adishiv`. `tej.lil.diary`: median 475 comments on those posts vs 2 on others. One post: 61,684 comments | Keep comment rate out of the score, or use non-bait posts only |
| Comments switched off | `ohmother.in`: 10.8M plays, 0 comments | Treat 0 as unavailable on high-play posts |
| Possibly boosted plays | `radhikabansal0908`: 20 of 20 posts sponsored, median 1.02M plays, median 7 reshares. No organic baseline exists | Flag it. Cannot be proven from this data |
| Post `language` is wrong | Of 66 English-labelled posts with a language-tagged transcript, only 11 are in English (42 are Hinglish): 83% mismatch. The column also has 13 spelling variants | Use `transcript_language`, which has one corrupted row to repair |
| Profile vs reality | `paediatrics_decoded` and `ekamichildcare` are described as English-speaking, but all 12 of their transcripts are Hinglish | This is what the authenticity check is for |
| Credentials unverifiable | `parentingtips_surat` has a blank bio but a "Clinical Pediatrician" persona | Flag it. Don't repeat the credential as fact |
| Audience file isn't comparable | `parentingtips_surat`: Facebook, India only 64.4%, Pakistan and Bangladesh 16.8% | Never compare directly with the Instagram rows |
| AI audience label failed a check | `storiesbyvihaa` posts say "families, parents", while the real audience is 70.1% men | Don't use `audience_signal` as a stand-in for demographics |

### 3.4 Creator fact sheet (Observed; not a ranking)

**Superseded by Milestone 3.** Use [outputs/creator_profiles.md](outputs/creator_profiles.md), which has checked brand lists and child ages. For example, this early table misses Good Monk and Manna for `doc_mama_and_babies`.

Posts within 365 days of 27 Oct 2026. Play medians are for videos only. Child ages are shares of AI labels and need audit.

| Handle | Followers | Recent posts | Organic median plays (n) | Sponsored median plays (n) | % sponsored | Top-post share | Child ages on camera | Spoken language (transcripts) | Kids' food/nutrition brands seen |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| `drgarima_mehta` | 48,906 | 20/20 | 111,770 (18) | 5,160 (2) | 10% | 38% | 0-2: 94% | Hinglish 5 | none |
| `livesimply_withkripa` | 67,658 | 20/20 | 1,040,230 (19) | n/a | 0% | 31% | 13-17: 100% | Hinglish 6 | none |
| `ekamichildcare` | 164,333 | 20/20 | 497,654 (18) | 51,898 (2) | 10% | 25% | 0-2: 55%, 3-7: 40% | Hinglish 6 | Troovy; Little Tummys |
| `hello_ps8` | 216,882 | 20/20 | 731,154 (11) | 957,270 (2) | 10% | 18% | 3-7: 83% | Hinglish 3, Hindi 2 | none |
| `sia_3vedi` | 2,831,180 | 18/20 | 4,242,421 (14) | 2,825,061 (1) | 5% | 43% | 3-7: 92% | Hinglish 5, English 1 | **Gritzo** (28 Sep) |
| `thatkushalmistry` | 1,706,047 | 18/20 | 4,527,101 (17) | 1,990,625 (1) | 5% | 38% | No children | Gujarati 4, Hinglish 2 | none |
| `ohmother.in` | 34,672 | 19/20 | 47,408 (14) | 23,453 (4) | 20% | 81% | 3-7: 70%, 8-12: 26% | English 3, Hinglish 2 | one.science.nutrition (also in bio) |
| `the_mum_wife_playbook` | 39,571 | 19/20 | 37,857 (13) | 86,750 (4) | 20% | 53% | 3-7: 94% | Hinglish 4, Hindi 2 | none |
| `doc_mama_and_babies` | 153,896 | 11/20 | 511,128 (1) | 214,281 (7) | 80% | 23% | 3-7: 50%, 8-12: 50% | Hinglish 3, English 2 | **Little Joys** (Jul 2025) |
| `couple_adishiv` | 48,934 | 20/20 | 728,418 (12) | 381,250 (7) | 35% | 36% | 0-2: 82% | Hinglish 6 | **Gritzo** (6 Sep) |
| `raja_choudhary04` | 196,955 | 20/20 | 256,671 (12) | 924,504 (7) | 35% | 26% | 3-7: 68%, 0-2: 19% | Hinglish 6 | **Gritzo** x2; Troovy (7 Oct) |
| `raising_zohran` | 22,659 | 20/20 | 14,310 (14) | 9,727 (3) | 15% | 58% | 0-2: 100% | Hinglish 2, Hindi 1 | none |
| `mumma_and_ridhu` | 115,612 | 20/20 | 184,756 (4) | 122,183 (11) | 60% | 96% | 3-7: 62%, 8-12: 38% | Hinglish 4, Odia 1 | none |
| `parentingtips_surat` | 1,120,817 | 20/20 | 306,092 (19) | n/a | 0% | 28% | 3-7: 67%, 0-2: 33% | Hinglish 5, Hindi 1 | none |
| `tej.lil.diary` | 35,280 | 20/20 | 71,767 (12) | 40,974 (6) | 30% | 75% | 0-2: 73%, 3-7: 27% | Hinglish 3, Telugu 1 | Shivan shishu aahar |
| `paediatrics_decoded` | 263,188 | 20/20 | 227,894 (18) | n/a | 0% | 49% | 0-2: 87% | Hinglish 6 | none |
| `radhikabansal0908` | 395,569 | 20/20 | **no organic posts** | 1,023,759 (20) | 100% | 14% | 3-7: 67%, 0-2: 33% | English 4, Hinglish 1 | none |
| `foodies_by_neha` | 1,009,385 | 9/12 | 211,809 (7) | 428,591 (1) | 8% | 66% | No children | Hinglish 5 | **Little Joys** (ad LJ-039) |
| `instamommy_suchi` | 288,693 | 20/20 | 1,529,438 (3) | 857,458 (14) | 75% | 10% | 8-12: 44%, 3-7: 33%, 0-2: 22% | Hinglish 5, Hindi 1 | **Bournvita** (2 Aug); **Complan** (6 Oct) |
| `storiesbyvihaa` | 827,496 | 20/20 | 2,214,729 (14) | 2,021,222 (2) | 10% | 17% | 3-7: 100% | Telugu 5 | **Little Joys** (audience file only) |

Brand dates are 2026 unless stated. Brand tags are AI labels, so "seen" doesn't prove a contract and we can't see any exclusivity terms.

Real audience data exists for three creators only:

| Handle | Platform | Women | Men | Largest age group | India share |
|---|---|---:|---:|---|---:|
| `tej.lil.diary` | Instagram | 83.4% | 16.6% | 25-34: 71.9% | 88.3% |
| `storiesbyvihaa` | Instagram | 29.9% | 70.1% | 25-34: 44.4% (18-24: 30.5%) | 95.7% |
| `parentingtips_surat` | Facebook | 65.0% | 35.0% | 25-34: 48.3% (35-44: 40.1%) | 64.4% |

---

## 4. Analytical approach

### 4.1 Ad intelligence

1. **Clean first:** collapse duplicate videos, set LJ-089's conversions to missing, tag LJ-004, build the product column, separate moms' and teen products.
2. **Audit labels we rely on.** Galvor says to check them. Review 15 to 20 ad videos (frames plus transcript), including LJ-004 and LJ-089, against the labels we use, and publish the error rate. `ffmpeg` isn't installed, so we'd extract frames with a Python package.
3. **Analyse by funnel stage, not one ROAS league table:** attention (hook, hold), interest (CTR), and purchase intent (add-to-cart, CVR). Report ROAS, but explain it as a result of those stages.
4. **Three views of every pattern:** pooled, pooled without the two outlier ads, and median, with bootstrap intervals and permutation tests.
5. **Control for the obvious confounders:** product, language and spend level, in a simple regression as a check, not as the headline.
6. **Grade every finding:** *Supported*, *Directional* or *Inconclusive*, with supporting ad IDs. About 35 labels with many levels means false positives are guaranteed if we just look for winners.

**Superseded by Milestone 2.** The table below is the first exploratory pass, kept as a record. It didn't group near-copies or test all patterns, and several readings changed. Use [outputs/ad_patterns.md](outputs/ad_patterns.md) instead.

**First-pass signal (Observed, exploratory).** 21 labels were tested on 3 metrics, chosen after seeing the data, so these p-values are optimistic. Without LJ-004 and LJ-089:

| Pattern | n | Attention (hook) | Conversion (CVR) | ROAS | Preliminary read |
|---|---:|---|---|---|---|
| Child in first 3s | 39 | **+8.5 pts**, p≈0.001 | -0.1 pt | p=0.40 | Buys attention, not sales |
| Hindi language | 10 | **+11 pts**, p≈0.001 | -0.9 pt | -0.52, p=0.11 | Attention, weak sales |
| Fear appeal | 10 | +8.8 pts, p=0.02 | -1.3 pts, p=0.02 | -0.63, p=0.05 | Attention, poor sales |
| Recipe narrative | 31 | +6.7 pts, p=0.003 | -0.4 pt | -0.03, p=0.93 | Attention, neutral sales |
| English language | 38 | -4.8 pts, p=0.06 | **+1.2 pts**, p=0.001 | +0.49, p=0.04 | Possible sales signal; check for confounds |
| Taste as main benefit | 7 | -2.8 pts | +1.4 pts, p=0.02 | +0.74, p=0.04 | Promising, small n |
| Child-led format | 7 | +5.8 pts | +0.9 pt | +0.92, p=0.02 | Promising, small n, and holds up without LJ-004 |
| Child reacts to taste | 38 | +2.6 pts | +0.4 pt | +0.46, p=0.05 | Directional |
| Personal-experience hook | 29 | +0.9 pt | -1.1 pts, p=0.01 | -0.39, p=0.11 | May hurt conversion |
| Routine integration | 27 | 0 | -0.6 pt | p=0.73 | **No effect**, despite a 2.34 pooled ROAS |
| Brand named within 10s | 59 | -1.9 pts | +0.6 pt | p=0.84 | No clear effect |
| Authority/science | 24 | -3.6 pts | 0 | p=0.24 | No evidence it helps |

Only the child-in-first-3s and Hindi hook effects would clear a strict correction across all 63 tests. The honest picture is a few real attention effects and several promising but unproven sales signals. **The doctor-led route has almost no support:** one ad is labelled `medical_professional` (LJ-057, ₹19,099).

### 4.2 Creator intelligence

Build one table of consistent features for all 20 creators, from their posts and not just their profiles, and treat unavailable values as missing, never zero:

- **Reach you can repeat:** median organic plays in the last 365 days, with top-post share. Not followers or means.
- **Product and buyer fit:** share of content with children in the eligible age range, parent-directed content, food or mealtime topics, checked by reading captions and transcripts.
- **Creative fit:** overlap between the creator's habits and the ad patterns that survive 4.1.
- **Paid-content readiness:** sponsored vs organic plays (only where n is large enough), how saturated the feed is with ads, past brand category.
- **Profile vs reality:** does the persona match the posts?

### 4.3 Scoring framework: proposal

**Change from the starting weights.** I recommend gates first, then a score. A plain weighted sum lets 5M plays cancel out a wrong audience or a product the child is too young for.

**Stage 1: eligibility gates (transparent yes/no, all 20 shown)**

| Gate | Rule (draft) | Why |
|---|---|---|
| Product age | Most on-camera children are 2 or older, or the content addresses parents of eligible kids | Ads only claim 2+ and 7+ products. A feed about babies under 2 is the wrong buyer, and shouldn't show them consuming it |
| Relevant viewers | The feed includes parenting, family or food content | A large comedy audience isn't evidence of parents |
| Active | Posted in the last 90 days | Must be able to deliver soon |

**Stage 2: fit score (0 to 100)**

| Criterion | Your starting weight | Proposed | Reason for the change |
|---|---:|---:|---|
| Brand and product fit | 25% | **30%** | The ad data suggests what's sold and to whom matters most, and this is our most direct evidence |
| Creative compatibility | 20% | **25%** | "What should they say" only works if the creator can naturally deliver the patterns that sell |
| Engagement quality | 20% | **20%**, renamed **repeatable reach** | Likes and comments are unreliable in this data. Plays are the usable signal |
| Paid-content readiness (was Sponsorship experience) | 10% | **15%** | More sponsorship isn't simply better: 100% sponsored is a warning sign. Measures retention and saturation instead |
| Authenticity and native integration | 15% | **10%** | Partly overlaps the two fit criteria and depends on AI-written fields, so it carries less weight |
| Audience relevance | 10% | **0%, as override and confidence input** | Only 3 of 20 have data. Scoring it either penalises 17 creators or rewards missing data. Real data still acts: 70.1% men is shown and caps a creator; absence lowers confidence, not the score |

**Risk flags stay outside the score, and always visible:** recent competitor work, an existing Little Joys relationship, on-camera talent who are minors, unverifiable credentials, possibly boosted plays.

**Why the framework needs validation.** There is no outcome to train or test against, so no weights can be proven correct. These weights are my judgment. We make that visible instead of hiding it by testing:

- about 6 named weighting scenarios plus thousands of random weightings, and reporting **how often each creator makes the top 5**
- removing one criterion at a time
- competitor rule both ways (excluded vs flagged), and ad patterns with and without LJ-004
- a check that the score isn't just following follower count

If the five aren't stable, the report says which slots are firm and which are close calls.

**Confidence is separate from fit:** High, Medium or Low, based on the number of recent organic posts, transcripts available, hidden-metric share, label audit results, and whether real audience data exists.

### 4.4 Creative briefs

Python selects creators and builds a checked evidence pack for each: relevant ad patterns, the creator's actual posts and voice, and allowed claims. The LLM drafts only from that pack, to a fixed JSON schema. A validator then rejects any brief that fails its checks.

**No approved product information exists in the data.** `claims_made` shows what ads have said, not what the brand has cleared. So we'll build a claims library and tier it:

- **Factual, label-check needed:** e.g. "12g protein per 15g scoop", which appears consistently
- **Needs approval:** benefit claims such as immunity, brain/DHA, growth, digestion
- **Do not use without substantiation:** superlatives and comparisons such as "India's ONLY...", "2.5X more protein", "3x more calcium than milk"

We'll also flag claims that conflict across ads (e.g. 11 vs 11+ vs 12 vitamins and minerals, "zero added sugar" alongside jaggery sweetening).

**Validator checks:**

- every `ad_id` and `post_url` exists and belongs to that creator
- every number matches the source
- every product claim traces to the library
- correct creator and product age

If no LLM is available, it falls back to a template brief, clearly labelled as such.

### 4.5 Closing the loop: a test plan

Since the data can't show that a creator will sell, each brief ships with a low-cost test: suggested spend, a benchmark from this ad file (for example the hook, CTR and CVR quartiles), and stop/scale rules. The test spend needed to read a result will be calculated from the data, not guessed. This is where the product answers "how would we know if this was wrong?"

---

## 5. System architecture

```
little-joys-data.zip  (checksum verified, never modified)
        |
  ingest + validate   schema, types, ranges, joins; writes a data-quality report
        |
  clean + derive      missing-value rules, product column, duplicate groups, metrics
        |
   +----+---------------------+
   |                          |
 ad analytics             creator features
 (graded patterns)        (all 20, consistent)
   |                          |
   +----------+---------------+
              |
       gates + scoring + sensitivity  -> creator_rankings.csv
              |
       evidence packs (deterministic)
              |
       LLM draft -> validator -> briefs (rejected drafts logged)
              |
        outputs/   (the single source for everything below)
         |       |
      report   Streamlit app (reads outputs only, holds no business logic)
```

**Deliberately left out:** a database, Docker, vector search/RAG, FAISS, and sentence embeddings. With 392 posts and 113 transcripts, filtering structured data is simpler and more traceable, and every citation stays checkable.

**Evidence trail:** every recommendation links through reasoning to creator evidence and ad evidence, down to the source row or URL.

**Layout (adapted from your suggestion)**

```
src/lj/        ingestion, cleaning, ads, creators, scoring, briefs, validation, reporting
app.py         Streamlit entry point
tests/         pytest
outputs/       generated results (committed, except anything restricted)
prompts/       LLM prompts
docs/          NOTE.md, AI_LOG.md, methodology
CLAUDE.md      Instructions and guardrails for AI tools
```

---

## 6. Hypotheses to test

These are untested, and each could be wrong.

| # | Hypothesis | How we'd test it |
|---|---|---|
| H1 | Ad patterns differ by funnel stage, so a creator chosen for attention won't automatically sell | Stage-by-stage analysis with robustness checks |
| H2 | Taste-led messages convert better than immunity or growth messages | Compare within the same product; audit the 7 taste-led ads |
| H3 | Child-led delivery has a real sales effect, independent of LJ-004 and product | Regression with product and language controls |
| H4 | Language effects are really product or targeting effects | Compare within products. Creators are mostly Hinglish, so "English wins" can't be applied directly |
| H5 | Doctor-style creators won't be supported by this data despite looking like an obvious fit | Infant-heavy feeds, one medical ad, weak authority signal |
| H6 | Naive scoring would pick the largest child-led accounts; gates and overrides change this | Compare naive vs final ranking and show both |
| H7 | Likely contenders include `foodies_by_neha`, `hello_ps8`, `the_mum_wife_playbook`, `mumma_and_ridhu` and `raja_choudhary04` | Not a selection. Only the pipeline decides, and I'll report it if this list is wrong |
| H8 | The five stay stable under reasonable weightings | Sensitivity analysis; slots 4 and 5 are the most likely to move |

---

## 7. Risks and limitations

**In the data, and permanent**

1. No creator-to-sales link exists, so fit is the most we can estimate.
2. Ad performance is synthetic. Conclusions hold only for this export.
3. With n=100 across many labels, most pattern findings will stay directional.
4. No purchase or profit data for creator content, and no margins.
5. Real audience data exists for only 3 of 20.
6. We have comment counts but no comment text, so we can't judge comment quality or bot activity.
7. Labels contain errors we can only sample-check.
8. Competitor and past-brand evidence is limited to the posts in this sample. Exclusivity terms and creator rates are unknown, so we can't compute cost-effectiveness.

**In our build, and manageable**

| Risk | Mitigation |
|---|---|
| Over-reading noise | Grading system, near-copies counted once, no winners from small n |
| The scoring looks more precise than it is | Report top-5 frequency and confidence; avoid decimal-point rankings |
| My own errors in analysis (one script bug was already caught during profiling) | Tests on metric and scoring functions; hand-check key numbers against the raw files |
| LLM invents claims or citations | Evidence packs, fixed schema, validator, human review |
| Crossing into medical or regulatory advice from general knowledge | Limit recommendations to data. Mention doctor endorsement rules and rules on child talent only as "check with legal", clearly marked as outside the data |
| Polish overruns the 12-hour budget | The report comes before the app; cut order is in section 9 |
| Raw data leaks into a public repo | `.gitignore` before the first commit (**avoid `git add .` until then**) |

---

## 8. Technology

| Need | Choice | Why |
|---|---|---|
| Runtime | Python 3.12 via `uv`, with a lockfile | Already installed; reproducible |
| Analysis | pandas, numpy, plus scipy or statsmodels only if needed | Simple and auditable |
| Schemas and validation | pydantic | Fits both LLM output and data checks |
| Tests | pytest | As you requested |
| Charts and app | Plotly, Streamlit | Fast to build, easy to run |
| LLM | Gemini (decided) | Key kept in a local `.env`; results cached so the app runs without a key |
| Frames for label audit | `imageio-ffmpeg` or OpenCV | `ffmpeg` isn't installed here |

---

## 9. Roadmap (about 12 hours)

| When | Milestone | Hours | Done means |
|---|---|---:|---|
| Day 1 | **M1** Foundation: repo setup, ingest from zip, validation, cleaning, label audit | 2 | Tests pass; data-quality report and audit results reviewed |
| Day 1 | **M2** Ad intelligence | 2 | Graded findings with ad IDs; outlier-sensitive results shown both ways |
| Day 1 | **M3** Creator features | 2 | All 20 profiled; missing data handled; competitor and age evidence checked |
| Day 2 | **M4** Gates, scoring, sensitivity | 1.5 | `creator_rankings.csv`; stability known; rejected candidates explained |
| Day 2 | **M5** Briefs and validator | 2 | Five distinct briefs pass validation; a deliberately bad brief gets rejected |
| Day 2 | **M6** Report and app | 1.5 | Report stands alone; app works end to end |
| Day 2 | **M7** Review and packaging | 1 | Strict review done; note, README, AI log, public repo |

**Each milestone stops for your review.** If time runs short, cut in this order: screen recording, then app pages beyond the core, then regression extras. Never cut validation, the sensitivity analysis, or limitations.

---

## 10. Decisions needed

| # | Decision | My recommendation | If you don't say otherwise |
|---|---|---|---|
| 1 | **App scope:** your 7 pages, or a smaller app? | **Report as the primary answer, plus a 4-page app** (Answer; All 20 creators and sensitivity; Briefs; Evidence and data, with exports). Galvor rewards plain and sound over polished, and a marketing manager won't run Python | 4 pages |
| 2 | **LLM for briefs:** do you have a Gemini or OpenAI key? | **Decided: Gemini.** The key stays in a local `.env`, never in the repo | Gemini |
| 3 | **Recent competitor work** (`sia_3vedi`, `raja_choudhary04`, `couple_adishiv`, `instamommy_suchi`, `doc_mama_and_babies`, `ekamichildcare`): exclude or flag? | **Flag it and run both ways.** It's a brand decision and we can't see contract terms, but the report should say whether the five change | Flag, both scenarios |
| 4 | **Existing Little Joys relationships** (`doc_mama_and_babies`, `storiesbyvihaa`, `foodies_by_neha`): are they eligible for "next"? | Eligible and flagged. Prior work with the brand isn't a negative. The brand knows the results; we don't | Eligible |
| 5 | **Public repo vs data:** the assignment doesn't say whether the data can be republished | Keep raw data out and commit derived outputs. Worth one email to Galvor, since they invite questions | Not committed |
