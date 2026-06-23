# Research: Current Language-Learning Products

Compiled 2026-06-23. Observable mechanics only; vendor claims labeled **[MARKETING]**, third-party/independent observations **[OBSERVED]**, my reading **[INFERENCE]**. Sources with retrieval dates in `research/sources.md`.

Each product is read against the project's ten questions: *what is scheduled, what counts as mastery, how errors are reused, how much production is required, how listening is tested, how hints work, how motivation is maintained, whether the AI remembers the learner, whether open questions are supported, how transparent the model is.*

---

## Duolingo
- **Scheduled:** lessons/skills, ordered in real time by the **Birdbrain** model — a deep net trained on ~1.25B daily exercises that predicts per-learner probability of answering each exercise correctly, then tunes difficulty/timing to keep the learner in a not-too-hard/not-too-easy band. **[OBSERVED/MARKETING]** A separate legacy "strength" decay drives review prompts.
- **Mastery:** crown/level progression and section checkpoints; largely *coverage + repeated correct*, not delayed unaided production. **[OBSERVED]**
- **Errors reused:** "Mistakes" review and personalized practice resurface missed items. **[OBSERVED]**
- **Production:** low–moderate; heavy use of tap-the-tiles and multiple choice means much "production" is actually recognition. Max adds AI speaking ("Video Call," role-play). **[OBSERVED]**
- **Listening:** dictation + audio match; integral. **[OBSERVED]**
- **Hints:** word hover/tap glosses; effectively unlimited and unpriced. **[OBSERVED]**
- **Motivation:** streaks, XP, leagues, gems, hearts/energy, daily quests — the most aggressive engagement stack in the category. Streak = loss-aversion engine. **[OBSERVED]**
- **AI memory:** Birdbrain remembers skill estimates; conversational memory is shallow. **[INFERENCE]**
- **Open questions:** only via Max "Explain my Answer" / role-play; base app, no. **[OBSERVED]**
- **Transparency:** low; the learner cannot inspect the model. **[OBSERVED]**
- **Borrow:** real-time difficulty targeting toward ~50–80% success; resurfacing mistakes. **Avoid:** recognition-as-production; unpriced hints; streak/loss-aversion pressure; opacity.

## Glossika (Tom's prior tool — central)
- **Scheduled:** individual **sentences**, via an SRS that scores each rep and pushes hard ones sooner, easy ones later; a learner sees a given sentence ~15–20× across a year. Difficulty defaults are tuned from *global* learner performance per language pair. **[MARKETING/OBSERVED]**
- **Mastery:** implicit — repeated correct reps over time; no explicit skill model. **[OBSERVED]**
- **Errors reused:** stumbled sentences return sooner. **[MARKETING]**
- **Production:** full-sentence listen-and-repeat / translate; high *volume*, but corpus sentences, not learner-chosen meanings. **[OBSERVED]**
- **Listening:** core (audio-first, mass listening). **[OBSERVED]**
- **Hints:** show text/translation on demand. **[OBSERVED]**
- **Motivation:** reps counter, daily goal; light gamification. **[OBSERVED]**
- **AI memory / open Q / transparency:** no tutor, no questions, scheduling is opaque. **[OBSERVED]**
- **Critical for this project:** Glossika gave Tom broad *recognition* familiarity over ~1,300 sentence pairs but (a) at the **sentence** grain, not the skill grain, and (b) without forcing self-initiated production or tracking *which structures* are weak. The new tutor's job is precisely to convert that recognition stock into skill-indexed production. **Borrow:** sentence-as-context, mass meaningful input, audio-first listening. **Avoid:** sentence-level-only scheduling (causes card explosion — the project's stated fear) and treating every corpus line as a natural production target.

## Anki + FSRS
- **Scheduled:** user-authored cards via **FSRS** (default since 2025) — stability/difficulty/retrievability, target retention configurable. **[OBSERVED]**
- **Mastery:** none beyond "interval is long"; Anki is a scheduler, not a pedagogy. **[OBSERVED]**
- **Errors reused:** lapses reset/shorten stability; "leech" tagging after repeated failures. **[OBSERVED]**
- **Production / listening / hints:** entirely up to card design (its weakness and strength). **[OBSERVED]**
- **Motivation:** minimal (counts, heatmap); attracts intrinsically-motivated users. **[OBSERVED]**
- **AI memory / open Q:** none. **Transparency:** high — open algorithm, inspectable scheduler. **[OBSERVED]**
- **Borrow:** FSRS scheduling math; the **leech** concept (repeated failure → flag for redesign, not infinite re-drill); full transparency. **Avoid:** zero pedagogy; the "one fact per card" grain that explodes for sentences.

