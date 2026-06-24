# Claude First Iteration

Date 2026-06-24. Author: independent Claude architecture and prototype agent. This round is architecture, self-critique, and a narrow database proof. It does not implement the full tutor. The Codex repository and proposal were not inspected.

## 1. What this round delivers

A reorientation of the project around a single principle (the AI is the teacher, the database is its memory), four architecture documents that draw the boundary precisely, a minimal and evolvable SQLite schema with its first migration, a thin deterministic helper layer, and three tests that prove the database can record a real evaluated attempt and serve the next session, without the database ever judging Tagalog.

Files created this round are listed in section 14. The proof is described in section 11 and validated by the tests in section 13.

## 2. What the AI teacher does

The AI does everything that needs language understanding and pedagogical judgment. It interprets free form Tagalog, judges intended meaning, accepts valid alternative constructions, explains grammar, rules on naturalness and register, chooses and adapts drills, answers spontaneous questions, decides what an error actually means, conducts text based messy speaking, decides what evidence is worth recording, decides the next review interval, and writes the session summary. When Tom challenges an explanation or asks for another example, the AI simply teaches. None of this is delegated to a schema or a formula.

## 3. What the database does

The database remembers. It stores learner history, attempts, active weak points, review timing, skill and scene evidence, error patterns, the curriculum pointer, Glossika anchors, explanations that have landed, preferences references, and progress summaries. It answers one question well: given today, what is due, weak, and recently wrong. It enforces structure with foreign keys and value constraints, and it guarantees that a learning event and all its consequences commit atomically. It never decides whether a sentence is correct. Every judgment column is written by the AI and merely persisted.

## 4. What the helper scripts do

`db/tutor_db.py` is the deterministic plumbing, standard library only, with no Tagalog logic. It opens the connection with foreign keys on, applies migrations idempotently, writes one evaluated attempt and all of its consequences in a single transaction (`record_attempt`), runs the context query (`due_context`), exports that context as deterministic JSON (`export_context_json`), derives mastery from evidence rows, and offers a small default review interval the AI may override (`suggest_due`). It is about 350 lines and auditable by hand.

## 5. What cannot be reduced to deterministic code

Tagalog evaluation, lesson construction, and naturalness and register rulings. Whether a production conveys the intended meaning, whether an alternative is acceptable, whether something is natural, and what an error reveals are judgments. Some teaching rules are simplifications rather than laws, including the `dapat` plus base form rule, so a deterministic checker would be wrong at the edges or would freeze a simplification into a false rule. The proof supplies the evaluation as input precisely because the live AI performs that judgment. This is stated and enforced throughout; see `architecture/TUTOR_VS_TOOL_BOUNDARY.md`.

## 6. How arbitrary questions are handled

Most of what Tom types is not an attempt. Questions, challenges, requests for another example or a different explanation, and "stop for today" are answered in conversation and written nowhere. The design distinguishes six things the prior version blurred: conversation, teaching explanation, formal attempt, correction, database update, and session summary. Only a formal attempt becomes an `attempts` row. The one optional exception is that a visibly successful explanation may be saved to `explanations` for reuse. This guardrail is what keeps the system feeling like a conversation rather than a form.

## 7. How "continue" works

The AI reads the tutor protocol and learner files (git), runs `due_context` against SQLite, reads the deterministic export, and uses judgment to build the lesson in conversation. No service ran in the background; no formula produced the lesson. The query returns the current module, due skills, overdue items, weak skills, active and recent errors, and landed explanations for the due skills. The full step by step is in `architecture/SESSION_FLOW.md`.

## 8. How review dates work without a scheduler service

Review timing is stored, not computed by a running process. Each attempt writes the next due date onto the projected state and logs an immutable `scheduling_events` row. The next "continue" selects rows where due is today or earlier. The AI decides the interval and `scheduling_events.decided_by` records `ai`; when the AI declines, it can take a tiny transparent default from `suggest_due` (fail comes back tomorrow, hinted pass short, unaided pass expands, capped). Nothing runs between sessions.

## 9. How messy speaking is stored

A messy scene is conversation, so most of it is never written. The AI does not correct mid turn, tracks weak points silently, gives a short batch summary, then records at most around three extracted weak points as `attempts` with mode messy, each with its own credit vector and error rows, plus `scene_use` mastery evidence for skills used correctly under pressure. The session is one `sessions` row of kind messy. A ten minute conversation yields a few attempts, not dozens of cards.

## 10. Why listening is deferred

Phase one has no audio, so listening is not active and must never be required for mastery. The schema can carry a listening modality and a `listening_check` evidence type for future compatibility, but the phase one mastery gate is exactly three things: unaided delayed production, scene use, and variation handled. Listening is recorded if it ever occurs and never gates anything. The test `test_mastery_promotes_only_with_full_phase1_evidence` proves the three are sufficient.

## 11. How the tutor avoids becoming an app

