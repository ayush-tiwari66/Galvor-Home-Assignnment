# Ad patterns

All ad performance figures are made up for this exercise and are not Little Joys' real results. These patterns show association within this export. They don't prove cause.

**Scope:** 91 ads for kids' products, grouped into 78 concepts so that near-copies count once. LJ-004 is set aside in the main results because of its size. LJ-089 counts for attention and clicks but not for purchases.

**Tested:** 553 comparisons (111 patterns on 5 metrics). **Result:** 0 Supported, 53 Directional, 500 Inconclusive. 57 comparisons came in below p = 0.05, where about 28 would be expected by chance, so the file holds real signal, but no single pattern is firmly established.

**Stability:** re-running with 3 other random seeds kept 50 to 53 of the 53 graded results, and none reached Supported. Results near p = 0.05 can change grade between runs.

**Grades (fixed before results were seen):**

- **Supported:** at least 10 concepts on each side, false discovery rate below 10%, a lift of at least 10% and significant after controlling for product and language, with the direction agreeing across all five views.
- **Directional:** at least 5 concepts on each side, p below 0.05, and the direction agreeing across all five views. Worth testing, not proven.
- **Inconclusive:** everything else.

The five views are: pooled without LJ-004, adjusted for product, the median, pooled without the group's largest concept, and the regression with controls.

## What this means (interpretation)

The readings below are judgment. The numbers are from the analysis. A star marks a result significant after controlling for product and language.

### A child visibly enjoying the product goes with better sales

This is the strongest sales signal in the file, and it holds when each group's three biggest concepts are removed. Count it as one signal, not several: every `taste_test` concept is also `reacts_to_taste`. The label is broad, meaning a child shown enjoying the product, not a formal test. Briefs should build around this moment.

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| demo_shown = taste_test | cvr | 17 | 3.5% | 2.3% | 3.1% | +37%* | Directional |
| demo_shown = taste_test | roas | 17 | 1.78 | 0.93 | 1.41 | +67%* | Directional |
| child_role = reacts_to_taste | roas | 32 | 1.57 | 0.85 | 1.27 | +56%* | Directional |
| child_role = consumes_product | roas | 43 | 1.52 | 0.83 | 1.24 | +46%* | Directional |
| narratives = taste_better_than_other_brands | roas | 24 | 1.61 | 0.96 | 1.21 | +41%* | Directional |

### Child-led ads look promising but can't be graded

A child speaking goes with more clicks, but its lead on return mostly disappears without its three biggest concepts. Fully child-led ads have only 4 concepts once LJ-004 and near-copies are accounted for, so they got no test (see 'Too few concepts to grade'). LJ-004 is this format, and its success can't be told apart from luck or targeting. The same boy and set gave both a strong and a below-average result in `nutrimix_batman_boy_protein`. Worth testing with creators, not assuming.

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| child_role = speaks | ctr | 18 | 1.1% | 0.9% | 1.0% | +25%* | Directional |
| child_role = speaks | roas | 18 | 1.61 | 1.03 | 1.07 | +41%* | Directional |

### Attention and sales are different jobs

A child in the first 3 seconds came closest to the top grade but didn't reach it. It goes with more people watching, with no change in purchases once they click. Use it to win attention, and rely on something else to make the sale. Hindi ads also show high attention, but from few concepts, and the lead disappears without the three biggest. Don't choose creators or scripts on attention alone.

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| child_in_first_3s = yes | hook_rate | 33 | 35.5% | 26.7% | 34.1% | +21%* | Directional |
| child_in_first_3s = yes | cvr | 32 | 2.8% | 2.9% | 2.5% | +6% | Inconclusive |
| language = Hindi | hook_rate | 5 | 41.6% | 30.2% | 30.4% | +44%* | Directional |
| hook_type = question | hook_rate | 25 | 25.9% | 33.5% | 25.2% | -11% | Directional |

### A parent's personal story may sell less well

This matters here because most candidate creators are parents making UGC, so treat it as a caution and not a reason to change the format. Only personal-experience hooks hold after controls, and the testimonial and UGC gaps largely disappear without their biggest concepts. It doesn't show parent creators fail, and peer trust isn't something this file can measure. Keep the parent's voice and pair it with a child enjoying the product (see 'Follow-up checks').

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| creator_type = parent_or_caregiver | cvr | 46 | 2.4% | 3.3% | 2.4% | -11% | Directional |
| hook_driver = personal_experience | cvr | 24 | 2.0% | 3.1% | 1.8% | -23%* | Directional |
| hook_driver = personal_experience | hold_rate | 24 | 21.2% | 26.1% | 22.1% | -10% | Directional |
| proof_used = creator_testimonial | cvr | 19 | 2.3% | 3.0% | 3.0% | -19% | Directional |
| production = ugc | cvr | 23 | 2.2% | 3.0% | 2.8% | -11% | Directional |

