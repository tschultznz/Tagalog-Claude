"""test_attempt_transaction.py -- the narrow database proof.

ONE real learner production, evaluated BY THE AI (supplied here as data), is
written together with every consequence in a single atomic transaction:

    expected:  Dapat akong magpatingin.
    learner:   Dapat akong magpapatingin.   (future-overmarked the verb after a modal)

The test demonstrates, against a real SQLite database:
  * partial credit to multiple skills from one answer (4 pass, 2 fail)
  * error pattern recorded and linked to the attempt
  * future reviews created/updated (failed skills due tomorrow, passed pushed out)
  * mastery evidence recorded (and NOT enough to wrongly promote a failed skill)
  * the whole write is ATOMIC: a bad credit entry rolls everything back

IMPORTANT: this test does NOT evaluate Tagalog. The evaluation dict is the live
AI teacher's verdict, supplied as input -- because judging the language is the
AI's job, not the database's. Pure stdlib + sqlite3.
    python3 tests/test_attempt_transaction.py
"""
import os
import sqlite3
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "db"))

import tutor_db as t  # noqa: E402

TODAY = date(2026, 6, 23)

# Prior projected state for the six skills the answer touches.
# (slug -> last_review, strength, status, lapses)
PRIOR = {
    "voice.actor":            ("2026-06-14", 8.0, "active", 0),
    "causative.magpa":        ("2026-06-17", 6.0, "active", 0),
    "clitic.second_position": ("2026-06-18", 5.0, "active", 0),
    "lex.health":             ("2026-06-20", 4.0, "active", 0),
    "modal.base_form":        ("2026-06-20", 3.0, "active", 2),
    "aspect.contemplated":    ("2026-06-21", 2.0, "active", 1),
}

# The AI teacher's verdict on this one production -- SUPPLIED, not computed.
EVALUATION = {
    "meaning_ok": True,
    "register_ok": True,
    "naturalness": "understandable",
    "corrected_tl": "Dapat akong magpatingin.",
    "reason": "After dapat, keep the verb in base form -- dapat already carries the 'should' sense.",
    "credit_vector": [
        {"skill": "voice.actor",            "outcome": "pass"},
        {"skill": "causative.magpa",        "outcome": "pass"},
        {"skill": "clitic.second_position", "outcome": "pass"},
        {"skill": "lex.health",             "outcome": "pass"},
        {"skill": "modal.base_form",        "outcome": "fail"},
        {"skill": "aspect.contemplated",    "outcome": "fail"},
    ],
    "error_tags": [
        {"tag": "aspect.future_overmark_after_modal",
         "description": "future-marked the verb after a modal (dapat)"},
    ],
}


def build_db():
    conn = t.connect(":memory:")
    t.apply_migrations(conn)
    t.seed_reference_data(conn)
    lid = t.create_learner(conn, "tom")
    sid = t.open_session(conn, lid)
    for slug, (lr, strength, status, lapses) in PRIOR.items():
        conn.execute(
            "INSERT INTO skill_state (learner_id, skill_id, strength, due, last_review, reps, lapses, status) "
            "VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
            (lid, t.skill_id(conn, slug), strength, lr, lr, lapses, status))
    conn.commit()
    return conn, lid, sid


def schedule_from(evaluation):
    """Build the AI-decided schedule. Here we take the transparent default that
    the AI is free to override (decided_by='helper_default'); the point is that
    the next_due lands in the DB, not which formula produced it."""
    sched = []
    for e in evaluation["credit_vector"]:
        slug, outcome = e["skill"], e["outcome"]
        lr = date.fromisoformat(PRIOR[slug][0])
        next_due, interval, reason = t.suggest_due(outcome, TODAY, last_review=lr)
        sched.append({
            "unit_type": "skill", "skill": slug,
            "next_due": next_due, "interval_days": interval, "reason": reason,
            "decided_by": "helper_default",
            "lapse": outcome == "fail",
            "status": "lapsed" if outcome == "fail" else "active",
            "strength": PRIOR[slug][1],
        })
    return sched


def record(conn, lid, sid, evaluation, mastery=None, xp=None):
    return t.record_attempt(
        conn, session_id=sid, learner_id=lid, occurred_on=TODAY,
        prompt_shown="I should go get myself looked at (see a doctor).",
        response_tl="Dapat akong magpapatingin.",
        evaluation=evaluation, schedule=schedule_from(evaluation),
        mastery=mastery, xp=xp)


# ---------------------------------------------------------------------------
def test_partial_credit_recorded():
    conn, lid, sid = build_db()
    aid = record(conn, lid, sid, EVALUATION)
    rows = conn.execute(
        "SELECT s.slug, c.outcome FROM attempt_skill_credit c "
        "JOIN skills s ON s.id = c.skill_id WHERE c.attempt_id = ?", (aid,)).fetchall()
    outcomes = {r["slug"]: r["outcome"] for r in rows}
    assert len(outcomes) == 6, outcomes
    passed = [s for s, o in outcomes.items() if o == "pass"]
    failed = [s for s, o in outcomes.items() if o == "fail"]
    assert len(passed) == 4 and len(failed) == 2, (passed, failed)
    assert outcomes["modal.base_form"] == "fail"
    assert outcomes["voice.actor"] == "pass"


