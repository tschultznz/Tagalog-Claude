# SQLite Schema Proposal

Status: first iteration, matches `db/migrations/001_initial_schema.sql`. The schema is exercised by three tests under `tests/` and is deliberately minimal and evolvable. Date 2026-06-24.

## 1. Principles

The database is the canonical mutable store, opened through Python's standard `sqlite3`. Git tracked files remain the source of truth for everything that is authored and slow changing: the tutor protocol, learner profile and preferences, curriculum and skill graph edges, language notes, the raw corpus, research, code, these specs, the migrations, and the tests. The live database file is ignored by git; only its migrations and exports are versioned.

Three rules shape every table.

Immutable evidence is kept separate from projected current state. The evidence tables (`attempts`, `attempt_skill_credit`, `attempt_errors`, `scheduling_events`, `mastery_evidence`, `xp_events`) are append only and never rewritten. The projected tables (`skill_state`, `review_items` timing fields, `errors.status`) are a cache of where the learner is now, and could be rebuilt by replaying the evidence. This is the database form of the audit's instruction to split learner state from review history.

Judgment values are written by the AI, not derived by the database. Columns such as `attempts.meaning_ok`, `attempt_skill_credit.outcome`, `attempts.naturalness`, the error tags, and the chosen `next_due` all arrive from the AI teacher as data. The schema records and constrains them; it does not compute them.

Foreign keys and transactions are always on. Every connection runs `PRAGMA foreign_keys = ON`. Every multi row learning event is written inside a single transaction so it commits whole or not at all.

## 2. Tables

Migration bookkeeping. `schema_migrations` records which numbered migrations have run, so `apply_migrations` is idempotent.

Identity and sittings. `learners` holds one row per learner with a current module pointer (the pointer only; whether a module is done is derived from skill mastery, not stored as a flag). `sessions` is one row per conversational sitting, with a kind (lesson, messy, review, qa, mixed) and an AI written summary. Most chat turns never create a session related row.

Skill catalog and state. `skills` is the slow changing definition layer: slug, practical label, honest linguistic label, type, teaching note, and a `humility_flag` that tells the AI to hedge on teaching simplifications such as the `dapat` plus base form rule. `skill_state` is the projected mutable state per learner and skill: a coarse `strength` proxy, `due`, `last_review`, `reps`, `lapses`, and a `status` whose `mastered` value is derived from evidence, never set arbitrarily.

Exact items. `review_items` are the scarce, promotion gated chunks and contrasts. They carry their own timing fields, a source kind (module anchor, corpus, learner error, tutor authored), an optional link to a Glossika anchor, and an optional link to the attempt that spawned them.

Scenes. `scenes` are applied competence tests, with a boss flag for graded milestones. `scene_skills` maps a scene to its component skills.

Corpus reuse. `glossika_anchors` are pointers into the immutable raw corpus file, tagged with register, naturalness, and intended use. The corpus line is referenced, not copied into a card.

The atomic learning event. `attempts` is the immutable record of one meaningful learner production: verbatim response, prompt, modality, mode (drill, messy, recovery), hint level, and the AI's judgments (meaning ok, register ok, naturalness, correction, one line reason). `attempt_skill_credit` is the partial credit vector, one row per skill the answer exercised, with an outcome the AI supplied. `attempt_errors` links an attempt to the error patterns it exhibited.

Error patterns. `errors` is a per learner registry of recurring weak points (tag, description, status active or watch or resolved, occurrence count, first and last seen). It is projected state: status changes as the learner improves. The immutable side is `attempt_errors`, which never changes.

Scheduling. `scheduling_events` is the immutable log of every due change: the unit, the previous and next due dates, the interval, a reason, and whether the AI or the default helper decided it. The projected `due` lives on `skill_state` and `review_items`; the event log makes the history auditable and replayable.

Mastery. `mastery_evidence` is immutable evidence rows of four types. The phase one gate requires three of them (unaided delayed production, scene use, variation handled). The fourth, listening check, is recorded if it ever happens and never required. Mastery is derived by checking the evidence, in `tutor_db._maybe_promote_to_mastered`, not stored as a guess.

Memory and gamification. `explanations` stores phrasings that landed for this learner, so the AI can reuse them. `xp_events` is an optional, immutable, honest gamification log that rewards only science aligned events such as delayed recall wins and recoveries.

## 3. What deliberately lives in Markdown, not the database

The task asked to evaluate whether some concepts belong in Markdown rather than tables. Several do.

Skill graph edges (prerequisite, confusable, composes into) stay in the git tracked curriculum and language notes. They are static authored knowledge the AI reads directly, and putting them in the database would invite a selection algorithm to consume them, which would pull pedagogy back into the tool. They become database worthy only if and when selection is automated, which phase one explicitly avoids.

Learner profile and preferences stay in `LEARNER_PROFILE_TOM.md` and a preferences file. They are Tom editable, rarely change, and benefit from being diffable prose rather than rows.

The tutor protocol, evaluation rubric, and session flow stay as specs. They are instructions to the AI, not data about the learner.

The raw corpus stays an immutable text file. Only thin anchors into it live in the database.

## 4. Justified omissions

`review_item_skills`, an item to skill junction, is intentionally not in this migration. In phase one an exact item records which skills it exercised through the `attempt_skill_credit` vector each time it is attempted, so a separate static mapping is not yet needed. A later migration can add it without touching existing data. This is noted in `tests/test_database_smoke.py`.

Per modality SRS state is not modeled as parallel rows. The prior design kept three SRS states per skill plus a weighting multiplier, which conflated two different ideas. Here, modality is a column on `attempts`, and the rule that recognition is not production evidence is enforced by the mastery model rather than by discounting a number. If a richer per modality projection is ever needed, it is an additive migration.

A scene state table per learner is deferred. Phase one tracks scene competence through `mastery_evidence` of type scene use. A `scene_state` table can be added when scenes become graded bosses with their own due dates.

## 5. Migrations

Migrations are numbered SQL files under `db/migrations`. `apply_migrations` creates the bookkeeping table if needed, then runs each unapplied file in order and records its version. `CREATE TABLE IF NOT EXISTS` plus an `INSERT OR IGNORE` of the version row makes the whole thing safe to run repeatedly, which `test_database_smoke.py` checks. Schema changes ship as new numbered files; existing files are never edited once applied.

## 6. Proof coverage

`test_database_smoke.py` proves database creation, migration idempotency, presence of every required table, learner and session creation, foreign key enforcement, and idempotent reference seeding. `test_attempt_transaction.py` proves the partial credit vector, error recording and linkage, future review creation in both directions, mastery derivation including the refusal to promote a failed skill, and atomic rollback when a bad credit entry is supplied. `test_due_context_query.py` proves the compact context query (due, weak, active and recent errors, current module, landed explanations) and a deterministic JSON export. All run on Python's standard library with no third party dependency.