### Language matters, but this file can't say why

English ads convert better and regional ones worse. We can't see targeting, so this could be who was shown the ad rather than the language itself. Hinglish, the language of most candidate creators, shows no clear gap on purchases. Don't push creators out of their natural language on this evidence.

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| language = English | cvr | 27 | 3.7% | 2.5% | 3.2% | +45%* | Directional |
| language = regional | cvr | 18 | 1.9% | 3.1% | 2.4% | -35%* | Directional |
| language = regional | hold_rate | 18 | 21.2% | 26.1% | 23.1% | -15%* | Directional |
| language = Hinglish | cvr | 21 | 3.1% | 2.6% | 2.9% | +9% | Inconclusive |

### A clear ask goes with more purchases

Many ads end with no request at all. Asking costs nothing, so every brief should end with one. The buy-now group also holds many of the strongest ads, so the true effect may be smaller than this.

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| cta_type = buy_now | cvr | 41 | 3.3% | 2.2% | 3.1% | +32%* | Directional |

### Popular themes: keep them as the reason to care, not the proof

No evidence either way is different from evidence against, so none of these should be dropped. The brand uses them widely, and growth, immunity and picky eating may well be why parents start looking. Several looked like winners only because LJ-004 carries those labels, and protein's lead falls away without its biggest concepts. So they don't work as the sales proof by themselves. In these ads they do better alongside a child enjoying the product (see 'Follow-up checks'). The science-led route has the least support.

| Pattern | Metric | Concepts | In group | Rest | Without group's 3 largest | After controls | Grade |
|---|---|---:|---:|---:|---:|---:|---|
| story_structure = routine_integration | roas | 20 | 1.23 | 1.24 | 1.00 | -4% | Inconclusive |
| narratives = recipe | roas | 24 | 1.21 | 1.25 | 1.06 | -6% | Inconclusive |
| main_benefit = protein_intake | roas | 16 | 1.82 | 1.11 | 1.20 | +36% | Inconclusive |
| hook_type = story_open | roas | 16 | 1.01 | 1.28 | 0.90 | -8% | Inconclusive |
| persuasion = authority_science | roas | 18 | 0.94 | 1.35 | 1.08 | -29%* | Inconclusive |
| narratives = kids_immunity | roas | 19 | 0.94 | 1.32 | 1.06 | -23% | Inconclusive |

## Follow-up checks after the project owner's review

The project owner cautioned that, in Indian parenting, peer validation builds trust and weak parent ads may reflect hooks or pacing rather than UGC, and that growth, immunity and picky eating are main buying triggers. That is category knowledge, which this file can't confirm or rule out. These checks test what the file can. They were chosen after seeing results and are ungraded, so they're leads, and groups overlap.

### Is it weak hooks or pacing?

| Group | Concepts | Hook rate | Hold rate | CVR | ROAS |
|---|---:|---:|---:|---:|---:|
| Parent-led | 47 | 32.7% | 25.6% | 2.4% | 1.04 |
| Not parent-led | 30 | 30.6% | 24.0% | 3.3% | 1.47 |
| Personal-experience hook | 24 | 33.0% | 21.2% | 2.0% | 0.97 |
| Other hook drivers | 53 | 31.5% | 26.1% | 3.1% | 1.32 |
| UGC | 23 | 32.6% | 26.3% | 2.2% | 0.90 |
| Not UGC | 54 | 31.5% | 24.4% | 3.0% | 1.37 |
| Parent-led, stronger hook | 24 | 36.7% | 25.2% | 2.0% | 0.88 |
| Parent-led, weaker hook | 23 | 24.2% | 26.6% | 3.0% | 1.28 |
| Parent-led, stronger hold | 24 | 33.6% | 28.9% | 2.6% | 1.05 |
| Parent-led, weaker hold | 23 | 31.2% | 19.8% | 2.1% | 1.02 |

Among parent-led concepts, rank correlation with CVR: hook rate -0.46, hold rate +0.19.

Reading: weak hooks don't explain it here. Parent-led ads hook at least as well as others, and those with stronger hooks convert less. Pacing may play a part for personal-story hooks, which hold viewers less well, but better hold goes with only a small gain in parent-led CVR and none in ROAS.

### Do these angles work when paired with a child enjoying the product?

