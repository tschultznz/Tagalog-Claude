# AI Teacher Architecture

Status: first iteration of the SQLite-backed design. Date 2026-06-24. Author: independent Claude agent. This round is architecture, self-critique, and a narrow database proof. It does not implement the full tutor.

## 1. The one idea this architecture is built on

The teacher is the AI. Not a program that imitates a teacher, not a schema that encodes lessons, not a scheduler that decides what Tom sees. When Tom opens the project and talks, he is talking to Codex, Claude, or ChatGPT, and that model does the teaching: it reads free Tagalog, judges what he meant, recognizes valid alternative phrasings, explains grammar, handles register and naturalness, runs messy speaking, answers whatever he asks, and decides what an error actually means.

The database is the teacher's memory. It is where the teacher writes down what happened and reads back what is due, weak, or recently wrong. It is a much more reliable and auditable version of the single `progress.txt` file the current GPT tutor keeps. It is not a curriculum engine and it is not an evaluator.

Everything below follows from holding that line. The failure mode this design is most afraid of is a system that quietly turns the database into the teacher: schemas pretending to encode pedagogy, a scheduler formula deciding the lesson, command syntax replacing conversation. The previous Claude design drifted toward that, and the self-audit in `collaboration/claude_first_iteration.md` says where.

## 2. Three roles, kept separate

The AI teacher does the work that needs language understanding and judgment. It interprets Tagalog input, judges intended meaning, accepts valid alternative constructions, explains structure, rules on naturalness and register, adapts drills to how Tom is doing, answers spontaneous questions, decides what an error means, conducts text based messy speaking, and decides what is worth recording as structured evidence. None of this is reducible to a deterministic function, and the architecture never pretends otherwise.

The database stores and retrieves. It holds learner history, attempts, active weak points, review timing, skill evidence, scene evidence, error patterns, curriculum pointer, Glossika anchors, explanations that have landed, preferences, and progress summaries. It answers one compact question well: given today, what is due, weak, and recently wrong. It enforces structure (foreign keys, allowed value sets) and atomicity (a learning event and all its consequences commit together or not at all). It never decides whether a Tagalog sentence was correct.

The helper scripts do the deterministic plumbing between the two. They open the database with foreign keys on, apply migrations, write one evaluated attempt and all of its consequences in a single transaction, run the due/weak/recent context query, export that context as deterministic JSON the AI can read, and offer a small default review interval that the AI is free to override. The whole helper layer is `db/tutor_db.py`, about 350 lines of standard library Python, auditable by hand. It contains no Tagalog logic.

A blunt test for which role owns a piece of behavior: if getting it wrong is a language mistake, it belongs to the AI; if getting it wrong is a bookkeeping mistake, it belongs to the database or a helper. Judging `Dapat akong magpapatingin` as future overmarking after a modal is a language judgment, so the AI owns it. Making sure that judgment, once made, updates six skills and a review date together without leaving a half written record is bookkeeping, so a helper owns it.

## 3. What cannot be reduced to deterministic code

This is worth stating plainly because the temptation to encode it is the main way the project could go wrong.

Tagalog evaluation cannot be deterministic. Whether a production conveys the intended meaning, whether `dapat akong magpatingin` and `kailangan kong magpatingin` are both acceptable, whether a sentence is natural or merely understandable, what register it lands in, and what a given error reveals about Tom's model of the grammar are all judgments. The `dapat` plus base form rule is itself a teaching simplification, not an absolute law, since aspect can co-occur with `dapat` in some natural speech. A deterministic checker would either be wrong at the edges or would freeze a simplification into a fake rule. The database carries a `humility_flag` on such skills precisely so the AI keeps hedging instead of asserting.

Lesson construction cannot be deterministic either. Which due item to open with, how to interleave two confusables, when to drop a hint level, when to switch to messy speaking, and when to stop for the day are pedagogical choices the AI makes from the context the database hands it. The database supplies the raw material (what is due, what is weak, what recently went wrong, which explanations have worked before). The AI builds the lesson in conversation.

