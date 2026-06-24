# Claude Convergence Deltas

Date 2026-06-24. A delta against Codex's `CONVERGED_SCHEMA_DRAFT.md` at Tagalog-Codex `f80c672`, not a new architecture. Each proposed table gets one verdict: KEEP, SIMPLIFY, MERGE, DEFER, or REMOVE. Evidence cites real files in both repositories.

## 1. Table-by-table verdict

| Table (converged draft) | Verdict | Delta |
|---|---|---|
| `schema_migrations` | SIMPLIFY | Keep; adopt version-skipping execution from `tagalog_tutor_project_starter/db/tutor_db.py:59-76`. Drop `checksum` unless a checksum test exists; it is unused surface otherwise. |
| `learners` | KEEP | Keep identity and `current_module` pointer. Move "preferred teaching constraints" to the git profile, not a column. |
| `sessions` | KEEP | One sitting, kind, AI summary. Also export the summary to git markdown (response Q28). |
| `skills` | KEEP | Catalog only. Fix canonical key style first (response Q7). No insert during attempt recording. |
| `skill_state` | KEEP | Channel-keyed `(learner_id, skill_id, channel)`. Channel domain `('production','recognition','listening')` only; listening inactive. `due_at` lives here and is part of the schedule source of truth. |
| `review_items` | KEEP | Scarce, promotion-gated. `due_at`/`status` on the item is its own schedule source. |
| `review_item_skills` | KEEP | Adopt from Codex (`db/migrations/001_initial_schema.sql:74-79`). Require at least one link by default; allow a lexical/pragmatic catalog skill instead of forcing structural links (response Q9). |
| `scenes` | KEEP | Catalog. |
| `scene_skills` | KEEP | Intended coverage. |
| `scene_state` | SIMPLIFY | Keep only `learner_id, scene_id, status, due_at, support_level, notes`. Derive `last_attempted_on`, `last_success_on`, `success_count`, `blocking_error_count`, `communication_success` from `attempts` (response Q4). |
| `attempts` | SIMPLIFY | Keep normalized columns as authoritative. `evaluation_json` is retained as write-once audit only and is never read by replay or context (response Q4). |
| `attempt_skill_credit` | KEEP | Channel in the primary key (`db/migrations/001_initial_schema.sql:132`). This plus `attempts` is the canonical basis for mastery. |
| `attempt_errors` | KEEP | Add a `mastery_blocking` boolean beside `severity` (response Q14). |
| `errors` | KEEP | Canonical taxonomy. Resolve-or-fail, no auto-create (`db/sqlite_store.py:89-106` is the defect). |
| `learner_error_state` | MERGE | Adopt; it merges Codex severity with my active/recent context (`tagalog_tutor_project_starter/db/tutor_db.py:358-373`). `due_at` here is part of the schedule source of truth. |
| `review_schedule` | REMOVE | Two writable sources of due with per-entity `due_at` (response Q30). The open queue becomes a query. Polymorphic target also lacks integrity (`db/migrations/001_initial_schema.sql:158-163`). |
| `scheduling_events` | KEEP | Redesign targets: typed nullable foreign keys with a one-hot `CHECK`, plus `source_attempt_id`, `decided_by` in `('ai','helper_default','human')`, `prev_due`, `next_due`, `reason`. Drop the `review_schedule_id` dependency. |
| `mastery_evidence` | REMOVE | Duplicates facts already in `attempts` + `attempt_skill_credit` + `attempt_errors`; Codex also misuses it for every credit including failures (`db/sqlite_store.py:279-304`). Derive mastery at read time. |
| `glossika_anchors` | SIMPLIFY | Keep. `recommended_use` becomes a controlled enum plus a free-text note; add `naturalness_status` enum and nullable `production_target_override` (response Q18, Q19). |
| `glossika_anchor_skills` | KEEP | The one anchor link table phase one needs. Include a `role`. |
| `glossika_anchor_errors` | DEFER | Route error relevance through skill (response Q17). |
| `glossika_anchor_review_items` | DEFER | Route item relevance through skill. |
| `glossika_anchor_scenes` | DEFER | Route scene relevance through skill. |
| `landed_explanations` | DEFER | Unproven; agree with the draft (`CONVERGED_SCHEMA_DRAFT.md:279-282`). |
| `xp_events` | DEFER | Not needed to prove the loop. |
| `progress_exports` | DEFER | Use a deterministic export file, not a table. |

## 2. Canonical immutable evidence

These are append-only and never rewritten:

- `attempts` (one meaningful production; `occurred_at`, `mode`, channel via the credit rows, normalized outcomes, `evaluation_json` as audit only),
- `attempt_skill_credit` (the partial-credit vector, channel in the key),
- `attempt_errors` (with `severity` and `mastery_blocking`),
- `scheduling_events` (every due change, including `decided_by = 'human'` manual corrections).

No `mastery_evidence` row exists. Mastery is not stored evidence; it is a read over the four above.

## 3. Projected state (a rebuildable cache)

- `skill_state` per `(learner, skill, channel)`: `status`, `due_at`, `evidence_count`, `last_seen_at`,
- `review_items`: `due_at`, `status`,
- `scene_state`: `status`, `due_at`, `support_level`, `notes`,
- `learner_error_state`: `status`, `occurrence_count`, `first_seen`, `last_seen`, `due_at`.