| Group | Concepts | Hook rate | Hold rate | CVR | ROAS |
|---|---:|---:|---:|---:|---:|
| Picky eating, with a child enjoying | 11 | 29.5% | 26.6% | 3.5% | 1.65 |
| Picky eating, without | 15 | 36.3% | 27.9% | 2.0% | 0.83 |
| Recipe, with a child enjoying | 6 | 36.2% | 21.5% | 3.0% | 1.78 |
| Recipe, without | 18 | 35.3% | 27.1% | 2.0% | 0.82 |
| Growth, with a child enjoying | 5 | 33.3% | 24.3% | 3.4% | 1.58 |
| Growth, without | 36 | 31.9% | 22.9% | 2.3% | 0.93 |
| Immunity, with a child enjoying | 2 | 31.1% | 25.1% | 2.3% | 1.22 |
| Immunity, without | 17 | 28.7% | 22.6% | 2.3% | 0.93 |
| Science-led, with a child enjoying | 1 | 27.5% | 21.3% | 4.0% | 1.46 |
| Science-led, without | 17 | 28.2% | 23.8% | 2.4% | 0.87 |
| Parent-led, with a child enjoying | 10 | 31.6% | 25.3% | 2.8% | 1.35 |
| Parent-led, without | 37 | 32.9% | 25.6% | 2.3% | 0.97 |

Reading: in this file, picky eating, recipes, growth and parent-led ads all do better when paired with a child enjoying the product. Immunity and science have too few such ads to tell. A few large ads sit behind several of these groups, and pairing was never tested on purpose, so the first campaign should test it.


## Where the money went

Rank correlations across concepts: spend and hook rate +0.38, spend and ROAS -0.09, hook rate and CVR -0.33. Spend follows attention, not return, so high spend isn't proof that an ad worked.

## By product line

Without LJ-004, which is a Proteinmix ad. Moms' and teen products are outside this analysis.

| Product line | Concepts | Spend (₹) | Hook rate | CTR | CVR | ROAS | Median ROAS |
|---|---:|---:|---:|---:|---:|---:|---:|
| nutrimix_kids | 33 | 2,635,358 | 32.1% | 0.95% | 3.0% | 1.38 | 1.18 |
| proteinmix | 14 | 1,280,815 | 35.7% | 0.94% | 2.7% | 1.23 | 0.96 |
| gummies_kids | 16 | 1,015,772 | 30.4% | 0.84% | 2.4% | 0.87 | 0.86 |
| combo_kit | 6 | 487,467 | 25.1% | 1.15% | 3.0% | 1.27 | 1.27 |
| breakfast_mixes | 4 | 300,195 | 24.1% | 0.89% | 3.9% | 1.57 | 1.79 |
| spreads_condiments | 4 | 149,219 | 35.9% | 1.18% | 1.2% | 0.86 | 0.84 |

## Supported

No pattern met this grade.

## Directional

