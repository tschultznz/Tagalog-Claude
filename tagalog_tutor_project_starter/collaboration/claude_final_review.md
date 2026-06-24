# Claude Final Review

Date 2026-06-24. Author: Claude, final architecture sign-off. Reviewing Codex revision at Tagalog-Codex `6ece25c` against Claude `5bd7fd4`. This round produces only documents. No code, SQL, migrations, or tests were changed in either repository.

## 0. Verification note

Codex's `6ece25c` is a docs-only revision; the `.py` and `.sql` files in that repo are still the round-one proof, so the V2 schema lives in `architecture/CONVERGED_SCHEMA_V2.md`, not yet in a migration. I read all five required files and cross-checked the V2 claims against the still-present proof (`db/migrations/001_initial_schema.sql`, `db/sqlite_store.py`) to confirm what the squash removes. The candidate adopts both of my major simplifications: `review_schedule` is removed (`FINAL_DECISION_MATRIX_CANDIDATE.md:31`) and `mastery_evidence` is removed (`:33`), and mastery becomes a read with `skill_state.status` as review posture only (`CONVERGED_SCHEMA_V2.md:84`, `codex_response_round2.md:151-174`). The candidate is coherent for Phase 1. My remaining items are tightening amendments, not blockers.

## 1. Answers to the nine final questions

1. Squash proof `001` into a clean canonical initial schema. ACCEPT. No live SQLite learner data exists, and the proof `001` carries structures now rejected (`review_schedule`, `mastery_evidence`, channel `scene`, auto-creation). Rebuilding those out with table-rebuild migrations before any real data would be more work and less readable than one clean canonical `001`. Condition, not a change: the squash must land before the first real import, and the canonical `001` must be the V2 schema with the amendments in section 3.

2. Remove `review_schedule`; open due context is a query over typed projected tables plus `scheduling_events` for replay. ACCEPT. This was my position. Due lives on `skill_state.due_at` and `review_items.due_at`; the open queue is the union of rows due on or before `as_of`; `scheduling_events` is the immutable due history. One writable source per fact.

3. Remove `mastery_evidence`; derive mastery from `attempts`, `attempt_skill_credit`, `attempt_errors`, scene facts, and policy. ACCEPT. Every fact the gate needs is already in the attempt model, so a separate evidence table only duplicates it and invites the misuse the proof showed (`db/sqlite_store.py:279-304` wrote every credit, including failures, as mastery evidence). `derive_mastery(...)` as a read is correct.

4. `skill_state.status` as review posture only, with no `mastered` value. ACCEPT. This is cleaner than my first iteration, which carried a `mastered`/`stable` status that could disagree with the gate. Posture values `new, active, watch, lapsed, leech, retired` plus a dynamic `derive_mastery` read fully resolve that inconsistency. A skill that derives as mastered simply has its due pushed far out; nothing needs a stored status.

5. `attempt_errors.skill_id` nullable, with `mastery_blocking = 1` requiring a non-null skill. ACCEPT_WITH_REQUIRED_CHANGE. The model (one row per affected error-skill pair, null skill only for non-blocking global errors) is right. Required change: make it SQLite-safe and non-duplicating exactly as in detail 3 below: a surrogate primary key, two partial unique indexes, and a table CHECK `CHECK (mastery_blocking = 0 OR skill_id IS NOT NULL)`. Without the partial indexes the nullable skill column permits duplicate rows; without the CHECK the blocking-requires-skill rule is unenforced.

6. Wrap metadata-complete taxonomy declarations inside `record_learning_event` when a new skill, error, or item is discovered, while rejecting bare unknown keys. ACCEPT_WITH_REQUIRED_CHANGE. I prefer this to my earlier separate `declare_*` calls: wrapping declarations in the same transaction as the attempt means a failed attempt rolls the new taxonomy back, so live teaching cannot leave orphan rows. Required change: a declaration is insert-if-absent and must not silently mutate an existing catalog entry. Re-declaring an existing key with different metadata must either no-op on the existing row or fail; it must never overwrite the canonical label, category, or severity. This keeps live teaching able to add taxonomy but never able to silently redefine it. Bare keys with no metadata still fail (unchanged).

