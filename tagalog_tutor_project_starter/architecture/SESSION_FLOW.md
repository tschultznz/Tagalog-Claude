# Session Flow

Status: first iteration. Describes how one session runs as a conversation in which the AI teaches and the database remembers. Date 2026-06-24. Detailed boundary rules are in `TUTOR_VS_TOOL_BOUNDARY.md`.

## 1. The required operational flow, concretely

The instruction lists twelve steps. Here is how each maps to the AI, the database, and the helper layer.

1. Tom opens the AI coding project. Nothing runs automatically.

2. Tom says "continue" (or anything that means start). This is a word, not a command parser.

3. The AI reads the tutor protocol and current learner context. The protocol is a git tracked spec; the learner profile and preferences are git tracked files. The AI reads them as plain text.

4. The AI queries SQLite for context. One call to `due_context(conn, learner_id, today)` returns the current module, the skills due today or earlier, the overdue exact items, the weak skills, the active error patterns, the errors from the last two weeks, and the explanations that have previously landed for the due skills. `export_context_json` gives the AI a deterministic, sorted view of all of it.

5. The AI decides what to teach. This is judgment, not a formula. It weighs what is most overdue, what is weak, which confusables should be interleaved, and how Tom seemed last time. The database supplied the raw material; the AI composes the lesson.

6. The AI conducts the lesson conversationally. Recovery check if Tom has been away, highest priority due items first, one concept hint where a skill needs it, production first drills with hints sitting below the prompt, controlled variation, then a messy scene when it fits.

7. Tom asks arbitrary questions or challenges explanations. The AI answers as a teacher. Most of these turns write nothing to the database.

8. The AI answers normally without forcing every message into a record. Conversation and explanation are not attempts. See section 3.

9. Meaningful learning attempts are evaluated by the AI. When Tom produces Tagalog in response to a prompt, the AI judges it: meaning, register, naturalness, a per skill outcome vector, and any error tags. This judgment is the AI's, not the database's.

10. The AI writes the attempt and resulting state changes atomically. One call to `record_attempt` writes the attempt, its partial credit vector, its error rows, the schedule changes, any mastery evidence, and any xp, all inside a single transaction. If anything fails, nothing is written.

11. The AI ends with a concise summary. It writes a short honest note to `sessions.summary` and shows Tom a compact state delta, including a delayed recall win if one happened, so he trusts the spaced approach.

12. The next session resumes from persistent state. Because every due date and weak point is stored, the next "continue" picks up exactly where this one left off.

## 2. The worked example end to end

Today is 2026-06-23. The context query surfaces `dapat akong magpatingin vs magpapatingin ako bukas` as a high priority due item, carried over from the current `progress.txt`. The AI prompts Tom in English: "say you should go get yourself looked at, now." Tom produces `Dapat akong magpapatingin`.

The AI evaluates. Meaning is fine, so this is a form error, not a meaning error. Actor voice, clitic placement, the magpa causative, and health vocabulary are all correct. The modal base form is wrong and the contemplated aspect is overmarked. The AI phrases the correction in Tom's preferred style: wrong form, better form, one short reason, hedged because the rule is a teaching simplification. "Use `magpatingin`, not `magpapatingin`. After `dapat`, keep the verb in base form; `dapat` already carries the should sense."

The AI then writes one attempt. Six `attempt_skill_credit` rows: four pass, two fail. One `errors` row, `aspect.future_overmark_after_modal`, linked through `attempt_errors`. Six `scheduling_events`: the two failed skills come back tomorrow, 2026-06-24, with a lapse counted; the four passed skills push out to dates between 2026-06-27 and 2026-07-11. The whole thing commits together. The AI spawns a contrast item, `should see a doctor now` versus `will see one tomorrow`, so the two confusable skills get interleaved next time. This entire transaction is what `tests/test_attempt_transaction.py` validates against a real database.

When Tom returns and says "continue", the context query selects the two skills now due, and the AI opens with the contrast it queued.

## 3. Conversation, attempt, correction, update, summary

The flow only works if these five are kept distinct. The prior design tended to blur them, which is what made it feel like it wanted every sentence to be a flashcard.

Conversation is Tom talking and the AI answering. "Explain that differently", "why `ko` not `ako`", "give me another example", "can we do messy speaking", "stop for today". None of these are attempts. The database is untouched unless the AI decides otherwise.

A teaching explanation is the AI explaining structure. It is not stored, with one optional exception: if an explanation visibly lands, the AI may save it to `explanations` for reuse. That is a memory aid, not a transcript.

A formal learner attempt is a Tagalog production in response to a prompt that the AI judges worth recording. It becomes one `attempts` row with its evaluation. This is the only thing that creates an attempt.

A correction is part of an attempt's evaluation (the corrected form and one line reason live on the attempt), not a separate event.

A database update is the atomic write of an attempt and its consequences, or a small status change such as marking an error pattern resolved.

A session summary is the AI's concise end of session note, one `sessions.summary` string, the structured successor to the over compressed `progress.txt` summary.

## 4. Messy speaking inside the flow

A messy scene is conversation first. The AI does not correct mid turn. It tracks candidate weak points silently. At the end it gives a short batch summary, then records at most around three extracted weak points as `attempts` with mode messy, each with its own credit vector and error rows, plus `scene_use` mastery evidence for skills Tom used correctly under pressure. The session is one `sessions` row of kind messy. A ten minute free conversation might produce three attempts, not thirty cards.

## 5. Recovery and load

If Tom has been away, the AI runs a short recognition first recovery before new production, an existing rule worth keeping. Selection is gentle: clear the most overdue high priority items first, cap how much is new, and never punish a skill for calendar backlog. A skill is only marked lapsed by an actual failed attempt, never by the clock. Because nothing runs between sessions, there is no overdue avalanche to absorb; the context query simply returns what is due and the AI picks a sane subset.

## 6. Why this needs no API and no service

Every step is the AI reading git files and a small SQLite database, teaching in conversation, and writing back through one transactional helper. There is no external model API: the language ability is the AI Tom is already using. There is no background scheduler: review dates are stored and read on demand. There is no UI: the interface is the conversation. Migrating to an app later means wrapping these same files and tables, with no change to how the learner is modeled.