| Pattern | Stage | Concepts | In group | Rest | Gap without LJ-004 | 95% interval | After controls | p | q | Ads (largest first) |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| child_in_first_3s = yes | attention | 33 | 35.5% | 26.7% | +8.8 pts | +4.8 pts to +12.3 pts | +21%* | 0.0003 | 0.11 | LJ-069 | LJ-089 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 |
| language = Hindi | attention | 5 | 41.6% | 30.2% | +11.4 pts | +3.9 pts to +14.6 pts | +44%* | 0.0004 | 0.11 | LJ-069 | LJ-014 | LJ-031; LJ-032 | LJ-082 | LJ-094 |
| persuasion = storytelling | attention | 42 | 34.7% | 26.5% | +8.2 pts | +4.2 pts to +11.3 pts | +18%* | 0.0008 | 0.15 | LJ-069 | LJ-089 | LJ-097; LJ-006 | LJ-008; LJ-078 | LJ-009 |
| language_mixing = occasional_borrowing | attention | 46 | 34.1% | 26.4% | +7.7 pts | +3.4 pts to +11.3 pts | +19%* | 0.0061 | 0.31 | LJ-069 | LJ-089 | LJ-035; LJ-055 | LJ-008; LJ-078 | LJ-051 |
| hook_type = question | attention | 25 | 25.9% | 33.5% | -7.6 pts | -10.6 pts to -3.9 pts | -11% | 0.0094 | 0.31 | LJ-063 | LJ-080 | LJ-095 | LJ-033; LJ-092; LJ-057 | LJ-052 |
| persuasion = contrast_with_competitors | attention | 18 | 25.3% | 33.1% | -7.8 pts | -12.2 pts to -3.3 pts | -18%* | 0.0143 | 0.35 | LJ-051 | LJ-021 | LJ-033; LJ-092; LJ-057 | LJ-084 | LJ-085 |
| performance_style = earnest_talk | attention | 15 | 24.3% | 32.6% | -8.3 pts | -12.0 pts to -4.2 pts | -15% | 0.0144 | 0.35 | LJ-021 | LJ-033; LJ-092; LJ-057 | LJ-052 | LJ-086 | LJ-010 |
| first_frame = child | attention | 13 | 37.5% | 29.9% | +7.6 pts | +0.9 pts to +11.1 pts | +14% | 0.0148 | 0.35 | LJ-069 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-040 |
| persuasion = fear_appeal | attention | 9 | 38.0% | 30.6% | +7.4 pts | -5.7 pts to +11.1 pts | +1% | 0.0150 | 0.35 | LJ-069 | LJ-047 | LJ-019; LJ-091 | LJ-040 | LJ-028 |
| ad_format = explainer_to_camera | attention | 18 | 25.4% | 33.1% | -7.7 pts | -12.1 pts to -3.4 pts | -18%* | 0.0213 | 0.38 | LJ-051 | LJ-021 | LJ-033; LJ-092; LJ-057 | LJ-036; LJ-056; LJ-071 | LJ-018; LJ-079 |
| persuasion = statistics_specificity | attention | 29 | 27.3% | 33.1% | -5.8 pts | -9.9 pts to -1.3 pts | -10% | 0.0230 | 0.38 | LJ-081; LJ-050 | LJ-021 | LJ-036; LJ-056; LJ-071 | LJ-020 | LJ-086 |
| narratives = label_check | attention | 17 | 25.7% | 33.1% | -7.4 pts | -11.7 pts to -2.9 pts | -16%* | 0.0266 | 0.40 | LJ-063 | LJ-051 | LJ-033; LJ-092; LJ-057 | LJ-052 | LJ-084 |
| humour = any | attention | 15 | 36.7% | 29.7% | +7.0 pts | +2.7 pts to +11.4 pts | +30%* | 0.0317 | 0.44 | LJ-089 | LJ-008; LJ-078 | LJ-009 | LJ-081; LJ-050 | LJ-014 |
| language = English | attention | 27 | 27.8% | 32.9% | -5.1 pts | -9.9 pts to -0.5 pts | -13% | 0.0347 | 0.45 | LJ-097; LJ-006 | LJ-080 | LJ-021 | LJ-033; LJ-092; LJ-057 | LJ-036; LJ-056; LJ-071 |
| hook_type = story_open | attention | 17 | 35.9% | 30.5% | +5.5 pts | +0.0 pts to +9.9 pts | +17%* | 0.0404 | 0.45 | LJ-089 | LJ-081; LJ-050 | LJ-014 | LJ-044 | LJ-003; LJ-059 |
| child_role = speaks | interest | 18 | 1.1% | 0.9% | +0.2 pts | +0.1 pts to +0.3 pts | +25%* | 0.0039 | 0.31 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-014 |
| story_structure = problem_agitate_solve | interest | 23 | 0.8% | 1.0% | -0.2 pts | -0.2 pts to -0.0 pts | -9% | 0.0370 | 0.45 | LJ-069 | LJ-021 | LJ-095 | LJ-020 | LJ-086 |
| persuasion = contrast_with_competitors | interest | 18 | 0.8% | 1.0% | -0.2 pts | -0.3 pts to -0.0 pts | -14%* | 0.0416 | 0.45 | LJ-051 | LJ-021 | LJ-033; LJ-092; LJ-057 | LJ-084 | LJ-085 |
| persuasion = fear_appeal | interest | 9 | 0.8% | 1.0% | -0.2 pts | -0.3 pts to -0.1 pts | -13% | 0.0455 | 0.45 | LJ-069 | LJ-047 | LJ-019; LJ-091 | LJ-040 | LJ-028 |
| narratives = taste_better_than_other_brands | interest | 25 | 1.0% | 0.9% | +0.1 pts | +0.0 pts to +0.3 pts | +10% | 0.0459 | 0.45 | LJ-089 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 |
| production = ugc | purchase | 23 | 2.2% | 3.0% | -0.9 pts | -1.6 pts to +0.0 pts | -11% | 0.0043 | 0.31 | LJ-069 | LJ-063 | LJ-044 | LJ-086 | LJ-018; LJ-079 |
| demo_shown = taste_test | purchase | 17 | 3.5% | 2.3% | +1.2 pts | +0.4 pts to +1.8 pts | +37%* | 0.0075 | 0.31 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-080 |
| cta_type = buy_now | purchase | 41 | 3.3% | 2.2% | +1.2 pts | +0.4 pts to +1.8 pts | +32%* | 0.0078 | 0.31 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-051 | LJ-081; LJ-050 | LJ-080 |
| production = semi_pro | purchase | 45 | 3.1% | 2.2% | +0.9 pts | +0.1 pts to +1.5 pts | +7% | 0.0177 | 0.37 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-051 | LJ-009 | LJ-081; LJ-050 |
| creator_type = parent_or_caregiver | purchase | 46 | 2.4% | 3.3% | -0.9 pts | -1.6 pts to -0.0 pts | -11% | 0.0180 | 0.37 | LJ-069 | LJ-063 | LJ-021 | LJ-014 | LJ-044 |
| creator_type = multiple | purchase | 9 | 3.9% | 2.6% | +1.2 pts | +0.1 pts to +1.8 pts | +25% | 0.0217 | 0.38 | LJ-035; LJ-055 | LJ-080 | LJ-033; LJ-092; LJ-057 | LJ-052 | LJ-084 |
| language = English | purchase | 27 | 3.7% | 2.5% | +1.2 pts | +0.4 pts to +1.8 pts | +45%* | 0.0222 | 0.38 | LJ-097; LJ-006 | LJ-080 | LJ-021 | LJ-033; LJ-092; LJ-057 | LJ-036; LJ-056; LJ-071 |
| hook_driver = personal_experience | purchase | 24 | 2.0% | 3.1% | -1.1 pts | -1.8 pts to -0.3 pts | -23%* | 0.0241 | 0.38 | LJ-081; LJ-050 | LJ-014 | LJ-044 | LJ-003; LJ-059 | LJ-096 |
| captions = minimal | purchase | 21 | 3.5% | 2.4% | +1.1 pts | +0.2 pts to +1.7 pts | +21% | 0.0241 | 0.38 | LJ-035; LJ-055 | LJ-063 | LJ-097; LJ-006 | LJ-009 | LJ-031; LJ-032 |
| proof_used = creator_testimonial | purchase | 19 | 2.3% | 3.0% | -0.7 pts | -1.4 pts to +0.7 pts | -19% | 0.0279 | 0.41 | LJ-069 | LJ-021 | LJ-047 | LJ-086 | LJ-018; LJ-079 |
| language = regional | purchase | 18 | 1.9% | 3.1% | -1.2 pts | -1.9 pts to -0.3 pts | -35%* | 0.0308 | 0.44 | LJ-008; LJ-078 | LJ-044 | LJ-003; LJ-059 | LJ-096 | LJ-047 |
| creator_gender = multiple | purchase | 8 | 3.9% | 2.6% | +1.2 pts | -0.0 pts to +1.8 pts | +22% | 0.0367 | 0.45 | LJ-035; LJ-055 | LJ-080 | LJ-033; LJ-092; LJ-057 | LJ-052 | LJ-038 |
| narratives = taste_better_than_other_brands | purchase | 24 | 3.3% | 2.4% | +0.9 pts | -0.0 pts to +1.6 pts | +27% | 0.0398 | 0.45 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-021 |
| creator_gender = female | purchase | 49 | 2.3% | 3.2% | -0.9 pts | -1.5 pts to -0.0 pts | -8% | 0.0446 | 0.45 | LJ-069 | LJ-021 | LJ-014 | LJ-044 | LJ-003; LJ-059 |
| language_mixing = occasional_borrowing | purchase | 45 | 2.5% | 3.4% | -1.0 pts | -1.6 pts to -0.2 pts | -25%* | 0.0452 | 0.45 | LJ-069 | LJ-035; LJ-055 | LJ-008; LJ-078 | LJ-051 | LJ-009 |
| audio = on_camera_speech | purchase | 19 | 3.4% | 2.4% | +1.0 pts | +0.1 pts to +1.7 pts | +19% | 0.0478 | 0.46 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-051 | LJ-081; LJ-050 | LJ-080 |
| narratives = fussy_eating | retention | 26 | 27.4% | 22.7% | +4.7 pts | +1.6 pts to +6.8 pts | +18%* | 0.0096 | 0.31 | LJ-069 | LJ-089 | LJ-035; LJ-055 | LJ-080 | LJ-021 |
| hook_driver = personal_experience | retention | 24 | 21.2% | 26.1% | -5.0 pts | -7.1 pts to -2.0 pts | -10% | 0.0116 | 0.33 | LJ-081; LJ-050 | LJ-014 | LJ-044 | LJ-003; LJ-059 | LJ-096 |
| language = regional | retention | 18 | 21.2% | 26.1% | -4.9 pts | -7.4 pts to -1.4 pts | -15%* | 0.0164 | 0.36 | LJ-008; LJ-078 | LJ-044 | LJ-003; LJ-059 | LJ-096 | LJ-047 |
| main_benefit = fussy_eating | retention | 12 | 28.3% | 23.5% | +4.9 pts | +2.2 pts to +6.7 pts | +18%* | 0.0210 | 0.38 | LJ-069 | LJ-089 | LJ-021 | LJ-095 | LJ-086 |
| captions = bold_subtitles | retention | 19 | 28.0% | 24.1% | +3.9 pts | +1.4 pts to +6.0 pts | +16%* | 0.0251 | 0.39 | LJ-069 | LJ-036; LJ-056; LJ-071 | LJ-052 | LJ-017 | LJ-084 |
| persuasion = social_proof | retention | 5 | 29.3% | 24.1% | +5.2 pts | +2.2 pts to +7.3 pts | +12%* | 0.0421 | 0.45 | LJ-089 | LJ-035; LJ-055 | LJ-036; LJ-056; LJ-071 | LJ-067 | LJ-098 |
| language = Hinglish | retention | 22 | 26.8% | 23.9% | +2.9 pts | -0.8 pts to +6.1 pts | +15%* | 0.0443 | 0.45 | LJ-089 | LJ-035; LJ-055 | LJ-063 | LJ-051 | LJ-009 |
| brand_said_aloud = yes | retention | 53 | 24.0% | 27.2% | -3.2 pts | -5.8 pts to +0.4 pts | -16%* | 0.0446 | 0.45 | LJ-089 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-008; LJ-078 | LJ-051 |
| demo_shown = taste_test | return | 17 | 1.78 | 0.93 | +0.86 | +0.41 to +1.15 | +67%* | 0.0022 | 0.30 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-080 |
| child_role = reacts_to_taste | return | 32 | 1.57 | 0.85 | +0.72 | +0.33 to +1.01 | +56%* | 0.0049 | 0.31 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-080 |
| production = semi_pro | return | 45 | 1.44 | 0.88 | +0.56 | +0.16 to +0.88 | +22% | 0.0096 | 0.31 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-051 | LJ-009 | LJ-081; LJ-050 |
| child_role = consumes_product | return | 43 | 1.52 | 0.83 | +0.69 | +0.32 to +0.97 | +46%* | 0.0096 | 0.31 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-080 |
| captions = minimal | return | 21 | 1.72 | 1.03 | +0.69 | +0.04 to +1.13 | +31% | 0.0103 | 0.32 | LJ-035; LJ-055 | LJ-063 | LJ-097; LJ-006 | LJ-009 | LJ-031; LJ-032 |
| narratives = taste_better_than_other_brands | return | 24 | 1.61 | 0.96 | +0.65 | +0.18 to +0.99 | +41%* | 0.0120 | 0.33 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-021 |
| production = ugc | return | 23 | 0.90 | 1.37 | -0.47 | -0.79 to -0.00 | -15% | 0.0227 | 0.38 | LJ-069 | LJ-063 | LJ-044 | LJ-086 | LJ-018; LJ-079 |
| child_role = speaks | return | 18 | 1.61 | 1.03 | +0.58 | +0.05 to +0.98 | +41%* | 0.0400 | 0.45 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-014 |
| demo_shown = child_consuming | return | 44 | 1.46 | 0.86 | +0.60 | +0.20 to +0.91 | +42%* | 0.0447 | 0.45 | LJ-035; LJ-055 | LJ-097; LJ-006 | LJ-008; LJ-078 | LJ-009 | LJ-081; LJ-050 |