The proof in `tests/` honors this by supplying the evaluation as input. The test never grades Tagalog. It hands the database a verdict that a real AI teacher would produce and checks that the database records it faithfully and atomically.

## 4. The three grains, retained

The current method already tracks three things at once, and that is right, so it stays: the exact item (a high value chunk or contrast such as `Dapat akong magpatingin`), the underlying skill (modal plus actor pronoun plus base verb), and the scene (describe symptoms and agree to see a doctor). One answer updates all the grains it touches.

The mechanism is the partial credit vector. The AI decomposes one production into a set of per skill outcomes and the database writes them together. The worked example: Tom is prompted for `Dapat akong magpatingin` and says `Dapat akong magpapatingin`. The AI judges meaning fine, actor voice fine, clitic placement fine, causative and health vocabulary fine, but the modal base form and the contemplated aspect wrong. That is four passes and two fails from one sentence, recorded as four `attempt_skill_credit` rows marked pass and two marked fail, plus one `errors` row for the future overmarking, plus six `scheduling_events` that bring the two failed skills back tomorrow and push the four passed skills out. This is validated in `tests/test_attempt_transaction.py`.

Exact items stay scarce and promotion gated, so the system does not mint a card per sentence. A chunk becomes a scheduled `review_item` only when it is high value, such as a module anchor or a contrast spawned by a real error. Skills are the durable layer. Scenes are the transfer test.

## 5. How arbitrary questions are handled

Most of what Tom types is not an attempt. When he says "explain that differently", "why is it `ko` rather than `ako`", "give me another example", "that rule seems inconsistent", or "was that natural", the AI just answers as a teacher. Nothing is written to `attempts`. The database is not in the loop at all unless the AI decides something durable happened.

The architecture makes this explicit by distinguishing six things that the prior design tended to blur: conversation, teaching explanation, a formal learner attempt, a correction, a database update, and a session summary. Only a formal attempt becomes an `attempts` row. A correction is part of an attempt's evaluation. A summary is a `sessions.summary` string written at the end. Conversation and explanation are usually not stored at all, with one optional exception: when an explanation visibly lands, the AI may save it to `explanations` so it can reuse the phrasing later. That is a memory aid, not a transcript.

This is the single most important behavioral guardrail against the system feeling like an app. Tom is having a conversation. The database is listening only for the moments worth remembering, and the AI decides which moments those are.

## 6. How "continue" works

When Tom says "continue", the AI does four things and then teaches. It reads the tutor protocol (a git tracked file), runs the context query against SQLite, reads back the compact result, and uses its judgment to decide what to teach. There is no service that ran in the background and no formula that produced the lesson.

The context query is one function, `due_context`, returning a small object: the learner and current module, the skills due today or earlier (ordered by due date), the overdue exact items, the weak skills (lapsed, leech, or repeatedly lapsing), the active error patterns, the errors seen in the last two weeks, and any explanations that have previously landed for the due skills. `export_context_json` renders that as deterministic, sorted JSON the AI reads at the top of the session. From there the AI builds the lesson in conversation: recovery check if Tom has been away, the highest priority due items first, one concept hint where a skill needs it, production first drills with hints below, evaluation with concise correction, a messy scene when appropriate, and a short honest summary at the end.

The full step by step is in `SESSION_FLOW.md`. The boundary that keeps this from becoming an app is in `TUTOR_VS_TOOL_BOUNDARY.md`.

## 7. Review dates without a scheduler service

Review timing is stored, not computed by a running process. Each attempt writes the next due date onto the projected state (`skill_state.due`, `review_items.due`) and logs an immutable `scheduling_events` row recording the change and who decided it. The next time Tom says "continue", the context query simply selects rows where due is today or earlier. That is the whole mechanism. Nothing needs to run between sessions.

