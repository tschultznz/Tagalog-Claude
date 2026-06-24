# Final Agreement Proposal

Status: signable architecture for Phase 1. Date 2026-06-24. Agreed between Claude `5bd7fd4` and Codex `6ece25c`. Verdict: SIGNED_OFF_WITH_LISTED_AMENDMENTS. This is the document to copy into the canonical Codex repository after sign-off. It incorporates the seven amendments from `collaboration/claude_final_review.md` section 4.

## 1. AI-teacher boundary

Codex (or Claude, or ChatGPT) is the conversational Tagalog teacher. It interprets free Tagalog, judges meaning, accepts valid alternatives, explains grammar, rules on naturalness and register, adapts drills, answers arbitrary questions, runs text-based messy speaking, decides what an error means, and decides what is worth recording. SQLite and the helper layer are persistent memory: they store and retrieve, enforce structure and atomicity, return compact due context, and keep an audit trail. They never judge Tagalog, never generate a lesson, never require commands, never run a background process, and never form a separate app. Every judgment value stored arrives from the AI as data.

## 2. Canonical Phase 1 tables

`schema_migrations` (integer version, name, applied_at; no checksum yet). `learners` (stable key, current_module pointer; preferences stay in the Git profile). `sessions` (learner FK, kind, timestamps, AI summary). `skills` (dotted ASCII hierarchical key `^[a-z0-9]+(\.[a-z0-9_]+)+$`, practical label, linguistic label, category, active flag). `skill_state` (PK `(learner_id, skill_id, channel)`; status as review posture only; due_at, evidence_count, last_seen_at, lapse_count, notes). `review_items` (learner-specific; item key; channel; mode; prompt; optional target; `UNIQUE(id, channel)`; uniqueness over learner, key, channel). `review_item_skills` (item FK, skill FK, role; at least one link by default). `errors` (key, label, default severity). `attempts` (session FK, learner FK, nullable review_item FK, occurred_at, channel, mode, prompt, response, normalized outcome columns, evaluation_json as audit only; composite FK `(review_item_id, channel) REFERENCES review_items(id, channel)`). `attempt_skill_credit` (attempt FK, skill FK, credit; PK `(attempt_id, skill_id)`; no channel column, channel inherited from the attempt). `attempt_errors` (surrogate id PK, attempt FK, error FK, nullable skill FK, severity, mastery_blocking, notes; two partial unique indexes; `CHECK (mastery_blocking = 0 OR skill_id IS NOT NULL)`). `scheduling_events` (nullable source_attempt FK, one-hot `skill_id` or `review_item_id`, channel, prev_due, next_due, decided_by, reason).

Channel domain is exactly `('production','recognition')` in every channel column in Phase 1.

## 3. Canonical immutable evidence

`attempts`, `attempt_skill_credit`, `attempt_errors`, and `scheduling_events`. These are append-only and are the single source from which projected state is rebuilt. `evaluation_json` on `attempts` is audit only and is never parsed by context or replay.

## 4. Projected state (rebuildable cache)

`skill_state` per `(learner, skill, channel)`: status, due_at, evidence_count, last_seen_at, lapse_count. `review_items`: due_at, status. Both are derivable from the immutable evidence plus policy. No `mastered` status exists; mastery is a read introduced in Phase 2.

## 5. Due-date source of truth

`due_at` on the typed projected tables (`skill_state`, `review_items`) is the only writable due. `scheduling_events` is the immutable due-change history and the replay authority for due. The open review queue is a query: the union of projected rows with `due_at <= as_of`, ranked by due date then priority, capped per category. There is no `review_schedule` table.

## 6. Channel semantics

Production and recognition are separate channels and separate `skill_state` rows; a recognition attempt never updates production state and the reverse, guaranteed by the composite key. `attempts.channel` is authoritative for an attempt and all its credits. Review items carry their own channel, so production and recognition uses of the same source sentence are separate rows with separate due state, enforced by the composite foreign key from `attempts`. Scene competence is not a channel. Listening is not in the Phase 1 channel domain and is added by a later migration when audio exists.

## 7. Taxonomy creation