## False leads

These look like winners with LJ-004 included (ROAS lead of at least 1.0) but fail the checks.

| Pattern | Concepts | ROAS gap with LJ-004 | Without LJ-004 | Median gap | p |
|---|---:|---:|---:|---:|---:|
| main_benefit = protein_intake | 16 | +1.99 | +0.71 | +0.15 | 0.065 |
| language_mixing = sentence_level_switching | 9 | +1.67 | -0.08 | -0.01 | 0.864 |
| persuasion = statistics_specificity | 29 | +1.43 | +0.13 | +0.20 | 0.880 |
| story_structure = routine_integration | 20 | +1.37 | -0.01 | +0.13 | 0.831 |
| hook_type = story_open | 16 | +1.34 | -0.27 | -0.31 | 0.352 |
| first_frame = child | 13 | +1.28 | +0.15 | +0.12 | 0.761 |
| hook_driver = curiosity_gap | 26 | +1.22 | +0.20 | +0.09 | 0.438 |
| demo_shown = live_use | 13 | +1.21 | -0.10 | -0.28 | 0.826 |
| cta_type = buy_now | 41 | +1.13 | +0.49 | +0.26 | 0.057 |
| language = Hinglish | 21 | +1.13 | +0.18 | -0.15 | 0.201 |
| narratives = recipe | 24 | +1.04 | -0.04 | -0.04 | 0.736 |
| performance_style = demo_walkthrough | 20 | +1.02 | -0.25 | +0.24 | 0.258 |