7. Phase 1 excludes scene state, learner error state, mastery, Glossika relevance, replay, XP, and explanation memory, while remaining usable for a real lesson. ACCEPT. A real lesson can begin: the teacher gets channel-correct due skills and due items with their linked skills, records the `Dapat akong magpatingin` attempt atomically, and writes a concise summary. Scenes, mastery readout, and Glossika reuse are genuinely not on the critical path to a first usable lesson.

8. Dotted hierarchical skill keys as final. ACCEPT. Lowercase, dot-separated, ASCII, `category.subtype[.detail]`, validated by `^[a-z0-9]+(\.[a-z0-9_]+)+$`, with the leading segment equal to the skill's `category`. Examples `modal.base_form`, `clitic.second_position`, `aspect.contemplated`, `lex.health`. This groups and sorts naturally and lets the context query and humility flag key off the category prefix.

9. Glossika anchor-to-skill relevance in Phase 3, not Phase 1, despite one link table being eventually enough. ACCEPT. The user's Phase 1 boundary explicitly excludes Glossika relevance, and my own slicing already placed it in Phase 3. One link table (`glossika_anchor_skills`) remains the right and only first link table when Glossika enters.

## 2. Accepted decisions (no change requested)

Codex-as-teacher boundary; version-aware migrations; dotted keys; channel-keyed `skill_state` (production, recognition); scene as non-channel; `review_item_skills`; normalized rows authoritative with raw JSON audit only; remove `review_schedule`; remove `mastery_evidence`; no stored `mastered` status; defer `learner_error_state`, scenes, mastery derivation to Phase 2; defer replay, Glossika relevance, generated exports to Phase 3; defer XP and explanations beyond. Phase plan structure (`CONVERGED_PHASE_PLAN_V2.md`) is accepted with the Phase 1 boundary as written.

## 3. The eight additional Phase 1 details

### 1. Canonical attempt channel

Decision: option A. `attempts.channel` is authoritative; remove `channel` from `attempt_skill_credit`. One attempt is single-channel in this product (a production attempt or a recognition attempt), so every credit row inherits the attempt's channel; storing it again is denormalization that can diverge. New credit key is `(attempt_id, skill_id)`, which is correct because one attempt credits a given skill at most once.

How production and recognition stay separated in `skill_state`: replay and the live upsert read each credit row, take the channel from its parent attempt, and write `skill_state(learner_id, skill_id, attempts.channel)`. Because a production attempt and a recognition attempt are different rows with different `attempts.channel`, their credits land in different `skill_state` rows. The composite key `(learner_id, skill_id, channel)` is what guarantees no collision; the channel does not need to be repeated on the credit row to achieve that.

If Codex insists on keeping `attempt_skill_credit.channel` for self-contained evidence, the only acceptable form is a composite foreign key `attempt_skill_credit(attempt_id, channel) REFERENCES attempts(id, channel)` with `UNIQUE(id, channel)` on `attempts`, so equality is enforced by the schema, not by helper code that can be bypassed. Helper-only equality validation is not acceptable. I recommend option A as the smaller design.

### 2. Review-item channel validation

Enforce `attempt.channel = review_items.channel` by schema redesign, not helper validation alone. Add `UNIQUE(id, channel)` to `review_items` and a composite foreign key on `attempts`: `FOREIGN KEY (review_item_id, channel) REFERENCES review_items(id, channel)`. Because `attempts.channel` is NOT NULL and `review_item_id` is nullable, SQLite enforces the pair only when `review_item_id` is non-null (NULL `review_item_id` skips the constraint), which is exactly right: a free attempt with no stored item is unconstrained, and any attempt that does reference an item must match its channel. This makes it structurally impossible for a production attempt to consume a recognition item or update the wrong due row. Keep a helper assertion as defense in depth, but the schema is the guarantee.

### 3. Null-safe uniqueness for attempt errors

Confirm the preferred candidate, with the surrogate key and both partial indexes:

