"""test_due_context_query.py -- the compact next-session context query.

When Tom says "continue", the AI does not run a scheduler service. It runs ONE
small query for what is due, weak, and recently wrong, then uses its own
judgment to build the lesson conversationally. This test pins that query's
behavior and proves the export is deterministic and AI-readable.

Pure stdlib + sqlite3.
    python3 tests/test_due_context_query.py
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "db"))

import tutor_db as t  # noqa: E402

TODAY = date(2026, 6, 24)   # recent window default 14d -> cutoff 2026-06-10


def build_db():
    conn = t.connect(":memory:")
    t.apply_migrations(conn)
    t.seed_reference_data(conn)
    lid = t.create_learner(conn, "tom", current_module="62")
    sid = t.open_session(conn, lid)

    # skill_state: a spread of due dates and statuses
    rows = [
        # slug,                  due,          status,  strength, lapses, last_review
        ("modal.base_form",      "2026-06-22", "lapsed", 0.9, 3, "2026-06-21"),  # overdue + weak
        ("voice.actor",          "2026-06-24", "active", 9.2, 0, "2026-06-15"),  # due today
        ("causative.magpa",      "2026-07-01", "active", 7.0, 0, "2026-06-20"),  # future -> excluded
        ("aspect.contemplated",  "2026-07-05", "leech",  0.6, 4, "2026-06-20"),  # weak, not due
    ]
    for slug, due, status, strength, lapses, lr in rows:
        conn.execute(
            "INSERT INTO skill_state (learner_id, skill_id, strength, due, last_review, reps, lapses, status) "
            "VALUES (?,?,?,?,?,1,?,?)",
            (lid, t.skill_id(conn, slug), strength, due, lr, lapses, status))

    # review_items: one overdue, one in the future
    conn.execute(
        "INSERT INTO review_items (learner_id, slug, intent_en, target_tl, due, status, source_kind) "
        "VALUES (?,?,?,?,?,?,?)",
        (lid, "item.health.dapat_magpatingin", "say you should see a doctor (now)",
         "Dapat akong magpatingin.", "2026-06-20", "active", "learner_error"))
    conn.execute(
        "INSERT INTO review_items (learner_id, slug, intent_en, target_tl, due, status, source_kind) "
        "VALUES (?,?,?,?,?,?,?)",
        (lid, "item.shopping.magkano", "ask the price politely",
         "Magkano po ito?", "2026-07-02", "active", "module_anchor"))

    # errors: active, watch, and resolved (resolved must NOT appear)
    conn.executemany(
        "INSERT INTO errors (learner_id, tag, description, status, occurrences, first_seen, last_seen) "
        "VALUES (?,?,?,?,?,?,?)",
        [
            (lid, "aspect.future_overmark_after_modal", "future after modal", "active", 3, "2026-06-10", "2026-06-23"),
            (lid, "clitic.placement", "clitic after hindi/dapat", "watch", 1, "2026-06-18", "2026-06-18"),
            (lid, "spelling.only", "ubo vs abo", "resolved", 2, "2026-06-05", "2026-06-12"),
        ])

    # attempts feeding recent_errors: one INSIDE the 14d window, one OUTSIDE
    err_id = conn.execute(
        "SELECT id FROM errors WHERE learner_id=? AND tag='aspect.future_overmark_after_modal'",
        (lid,)).fetchone()["id"]
    a_in = conn.execute(
        "INSERT INTO attempts (session_id, learner_id, occurred_on, response_tl) VALUES (?,?,?,?)",
        (sid, lid, "2026-06-23", "Dapat akong magpapatingin.")).lastrowid
    a_out = conn.execute(
        "INSERT INTO attempts (session_id, learner_id, occurred_on, response_tl) VALUES (?,?,?,?)",
        (sid, lid, "2026-06-01", "old attempt")).lastrowid
    conn.executemany("INSERT INTO attempt_errors (attempt_id, error_id) VALUES (?,?)",
                     [(a_in, err_id), (a_out, err_id)])

    # explanations: one for a DUE skill (should surface), one for a future skill (should not)
    conn.execute(
        "INSERT INTO explanations (learner_id, skill_id, text, effectiveness, last_used) VALUES (?,?,?,?,?)",
        (lid, t.skill_id(conn, "voice.actor"),
         "ako = I'm the doer; the verb starts with mag-/um-.", "landed", "2026-06-15"))
    conn.execute(
        "INSERT INTO explanations (learner_id, skill_id, text, effectiveness, last_used) VALUES (?,?,?,?,?)",
        (lid, t.skill_id(conn, "causative.magpa"),
         "magpa- = have it done to you.", "landed", "2026-06-20"))
    conn.commit()
    return conn, lid


def test_due_skills_are_only_those_due_today_or_earlier():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)
    slugs = [s["slug"] for s in ctx["due_skills"]]
    assert slugs == ["modal.base_form", "voice.actor"], slugs   # ordered by due asc
    assert "causative.magpa" not in slugs                       # future excluded
    assert "aspect.contemplated" not in slugs                   # future excluded


def test_due_items_surface_overdue_only():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)
    slugs = [i["slug"] for i in ctx["due_items"]]
    assert slugs == ["item.health.dapat_magpatingin"], slugs


def test_weak_skills_include_lapsed_and_leech():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)
    weak = {s["slug"] for s in ctx["weak_skills"]}
    assert "modal.base_form" in weak and "aspect.contemplated" in weak
    assert "voice.actor" not in weak


def test_active_errors_exclude_resolved():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)
    tags = {e["tag"] for e in ctx["active_errors"]}
    assert "aspect.future_overmark_after_modal" in tags
    assert "clitic.placement" in tags          # 'watch' counts as active context
    assert "spelling.only" not in tags         # resolved excluded


def test_recent_errors_respect_the_window():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)   # window 14d -> cutoff 2026-06-10
    rec = {e["tag"]: e["hits"] for e in ctx["recent_errors"]}
    # only the 2026-06-23 attempt is inside the window; the 2026-06-01 one is not
    assert rec.get("aspect.future_overmark_after_modal") == 1, rec


def test_explanations_only_for_due_skills():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)
    slugs = {e["slug"] for e in ctx["explanations_that_landed"]}
    assert "voice.actor" in slugs               # due -> surfaced
    assert "causative.magpa" not in slugs       # future -> not surfaced


def test_current_module_present():
    conn, lid = build_db()
    ctx = t.due_context(conn, lid, TODAY)
    assert ctx["learner"]["current_module"] == "62"
    assert ctx["as_of"] == "2026-06-24"


def test_export_is_deterministic_and_parseable():
    conn, lid = build_db()
    out1 = t.export_context_json(conn, lid, TODAY)
    out2 = t.export_context_json(conn, lid, TODAY)
    assert out1 == out2                          # stable ordering
    parsed = json.loads(out1)                    # valid JSON the AI can read
    assert parsed["due_skills"][0]["slug"] == "modal.base_form"
    # keys are sorted (deterministic export)
    assert list(parsed.keys()) == sorted(parsed.keys())


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS", name)
    print("ALL DUE-CONTEXT TESTS PASSED")


if __name__ == "__main__":
    main()