## Too few concepts to grade

Fewer than 5 concepts, not counting LJ-004, so these got no test. The figures are description only.

| Pattern | Concepts | Spend (₹) | ROAS without LJ-004 | ROAS with LJ-004 | Median ROAS | Ads |
|---|---:|---:|---:|---:|---:|---|
| ad_format = child_led | 4 | 719,005 | 2.06 | 3.47 | 1.74 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-042 |
| creator_type = child_presenter | 4 | 719,005 | 2.06 | 3.47 | 1.74 | LJ-097; LJ-006 | LJ-009 | LJ-081; LJ-050 | LJ-042 |
| hook_type = educational_explainer | 3 | 572,510 | 1.65 | 1.65 | 0.64 | LJ-097; LJ-006 | LJ-008; LJ-078 | LJ-011 |
| main_benefit = taste | 4 | 551,989 | 1.90 | 1.90 | 1.45 | LJ-035; LJ-055 | LJ-036; LJ-056; LJ-071 | LJ-053 | LJ-060 |
| proof_used = customer_review | 3 | 515,385 | 1.96 | 1.96 | 1.63 | LJ-035; LJ-055 | LJ-036; LJ-056; LJ-071 | LJ-067 |
| setting = outdoor | 3 | 494,766 | 1.85 | 1.85 | 0.83 | LJ-035; LJ-055 | LJ-084 | LJ-067 |
| hook_driver = social_proof | 2 | 429,385 | 2.02 | 2.02 | 1.46 | LJ-035; LJ-055 | LJ-067 |
| story_structure = testimonial_review | 2 | 429,385 | 2.02 | 2.02 | 1.46 | LJ-035; LJ-055 | LJ-067 |
| hook_type = bold_claim | 2 | 428,857 | 2.06 | 2.06 | 1.79 | LJ-035; LJ-055 | LJ-065 |
| proof_used = scientific_lab_visuals | 4 | 422,790 | 0.75 | 0.75 | 0.79 | LJ-008; LJ-078 | LJ-033; LJ-092; LJ-057 | LJ-040 | LJ-024 |
| story_structure = science_explainer | 3 | 351,047 | 0.74 | 0.74 | 0.64 | LJ-008; LJ-078 | LJ-033; LJ-092; LJ-057 | LJ-011 |
| hook_type = pattern_interrupt | 2 | 282,872 | 0.94 | 0.94 | 1.13 | LJ-051 | LJ-036; LJ-056; LJ-071 |
| creator_type = professional_presenter | 2 | 282,872 | 0.94 | 0.94 | 1.13 | LJ-051 | LJ-036; LJ-056; LJ-071 |
| proof_used = lab_tested_certified | 4 | 253,934 | 0.93 | 0.93 | 0.93 | LJ-033; LJ-092; LJ-057 | LJ-052 | LJ-085 | LJ-042 |
| persuasion = certification_endorsement | 4 | 253,934 | 0.93 | 0.93 | 0.93 | LJ-033; LJ-092; LJ-057 | LJ-052 | LJ-085 | LJ-042 |
| main_benefit = problem_solution | 4 | 245,765 | 0.88 | 0.88 | 0.82 | LJ-019; LJ-091 | LJ-018; LJ-079 | LJ-085 | LJ-040 |
| performance_style = myth_busting | 3 | 142,696 | 1.04 | 1.04 | 0.89 | LJ-084 | LJ-061; LJ-100 | LJ-024 |
| story_structure = myth_busting | 3 | 142,696 | 1.04 | 1.04 | 0.89 | LJ-084 | LJ-061; LJ-100 | LJ-024 |
| language_mixing = constant_switching | 2 | 133,431 | 0.82 | 0.82 | 0.82 | LJ-018; LJ-079 | LJ-085 |
| cta_type = social_interface_referral | 2 | 133,101 | 0.80 | 0.80 | 1.01 | LJ-003; LJ-059 | LJ-013 |
| first_frame = scene | 4 | 131,010 | 0.70 | 0.70 | 0.89 | LJ-052 | LJ-090 | LJ-070 | LJ-058 |
| captions = caption_heavy | 2 | 130,717 | 0.74 | 0.74 | 1.07 | LJ-047 | LJ-087 |
| narratives = brand_milk_vs_regular_milk | 2 | 119,760 | 1.28 | 1.28 | 1.32 | LJ-085 | LJ-010 |
| creator_type = peer_reviewer | 2 | 101,461 | 0.84 | 0.84 | 0.85 | LJ-085 | LJ-024 |
| main_benefit = functional | 3 | 94,176 | 1.22 | 1.22 | 1.08 | LJ-029 | LJ-062 | LJ-028 |
| first_frame = text | 2 | 85,030 | 1.09 | 1.09 | 1.07 | LJ-019; LJ-091 | LJ-002 |
| hook_type = result_reveal | 2 | 83,188 | 1.01 | 1.01 | 1.12 | LJ-090 | LJ-076 |
| hook_type = direct_product | 2 | 55,613 | 0.78 | 0.78 | 1.11 | LJ-022 | LJ-083 |
| creator_type = silent_model | 2 | 41,456 | 1.39 | 1.39 | 1.38 | LJ-065 | LJ-060 |
| child_role = shows_result | 2 | 41,048 | 1.37 | 1.37 | 1.31 | LJ-041 | LJ-002 |
| ad_format = podcast_interview | 3 | 32,593 | 1.30 | 1.30 | 2.16 | LJ-067 | LJ-030 | LJ-072 |
| story_structure = straight_pitch | 2 | 18,637 | 1.27 | 1.27 | 1.36 | LJ-060 | LJ-083 |
| persuasion = empties_restock_narrative | 2 | 16,742 | 1.15 | 1.15 | 1.43 | LJ-034 | LJ-016 |
| cta_type = comment_for_link | 3 | 14,692 | 1.07 | 1.07 | 1.03 | LJ-027 | LJ-094 | LJ-039 |
| narratives = mom_research_about_product | 2 | 8,948 | 2.55 | 2.55 | 2.58 | LJ-030 | LJ-072 |