def test_error_recorded_and_linked():
    conn, lid, sid = build_db()
    aid = record(conn, lid, sid, EVALUATION)
    err = conn.execute(
        "SELECT id, tag, status, occurrences FROM errors WHERE learner_id = ?", (lid,)).fetchone()
    assert err["tag"] == "aspect.future_overmark_after_modal"
    assert err["status"] == "active" and err["occurrences"] == 1
    link = conn.execute(
        "SELECT 1 FROM attempt_errors WHERE attempt_id = ? AND error_id = ?",
        (aid, err["id"])).fetchone()
    assert link is not None


def test_future_reviews_created():
    conn, lid, sid = build_db()
    record(conn, lid, sid, EVALUATION)
    due = {r["slug"]: r for r in conn.execute(
        "SELECT s.slug, ss.due, ss.lapses, ss.status FROM skill_state ss "
        "JOIN skills s ON s.id = ss.skill_id WHERE ss.learner_id = ?", (lid,))}
    # failed skills come back tomorrow and take a lapse
    assert due["modal.base_form"]["due"] == "2026-06-24"
    assert due["modal.base_form"]["lapses"] == 3 and due["modal.base_form"]["status"] == "lapsed"
    assert due["aspect.contemplated"]["due"] == "2026-06-24"
    # passed skills are pushed into the future (strictly later than tomorrow)
    for slug in ("voice.actor", "causative.magpa", "clitic.second_position", "lex.health"):
        assert due[slug]["due"] > "2026-06-24", (slug, due[slug]["due"])
        assert due[slug]["status"] == "active"
    # one immutable scheduling event per affected unit
    n = conn.execute("SELECT COUNT(*) c FROM scheduling_events").fetchone()["c"]
    assert n == 6, n


def test_one_answer_moves_skills_both_directions():
    conn, lid, sid = build_db()
    record(conn, lid, sid, EVALUATION)
    # compare next_due vs the prior due implied by last_review: failed shrank, passed grew
    ev = conn.execute(
        "SELECT unit_id, prev_due, next_due FROM scheduling_events").fetchall()
    # at least one came earlier (relearn) and at least one went later (expand)
    earlier = [r for r in ev if r["next_due"] <= "2026-06-24"]
    later = [r for r in ev if r["next_due"] > "2026-06-29"]
    assert earlier and later, (len(earlier), len(later))


def test_mastery_evidence_does_not_promote_a_failed_skill():
    conn, lid, sid = build_db()
    # supply scene + variation evidence for the FAILED skill, but no unaided
    # delayed production -> gate not met -> must NOT become 'mastered'.
    mastery = [
        {"skill": "modal.base_form", "evidence_type": "scene_use"},
        {"skill": "modal.base_form", "evidence_type": "variation_handled"},
    ]
    record(conn, lid, sid, EVALUATION, mastery=mastery)
    status = conn.execute(
        "SELECT ss.status FROM skill_state ss JOIN skills s ON s.id = ss.skill_id "
        "WHERE ss.learner_id = ? AND s.slug = 'modal.base_form'", (lid,)).fetchone()["status"]
    assert status == "lapsed", status  # failed this attempt; cannot be mastered


def test_mastery_promotes_only_with_full_phase1_evidence():
    conn, lid, sid = build_db()
    # voice.actor passed; give it the three phase-1 evidence types -> mastered.
    # (listening_check is deliberately NOT supplied and NOT required.)
    mastery = [
        {"skill": "voice.actor", "evidence_type": "unaided_delayed_production"},
        {"skill": "voice.actor", "evidence_type": "scene_use"},
        {"skill": "voice.actor", "evidence_type": "variation_handled"},
    ]
    record(conn, lid, sid, EVALUATION, mastery=mastery)
    status = conn.execute(
        "SELECT ss.status FROM skill_state ss JOIN skills s ON s.id = ss.skill_id "
        "WHERE ss.learner_id = ? AND s.slug = 'voice.actor'", (lid,)).fetchone()["status"]
    assert status == "mastered", status


def test_transaction_rolls_back_on_bad_credit_entry():
    conn, lid, sid = build_db()
    # baseline counts
    def counts():
        return {tbl: conn.execute(f"SELECT COUNT(*) c FROM {tbl}").fetchone()["c"]
                for tbl in ("attempts", "attempt_skill_credit", "errors",
                            "scheduling_events", "mastery_evidence")}
    before = counts()
    bad = {**EVALUATION, "credit_vector": [
        {"skill": "voice.actor", "outcome": "pass"},      # valid, inserted first
        {"skill": "does.not.exist", "outcome": "fail"},   # bogus -> NULL skill_id -> IntegrityError
    ]}
    raised = False
    try:
        t.record_attempt(conn, session_id=sid, learner_id=lid, occurred_on=TODAY,
                         response_tl="x", evaluation=bad, schedule=[])
    except sqlite3.IntegrityError:
        raised = True
    assert raised, "expected IntegrityError on bogus skill slug"
    after = counts()
    assert before == after, (before, after)  # nothing partially written


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS", name)
    print("ALL ATTEMPT-TRANSACTION TESTS PASSED")


if __name__ == "__main__":
    main()
