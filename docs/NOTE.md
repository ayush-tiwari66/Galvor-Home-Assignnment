# Note: key choices and what comes next

The answer is in [REPORT.md](../REPORT.md).

## Key choices

**The score measures fit, not future sales.** No ad says which creator made it, so nothing links a creator to a purchase. The one exception, LJ-039, spent ₹3,101. So the ranking says who fits what the brand's ads suggest sells, and every pick ships as a paid test with stop and scale rules.

**Clean before learning.** LJ-004 brings in 29% of purchases on 9% of spend, and LJ-089 shows 1,544 add-to-carts with zero purchases. Either could decide the findings alone, so LJ-004 is set aside and LJ-089's purchases are treated as missing. Re-cuts and translations of one ad count once.

**Fix the bar before seeing results.** Of 553 pattern tests, none reached the top grade, and we didn't lower it. The briefs rest on the patterns that held across five views of the data, chiefly a child visibly enjoying the product.

**Weight that moment above follower count.** In the ads, spend followed attention rather than return. The three biggest accounts are a comedian with no children on camera, a child account with recent Gritzo work, and an audience that is 70% men. Reach still counts, as median organic plays.

**Pass/fail checks, then a score.** A weighted sum would let reach cancel out a feed of babies too young for the product. Creators first pass yes/no checks. The ranking is re-run under 5,000 random weightings to show which slots are firm.

**Leave out signals that don't hold up.** Likes are hidden on some accounts, and comments are inflated or switched off, so there's no engagement-rate term. Audience data exists for 3 of 20 creators, so it acts as a check, not a score: a 70%-male audience fails, and missing data lowers confidence.

**Make the competitor rule a visible choice.** Six creators did paid work for rivals in the last 90 days, all for products doing Nutrimix's or Proteinmix's job. Rather than hide this in a penalty weight, we report three settings side by side. An outside review proposed letting mass brands through. We built it, and it admits one creator, who put Bournvita and then Complan into their child's milk within ten weeks. So the strict rule stays the recommendation.

**Python decides, the LLM drafts, a validator checks.** Briefs were drafted in the Claude Code session. A validator rejects any brief with a wrong or missing post, an ad that doesn't exist, a claim no ad made, or a hand-typed number. On its first run it caught a post credited to the wrong creator. We dropped the Gemini step and cut the planned four-page app to one small explorer that shows how each score is built, to spend the time on checks.

**The human overrode the AI where it mattered.** The AI first read parent stories and picky-eating angles as weak. The owner disagreed from category knowledge, so we tested it. Those angles do better paired with a child enjoying the product, which is now the backbone of every brief. More in [AI_LOG.md](AI_LOG.md).

## With one more week

1. **Close the loop.** Run the five tests and fit the weights to real purchases instead of judgment.
2. **Watch the creators' videos.** Age and "child enjoying" calls came from captions and transcripts.
3. **Human-check a random sample of labels** for a real error rate. So far a person has checked six verdicts the AI picked.
4. **Get audience screenshots** from the shortlisted creators, and **approve the claims library** with the brand.
5. **Host the explorer** so the manager can open it from a link. It already has the competitor switch and weight sliders, and only re-weights scores computed in Python.
6. **Read comments, not just count them**, to see whether heavily sponsored audiences still trust the creator.