```
attempt_errors(
  id            INTEGER PRIMARY KEY,
  attempt_id    INTEGER NOT NULL REFERENCES attempts(id),
  error_id      INTEGER NOT NULL REFERENCES errors(id),
  skill_id      INTEGER REFERENCES skills(id),     -- nullable
  severity      TEXT NOT NULL,
  mastery_blocking INTEGER NOT NULL DEFAULT 0,
  notes         TEXT,
  CHECK (mastery_blocking = 0 OR skill_id IS NOT NULL)
);
CREATE UNIQUE INDEX ux_attempt_error_skill
  ON attempt_errors(attempt_id, error_id, skill_id) WHERE skill_id IS NOT NULL;
CREATE UNIQUE INDEX ux_attempt_error_global
  ON attempt_errors(attempt_id, error_id)            WHERE skill_id IS NULL;
```

This prevents duplicate rows for the same attempt, error, and non-null skill, and prevents more than one global row for the same attempt and error when skill is null, while still allowing one global row plus several skill-specific rows for the same attempt and error. SQLite supports partial unique indexes, so this is safe. The CHECK enforces that a mastery-blocking error names a skill.

### 4. Taxonomy source of truth

Confirm the preferred candidate, and adopt this exact resolution of the phrase "Git-seeded catalog plus explicit declarations": Git files seed the initial catalog at import; after import, SQLite is the single canonical mutable taxonomy; transactional declarations update SQLite (and only insert-if-absent, per question 6); a deterministic Git export may later mirror the taxonomy for human review but is never authoritative and never independently edited back in. Git and SQLite are never independently writable competing sources. The Git seed is an input event, not a live parallel store.

### 5. Audit JSON creation

Confirm the preferred flow, with one explicit prohibition: callers must not independently supply both normalized evidence and a separate arbitrary audit JSON string. The AI supplies one structured evaluation object; the helper validates it; the helper derives the normalized rows from that object; the helper serializes the same validated object into `evaluation_json`; the whole transaction commits or rolls back. Context and replay never parse `evaluation_json`. Because the JSON is the serialization of the exact object the normalized rows came from, they cannot diverge at write time; if a later read ever finds them disagreeing, normalized rows win and the mismatch is reported as an audit defect, never silently repaired (`CONVERGED_SCHEMA_V2.md:325-333`).

### 6. Listening constraint in Phase 1

Schema-level exclusion. The Phase 1 channel domain is exactly `CHECK (channel IN ('production','recognition'))` on `skill_state`, `attempts`, and `scheduling_events` (skill targets). Listening is documented as future and added by a later migration when audio actually exists. Do not include `listening` in the Phase 1 CHECK with helper-level rejection: an inactive value in the constraint is a value someone can write by mistake. "Reserved but inactive" in `CONVERGED_SCHEMA_V2.md:71` must mean reserved in documentation, absent from the Phase 1 CHECK. This is the one place the V2 wording needs to be made precise.

### 7. Scheduling-event target constraints

Confirm, with the exact one-hot CHECK and one clarification. Final Phase 1 rules:

```
scheduling_events(
  id, source_attempt_id NULL REFERENCES attempts(id),
  skill_id NULL REFERENCES skills(id),
  review_item_id NULL REFERENCES review_items(id),
  channel TEXT,            -- production|recognition for skill targets; NULL otherwise
  prev_due TEXT, next_due TEXT,
  decided_by TEXT NOT NULL CHECK (decided_by IN ('ai','helper_default','human')),
  reason TEXT, created_at TEXT NOT NULL,
  CHECK ( (skill_id IS NOT NULL) + (review_item_id IS NOT NULL) = 1 ),
  CHECK ( (skill_id IS NOT NULL AND channel IN ('production','recognition'))
       OR (skill_id IS NULL AND channel IS NULL) )
);
```

Exactly one of `skill_id` or `review_item_id` is populated; a skill target carries channel production or recognition; a review-item target carries channel NULL because the item row already carries its channel; previous and next due are auditable; `decided_by` covers AI, helper default, and human; no generic `unit_type + unit_id`. Required clarification: Phase 1 has no error scheduling target. The round-two prose left this open ("`error_id` or no error state target", `codex_response_round2.md:144`), but the V2 schema correctly lists only `skill_id` and `review_item_id` for Phase 1 (`CONVERGED_SCHEMA_V2.md:169-174`). Confirm the V2 form: recent error context in Phase 1 is evidence only and is not scheduled, so there is no error target until Phase 2.

