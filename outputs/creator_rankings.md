# Creator ranking

The score measures how well each creator fits what the brand's own ads suggest sells. It does not predict sales: nothing in the data links a creator to a purchase. The weights are judgment, so the ranking is tested against 5,000 random weightings and six named ones.

## Top five under each competitor rule

Whether recent work for a rival rules a creator out is a business decision, so all three versions are shown. The main answer uses the first. Change `COMPETITOR_RULE` in `src/lj/config.py` to switch.

| Competitor rule | Eligible | Top five |
|---|---:|---|
| Strict: any recent rival rules a creator out **(main answer)** | 6 | `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu`, `foodies_by_neha` |
| Challenger rivals rule out; mass brands only flagged | 7 | `instamommy_suchi`, `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu` |
| Nobody ruled out; competitor work flagged | 10 | `sia_3vedi`, `raja_choudhary04`, `instamommy_suchi`, `the_mum_wife_playbook`, `doc_mama_and_babies` |

**Recent rival work (last 90 days, all paid partnerships):**

- `ekamichildcare`: Troovy (07 Sep) (challenger)
- `sia_3vedi`: Gritzo (28 Sep) (challenger)
- `doc_mama_and_babies`: Good Monk (08 Sep) (challenger)
- `couple_adishiv`: Gritzo (06 Sep) (challenger)
- `raja_choudhary04`: Gritzo (31 Aug); Troovy Foods (07 Oct) (challenger)
- `instamommy_suchi`: Bournvita (02 Aug); Complan (06 Oct) (mass brand only)

## How it works

1. **Gates (yes/no).** Children on camera are mostly at or above the product's starting age, or the feed speaks to parents of school-age children; the feed is about family or food, and measured audience (where we have it) isn't mostly men; and the creator posted in the last 90 days.
2. **Competitor rule**, as above.
3. **Score (0 to 100)** from five criteria, each on a 0 to 1 scale:

| Criterion | Weight | How it's measured |
|---|---:|---|
| Can show a child enjoying the product | 30% | Already seen on camera = full marks, plausible = 0.6, unlikely without a new format = 0.1 |
| Children the right age, food in the feed | 25% | 60% from child age fit, 40% from the share of posts about food (30% or more = full marks) |
| Typical organic plays | 20% | Median plays on unpaid videos, on a log scale from 10k (0) to 3.2M (full marks). Under 5 unpaid videos uses all videos; none at all caps it at half |
| Feed not saturated with ads | 15% | Full marks up to 35% paid posts, falling to zero at 100% |
| Profile matches the posts | 10% | Matches = full marks, partly = half |

The child moment carries the most weight because it is the strongest sales signal in the brand's ads.

**Not in the score, on purpose:** likes and comments. Likes are hidden on some accounts, comment-for-link captions inflate comments, and some creators switch comments off, so plays are the only engagement signal that holds up. Audience data exists for 3 of 20 creators, so it acts as a check (a measured audience that is mostly men fails the gates) and lowers confidence when missing, rather than scoring 17 creators on nothing.

**Stability** is the share of random weightings under which a creator makes the top 5: Firm (80% or more), Likely (50 to 79%), Close call (20 to 49%), Rarely (under 20%). In a small pool most eligible creators make the top 5 by construction, so a high share there says little. The useful question is who drops out, and how far apart the scores are.

## All 20 creators