## How far near-copies differ

ROAS for ads from the same concept. Gaps of this size between two individual ads can arise with no real creative difference, though some of these ads are re-cuts or translations, so this is an upper guide rather than pure noise.

| Concept | Ads | ROAS range | Ratio |
|---|---|---|---:|
| nutrimix_batman_boy_protein | LJ-050, LJ-081 | 0.89 to 2.74 | 3.09x |
| nutrimix_label_table | LJ-033, LJ-057, LJ-092 | 0.82 to 1.40 | 1.72x |
| moms_gummies_vitamins | LJ-073, LJ-093 | 0.78 to 1.27 | 1.63x |
| proteinmix_pancake_taste_test | LJ-036, LJ-056, LJ-071 | 1.42 to 2.30 | 1.62x |
| proteinmix_waffle_boy | LJ-006, LJ-097 | 1.63 to 2.57 | 1.57x |
| pancake_mix_kitchen_demo | LJ-018, LJ-079 | 0.75 to 1.13 | 1.50x |
| nutrimix_bone_animation | LJ-008, LJ-078 | 0.52 to 0.77 | 1.47x |
| spreads_school_skit | LJ-003, LJ-059 | 0.58 to 0.78 | 1.34x |
| nutrimix_calcium_signs | LJ-019, LJ-091 | 1.05 to 1.29 | 1.23x |
| nutrimix_kids_milkshake_voxpop | LJ-035, LJ-055 | 2.06 to 2.48 | 1.21x |
| proteinmix_three_myths | LJ-061, LJ-100 | 1.42 to 1.68 | 1.18x |
| gummies_look_what_i_have_skit | LJ-031, LJ-032 | 0.86 to 0.97 | 1.12x |

