"""test_database_smoke.py -- database creation + migrations are sound.

Proves the mechanical foundation only:
  * a fresh database can be created from db/migrations/*.sql
  * applying migrations is idempotent (re-running applies nothing)
  * every required table from the schema proposal exists
  * a learner and a session can be created
  * foreign-key enforcement is ON (a dangling reference is rejected)

No Tagalog judgment happens here. Pure stdlib. Runnable directly or via pytest:
    python3 tests/test_database_smoke.py
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "db"))

import tutor_db as t  # noqa: E402

REQUIRED_TABLES = {
    "schema_migrations", "learners", "sessions", "attempts", "skills", "skill_state",
    "review_items", "scenes", "scene_skills", "errors", "attempt_skill_credit",
    "attempt_errors", "scheduling_events", "mastery_evidence", "glossika_anchors",
    "explanations", "xp_events",
}
# Note: this first migration ships scene_skills (scene<->skill) but DEFERS
# review_item_skills. In phase 1 an exact item carries its skills via the
# attempt_skill_credit vector, so a separate item<->skill junction is not yet
# needed. The schema proposal documents this as a justified omission; a later
# migration can add it without touching existing data.


def fresh_db():
    conn = t.connect(":memory:")
    t.apply_migrations(conn)
    return conn


def test_migration_creates_schema_and_is_idempotent():
    conn = t.connect(":memory:")
    applied = t.apply_migrations(conn)
    assert applied == [1], applied
    # second run is a no-op
    assert t.apply_migrations(conn) == []
    versions = [r["version"] for r in conn.execute("SELECT version FROM schema_migrations")]
    assert versions == [1], versions


def test_required_tables_exist():
    conn = fresh_db()
    have = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    missing = {tbl for tbl in REQUIRED_TABLES if tbl not in have}
    assert not missing, f"missing tables: {missing}"


def test_create_learner_and_session():
    conn = fresh_db()
    lid = t.create_learner(conn, "tom", l1="German", current_module="62")
    assert lid == 1
    sid = t.open_session(conn, lid, kind="lesson")
    assert sid == 1
    row = conn.execute("SELECT handle, current_module FROM learners WHERE id=?", (lid,)).fetchone()
    assert row["handle"] == "tom" and row["current_module"] == "62"


def test_foreign_keys_enforced():
    conn = fresh_db()
    # a session pointing at a non-existent learner must be rejected
    try:
        conn.execute("INSERT INTO sessions (learner_id, kind) VALUES (999, 'lesson')")
        conn.commit()
        raised = False
    except sqlite3.IntegrityError:
        raised = True
    assert raised, "expected FK violation for dangling learner_id"


def test_seed_reference_data_is_idempotent():
    conn = fresh_db()
    t.seed_reference_data(conn)
    t.seed_reference_data(conn)  # twice -> still one row per slug
    n = conn.execute("SELECT COUNT(*) c FROM skills").fetchone()["c"]
    assert n == len(t.SKILL_CATALOG), n


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS", name)
    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
