# Claude Phase 1 Final Verification

Date 2026-06-24. Reviewer: Claude, final narrow verification. Repaired implementation at Tagalog-Codex `e9043022548da04db620901e95a79b2cee401281` (repair commit `cfb6990`), against the prior review at Tagalog-Claude `3615f11` and the original implementation `fcc7bb4`. No file in the Codex repository was modified. All checks ran on a clean `git archive` export of `e904302`. Architecture is not reopened and no Phase 2 feature is proposed.

## 1. Test commands and actual results

```
python -m unittest discover -s tests   ->  Ran 41 tests ... OK
python -m pytest -q                     ->  41 passed, 17 subtests passed
```

Up from 21 tests at `fcc7bb4`. Both green on the repaired commit.

## 2. Diff inspected

`git diff --stat fcc7bb4..e904302`: 10 files, +1438 / -115. Migration renamed `001_initial_schema.sql` to `001_phase1_canonical.sql` (+36), `db/sqlite_store.py` (+342), new `tests/test_phase1_repairs.py` (+734, 20 tests), the three prior test files updated, and the agreement, implementation note, README, and a response document updated. I read each changed file and reproduced every closure independently rather than trusting the response.

## 3. Closure of every prior finding

Each row was reproduced against the repaired build with a fresh probe, not only by reading the added test.

| Finding | Severity | Status | Independent confirmation |
|---|---|---|---|
| P0-1 attempt under another learner's session | P0 | CLOSED | Helper raises `ValidationError` (session ownership check); raw insert raises `IntegrityError` from `FOREIGN KEY (session_id, learner_id)`. |
| P0-1b cross-learner review-item reference | P0 | CLOSED | Raw insert of learner B attempt against learner A item raises `IntegrityError` from `FOREIGN KEY (review_item_id, learner_id, channel)`; in-event declaration of another learner's item is rejected. |
| P1-1 scheduling events cannot identify learner | P1 | CLOSED | `scheduling_events.learner_id NOT NULL` present and populated; source-less human event still carries learner; a learner-less event is rejected; composite `(source_attempt_id, learner_id)` and `(review_item_id, learner_id)` FKs prevent dangling references. |
| P1-2 unaudited due write / insert-update divergence | P1 | CLOSED | A credit carrying `due_at` is rejected; a credit-only event leaves `skill_state.due_at` NULL with zero scheduling events; due changes only through `_record_scheduling_event`. |
| P1-3 production event reschedules recognition | P1 | CLOSED | A production event whose skill or item schedule names `recognition` raises `ValidationError`. |
| P1-4 not_tested corrupts the skill model | P1 | CLOSED | A `not_tested` credit writes the credit row but creates no `skill_state` row and no evidence increment. |
| P1-5 squashed-001 version collision | P1 | CLOSED | A database recording version 1 under the old name with `review_schedule` present now raises on `apply_migrations` (filename and canonical-signature validation), instead of silently skipping. |
| P1-6 zero-link items / silent role change | P1 | CLOSED | A review item with no skills is rejected; re-declaring a link with a different role raises; due context filters items with no links. |
| P2-1 migrations not atomic | P2 | CLOSED | A deliberately failing second migration leaves none of its objects and no version row (`BEGIN IMMEDIATE` plus rollback); duplicate versions are rejected. |
| P2-2 frozen proof timestamp / module default | P2 | CLOSED | `start_session` records a real `CURRENT_TIMESTAMP`; `create_learner` module default is NULL, not `62`. |
| P2-3 recent_attempts ignored as_of | P2 | CLOSED | A future-dated attempt no longer appears in `recent_attempts` for an earlier `as_of`; the window matches recent errors. |
| P2-4 cascade deletes immutable evidence | P2 | CLOSED | Deleting a referenced skill raises `IntegrityError` (`ON DELETE RESTRICT` on credit, error, and scheduling references). |

No finding is PARTIALLY_CLOSED or STILL_OPEN.

## 4. Added repairs verified

Event cannot declare another learner's review item: confirmed (`record_learning_event` rejects a declaration whose `learner_id` differs from the event). Schedule input cannot mutate posture: a schedule carrying `state_status` is rejected, and `_record_scheduling_event` updates only `due_at`, never status. Channel and mode matrix enforced in both layers: an invalid combination (recognition with contrast) is rejected by helper `ValidationError` and by the table CHECK. Context caps and `recent_days` reject invalid input: unknown cap key, negative, over-50, boolean, and out-of-range `recent_days` all raise. Rollback tests use specific exception types: no `assertRaises(Exception)` remains; tests use `ValidationError`, `sqlite3.IntegrityError`, or `sqlite3.OperationalError`. Every due-date change through the helper creates a scheduling event: due is written only inside `_record_scheduling_event`, which always inserts the event row; the credit and item-creation paths no longer write due at all.

## 5. Regressions introduced

None found. The three prior test files were updated consistently with the stricter contract and pass. The repaired schema preserves all previously verified strengths (no channel on credit, listening excluded, null-safe attempt-error uniqueness, composite review-item channel enforcement now extended with learner ownership).

## 6. Non-blocking notes

These do not block the first real database or a dry lesson and are not reopened findings or architecture changes.

First, genesis due seeding has no dedicated helper. Because review-item creation now rejects `due_at` and all due changes flow through scheduling events, seeding initial due dates at import (for example the OVERDUE and D3/D7 items in `progress.txt`) is done by writing an attempt-less scheduling event. I confirmed that path is schema-supported: an event with `source_attempt_id` NULL, `learner_id` set, and `decided_by='helper_default'` is accepted, and a learner-less event is rejected. A thin import helper that wraps the projected-due write plus the scheduling-event insert would make this cleaner, but it is not required for correctness.

Second, the canonical schema signature in `_validate_canonical_schema` is pinned to the exact Phase 1 table set, so it will need updating when the first Phase 2 migration adds tables. This is expected for a Phase 1 guard and is correct as-is for Phase 1.

## 7. Final verdict

`PASS_WITH_NON_BLOCKING_NOTES`.

The one P0, six P1, and four P2 findings from the prior review are all closed and independently reproduced as fixed, the six additional repairs hold, both suites pass at 41 tests with specific exception assertions, and no regression was introduced. The two notes above are advisory only.

## 8. May Codex proceed to real learner import and dry lesson

Yes. The memory layer is safe for the first real learner database and a dry lesson. Initial due dates should be seeded at import through attempt-less scheduling events (the schema-supported path confirmed above) rather than by setting `due_at` at item creation. Nothing else is required before import.