Every projected row is reconstructable from the immutable evidence plus the versioned policy. This is what the replay test proves.

## 4. Schedule source of truth

Option A. `due_at` lives on each typed projected-state table and is the only writable due. `scheduling_events` is the immutable audit and replay log. There is no separate `review_schedule` table. The "open queue" the teacher reads on continue is a query: the union of rows where `due_at <= as_of` across `skill_state`, `review_items`, `scene_state`, and `learner_error_state`, ranked by due date then priority, capped per category.

Why not a canonical `review_schedule` with no due fields on entities (option B): it forces a polymorphic target table whose integrity is hard to enforce in SQLite (the current draft `CHECK` requires at least one target, not exactly one, and does not match `target_type` to the populated foreign key, `db/migrations/001_initial_schema.sql:158-163`), and it has no channel, so it cannot separate production and recognition due. Co-locating due with the typed entity avoids all of that.

Why not both (option C): two writable sources drift. If a materialized queue is ever needed for performance, and at one learner it is not, it returns as an explicitly derived read-only cache rebuilt from entity due fields, never written directly.

## 5. Modality handling

Two active channels, production and recognition, as separate `skill_state` rows and separate `attempt_skill_credit` rows. Recognition can inform the teacher but never advances production state, enforced structurally by the channel key, not by a weighting multiplier. Listening is a reserved channel value, inactive, and never gates mastery. Scene competence is not a channel; it is `scene_state`.

## 6. Scene state

Smallest useful projection: `learner_id, scene_id, status, due_at, support_level, notes`. Counts and last-dates are derived from `attempts` filtered to the scene. A messy scene records a session row, a few `attempts` with `mode = 'messy_scene'`, their credit and error rows, and updates `scene_state.status`, `due_at`, and `support_level`. It does not maintain running counters.

## 7. Mastery derivation

Mastery is a read, not a row. `derive_mastery(learner, skill, channel='production', as_of, policy)` returns mastered or not plus the reasons, computed from immutable evidence:

1. at least one unaided production success: `attempt_skill_credit.credit = 'success_no_hint'`, channel production,
2. at least one delayed unaided success after the policy gap (default 2 days) measured on `attempts.occurred_at`,
3. successes on at least two distinct dates,
4. at least one controlled-variation success: a success on an attempt with `mode = 'controlled_variation'` crediting the skill,
5. at least one messy-scene success when the skill is scene-relevant (the skill appears in `scene_skills` for a scene the learner attempted): a success on `mode = 'messy_scene'`,
6. no AI-flagged `mastery_blocking` failure for that skill inside the policy window (default 7 days).

Database verifies dates, channels, modes, credits, distinct dates, gaps, and blocking-failure recency. The AI supplies the judgments those facts encode: whether a production was truly unaided (the `credit` value), whether a variation tests the same skill (by crediting that skill on a `controlled_variation` attempt), whether scene use was communicatively successful (the scene attempt outcome), and whether a failure is structural and blocking (the `mastery_blocking` flag). Thresholds are versioned policy in the helper, not schema rules, and the granting policy version is recorded on the decision.

## 8. Error creation pathway

Two pathways, clearly separated.

Strict at write time: `record_attempt` resolves every referenced skill, error, and scene key, and fails the whole transaction on any unknown key (my rollback discipline, `tagalog_tutor_project_starter/db/tutor_db.py:200-207`). No `INSERT OR IGNORE` inside the write path.

Explicit and deliberate for genuine discovery: separate `declare_skill`, `declare_error`, `declare_scene`, and `create_review_item` helpers that require full metadata (label, category, severity default, and so on). The AI calls these on purpose when it judges an observation new. A bare misspelled key arriving inside a credit row carries no metadata and is not a declare call, so it fails. This is the line between a typo that must fail and a new teaching observation that must not break the tutor.

## 9. Glossika linking

Phase one ships `glossika_anchor_skills(anchor_id, skill_id, role)` only, with `role` controlled. The continue context returns anchors only when they link to a selected due skill, or to the skill behind a due item, active error, or due scene. Item, error, and scene relevance route through skill, so the other three anchor link tables are deferred until a retrieval cannot be served that way. `recommended_use` is a controlled enum plus a free-text note; the active production target is `COALESCE(production_target_override, raw_tl)` used only when `naturalness_status` allows. Raw corpus stays immutable.

## 10. Replay strategy

Canonical events are `attempts`, `attempt_skill_credit`, `attempt_errors`, and `scheduling_events`. Two columns have two different owners: evidence-derived fields (`status`, `evidence_count`) are recomputed from attempts and credits plus policy; the AI-decided `due_at` is reconstructed from the latest `scheduling_events` row per unit, because the AI's chosen interval is a judgment not recomputable from attempts alone. Manual corrections are immutable `scheduling_events` rows with `decided_by = 'human'`, applied in timestamp order. Replay tolerates taxonomy change by keying evidence on the surrogate `skill_id`, never the slug, and by retiring rather than deleting skills. The replay test asserts semantic equality on meaningful columns, ignoring volatile audit timestamps. Phase one replays `skill_state` only; scene and error replay arrive with those projections.
