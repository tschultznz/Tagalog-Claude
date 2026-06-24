# Tutor vs Tool Boundary

Status: first iteration. This is the document the rest of the design defers to when a responsibility is unclear. Date 2026-06-24.

## 1. The boundary in one sentence

The AI is the teacher and owns every judgment that needs language understanding; the database and helper scripts are the memory and the plumbing and own every fact that needs to be stored, retrieved, or kept consistent. If getting something wrong would be a language mistake, the AI owns it. If getting it wrong would be a bookkeeping mistake, the tool owns it.

## 2. Who owns what

The AI teacher owns: interpreting free form Tagalog input; judging intended meaning; recognizing valid alternative constructions; explaining grammar and structure; ruling on naturalness and register; choosing and adapting drills; answering spontaneous questions; deciding what an error actually means; conducting text based messy speaking; deciding what structured evidence is worth recording; deciding the next review interval; and writing the concise session summary. These are judgments. The design never hides a language model behind a schema and pretends the schema decided.

The database owns: persisting learner history and attempts; holding the projected current state of skills, items, and error patterns; storing review timing, skill and scene evidence, curriculum pointer, Glossika anchors, landed explanations, and progress summaries; enforcing structure through foreign keys and allowed value sets; and guaranteeing that a learning event and all its consequences commit atomically. These are facts and invariants, not opinions.

The helper scripts own: opening the connection with foreign keys on; applying migrations idempotently; writing one evaluated attempt and all of its consequences in a single transaction; running the due and weak and recent context query; exporting that context as deterministic JSON; deriving mastery from evidence rows; and offering a small default review interval the AI may override. The entire helper layer is `db/tutor_db.py`, standard library only, with no Tagalog logic anywhere in it.

## 3. What must never be reduced to deterministic code

Tagalog evaluation. Whether a production means what was intended, whether an alternative phrasing is acceptable, whether something is natural or merely understandable, what register it carries, and what an error reveals are all judgments. Several of the teaching rules are simplifications rather than laws, including the `dapat` plus base form rule, so a deterministic checker would either be wrong at the margins or would harden a simplification into a false rule. The `humility_flag` on a skill exists so the AI keeps hedging.

Lesson construction. What to teach next, how to interleave confusables, when to fade a hint, when to move to messy speaking, and when to stop are pedagogical choices the AI makes from the supplied context.

Naturalness and register rulings. These are explicitly labeled as judgments when stored (`attempts.naturalness`, `attempts.register_ok`), never asserted as fact by the database.

The proof in `tests/` respects this by supplying the evaluation as input. No test grades Tagalog; the tests check that a supplied verdict is stored faithfully and atomically.

## 4. What must always be deterministic

Atomic writes. An attempt, its credit vector, its error rows, its schedule changes, and its mastery evidence either all land or none do. A language model should never be trusted to hand maintain six rows consistently across a transaction; the helper does it in one block.

The context query. Given today, the set of due, weak, and recently wrong units is a fact, computed the same way every time, so the AI starts from a stable picture rather than re reading prose.

Mastery derivation. Mastery is computed from evidence rows against a fixed gate, not asserted. This removes the inconsistency the prior design had between a `stable` status and the gate that was supposed to justify it.

Migrations and structure enforcement. Schema evolution and referential integrity are pure mechanism.

## 5. The dividing question, applied

A few concrete calls, to make the line usable.

Did Tom mean to say he should see a doctor? AI. Storing that the AI judged meaning ok? Database.

Is `magpapatingin` wrong here? AI. Recording the fail outcome for `modal.base_form`? Database.

Should this skill come back tomorrow or in nine days? AI decides; the helper offers a default if the AI declines to; the database stores the date and logs who decided.

Is this conversation turn worth remembering? AI. Once the AI says yes, writing it without leaving a half record? Helper and database.

Has this skill been mastered? Database, by deriving it from evidence the AI recorded. The AI cannot simply declare mastery; it must have produced the evidence.

## 6. Anti-patterns this boundary forbids

Turning every sentence into a flashcard. Only AI chosen productions become attempts; conversation and explanation are not stored.

Making Tom follow rigid command syntax. Commands are optional shortcuts; the interface is conversation.

Forcing deterministic naturalness judgments. Naturalness is stored as a labeled judgment, never computed.

Using the database as a curriculum engine. Skill graph edges and curriculum live in git markdown the AI reads; the database does not select lessons.

Building a conventional app. No UI, no service, no API.

Requiring listening evidence. The phase one mastery gate is production, scene, and variation; listening is recorded if present and never required.

Overengineering scheduling before real usage. The scheduler is a dozen line default the AI overrides, not a tuned engine.

A system that costs more to maintain than the learning it supports. One SQLite file, one thin helper, a few specs.

## 7. How to resolve a future dispute

When a new feature is proposed, ask first which side of the boundary it sits on. If it requires language judgment, it belongs to the AI and the only question is what evidence, if any, the database should keep. If it is storage, retrieval, or consistency, it belongs to the tool and must not start making pedagogical decisions. If it seems to need both, split it: give the judgment to the AI and the bookkeeping to the tool, the way `record_attempt` takes the AI's verdict as input and owns only the atomic write. A feature that cannot be split this way, that needs the tool to make a language call, is a feature this architecture should refuse.