No separate interface (Tom talks to the AI in the project), commands are optional shortcuts rather than a required syntax, the database is queried by the AI through small scripts or inline SQL rather than exposed as a UI, and nothing runs autonomously between sessions. There is also a maintenance line the system must not cross: it must not cost more effort to keep alive than the learning it supports. One SQLite file, one thin helper, and a few specs stay under that line.

## 12. Self-audit of the prior Claude design

I inspected the previous round's artifacts directly and did not defend them by default. The findings, point by point against the questions posed.

Drifting toward a standalone app. Partially true. The intent was conversational, but `tutor/session_protocol.md` framed the system around a table of thirteen slash commands, which reads like an app surface. Demoted: commands are now optional shortcuts and the interface is conversation.

FSRS-lite scheduler too central. True. `srs/scheduler.py` and `srs/scheduling_spec.md` put a 150 line model with eleven tuned constants at the heart of the system. For a single learner taught by a language model, that is too much machine and too little judgment. Demoted to a dozen line default the AI overrides.

Evaluator falsely presented as deterministic. Partially true. `tutor/evaluation_rubric.md` reads as a deterministic pipeline ("for each attempt: 1 meaning check, 2 decompose, ...") when in fact every step depends on AI judgment. The content is fine as guidance to the AI, but the framing implied a determinism the system does not and should not have. Corrected: the evaluation is explicitly the AI's, supplied as data; the rubric is advice, not an algorithm.

`stable` inconsistent with the mastery gate. True, and concrete. `scheduling_spec.md` section 8 defines a five condition mastery gate, but `scheduler.py` sets `status = "stable" if S_new >= STABLE_S else "active"`, that is, on a stability threshold alone, with none of the gate's evidence checked. The status and the gate disagreed in code. Fixed: status `mastered` is derived only from evidence rows against the gate, in one place, and a failed attempt cannot be mastered (proven by `test_mastery_evidence_does_not_promote_a_failed_skill`).

Modality weighting confused with separate modality state. True. The prior design kept three SRS states per skill (production, recognition, listening) and also a `w_modality` multiplier that discounted a recognition pass's contribution to production stability. That mixed two incompatible ideas: either recognition is a separate track, or it is a discounted contribution to one track, not both. Removed the multiplier. Modality is a column on attempts, and recognition is simply not production evidence, by structure.

Listening blocking mastery. True. Gate condition 3 required a listening check while the system has no listening, making full mastery unreachable in phase one. Removed listening from the gate.

Slash commands becoming the interface. True, addressed above.

The existing test truly end to end. False, as labeled. `tests/test_poc_flow.py` is a careful and useful test, but it exercises scheduler arithmetic over YAML fixtures in memory; it does not create a database, write state, and read it back. It is an arithmetic and design test presented as end to end. The new `tests/test_attempt_transaction.py` and `tests/test_due_context_query.py` close that gap by writing to a real SQLite database and querying it back, including atomic rollback.

Usable through normal conversation. Mostly true in intent, but obscured by the command framing and the centrality of the scheduler. The new design makes conversation the only required interface.

SQLite simplifies or invalidates existing file structures. It simplifies. The YAML state files (`skills_state.yaml`, `review_items.yaml`, `scenes_state.yaml`, `gamification.yaml`) and the JSONL logs are replaced by tables with real queries and atomic writes. The specs (research, pedagogy, curriculum, corpus mapping) remain valuable as git tracked knowledge the AI reads.

Which parts of the prior schema to discard rather than migrate. Discard the FSRS-lite numeric machinery (the power law constants, the stability growth formula, `w_grade`, `w_hint`, `w_modality`), the triple per modality SRS state, and the `stable` via stability threshold. Keep the shapes that were right: the three grains, the partial credit vector, the error taxonomy as tags, the scarce promotion gated items, and the immutable log idea (now `attempts` and the evidence tables).

## 13. Which prior parts remain valuable

The content and the structural bets. The curriculum (Modules 1 to 70), the root family explanations, the production first method, the actor versus target contrasts, and the Glossika corpus are good and preserved. The three grain model and the partial credit vector were the right core and are retained intact. Scarce promotion gated items remain the firewall against card explosion. Lazy Glossika reuse, immutable evidence separated from projected state, honest gamification that rewards only delayed recall and recovery, and the discipline that completion is not mastery all survive. The research files and the linguistic humility flags stay. The schema's instinct to label both a practical and a linguistic name for each skill is kept.

## 14. Files created or changed this round

Created: `architecture/AI_TEACHER_ARCHITECTURE.md`, `architecture/SQLITE_SCHEMA_PROPOSAL.md`, `architecture/SESSION_FLOW.md`, `architecture/TUTOR_VS_TOOL_BOUNDARY.md`, `db/migrations/001_initial_schema.sql`, `db/tutor_db.py`, `tests/test_database_smoke.py`, `tests/test_attempt_transaction.py`, `tests/test_due_context_query.py`, and this file `collaboration/claude_first_iteration.md`. Changed: `.gitignore` (ignore the live database file).