Git files seed the initial catalog at import. After import, SQLite is the single canonical mutable taxonomy. Unknown keys referenced during an attempt fail the transaction. A genuinely new skill, error, or item is created through a metadata-complete declarations section inside the same `record_learning_event` transaction, so a failed attempt rolls the new taxonomy back. Declarations are insert-if-absent and never silently mutate an existing entry. A bare key with no metadata always fails. A deterministic Git export may mirror the taxonomy for review but is never authoritative and never edited back independently; Git and SQLite are never competing writable sources.

## 8. Transaction boundary

`record_learning_event` runs one transaction that writes, or rolls back entirely: optional metadata-complete declarations, the attempt, its skill-credit vector, its skill-specific and global error rows, and one scheduling event per affected skill or item with the projected `due_at` update. Any unknown reference or constraint failure aborts the whole event. Recognition and production updates land in their own `skill_state` rows by channel.

## 9. Audit JSON rule

The AI supplies one structured evaluation object. The helper validates it, derives the normalized rows from it, and serializes that same validated object into `evaluation_json`. Callers never supply both normalized rows and a separate JSON string. Context and replay read only normalized rows. If a read ever finds JSON and rows disagreeing, normalized rows win and the mismatch is reported as an audit defect, never silently repaired.

## 10. Removed and deferred structures

Removed: `review_schedule`, `mastery_evidence`, `xp_events`, `landed_explanations`, generic `unit_type + unit_id` targets, auto-creation of taxonomy, stored `mastered` status. Deferred to Phase 2: `scenes`, `scene_skills`, `scene_state`, `learner_error_state`, active/watch/resolved error status, `derive_mastery`. Deferred to Phase 3: `glossika_anchors`, `glossika_anchor_skills`, `manual_correction_events`, skill-state replay, generated `progress.txt` and session exports. Deferred beyond: other anchor link tables, XP, explanation memory, scene and error replay.

## 11. Phase 1 acceptance tests

Migration applied twice is a no-op. An unknown skill, error, or item key rolls back the whole learning event. A metadata-complete declaration plus a failing attempt roll back together. A recognition credit does not change the production `skill_state` row, and the reverse. A production attempt cannot reference a recognition review item (composite FK rejects it). A review item exposes its linked skills before any attempt. `attempt_errors` with `mastery_blocking = 1` and null skill fails; a non-blocking global error with null skill succeeds; duplicate `(attempt, error, skill)` and duplicate global `(attempt, error)` rows are rejected. A scheduling event populates exactly one typed target; a skill event requires channel; a non-skill event requires channel null. Due context returns due production skills, due recognition skills, due items with linked skills, recent error evidence (count, dates, severity, linked skill, not active/watch/resolved), and a small recent-attempt tail, each within per-category caps. The deterministic export is stable across two runs.

Exit: a real Codex lesson can start on `continue`, the teacher sees production and recognition due separately and what each due item tests, records the `Dapat akong magpatingin` attempt atomically, and writes a concise summary. Typos fail instead of fragmenting the taxonomy.

## 12. Phase 2 and Phase 3 boundaries

Phase 2 adds `scenes`, `scene_skills`, `scene_state` (status, due_at, support_level, notes; counts derived), and `learner_error_state` (active, watch, resolved), plus `derive_mastery(learner, skill, channel, as_of, policy_version)` as a read over the attempt model and scene facts. Phase 2 default mastery policy: an unaided production success, a delayed unaided success after a 2-day gap, successes on at least two distinct dates, a controlled-variation success, a messy-scene success when scene-relevant, and no AI-flagged mastery-blocking failure in the last 7 days. Listening is not required. Due context gains due scenes and active learner error state.

Phase 3 adds `glossika_anchors` (controlled `recommended_use`, `use_note`, `naturalness_status`, nullable `production_target_override`), `glossika_anchor_skills` as the single relevance link, and `manual_correction_events`. It adds skill-state replay from immutable evidence with semantic equality, relevance-filtered Glossika anchors in `continue`, and deterministic generated `progress.txt` and per-session exports. Mastery thresholds are versioned policy in the derivation layer, not schema rules, and are revisited once real sessions exist.
