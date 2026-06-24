# Claude Phase Slicing

Date 2026-06-24. The converged synthesis proposes one next phase with ten work items in a single migration (`Tagalog-Codex/collaboration/codex_synthesis_round1.md:309-326`). That is a small rewrite, not a bounded slice: it couples channel state, taxonomy strictness, review-item links, scene state, Glossika link tables, mastery derivation, and projected-state replay into one step, so nothing is testable until all of it lands and a regression anywhere blocks everything.

Below are three narrow slices. Each compiles, passes tests, and leaves the system usable. Phase 1 is the smallest change that materially improves the live AI teacher.

## Phase 1: Trustworthy writes and channel separation

Goal: the teacher can trust what it reads and writes. Recognition stops corrupting production, typos stop fragmenting the taxonomy, and the teacher knows what an item tests before Tom attempts it. This is the smallest slice with real value because it fixes the two defects that silently corrupt memory.

Exact schema changes (migration `002`):

- `skill_state` keyed `(learner_id, skill_id, channel)`; channel domain `('production','recognition','listening')`, listening inactive; `due_at` stays on this table.
- add `review_item_skills(review_item_id, skill_id, role)`.
- `attempt_skill_credit` gains `channel` in its primary key.
- `attempt_errors` gains a `mastery_blocking` boolean alongside `severity`.
- no `review_schedule` table, no `mastery_evidence` table.
- `scheduling_events` with typed nullable foreign keys (`skill_id`, `review_item_id`), a one-hot `CHECK`, `source_attempt_id`, `decided_by IN ('ai','helper_default','human')`, `prev_due`, `next_due`, `reason`.

Exact helper behaviour:

- version-skipping `apply_migrations` (port from `tagalog_tutor_project_starter/db/tutor_db.py:59-76`).
- `record_attempt` resolves every skill, error, and (where referenced) item key inside SQL and fails the whole transaction on any unknown key; no `INSERT OR IGNORE` in the write path.
- `record_attempt` writes, atomically: the attempt, channel-keyed `attempt_skill_credit`, `attempt_errors`, per-channel `skill_state` upsert (status, `due_at`, `evidence_count`), and one `scheduling_events` row per affected unit.
- explicit `declare_skill`, `declare_error`, `create_review_item` helpers, separate from `record_attempt`, requiring full metadata.
- `due_context` returns due skills split by channel, due items, and active plus recent errors, with per-category caps.

Exact tests:

- recognition attempt does not change the production `skill_state` row, and the reverse.
- unknown skill key rolls back the entire attempt (extend `tagalog_tutor_project_starter/tests/test_attempt_transaction.py:202-222` to channel-keyed credit).
- migration applied twice is a no-op (port `tests/test_database_smoke.py:42-49`).
- `review_item_skills` lets the context name what a due item tests before any attempt.
- due context separates production and recognition and respects per-category caps.

Explicit non-goals: scene state, mastery derivation, Glossika relevance, learner-error-state split, replay.

Exit criteria: an attempt updates only the correct channel; an unknown key fails cleanly; the context query briefs the teacher with channel-correct due skills and the skills each due item tests.

Can a real Tagalog lesson begin after this phase: yes. The teacher gets channel-correct due context, can run the `dapat` base-form drill, and can record the `magpatingin` attempt so it updates production without touching recognition.

## Phase 2: Honest mastery, scene memory, errors as state

Goal: the teacher can schedule scenes and trust a mastery claim. This slice adds the projections and the derived mastery read.

Exact schema changes (migration `003`):

- add `scene_state(learner_id, scene_id, status, due_at, support_level, notes)`; counts derived, not stored.
- add `learner_error_state(learner_id, error_id, status, occurrence_count, first_seen, last_seen, due_at)`, split from the `errors` taxonomy.

Exact helper behaviour:

- `record_attempt` updates `scene_state` and `learner_error_state` in the same transaction; messy scenes write at most a few attempts with `mode = 'messy_scene'` plus a `scene_state` update, never running counters.
- `derive_mastery(learner, skill, channel, as_of, policy)`: a read over `attempts`, `attempt_skill_credit`, `attempt_errors` enforcing unaided success, a delayed unaided success after the policy gap (default 2 days), at least two distinct dates, a controlled-variation success, a messy-scene success when scene-relevant, and no AI-flagged `mastery_blocking` failure in the policy window (default 7 days). Thresholds are versioned policy constants, not schema rules; the granting policy version is returned.
- `due_context` adds due scenes and active errors from `learner_error_state`.

Exact tests:

- mastery requires two distinct dates and the gap; three labels or one attempt cannot grant it (the explicit fix to `tagalog_tutor_project_starter/db/tutor_db.py:295,298-315`).
- a recognition success cannot grant production mastery.
- an AI-flagged blocking failure inside the window prevents mastery; outside the window it does not.
- a scene-relevant skill is not mastered without a messy-scene success.
- due context returns due scenes separately from due skills and items.

Explicit non-goals: Glossika relevance, replay, XP, explanations.

Exit criteria: `derive_mastery` returns mastered only on genuine multi-date delayed evidence; scenes and learner errors appear as scheduled state.

Can a real Tagalog lesson begin after this phase: yes, and it can now include scheduled scene work and an honest mastery readout, not just drills.

## Phase 3: Replay, Glossika relevance, progress export

Goal: memory is auditable and Glossika reuse is live. This slice hardens; the lesson loop already works from phase 1.

Exact schema changes (migration `004`):

- add `glossika_anchor_skills(anchor_id, skill_id, role)`.
- extend `glossika_anchors` with a controlled `recommended_use` enum, a `use_note`, a `naturalness_status` enum, and a nullable `production_target_override`.

Exact helper behaviour:

- `due_context` returns anchors only when linked to a selected due skill, or to the skill behind a due item, active error, or due scene, sorted by relevance bucket and capped; the active production target is `COALESCE(production_target_override, raw_tl)` used only when `naturalness_status` allows.
- `replay_skill_state(conn, learner)`: rebuild `skill_state` (per channel: status, `due_at`, `evidence_count`) from `attempts`, `attempt_skill_credit`, and `scheduling_events`, applying `decided_by = 'human'` corrections in timestamp order.
- generate `current/progress.txt` and a per-session markdown summary as deterministic read-only exports from SQLite.

Exact tests:

- replay reproduces live `skill_state` by semantic equality after a multi-attempt scenario that includes a manual-correction event, ignoring volatile timestamps.
- anchors are returned only when linked to a due target; unrelated active anchors are not returned (the explicit fix to `Tagalog-Codex/db/sqlite_store.py:578-590`).
- a stilted anchor is never offered as a production target.
- the deterministic export is stable across two runs.

Explicit non-goals: the three other anchor link tables, XP, explanations, scene and error replay (add when those projections need their own replay proof).

Exit criteria: projected `skill_state` is provably rebuildable from immutable evidence; the continue context surfaces only relevant Glossika; `progress.txt` is a generated artifact, not mutable state.

Can a real Tagalog lesson begin after this phase: it already could after phase 1; this phase makes the memory auditable and brings Tom's prior Glossika exposure back into the lesson.

## Why this ordering

Phase 1 fixes corruption (channel collisions, taxonomy fragmentation) and is the smallest slice that improves the live teacher, so it ships first and de-risks the part that silently damages memory. Phase 2 adds the projections and the one genuinely hard read (mastery) once the write path is trustworthy. Phase 3 proves auditability and adds Glossika reuse, which is valuable but not on the critical path to a usable lesson. Each migration is additive and independently testable, so a regression in one slice never blocks the others, which the single ten-item phase cannot promise.