Who picks the date matters for the boundary. The AI decides the interval using its judgment, and `scheduling_events.decided_by` records `ai` when it does. When the AI does not feel strongly, it can take a small transparent default from `suggest_due`: a failed skill comes back tomorrow, a hinted pass gets a short interval, an unaided pass after a gap expands, capped for a single learner's sanity. That helper is about a dozen lines and carries no trained weights. It is a convenience the AI overrides, not an engine that runs the learner. This is a deliberate, large reduction from the previous design, where a 150 line FSRS-lite scheduler with eleven tuned constants sat at the center. The self-audit explains why that was too much machine for an n of one learner taught by a language model.

## 8. How messy speaking is stored

Messy speaking is a conversation, so most of it is never written down. The AI runs the scene without correcting mid turn to protect flow. It silently notes candidate weak points. At the end it gives a short batch summary, then writes only a handful of `attempts` with `mode` set to messy, each with its own partial credit vector and any error rows, plus `mastery_evidence` of type `scene_use` for skills Tom used correctly under pressure. The cap is small on purpose, at most around three extracted weak points, so a free conversation does not explode into dozens of flashcards. The session itself is one `sessions` row of kind messy with a summary. The distinction between conversation and recorded attempt, from section 5, is what makes this clean.

## 9. Why listening is deferred

Phase one has no audio, so listening is not active and must never be required for mastery. The schema can carry a listening modality on attempts and a `listening_check` evidence type, so the concept is future compatible, but the phase one mastery gate is exactly three things: unaided delayed production, use inside a scene, and handling a variation. Listening evidence is recorded if it ever occurs and never gates anything. This fixes a real bug in the prior design, where the mastery gate listed a listening check as a required condition while the system had no listening, which would have made full mastery unreachable. The gate now lives in one place, `db/tutor_db.py` `REQUIRED_MASTERY_EVIDENCE`, and the test `test_mastery_promotes_only_with_full_phase1_evidence` proves that production, scene, and variation evidence are sufficient without any listening.

## 10. How the tutor avoids becoming an app

Four commitments keep this a conversation rather than a product. There is no separate interface: Tom talks to the AI in the coding project, full stop. Commands are optional shortcuts, never the way in: "continue" is a word, not a parser rule, and Tom never has to learn a syntax. The database is queried by the AI through small scripts or inline SQL, not exposed as a UI. And nothing runs autonomously between sessions, so there is no service to operate or monitor.

There is also a maintenance line the project should not cross: the system must not cost more effort to keep alive than the learning it supports. A pile of hand tuned scheduler constants, per modality bookkeeping, and command handlers would have crossed it. A single SQLite file, a thin helper module, and a few git tracked specs do not.

## 11. What changed from the previous Claude design

The short version, with the full self-audit in `collaboration/claude_first_iteration.md`. Mutable learner state moves from YAML files into one SQLite database, so updates are atomic and queries are real queries instead of file parsing. The FSRS-lite scheduler is demoted from a central engine to an optional one paragraph default the AI overrides. The mastery gate drops its listening requirement and is derived from evidence rows rather than asserted, removing an internal inconsistency between the `stable` status and the gate. The modality weighting multiplier is removed, because mixing a fudge factor with genuine per modality state was confused; recognition simply is not production evidence, by structure, not by discount. Slash commands are demoted to optional shortcuts. What survives is the good content and the good bets: the three grain model, the partial credit vector, scarce promotion gated items, immutable attempt evidence kept separate from projected state, honest gamification that rewards only delayed recall and recovery, lazy Glossika reuse, and the discipline that completion is not mastery.

## 12. What Codex should challenge first

Whether the `strength` field on `skill_state` is even worth keeping, or whether due date plus lapse count is enough for an AI taught learner. Whether `errors` as a recurring pattern registry earns its place or duplicates what the AI can infer from `attempt_errors`. Whether `explanations` is real memory or clutter. Whether deriving "module done" from skill mastery, rather than storing it, holds up once real modules are loaded. And whether the context query returns too little or too much for the AI to build a good lesson. These are called out again, with ratings, in the report.
