# Claude Phase 1 Code Review

Date 2026-06-24. Reviewer: Claude, adversarial code review. Canonical implementation reviewed at Tagalog-Codex `fcc7bb478ee2e1885e1a39e5a0b1d257cd872405`. Agreement at `dbe5e1c`. Claude sign-off at `b3117b9`. No file in the Codex repository was modified. All probes ran on a clean `git archive` export of the commit, never on the working tree.

## 1. Test commands and actual results

Both required commands were run from a clean export of the reviewed commit.

```
python -m unittest discover -s tests   ->  Ran 21 tests ... OK
python -m pytest -q                     ->  21 passed, 6 subtests passed in ~3s
```

pytest was not preinstalled in the review environment; I installed it to satisfy the second command. Both suites are green at the reviewed commit.

## 2. Files reviewed

`architecture/FINAL_AGREEMENT.md`, `architecture/PHASE1_IMPLEMENTATION.md`, `db/README.md`, `db/migrations/001_initial_schema.sql`, `db/sqlite_store.py`, `tests/test_database_smoke.py`, `tests/test_attempt_transaction.py`, `tests/test_due_context_query.py`.

## 3. Implementation strengths (verified, not just claimed)

All seven signed amendments from `b3117b9` actually landed and hold up under probing. `attempt_skill_credit` has no channel column and key `(attempt_id, skill_id)` (`001_initial_schema.sql:127-134`). The review-item channel composite foreign key genuinely rejects a production attempt against a recognition item (`:124`, reproduced: insert raised IntegrityError). `attempt_errors` has the surrogate id, both partial unique indexes, and the blocking-requires-skill CHECK, all enforced at the schema level (`:136-154`, reproduced). The Phase 1 channel domain is schema-restricted to production and recognition (`:44`, `:60`, `:110`). Scheduling events use one-hot typed targets with a channel CHECK and no generic `unit_type` (`:156-173`). Key validation is defense in depth: dotted-key CHECK constraints in SQL plus regex validation in the helper. `record_learning_event` is genuinely atomic: unknown skill, error, or item keys roll the whole event back (reproduced; zero rows left). Conflicting declarations are rejected rather than silently mutating taxonomy (`sqlite_store.py:535-545`, test passes). This is a careful, high-quality implementation of the agreed schema. The defects below are real but narrow, and all are fixable before the first real database because canonical `001` may still be edited.

## 4. Findings

### P0

**P0-1. Attempt can be stored under one learner inside another learner's session.** `attempts.session_id` and `attempts.learner_id` are independent foreign keys with no constraint tying the attempt's learner to the session's owner (`001_initial_schema.sql:106-107`), and `record_learning_event` takes both fields from the event object without checking they agree (`sqlite_store.py:150-151`). This ambiguously assigns canonical learner memory: an attempt can claim learner B while sitting in learner A's session, so audit and future replay cannot say whose sitting produced it.

Reproduction (clean export):
```
learner A id=1, learner B id=2, session sA owned by A
raw INSERT attempts(session_id=sA, learner_id=2) -> ACCEPTED: attempt.learner=2 session.owner=1
record_learning_event(learner_id=2, session_id=sA) -> HELPER ALSO ACCEPTED
```
Related schema gap in the same family: an attempt can reference another learner's `review_item`, because the composite foreign key checks only `(review_item_id, channel)`, not learner (`:124`). Reproduced: learner B's attempt referenced learner A's item and was accepted. The helper resolves items within the learner, so this is reachable only by raw insert today, but the same composite-key fix closes both.

### P1

**P1-1. `scheduling_events` cannot identify the learner.** The table has a global `skill_id` and a channel but no `learner_id` (`001_initial_schema.sql:156-173`), and `source_attempt_id` is nullable with `ON DELETE SET NULL` (`:158`). The agreement names `scheduling_events` the immutable due-change history and replay authority (`FINAL_AGREEMENT.md:84,93`). Today the learner is recoverable only by joining `source_attempt_id` to `attempts`. Reproduced: after `DELETE FROM learners` cascades away the attempts, the scheduling event survives with `source_attempt_id=NULL`, `skill_id=1`, `channel=production`, and no way to attribute it. A source-less `decided_by='human'` correction (allowed now, used in Phase 3) would have the same problem from creation. Smallest fix is option A: `learner_id NOT NULL` on every scheduling event.