## Effect of label corrections

5 labels were corrected after video review. With the system's labels left as they were, 15 of 563 grades differ.

| Pattern | Metric | Grade | With uncorrected labels |
|---|---|---|---|
| ad_format = child_led | ctr | Too few to test | Directional |
| ad_format = child_led | cvr | Too few to test | Inconclusive |
| ad_format = child_led | hold_rate | Too few to test | Inconclusive |
| ad_format = child_led | hook_rate | Too few to test | Inconclusive |
| ad_format = child_led | roas | Too few to test | Directional |
| ad_format = silent_brand_film | ctr | Inconclusive | Too few to test |
| ad_format = silent_brand_film | cvr | Inconclusive | Too few to test |
| ad_format = silent_brand_film | hold_rate | Inconclusive | Too few to test |
| ad_format = silent_brand_film | hook_rate | Inconclusive | Too few to test |
| ad_format = silent_brand_film | roas | Inconclusive | Too few to test |
| creator_type = child_presenter | ctr | Too few to test | Directional |
| creator_type = child_presenter | cvr | Too few to test | Inconclusive |
| creator_type = child_presenter | hold_rate | Too few to test | Inconclusive |
| creator_type = child_presenter | hook_rate | Too few to test | Inconclusive |
| creator_type = child_presenter | roas | Too few to test | Directional |
