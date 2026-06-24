# Phase 1 Code Fix Plan

Date 2026-06-24. Bounded to Phase 1. No scenes, mastery, Glossika, learner error projection, replay, XP, or explanation memory are added. Target implementation: Tagalog-Codex `fcc7bb4`. Line references are to that commit.

## Migration strategy (applies to all schema fixes)

No live learner database exists (confirmed in `db/README.md:14` and `FINAL_AGREEMENT.md:35`). Therefore canonical `db/migrations/001_initial_schema.sql` may still be edited in place. All schema fixes below are edits to `001`, not new append-only migrations and not table-rebuild migrations. Append-only versioning begins only after the first real learner import. One consequence: do not promote any database that already recorded migration version 1 against the proof schema; fix F5 adds a guard so that cannot pass silently.

## Fix order

F1 (P0 ownership), F2 (P1 scheduling-event learner), F3 (P1 single due source), F4 (P1 channel match), F5 (P1 squash guard), F6 (P1 not_tested no-op), F7 (P1 zero-link), then the P2 batch F8 (timestamp), F9 (recent-attempts window), F10 (evidence FK restrict), F11 (migration atomicity). F1 first because it is the only P0. F2 to F7 are independent and can land in any order after F1. The P2 batch can follow.

---

## F1 (P0-1): tie attempt ownership to session and review item

Exact SQL change in `001`:

```sql
-- sessions: allow composite reference
CREATE TABLE sessions (
  ... existing columns ...
  , UNIQUE (id, learner_id)
);

-- review_items: allow learner+channel composite reference
CREATE TABLE review_items (
  ... existing columns ...
  , UNIQUE (id, learner_id, channel)   -- replaces or supplements UNIQUE(id, channel)
);

-- attempts: replace the two independent FKs with ownership-preserving composites
--   drop: FOREIGN KEY (review_item_id, channel) REFERENCES review_items(id, channel)
FOREIGN KEY (session_id, learner_id) REFERENCES sessions(id, learner_id),
FOREIGN KEY (review_item_id, learner_id, channel)
    REFERENCES review_items(id, learner_id, channel)
```

The review-item composite still has nullable `review_item_id`, so SQLite skips it when null (unchanged behaviour for attempts with no item) and enforces learner plus channel when present. This closes both the session mismatch and the cross-learner item reference with one change.

Exact helper change in `sqlite_store.py`: in `record_learning_event`, after reading `learner_id` and `session_id` (`:150-151`), assert the session belongs to the learner before the attempt insert, as defense in depth:

```python
owner = conn.execute("SELECT learner_id FROM sessions WHERE id = ?", (session_id,)).fetchone()
if owner is None or int(owner["learner_id"]) != learner_id:
    raise ValidationError("session does not belong to learner")
```

Exact test to add (`test_attempt_transaction.py`): create learner A and B, a session owned by A, then call `record_learning_event` with `learner_id=B, session_id=A_session`; assert `ValidationError`; assert zero attempts. Add a raw-insert variant asserting `sqlite3.IntegrityError` from the composite FK.

Exit: an attempt whose learner does not own its session or its review item cannot be inserted by helper or raw SQL.

## F2 (P1-1): give scheduling events a learner

Exact SQL change in `001`, `scheduling_events`:

```sql
learner_id INTEGER NOT NULL REFERENCES learners(id) ON DELETE CASCADE,
```

Exact helper change: `_record_scheduling_event` already receives `learner_id` (`:675`); add it to the INSERT column list and values (`:749-772`).

Exact test: record events for two learners on the same skill and channel; assert each `scheduling_events` row carries the correct `learner_id`; assert a `decided_by='human'` event with `source_attempt_id=NULL` still identifies its learner.

Exit: every scheduling event identifies its learner without depending on `source_attempt_id`.

## F3 (P1-2): one audited due path

Rule: `skill_state.due_at` changes only through scheduling-event application; credit rows never carry or write due. Review-item `due_at` set at creation is the genesis default; later changes go through a scheduling event.

Exact helper change: in `_upsert_skill_state_from_credit`, stop reading `credit.get("due_at")`; insert `due_at = NULL` and never set it on conflict (the function already omits it on update, `:650-656`). In `_validate_learning_event`, reject a credit that contains a `due_at` key so the single-source rule is explicit:

```python
if "due_at" in credit:
    raise ValidationError("skill credit must not carry due_at; due changes go through scheduling_events")
```

Exact test: a credit that includes `due_at` raises `ValidationError`; a normal credit leaves `skill_state.due_at` unchanged and adds no `scheduling_events` row; due only moves when a scheduling event is supplied.

Exit: no code path writes `skill_state.due_at` except `_record_scheduling_event`.

## F4 (P1-3): evidence-driven schedules must match the attempt channel

Exact helper change: in `record_learning_event`, validate each skill schedule against the attempt channel before applying. In the scheduling loop (`:246-252`) or in `_validate_schedule` given the event channel:

```python
for schedule in validated.get("scheduling_events", []):
    if schedule.get("target_type") == "skill" and schedule.get("channel") != channel:
        raise ValidationError("skill scheduling channel must equal attempt channel")
```