The prior round's files are left in place, not deleted, so the comparison and the self-audit remain checkable. The schema and helper supersede `srs/scheduler.py` for state, but that file and its spec are kept for the record and for the arithmetic insight they still hold.

## 15. Tests run and results

Run with the standard library, no third party dependency, from `tagalog_tutor_project_starter/`:

```
python3 tests/test_database_smoke.py        -> ALL SMOKE TESTS PASSED (5 tests)
python3 tests/test_attempt_transaction.py   -> ALL ATTEMPT-TRANSACTION TESTS PASSED (7 tests)
python3 tests/test_due_context_query.py     -> ALL DUE-CONTEXT TESTS PASSED (8 tests)
python3 tests/test_poc_flow.py              -> ALL ASSERTIONS PASSED (prior PoC, still green; needs PyYAML)
```

The proof demonstrates, against a real SQLite database: database creation; idempotent migrations; one learner; one session; one supplied AI evaluation of `Dapat akong magpatingin` versus `Dapat akong magpapatingin`; partial credit to six skills (four pass, two fail); error recording and linkage; creation of future reviews in both directions (failed skills due tomorrow, passed pushed out); a compact next session context query; transaction rollback when a bad credit entry is supplied; and a deterministic AI readable export. No deterministic Tagalog evaluation is implemented; the evaluation is supplied as input.

## 16. Candid ratings (1 to 10)

Alignment with AI as teacher: 9. The boundary is explicit and enforced; the database never judges language and the proof supplies the evaluation. Held back from 10 only because the specs that instruct the AI (protocol, rubric) still need rewriting to match this framing.

Simplicity: 8. One SQLite file, one helper, four docs, a dozen line default scheduler. Lower than 10 because the schema has seventeen tables, a few of which (errors, explanations) are not yet proven necessary.

Learner model quality: 7. Three grains and partial credit are strong and validated. The `strength` proxy is crude and unproven on real data, and the model has not yet met a real session.

Database quality: 8. Clean separation of immutable evidence from projected state, foreign keys, atomic writes, derived mastery, deterministic export. Open questions on whether `errors` and `explanations` earn their place keep it off 9.

Conversational flexibility: 9. Nothing forces structure; arbitrary questions write nothing; commands are optional. Off 10 only because flexibility in practice depends on the protocol spec, not yet written.

Implementation realism: 8. Tests pass, standard library only, small surface, runs anywhere Python does. The full tutor is not built, by design, so realism of the end system is asserted, not yet shown.

Maintenance burden: 8. Low. One file plus a helper plus specs. The risk is schema churn as real use reveals missing or surplus tables.

Readiness for adversarial review: 7. The proof is deliberately narrow and green, and the self-audit is specific. But many specs are still to be written, the `strength` field and a few tables are unproven, and the design has not survived a real learning session. It is ready to be challenged, not yet ready to ship.

## 17. Unresolved questions

Whether `strength` on `skill_state` earns its keep, or whether due date plus lapse count is enough for an AI taught learner. Whether `errors` as a recurring pattern registry duplicates what the AI can infer from `attempt_errors`, and whether `explanations` is real memory or clutter. Whether deriving "module done" from skill mastery holds once real modules are loaded, or whether a light curriculum state table is needed. Whether the context query returns too little or too much for the AI to build a good lesson. How the projected state should be rebuilt from evidence in practice (a replay helper is implied but not written). Whether `suggest_due` should exist at all, or whether the AI should always set the interval. How much of the prior YAML and JSONL design to formally retire versus leave as reference.

## 18. What Codex should challenge

Whether the SQLite reorientation is worth abandoning the file based design Tom can read and diff by hand, or whether a hybrid keeps more of the auditability. Whether seventeen tables is already too many for phase one, and which to cut. Whether removing the FSRS machinery throws away real spacing value, or rightly removes premature optimization. Whether the mastery gate of three evidence types is right, or whether variation handled and scene use overlap. Whether the boundary document's "refuse a feature that needs the tool to make a language call" is too strict. And whether the proof, being narrow by design, actually de risks the hard part or just the easy part.

## 19. Exact files ChatGPT should inspect first

In order: `architecture/TUTOR_VS_TOOL_BOUNDARY.md` (the governing idea), `architecture/AI_TEACHER_ARCHITECTURE.md` (how it all fits), `db/migrations/001_initial_schema.sql` (the schema as built), `db/tutor_db.py` (the deterministic layer, especially `record_attempt`, `due_context`, and `REQUIRED_MASTERY_EVIDENCE`), `tests/test_attempt_transaction.py` (the proof, including rollback), then `architecture/SQLITE_SCHEMA_PROPOSAL.md` and `architecture/SESSION_FLOW.md` for the rationale and the operational flow. This report, section 12, is the place to push back on the self-audit.

## 20. Git

Logical commits on branch `main`, pushed to `github.com/tschultznz/Tagalog-Claude`. The previous round (commit `8b9411f`) was the parent. Push succeeded; the remote head advanced from `8b9411f` to `9e09b39`, then to the SHA-record commit below.

## 21. Commit record

Branch `