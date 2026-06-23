# Research: Learning Science

Compiled 2026-06-23 for the Tom Tagalog tutor (independent Claude planning round).

Evidence labels used throughout:
- **[STRONG]** replicated meta-analytic or large-sample evidence
- **[MODERATE]** consistent but narrower or context-bound evidence
- **[INFERENCE]** my design reasoning from the evidence, not a finding
- **[CONTESTED]** genuinely disputed in the literature
- **[MARKETING]** vendor claim, not independently verified

Full citations with retrieval dates are in `research/sources.md`. This file states findings and their direct design consequence for Tom.

---

## 1. Spacing effect and optimal intervals

**[STRONG]** Distributing study across time beats massing it, across materials, ages, and retention intervals. Cepeda, Vul, Rohrer, Wixted & Pashler (2008, *Psychological Science*, n>1,350) mapped a "temporal ridgeline": the best inter-study gap grows with the target retention interval, but as a *proportion* of that interval it shrinks — roughly 20–40% of a one-week target down to ~5–10% of a one-year target.

**[INFERENCE]** Two consequences for Tom:
1. There is no single correct interval; intervals must lengthen as an item proves durable. This is exactly what a stability-based scheduler (below) does.
2. For items he wants to hold for months (his real goal — survive in the Philippines), gaps of days-to-weeks are appropriate once an item is past the fragile stage. The current tutor's habit of re-drilling within one session is close to the *worst* case (massing) for long-term retention.

## 2. Memory models: SM-2 vs FSRS

**[MODERATE]** The dominant open scheduler is now **FSRS** (Free Spaced Repetition Scheduler, Jarrett Ye / open-spaced-repetition). It models each item with three variables: **Difficulty** (1–10, how hard the item is for this learner; uses mean-reversion so it drifts back toward baseline after successes rather than staying permanently damaged), **Stability** (days for recall probability to fall from 100% to 90%), and **Retrievability** (current recall probability, decaying on a power-law forgetting curve). A review is due when retrievability drops to a target (commonly 0.90). FSRS became the default in Anki (native since v23.10, Nov 2023; FSRS-6 in 2025) and reportedly cuts reviews ~20–30% at equal retention. (open-spaced-repetition GitHub; Anki FAQ; both retrieved 2026-06-23.)

**[CONTESTED]** FSRS's superiority over the newest SuperMemo algorithms is debated by SuperMemo-aligned authors; the honest claim is "FSRS is the best *openly documented, free, well-tooled* option," not "FSRS is provably optimal."

**[INFERENCE]** For a file-based, no-API tutor I do **not** need to ship FSRS's full 21-parameter trained model. I need its *shape*: separate stability from difficulty, decay retrievability over real calendar time, lengthen intervals multiplicatively on clean success, and reset/shorten on failure. A transparent "FSRS-lite" with fixed, auditable parameters captures ~most of the benefit and stays inspectable in Markdown/JSON — which the project explicitly values over opaque scoring. The schema should leave room to adopt true FSRS later without re-modeling items (store stability + difficulty + last_review + due, which FSRS also needs).

## 3. Retrieval practice (the testing effect)

**[STRONG]** Recalling from memory produces more durable learning than re-studying. Roediger & Karpicke (2006) found 61% vs 40% retention at one week (recall vs reread). Meta-analyses: Rowland (2014) g≈0.50; Adesope et al. (2017) g≈0.61; transfer Pan & Rickard (2018) d≈0.40; classroom Yang et al. (2021) g≈0.50. The advantage *grows* with the retention interval.

**[INFERENCE]** The tutor's primary verb must be "make Tom retrieve," not "show Tom." This directly validates the existing production-first principle and argues that *recognition-only* exposure (re-reading corpus lines) should never advance an item's stability the way a successful production does. Recognition and production must be scored on different scales (Section 8).

## 4. Generation effect (produce before the answer)

**[STRONG]** Self-generated answers are remembered better than read ones, even when the generation attempt *fails*, provided corrective feedback follows (the "errorful generation" / pretesting effect). ~47 years of evidence, 300+ experiments, three meta-analyses; applies directly to vocabulary and translation.

**[INFERENCE]** This is the strongest scientific endorsement of Tom's existing "no answer key before I try" rule and his preference to write his attempt before the corrected form. It also means a *wrong* attempt is pedagogically valuable, not a waste — so the system should **log the attempt verbatim** and treat the error as a learning event that seeds future contrast items, not merely a failed card.

## 5. Interleaving and desirable difficulty

**[STRONG]** Interleaving related skills (vs blocking one skill at a time) depresses in-session performance but improves delayed retention and transfer (e.g., Rohrer & Taylor volume-formula studies: 63% vs 20% on a delayed test). Bjork's storage-strength vs retrieval-strength distinction explains why: massed/blocked practice inflates momentary retrieval strength without building durable storage strength.

**[STRONG]** Learners (and tutors) systematically *misjudge* this — blocked practice "feels" more effective, so people under-adopt interleaving. (Bjork & Bjork, "the myth that blocking helps.")