**P1-2. Due state has an unaudited write path, and insert and update diverge.** `_upsert_skill_state_from_credit` writes `skill_state.due_at` directly from `credit.due_at` with no scheduling event (`sqlite_store.py:663`), and the `ON CONFLICT` branch does not touch `due_at` at all (`:650-656`). So a skill credit can change due state without any row in the agreed due-history table, and the behavior differs between first credit and later credits. Reproduced:
```
1st credit due_at=2026-07-09 -> skill_state.due_at=2026-07-09, scheduling_events=0   (unaudited)
2nd credit due_at=2099-01-01 -> skill_state.due_at=2026-07-09                          (silently ignored on update)
```
This violates the agreement that `scheduling_events` is the due authority (`FINAL_AGREEMENT.md:86-93`); replay from events could not reproduce `skill_state.due_at`.

**P1-3. A production event can reschedule recognition.** `_record_scheduling_event` uses the schedule's own channel for skill targets (`sqlite_store.py:686`) and `_validate_schedule` never checks it against the attempt channel (`:354-371`). The agreement states plainly that a production attempt never updates recognition state (`FINAL_AGREEMENT.md:67`). Reproduced: a production learning event carrying a skill schedule with `channel=recognition` set the recognition `skill_state.due_at` to 2027-01-01 while production stayed null. This is a direct violation of a signed channel-isolation invariant.

**P1-4. `not_tested` credit corrupts the skill model.** Every credit, including `not_tested`, flows through `_upsert_skill_state_from_credit` (`sqlite_store.py:201-217`), which has no `not_tested` guard. Reproduced: a `not_tested` credit created a `skill_state` row with `status='watch'`, `evidence_count=1`, and `last_seen_at` set. A skill that was explicitly not tested should not gain evidence or change posture. The credit enum includes `not_tested` (`001_initial_schema.sql:131`), so this is reachable in normal use.

**P1-5. Squashed-`001` version collision silently skips the canonical schema.** Migration version is parsed from the filename, so both the old proof and the new canonical schema are version 1. `apply_migrations` skips any version already in `schema_migrations` (`sqlite_store.py:54-64`). Reproduced: a database that recorded version 1 from the proof and still has `review_schedule` was opened with the new helper; `apply_migrations` returned `[]`, `attempts` was never created, and stale `review_schedule` remained, yet the database was treated as up to date. No real database exists yet, so this must be guarded before the first one is created.

**P1-6. Review items can exist with zero linked skills and appear in context with no explanation; link role changes are silently dropped.** `_declare_review_item` requires no skill link and inserts links with `INSERT OR IGNORE` (`sqlite_store.py:523-531`). Reproduced: an item created with `skills` omitted has zero links and `due_context` returns it with `linked_skills=[]`, so a due production item reaches the teacher with no statement of what it tests. Separately, re-declaring an existing link with `role='contrasts'` left the stored role as `tests` (silently ignored). The agreement and the Claude amendment expect at least one link by default (`FINAL_AGREEMENT.md:51`, `CONVERGED_SCHEMA_V2` review-item note).

### P2

**P2-1. Migrations are not atomic.** `apply_migrations` runs `executescript` then a separate version insert, and `executescript` auto-commits (`sqlite_store.py:65-69`). Reproduced with a deliberately broken second migration: `t2` was partially created and a row inserted even though the migration raised, and version 2 was not recorded. Canonical `001` is idempotent (`CREATE TABLE IF NOT EXISTS`), so first application is safe, but any future non-idempotent migration that fails midway leaves partial schema with no version row and cannot cleanly re-run.

**P2-2. `start_session` defaults to the frozen proof timestamp.** The default `started_at` is `"2026-06-24T00:00:00+08:00"` (`sqlite_store.py:106`), not the current time, while the column already has `DEFAULT CURRENT_TIMESTAMP` (`001_initial_schema.sql:18`). Reproduced: a session created with no explicit time recorded the fixed proof date rather than now. Real sessions would carry a wrong timestamp unless every caller overrides it.