| Creator | Gates | Recent rival work | Score | Rank: strict | Rank: challengers only | Rank: flag only | Stability (main) | Confidence |
|---|---|---|---:|---:|---:|---:|---|---|
| `the_mum_wife_playbook` | Pass | No | 75 | 1 | 2 | 4 | Firm (98%) | Medium |
| `hello_ps8` | Pass | No | 70 | 2 | 3 | 6 | Firm (100%) | Medium |
| `ohmother.in` | Pass | No | 67 | 3 | 4 | 7 | Firm (99%) | Low |
| `mumma_and_ridhu` | Pass | No | 58 | 4 | 5 | 8 | Firm (99%) | Low |
| `foodies_by_neha` | Pass | No | 56 | 5 | 6 | 9 | Firm (89%) | Low |
| `radhikabansal0908` | Pass | No | 46 | 6 | 7 | 10 | Rarely (14%) | Low |
| `sia_3vedi` | Pass | Gritzo (28 Sep) | 92 |  |  | 1 |  | High |
| `raja_choudhary04` | Pass | Gritzo (31 Aug); Troovy Foods (07 Oct) | 91 |  |  | 2 |  | High |
| `storiesbyvihaa` | Fail: measured audience is 70% men | No | 80 |  |  |  |  | High |
| `instamommy_suchi` | Pass | Bournvita (02 Aug); Complan (06 Oct) | 78 |  | 1 | 3 |  | Medium |
| `doc_mama_and_babies` | Pass | Good Monk (08 Sep) | 73 |  |  | 5 |  | Medium |
| `couple_adishiv` | Fail: children shown are mostly under the product's starting age | Gritzo (06 Sep) | 61 |  |  |  |  | Medium |
| `ekamichildcare` | Fail: most children shown are under the product's starting age | Troovy (07 Sep) | 49 |  |  |  |  | Medium |
| `thatkushalmistry` | Fail: no children on camera; feed isn't about family or food | No | 48 |  |  |  |  | Medium |
| `livesimply_withkripa` | Fail: only teenagers on camera | No | 46 |  |  |  |  | Medium |
| `drgarima_mehta` | Fail: children shown are mostly under the product's starting age | No | 45 |  |  |  |  | Medium |
| `parentingtips_surat` | Fail: most children shown are under the product's starting age | No | 44 |  |  |  |  | High |
| `paediatrics_decoded` | Fail: children shown are mostly under the product's starting age | No | 40 |  |  |  |  | Medium |
| `tej.lil.diary` | Fail: children shown are mostly under the product's starting age | No | 38 |  |  |  |  | Medium |
| `raising_zohran` | Fail: children shown are mostly under the product's starting age | No | 24 |  |  |  |  | Low |

## Score breakdown for eligible creators

| Creator | Can show a child enjoying the product | Children the right age, food in the feed | Typical organic plays | Feed not saturated with ads | Profile matches the posts | Plays used for reach |
|---|---:|---:|---:|---:|---:|---|
| `sia_3vedi` | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 4,242,421 (organic) |
| `raja_choudhary04` | 1.00 | 1.00 | 0.56 | 1.00 | 1.00 | 256,671 (organic) |
| `instamommy_suchi` | 1.00 | 0.87 | 0.79 | 0.38 | 0.50 | 925,519 (all videos (few organic)) |
| `the_mum_wife_playbook` | 1.00 | 0.62 | 0.23 | 1.00 | 1.00 | 37,857 (organic) |
| `doc_mama_and_babies` | 1.00 | 0.84 | 0.54 | 0.42 | 0.50 | 227,438 (all videos (few organic)) |
| `hello_ps8` | 0.60 | 0.67 | 0.75 | 1.00 | 0.50 | 731,154 (organic) |
| `ohmother.in` | 0.60 | 0.74 | 0.27 | 1.00 | 1.00 | 47,408 (organic) |
| `mumma_and_ridhu` | 0.60 | 0.67 | 0.45 | 0.62 | 0.50 | 131,978 (all videos (few organic)) |
| `foodies_by_neha` | 0.10 | 0.70 | 0.53 | 1.00 | 1.00 | 211,809 (organic) |
| `radhikabansal0908` | 0.60 | 0.50 | 0.50 | 0.00 | 0.50 | 1,023,759 (all videos (no organic)) |

## Named weightings