**[INFERENCE]** Two design rules:
1. A session should interleave Tom's confusable families (actor vs target track; `kunin` vs `kumuha`; modal+base vs contemplated) rather than drilling one in isolation. His own weak list ("switching between actor and target tracks") is an interleaving problem.
2. Because interleaving feels worse, the tutor must *show Tom the evidence* (delayed-recall wins, mastery map) so he trusts the harder path. This is where honest gamification earns its keep (Section 7).

## 6. Hint dependence and the assistance dilemma

**[MODERATE]** Intelligent-tutoring research names the "assistance dilemma": too little help blocks progress, too much breeds dependence and produces performance that collapses when help is withdrawn. Step-by-step bottom-out hints correlate with *worse* learning when over-used; strategic hints do not. Adaptive systems aim help at the point where predicted success is ~0.5 (the edge of the learner's ability).

**[INFERENCE]** Hints must be *priced into scheduling*, not free. Tom's profile explicitly says structure is his bridge when retrieval fails — good — but the system must distinguish "produced unaided" from "produced after a hint" and grant much less stability gain to the hinted success, or the mastery signal inflates. This is the single most important correction to the current method, alongside mechanical scheduling. Hints should also fade: a structure that needed a full scaffold last week should be offered only a label this week.

## 7. Gamification, motivation, and manipulation risk

**[MODERATE]** Gamification can support the three Self-Determination-Theory needs — competence (mastery feedback), autonomy (chosen challenge), relatedness (social) — and the features with the most consistent *learning* benefit are immediate feedback, progress tracking, and adaptive challenge. Points/badges/leaderboards show *mixed* outcomes and are weaker.

**[CONTESTED / ETHICS]** Streaks exploit loss aversion and habit loops. Commentary on Duolingo's streak argues it can shift motivation from learning to streak-protection and induce anxiety/burnout when a day is missed. (These are largely critical essays and blogs, not RCTs — labeled [CONTESTED].)

**[INFERENCE]** For Tom specifically (his profile: motivated by "gamification tied to actual learning quality," not decorative rewards), the design rule is: **reward the behaviors science rewards** — unaided production, delayed recall, recovery after a lapse, scene transfer — and *never* reward trivial recognition or mere app-opening. Prefer a "due-review streak" (did you clear what was actually due) over a raw daily streak, and build a **streak-freeze / recovery** mechanic so a missed day doesn't nuke motivation. Avoid loss-aversion traps and any countdown pressure. Make the progress model transparent (Tom can read his own state file), which is itself autonomy-supportive.

## 8. Recognition vs production vs listening

**[MODERATE]** Production (recall + generate form) is a harder, more durable retrieval mode than recognition (choose/verify). Listening comprehension is a third, partially separable skill. The L2 literature treats receptive and productive knowledge as related but non-identical, with receptive typically leading productive.

**[INFERENCE]** Track at least three modalities per skill — recognition, production, listening — with independent state. "Recognition is not mastery" (the project's own principle) becomes mechanical: an item cannot reach "stable" on recognition evidence alone; stability requires *unaided delayed production* plus at least one scene use and one listening check (matches the project's stated mastery bar).

## 9. Corrective feedback timing

**[CONTESTED]** Theory (behaviorist habit-formation, interaction hypothesis) and learner preference favor *immediate* correction; immediate feedback is generally at least as good as delayed for grammar, and learners prefer it. Some cognitive-psychology work suggests delayed correction can aid retention via spacing, and vocabulary may benefit more from delay than grammar does. Net: mixed, task-dependent.

**[INFERENCE]** Keep the current "produce, then immediate concise correction" loop for in-session work (good for Tom's morale and for meaning-blocking errors), but get the *spacing* benefit elsewhere — by scheduling a **delayed contrast re-test** of the corrected point days later. So: immediate correction now + mechanically spaced re-test later. This resolves the tension instead of picking a side.

## 10. Overtesting, load, and habit

**[MODERATE]** Retrieval helps, but session overload and excessive new-item introduction raise failure rates and harm motivation; spaced *expanding* schedules and capping new material protect both retention and adherence. Habit formation favors short, low-friction, consistent sessions.

**[INFERENCE]** Cap new material at ~25–35% of a session (the project's own figure, which the evidence supports), cap total due load per session to avoid overdue avalanches, and prefer shorter daily sessions over long sporadic ones. The scheduler must actively *throttle* due items (Section: scheduling spec) so a 9-day absence doesn't produce a punishing 80-item queue.

---

## Summary: the eight rules this evidence imposes on the design

1. Schedule by **stability**, lengthen intervals multiplicatively, decay over real time (FSRS-lite).
2. **Produce before answer**; log the verbatim attempt; errorful attempts are valuable.
3. Score **production > recognition**; stability cannot rise on recognition alone.
4. **Interleave** confusable families; show Tom the delayed-recall payoff so he trusts it.
5. **Price hints in**: hinted success earns less stability; hints fade over time.
6. **Immediate** in-session correction **plus** a **spaced** delayed re-test of the same point.
7. **Throttle** session load; cap new items; protect against overdue avalanches.
8. Gamify **learning-quality** signals only; transparent state; recovery over punishment.