### 8. Scope discipline

Confirm. Phase 1 contains exactly: clean canonical initial migration; migration versioning; channel-safe `skill_state`; learner-specific channel-safe `review_items`; `review_item_skills`; strict taxonomy resolution (with in-transaction declarations); atomic `record_learning_event`; `attempts`, `attempt_skill_credit`, skill-specific `attempt_errors`; typed `scheduling_events`; recent error evidence; due context for skills and items. No scenes, mastery, learner error projection, Glossika relevance, replay, XP, or explanation memory. The V2 Phase 1 table list (`CONVERGED_PHASE_PLAN_V2.md:28-52`) matches this exactly. I confirm the boundary.

## 4. Required amendments before implementation

1. Remove `attempt_skill_credit.channel`; `attempts.channel` is authoritative; credit key `(attempt_id, skill_id)`. If kept, only via composite FK to `attempts(id, channel)`, never helper-only validation. (Detail 1.)
2. Enforce review-item channel match with a composite FK `attempts(review_item_id, channel) REFERENCES review_items(id, channel)` and `UNIQUE(id, channel)` on `review_items`. (Detail 2.)
3. `attempt_errors`: surrogate `id` primary key, the two partial unique indexes, and `CHECK (mastery_blocking = 0 OR skill_id IS NOT NULL)`. (Question 5, detail 3.)
4. Phase 1 channel CHECK is exactly `('production','recognition')` on all channel columns; listening is added by a later migration, not present and helper-rejected. (Detail 6.)
5. `scheduling_events`: explicit one-hot CHECK over `skill_id` and `review_item_id`; skill target requires channel in production or recognition; non-skill target requires channel NULL; `decided_by IN ('ai','helper_default','human')`; no error target in Phase 1. (Detail 7.)
6. `record_learning_event` serializes `evaluation_json` itself from the single validated evaluation object; callers never pass both normalized rows and a separate JSON string. (Detail 5.)
7. In-transaction taxonomy declarations are insert-if-absent and must not silently mutate an existing catalog entry (no-op or fail on a key that already exists with different metadata). (Question 6.)

All seven are precise, local, and additive. None changes the product or the table set.

## 5. Architectural blocker

None. Every disagreement is a schema-detail tightening that makes a coherent Phase 1 stricter, not a conflict that prevents one.

## 6. Final verdict

SIGNED_OFF_WITH_LISTED_AMENDMENTS.

Codex can implement Phase 1 immediately after adopting the seven amendments in section 4. They are constraint and helper-flow details that can be written directly into the canonical `001` migration and `record_learning_event`; none requires another architecture round.

## 7. Exact Phase 1 implementation boundaries

In Phase 1: clean canonical `001`; `schema_migrations`, `learners`, `sessions`, `skills`, `skill_state` (channel-keyed), `review_items` (channel in identity), `review_item_skills`, `errors`, `attempts`, `attempt_skill_credit` (no channel column), `attempt_errors` (nullable skill, partial indexes, blocking CHECK), `scheduling_events` (typed one-hot targets, channel rule). Version-aware migrations; strict taxonomy resolution with in-transaction declarations; atomic `record_learning_event`; recent error evidence query; compact due context for due production skills, due recognition skills, due items with their linked skills, recent error occurrences (count, dates, severity, linked skill), and a small recent-attempt tail; deterministic export; per-category caps.

Not in Phase 1: `scenes`, `scene_skills`, `scene_state`, `learner_error_state`, active/watch/resolved error status, `derive_mastery`, any `mastered` status, `review_schedule`, `mastery_evidence`, Glossika tables and relevance, replay, `manual_correction_events`, XP, explanation memory, generated `progress.txt`. Scenes, learner error state, and mastery are Phase 2. Replay, Glossika relevance, manual-correction events, and generated exports are Phase 3.