| Weighting | Strict: any recent rival rules a creator out | Challenger rivals rule out; mass brands only flagged | Nobody ruled out; competitor work flagged |
|---|---|---|---|
| Default | `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu`, `foodies_by_neha` | `instamommy_suchi`, `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu` | `sia_3vedi`, `raja_choudhary04`, `instamommy_suchi`, `the_mum_wife_playbook`, `doc_mama_and_babies` |
| Equal weights | `the_mum_wife_playbook`, `ohmother.in`, `hello_ps8`, `foodies_by_neha`, `mumma_and_ridhu` | `the_mum_wife_playbook`, `ohmother.in`, `instamommy_suchi`, `hello_ps8`, `foodies_by_neha` | `sia_3vedi`, `raja_choudhary04`, `the_mum_wife_playbook`, `ohmother.in`, `instamommy_suchi` |
| Reach first | `hello_ps8`, `the_mum_wife_playbook`, `ohmother.in`, `foodies_by_neha`, `mumma_and_ridhu` | `instamommy_suchi`, `hello_ps8`, `the_mum_wife_playbook`, `ohmother.in`, `foodies_by_neha` | `sia_3vedi`, `raja_choudhary04`, `instamommy_suchi`, `hello_ps8`, `doc_mama_and_babies` |
| Fit first | `the_mum_wife_playbook`, `ohmother.in`, `hello_ps8`, `mumma_and_ridhu`, `radhikabansal0908` | `instamommy_suchi`, `the_mum_wife_playbook`, `ohmother.in`, `hello_ps8`, `mumma_and_ridhu` | `raja_choudhary04`, `sia_3vedi`, `instamommy_suchi`, `doc_mama_and_babies`, `the_mum_wife_playbook` |
| Ignore reach | `the_mum_wife_playbook`, `ohmother.in`, `hello_ps8`, `mumma_and_ridhu`, `foodies_by_neha` | `the_mum_wife_playbook`, `ohmother.in`, `instamommy_suchi`, `hello_ps8`, `mumma_and_ridhu` | `raja_choudhary04`, `sia_3vedi`, `the_mum_wife_playbook`, `ohmother.in`, `instamommy_suchi` |
| Trust first | `the_mum_wife_playbook`, `ohmother.in`, `hello_ps8`, `foodies_by_neha`, `mumma_and_ridhu` | `the_mum_wife_playbook`, `ohmother.in`, `instamommy_suchi`, `hello_ps8`, `foodies_by_neha` | `sia_3vedi`, `raja_choudhary04`, `the_mum_wife_playbook`, `ohmother.in`, `instamommy_suchi` |

## Removing one criterion at a time (main answer)

| Without | Top 5 |
|---|---|
| Can show a child enjoying the product | `foodies_by_neha`, `hello_ps8`, `ohmother.in`, `the_mum_wife_playbook`, `mumma_and_ridhu` |
| Children the right age, food in the feed | `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu`, `foodies_by_neha` |
| Typical organic plays | `the_mum_wife_playbook`, `ohmother.in`, `hello_ps8`, `mumma_and_ridhu`, `foodies_by_neha` |
| Feed not saturated with ads | `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu`, `radhikabansal0908` |
| Profile matches the posts | `the_mum_wife_playbook`, `hello_ps8`, `ohmother.in`, `mumma_and_ridhu`, `foodies_by_neha` |

## Checks

- Rank correlation between score and followers among gate-passing creators: +0.07. The score isn't just following audience size.
- Confidence is separate from fit. It counts six kinds of evidence: enough organic videos, transcripts, reach that isn't one viral post, a child already seen enjoying food on camera, a confirmed child age, and real audience data. High is 5 or 6, Medium 4, Low 3 or fewer.

## Confidence gaps for the main five

| Creator | Confidence | What we don't have |
|---|---|---|
| `the_mum_wife_playbook` | Medium | child's age confirmed; real audience data |
| `hello_ps8` | Medium | child enjoying food already seen; real audience data |
| `ohmother.in` | Low | reach not one viral post; child enjoying food already seen; real audience data |
| `mumma_and_ridhu` | Low | enough organic videos; reach not one viral post; child enjoying food already seen; real audience data |
| `foodies_by_neha` | Low | enough organic videos; reach not one viral post; child enjoying food already seen; real audience data |