## SuperMemo
- **Scheduled:** SM-series algorithms (latest SM-line, 2020s) + incremental reading. The origin of modern SRS. **[OBSERVED]**
- **Transparency:** algorithm partly proprietary; UI complex. **[OBSERVED]**
- **Borrow:** the historical core (expanding intervals, item difficulty) and incremental reading's idea of *gradually* promoting raw material into active items — directly relevant to staged Glossika migration. **Avoid:** complexity/opacity.

## Babbel
- **Scheduled:** dialogue-based lessons + a daily **spaced review** of past words/phrases before the main lesson; AI mainly powers smart review + pronunciation scoring. **[OBSERVED]**
- **Mastery / production:** scripted dialogues, moderate production, grammar made explicit (good for analytical learners). **[OBSERVED]**
- **Borrow:** "quick due-review *before* new content" (matches the project's session-start rule); explicit, compact grammar for analytical learners (fits Tom). **Avoid:** scripted-only production.

## Busuu
- **Scheduled:** CEFR-leveled lessons + a vocab SRS; **Busuu Conversations** (since late 2024) is an AI speaking partner. **[OBSERVED]**
- **Notable mechanic:** AI conversation gives **no mid-turn correction** — you talk freely, then get an **end-of-session summary** of fixes. **[OBSERVED]**
- **Errors reused / community:** human-corrected exercises feed review. **[OBSERVED]**
- **Borrow:** the **"talk now, correct in a batch after"** model is an excellent fit for Tom's "messy speaking" — it protects flow, then extracts weak points. The new design adopts exactly this for messy-speaking scenes. **Avoid:** none major; mid-conversation silence on errors is a feature here.

## Memrise
- **Scheduled:** SRS over words/phrases with crowd-sourced **"mems"** (mnemonics) and native-speaker video clips. **[OBSERVED]**
- **Borrow:** mnemonic encoding hooks and authentic-audio listening. **Avoid:** mem quality is uneven; recognition-heavy.

## LingQ
- **Scheduled:** not a scheduler — **comprehensible-input** reading/listening; you mark words known/unknown ("LingQs") and accumulate exposure. **[OBSERVED]**
- **Borrow:** the input-volume philosophy and a *known/unknown* tagging pass — useful for the lightweight Glossika triage (Section corpus_mapping). **Avoid:** weak on forced production and on scheduling rigor.

## Speak
- **Scheduled:** a **Learn → Practice → Real Conversation** loop; OpenAI-model AI tutor; you drill native phrase patterns, then apply them in open AI dialogue with real-time feedback; "Speak Tutor" answers grammar questions and builds custom lessons on demand. **[MARKETING]**
- **Production:** high — speaking-first; **listening** via the conversation. **[MARKETING]**
- **AI memory / open Q:** tutor answers questions; persistent learner memory unclear. **[INFERENCE]**
- **Borrow:** the explicit *pattern → automatize → free use* progression (mirrors exact-item → variation → scene); on-demand grammar Q&A. **Avoid:** API/cloud dependence (disqualifying for Phase 1's no-API rule); opacity of what's retained between sessions.

## Praktika / Loora / Gliglish (AI conversation tutors)
- **Scheduled:** open AI role-play conversation with avatars; feedback reports after sessions. **[MARKETING]**
- **Borrow:** low-stakes conversational reps and post-hoc feedback reports. **Avoid:** API dependence; thin/again-opaque mastery modeling; engagement-first framing.

---

## Cross-product synthesis

**What the market schedules well and we should copy:**
- FSRS-style stability scheduling (Anki) — but at the **skill** grain, not only the sentence grain.
- Real-time difficulty targeting toward the edge of ability (Duolingo Birdbrain) — emulated cheaply by choosing items whose estimated retrievability is mid-range.
- Resurfacing of past mistakes and **leech** flagging (Duolingo/Anki).
- Due-review *before* new content (Babbel) and capped new material.
- **Talk-now / correct-after** for free speech (Busuu) — the right shape for messy speaking.
- Pattern → automatize → free-use staging (Speak) — isomorphic to the project's exact-item → variation → scene model.

**What almost everyone gets wrong (and Tom explicitly dislikes), which becomes our differentiator:**
- **Recognition inflation** — counting taps/multiple-choice as production. We separate the scales.
- **Unpriced, non-fading hints.** We price and fade them.
- **Opaque models.** Ours is plain-text/JSON the learner can read.
- **Engagement over learning** (streak/loss-aversion). We reward learning-quality events and build recovery, not punishment.
- **No persistent, skill-level memory of the individual.** This is the single biggest gap and the thing a file-based system can actually do *better* than the apps, because the learner state is an auditable file rather than a hidden server model.

**[INFERENCE] Strategic position:** the new tutor is "Anki's scheduler + Speak's staging + Busuu's talk-then-correct + a transparent, skill-indexed learner memory," operated through chat over version-controlled files, with none of the API or engagement-dark-pattern dependencies. No existing product occupies that exact point because none of them is willing to be a transparent file system the user owns.