**P2-3. `recent_attempts` ignores `as_of`; window semantics differ from `recent_errors`.** `_recent_attempts` has no date filter (`sqlite_store.py:897-921`) while `_recent_errors` bounds by the window and by `<= as_of` (`:860-894`). Reproduced: an attempt dated 2026-07-01 appeared in `recent_attempts` for a `due_context(as_of='2026-06-25')` call, while `recent_error_evidence` was empty. For live `continue` at today there is no future data, but any historical or audit query leaks future attempts and the two lists disagree on their window.

**P2-4. Deleting a skill cascade-deletes immutable evidence.** `attempt_skill_credit.skill_id`, `attempt_errors.skill_id`, and `scheduling_events.skill_id` are `ON DELETE CASCADE` to `skills` (`001_initial_schema.sql:129,140,159`). Reproduced: `DELETE FROM skills` dropped the only `attempt_skill_credit` row, erasing immutable evidence. The agreed model retires skills (`active=0`) rather than deleting them, but the schema should not allow an evidence wipe; `ON DELETE RESTRICT` is safer.

## 5. Suspected findings rejected as NOT_A_BUG

Channel duplication on `attempt_skill_credit`: already removed; the column is absent and the key is `(attempt_id, skill_id)`. Listening at the schema level: already excluded from every channel CHECK. Review-item channel composite foreign key: implemented and enforced (verified). `attempt_errors` null-safe uniqueness: the surrogate key plus two partial indexes work exactly as specified (verified). `review_schedule` and `mastery_evidence`: confirmed absent. Replay, scenes, mastery, learner error state, Glossika, XP, explanation memory: deferred to Phase 2 or 3 by the agreement, not Phase 1 bugs.

## 6. Test-coverage gaps

No test exercises any of P0-1, P1-1, P1-2, P1-3, P1-4, P1-6, P2-1 (atomicity or squash), P2-2, or P2-3. Two rollback tests use broad `assertRaises(Exception)` (`test_attempt_transaction.py:339,378`) and trigger failure through incidental primary-key or unique-index collisions rather than the invariant under test, so they would pass even if the intended guard were absent. Behavior 7 in the coverage table ("production credit does not update recognition") is asserted only by checking that a normal production event creates no recognition rows; it does not test the real invariant that a production event cannot change recognition state, which P1-3 shows is violable. So the test exists but covers a weaker, nearby property than the agreement's invariant.

## 7. Are the claimed 28 acceptance behaviours genuinely covered

Mostly yes, with one substantive exception and one caveat. Each of the 28 (the table lists 29 rows) maps to a passing test, and the structural behaviours (channel key, no-channel credit, partial error indexes, blocking CHECK, one-hot scheduling targets, channel exclusion, deterministic export, caps, taxonomy conflict rejection) are genuinely and well covered. The exception is behaviour 7: its test does not cover the stated channel-isolation invariant, which is violable through a scheduling event (P1-3). The caveat is that two atomicity behaviours (12 and 24) are proven via collisions and broad exception matching rather than the specific failure path. The 28-behaviour set is real coverage of the happy path and the structural constraints, but it does not cover the ownership, due-audit, cross-channel, `not_tested`, migration-safety, or date-window invariants, all of which this review found violable.

## 8. Final verdict

`BLOCK_BEFORE_LIVE_DATABASE`.

The implementation is high quality and faithfully implements the signed schema, and there is no architectural problem. But it carries one P0 (cross-learner attribution) and six P1 defects, including a direct violation of a signed channel-isolation invariant (P1-3), an unaudited due-write path that undermines the agreed replay authority (P1-2), and a migration-version collision that would silently skip the canonical schema on any stale database (P1-5). Because no live learner database exists yet, every fix can be made by editing canonical `001` and the helper in place, with no table-rebuild migration. These must be patched before any real database is created, after which the layer is ready for controlled live use. The bounded fix plan is in `architecture/PHASE1_CODE_FIX_PLAN.md`.

## 9. Summary counts

P0: 1 (P0-1, which also folds in the cross-learner review-item reference). P1: 6 (P1-1 scheduling-event learner identity, P1-2 unaudited due path, P1-3 cross-channel reschedule, P1-4 not_tested projection, P1-5 squash-version collision, P1-6 zero-link review item). P2: 4 (P2-1 through P2-4). Rejected as NOT_A_BUG: 6 areas. Deferred features (not bugs): scenes, mastery, learner error state, Glossika relevance, replay, XP, explanations.