Cross-channel planning is not a Phase 1 operation; if it is ever needed it is a separate explicit helper, not a side effect of an attempt.

Exact test: a production event carrying a skill schedule with `channel=recognition` raises `ValidationError`; recognition `skill_state` is unchanged.

Exit: a production attempt can never change recognition state, matching `FINAL_AGREEMENT.md:67`.

## F5 (P1-5): guard the squashed-version collision

Exact helper change in `apply_migrations`: when a migration version is already recorded, verify the recorded name matches the file and that the expected schema is present, instead of silently skipping. Minimal form:

```python
recorded = {int(r["version"]): r["name"] for r in conn.execute("SELECT version, name FROM schema_migrations")}
...
if version in recorded:
    if recorded[version] != migration.name:
        raise ValidationError(
            f"version {version} already applied as {recorded[version]!r}, "
            f"refusing to treat {migration.name!r} as applied")
    continue
```

Optionally, after the loop, assert a canonical sentinel table exists (for example `attempts`) when version 1 is recorded, and raise if it does not. Pre-live safeguard: confirm no database carries a version-1 row from the proof before first import; since none should exist, this guard is belt and suspenders.

Exact test: pre-seed `schema_migrations` with version 1 named `001_old_proof` and an old table; `apply_migrations` raises rather than returning `[]` and leaving the canonical schema unbuilt.

Exit: an old-proof database cannot be silently treated as current.

## F6 (P1-4): make `not_tested` a projection no-op

Exact helper change: in `record_learning_event`, still insert the `attempt_skill_credit` row for `not_tested` (it is evidence the skill was considered), but skip the projection:

```python
if credit["credit"] != "not_tested":
    _upsert_skill_state_from_credit(conn, ...)
```

Exact test: a `not_tested` credit creates the credit row but no `skill_state` row, no `evidence_count` increment, no status or `last_seen_at` change.

Exit: a skill that was not tested gains no projected evidence or posture change.

## F7 (P1-6): require at least one skill link; reject silent role changes

Exact helper change: in `_validate_review_item_declaration`, require at least one link:

```python
if not declaration.get("skills"):
    raise ValidationError("review item must link at least one skill")
```

In `_declare_review_item`, replace `INSERT OR IGNORE` (`:527`) with conflict-aware behaviour: if the `(review_item_id, skill_id)` link exists with a different role, raise `ValidationError`; otherwise insert. This matches taxonomy conflict rejection (`_reject_conflict`).

Exact test: creating an item with no `skills` raises; re-declaring an existing link with a different role raises; `due_context` never returns an item with empty `linked_skills`.

Exit: every due review item arrives in context with at least one linked skill, and role changes are explicit, not silently dropped.

## F8 (P2-2): real session timestamp

Exact helper change: `start_session(..., started_at: str | None = None)`; when `None`, omit `started_at` from the INSERT so the column `DEFAULT CURRENT_TIMESTAMP` (`001:18`) fires.

Exact test: a session created with no explicit time has `started_at` close to now, not the frozen proof date.

## F9 (P2-3): consistent recent-attempt window

Exact helper change: `_recent_attempts(conn, learner_id, as_of, recent_days, limit)` adds `WHERE date(occurred_at) <= date(as_of) AND date(occurred_at) >= date(as_of, '-N days')`, matching `_recent_errors`. Pass `as_of` and `recent_days` from `due_context` (`:293`).

Exact test: an attempt dated after `as_of` is excluded from `recent_attempts`; recent attempts and recent errors share the same window.

## F10 (P2-4): do not cascade-delete immutable evidence

Exact SQL change in `001`: change `skill_id` foreign keys in `attempt_skill_credit` (`:129`), `attempt_errors` (`:140`), and `scheduling_events` (`:159`) from `ON DELETE CASCADE` to `ON DELETE RESTRICT`. Keep the policy that skills are retired (`active=0`), never deleted.

Exact test: deleting a referenced skill raises `IntegrityError`; evidence rows survive.

## F11 (P2-1): atomic migration application

Exact helper change in `apply_migrations`: apply each migration and record its version inside one explicit transaction so a failure leaves neither partial schema nor a half-recorded version. Because `executescript` issues its own commit, run the migration body and the version insert under a manual transaction, for example by disabling autocommit for the block (`conn.isolation_level` handling) or by executing statements within a single `BEGIN ... COMMIT` and inserting the version before commit. Verify with a deliberately failing temporary migration that nothing from it persists and its version is not recorded.

Exact test: a failing second migration leaves none of its objects and no version row; a re-run can proceed cleanly.

## Exit criteria for the whole plan

Both suites stay green after the edits. New tests cover P0-1, P1-1 through P1-6, and P2-1 through P2-4, each asserting the specific invariant rather than an incidental collision, and behaviour 7's test is strengthened to assert that a production event cannot change recognition state. The two broad `assertRaises(Exception)` rollback tests are narrowed to the specific exception type. After these land, canonical `001` carries the ownership composite keys, `scheduling_events.learner_id`, and `ON DELETE RESTRICT` on evidence; the helper enforces session ownership, single-source due, channel-matched schedules, `not_tested` no-op, at-least-one link, and migration-version integrity. At that point the layer is ready for the first real learner database and controlled live use.
