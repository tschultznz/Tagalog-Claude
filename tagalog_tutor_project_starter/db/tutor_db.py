"""tutor_db.py -- the deterministic MEMORY layer for the AI Tagalog teacher.

What this module is
-------------------
A thin, auditable set of helper functions over a SQLite database. It does the
boring, mechanical, *deterministic* work that should never depend on a language
model:

  * open a connection with foreign keys enforced
  * apply SQL migrations
  * write one learner production (an "attempt") and ALL of its consequences
    -- partial-credit vector, error rows, schedule changes, mastery evidence,
    xp -- in ONE atomic transaction
  * answer the compact "what is due / weak / recent" context query
  * export that context as deterministic, AI-readable JSON
  * offer a tiny, transparent default review interval the AI may OVERRIDE

What this module is NOT
-----------------------
It does not interpret Tagalog, grade an answer, decide what a sentence
exercised, judge naturalness, or generate a lesson. Every judgment value it
stores (meaning_ok, per-skill outcome, error tags, naturalness, the chosen due
date) arrives from the live AI teacher as plain input. The database is memory;
the AI is the teacher.

Pure standard library (sqlite3, json, datetime). No third-party deps.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_DIR = os.path.join(HERE, "migrations")


# ---------------------------------------------------------------------------
# connection + migrations
# ---------------------------------------------------------------------------
def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Open a connection with FK enforcement and Row access."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        " applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    return {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}


def apply_migrations(conn: sqlite3.Connection, migrations_dir: str = MIGRATIONS_DIR) -> list[int]:
    """Apply every *.sql in version order that has not yet been applied.

    Idempotent: re-running applies nothing. Returns the versions applied THIS call.
    """
    done = applied_versions(conn)
    newly: list[int] = []
    for fname in sorted(os.listdir(migrations_dir)):
        if not fname.endswith(".sql"):
            continue
        version = int(fname.split("_", 1)[0])
        if version in done:
            continue
        with open(os.path.join(migrations_dir, fname), encoding="utf-8") as f:
            conn.executescript(f.read())
        newly.append(version)
    conn.commit()
    return newly


# ---------------------------------------------------------------------------
# small lookups
# ---------------------------------------------------------------------------
def skill_id(conn: sqlite3.Connection, slug: str) -> int | None:
    row = conn.execute("SELECT id FROM skills WHERE slug = ?", (slug,)).fetchone()
    return row["id"] if row else None


def _d(value) -> str:
    """Normalize a date or 'YYYY-MM-DD' string to a string."""
    return value.isoformat() if isinstance(value, date) else value


# ---------------------------------------------------------------------------
# transparent default scheduler (a SUGGESTION the AI overrides)
# ---------------------------------------------------------------------------
def suggest_due(outcome: str, today: date, last_review: date | None = None) -> tuple[date, int, str]:
    """A deliberately tiny, transparent default interval.

    This is NOT an FSRS engine and carries no trained weights. It exists only so
    that "review dates work without a scheduler service": when the AI does not
    feel strongly, it can take this default; when it does, it passes its own
    next_due and this is ignored. Returns (next_due, interval_days, reason).
    """
    if outcome in ("fail", "partial"):
        return today + timedelta(days=1), 1, f"{outcome}->relearn next day"
    if outcome == "pass_hinted":
        return today + timedelta(days=2), 2, "hinted pass->short interval"
    if outcome == "pass":
        gap = (today - last_review).days if last_review else 1
        interval = max(2, min(gap * 2, 21))  # gentle expansion, capped for n=1 sanity
        return today + timedelta(days=interval), interval, "unaided pass->expand interval"
    # n/a or unknown: do not touch scheduling
    return None, 0, "no schedule change"  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# error registry
# ---------------------------------------------------------------------------
def _bump_error(conn: sqlite3.Connection, learner_id: int, tag: str,
                description: str | None, today_s: str) -> int:
    """Upsert a recurring error pattern; return its id."""
    conn.execute(
        "INSERT INTO errors (learner_id, tag, description, status, occurrences, first_seen, last_seen) "
        "VALUES (?,?,?,'active',0,?,?) "
        "ON CONFLICT(learner_id, tag) DO NOTHING",
        (learner_id, tag, description, today_s, today_s),
    )
    conn.execute(
        "UPDATE errors SET occurrences = occurrences + 1, last_seen = ?, "
        "status = CASE WHEN status = 'resolved' THEN 'active' ELSE status END "
        "WHERE learner_id = ? AND tag = ?",
        (today_s, learner_id, tag),
    )
    return conn.execute(
        "SELECT id FROM errors WHERE learner_id = ? AND tag = ?", (learner_id, tag)
    ).fetchone()["id"]


# ---------------------------------------------------------------------------
# THE atomic writer
# ---------------------------------------------------------------------------
def record_attempt(conn: sqlite3.Connection, *,
                   session_id: int,
                   learner_id: int,
                   occurred_on,
                   response_tl: str,
                   evaluation: dict,
                   item_id: int | None = None,
                   scene_id: int | None = None,
                   modality: str = "production",
                   mode: str = "drill",
                   prompt_shown: str | None = None,
                   hint_level: str = "none",
                   schedule: list[dict] | None = None,
                   mastery: list[dict] | None = None,
                   xp: list[dict] | None = None) -> int:
    """Persist one AI-evaluated production and ALL its consequences atomically.

    `evaluation` is the AI teacher's verdict, supplied as data, e.g.::

        {
          "meaning_ok": True, "register_ok": True, "naturalness": "understandable",
          "corrected_tl": "Dapat akong magpatingin.",
          "reason": "After dapat keep the verb in base form.",
          "credit_vector": [
             {"skill": "voice.actor", "outcome": "pass"},
             {"skill": "modal.base_form", "outcome": "fail"}, ... ],
          "error_tags": [
             {"tag": "aspect.future_overmark_after_modal",
              "description": "future-marked the verb after a modal"} ]
        }

    `schedule` is a list of due changes the AI decided (or took from
    suggest_due), each like::

        {"unit_type": "skill", "skill": "modal.base_form",
         "next_due": date(2026,6,24), "interval_days": 1,
         "reason": "fail->relearn", "decided_by": "ai",
         "lapse": True, "status": "lapsed", "strength": 0.9}

    Everything below runs inside a single `with conn:` block. If ANY statement
    raises (e.g. an unknown skill slug -> NOT NULL violation), the whole thing
    rolls back and no partial evidence is left behind.
    """
    today_s = _d(occurred_on)
    ev = evaluation
    with conn:  # BEGIN; COMMIT on success, ROLLBACK on any exception
        cur = conn.execute(
            "INSERT INTO attempts "
            "(session_id, learner_id, item_id, scene_id, occurred_on, modality, mode, "
            " prompt_shown, response_tl, hint_level, meaning_ok, register_ok, naturalness, "
            " corrected_tl, reason) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, learner_id, item_id, scene_id, today_s, modality, mode,
             prompt_shown, response_tl, hint_level,
             _b(ev.get("meaning_ok")), _b(ev.get("register_ok")), ev.get("naturalness"),
             ev.get("corrected_tl"), ev.get("reason")),
        )
        attempt_id = cur.lastrowid

        # partial-credit vector -- resolve slug INSIDE SQL so an unknown skill
        # makes skill_id NULL -> NOT NULL violation -> atomic rollback.
        for entry in ev.get("credit_vector", []):
            conn.execute(
                "INSERT INTO attempt_skill_credit (attempt_id, skill_id, outcome) "
                "VALUES (?, (SELECT id FROM skills WHERE slug = ?), ?)",
                (attempt_id, entry["skill"], entry["outcome"]),
            )

        # error rows
        for etag in ev.get("error_tags", []):
            err_id = _bump_error(conn, learner_id, etag["tag"],
                                 etag.get("description"), today_s)
            conn.execute(
                "INSERT OR IGNORE INTO attempt_errors (attempt_id, error_id) VALUES (?,?)",
                (attempt_id, err_id),
            )

        # schedule changes -> update projected state + log immutable event
        for ch in (schedule or []):
            _apply_schedule_change(conn, learner_id, attempt_id, today_s, ch)

        # mastery evidence (immutable; mastery is derived from these rows)
        for m in (mastery or []):
            conn.execute(
                "INSERT INTO mastery_evidence (learner_id, skill_id, evidence_type, attempt_id) "
                "VALUES (?, (SELECT id FROM skills WHERE slug = ?), ?, ?)",
                (learner_id, m["skill"], m["evidence_type"], attempt_id),
            )
            _maybe_promote_to_mastered(conn, learner_id, m["skill"])

        # xp (optional)
        for x in (xp or []):
            conn.execute(
                "INSERT INTO xp_events (learner_id, attempt_id, kind, points) VALUES (?,?,?,?)",
                (learner_id, attempt_id, x["kind"], x.get("points", 0)),
            )

    return attempt_id


def _b(v):
    return None if v is None else (1 if v else 0)


def _apply_schedule_change(conn, learner_id, attempt_id, today_s, ch) -> None:
    unit_type = ch["unit_type"]
    next_due = _d(ch.get("next_due"))
    if unit_type == "skill":
        sid = skill_id(conn, ch["skill"])
        if sid is None:
            raise ValueError(f"unknown skill slug in schedule: {ch['skill']}")
        row = conn.execute(
            "SELECT due FROM skill_state WHERE learner_id = ? AND skill_id = ?",
            (learner_id, sid),
        ).fetchone()
        prev_due = row["due"] if row else None
        # upsert projected state
        conn.execute(
            "INSERT INTO skill_state (learner_id, skill_id, strength, due, last_review, reps, lapses, status) "
            "VALUES (?,?,?,?,?,1,?,?) "
            "ON CONFLICT(learner_id, skill_id) DO UPDATE SET "
            "  strength = excluded.strength, due = excluded.due, last_review = excluded.last_review, "
            "  reps = skill_state.reps + 1, "
            "  lapses = skill_state.lapses + ?, "
            "  status = excluded.status",
            (learner_id, sid, ch.get("strength", 0.0), next_due, today_s,
             1 if ch.get("lapse") else 0, ch.get("status", "active"),
             1 if ch.get("lapse") else 0),
        )
        unit_id = sid
    elif unit_type == "item":
        unit_id = ch["item_id"]
        prev = conn.execute("SELECT due FROM review_items WHERE id = ?", (unit_id,)).fetchone()
        prev_due = prev["due"] if prev else None
        conn.execute(
            "UPDATE review_items SET due = ?, last_review = ?, reps = reps + 1, "
            "lapses = lapses + ?, status = ?, strength = ? WHERE id = ?",
            (next_due, today_s, 1 if ch.get("lapse") else 0,
             ch.get("status", "active"), ch.get("strength", 0.0), unit_id),
        )
    else:  # scene
        unit_id = ch["scene_id"]
        prev_due = None

    conn.execute(
        "INSERT INTO scheduling_events "
        "(attempt_id, unit_type, unit_id, prev_due, next_due, interval_days, reason, decided_by) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (attempt_id, unit_type, unit_id, prev_due, next_due,
         ch.get("interval_days"), ch.get("reason"), ch.get("decided_by", "ai")),
    )


# phase-1 mastery gate: listening_check is NOT required
REQUIRED_MASTERY_EVIDENCE = ("unaided_delayed_production", "scene_use", "variation_handled")


def _maybe_promote_to_mastered(conn, learner_id, slug) -> None:
    sid = skill_id(conn, slug)
    if sid is None:
        return
    have = {
        r["evidence_type"]
        for r in conn.execute(
            "SELECT DISTINCT evidence_type FROM mastery_evidence "
            "WHERE learner_id = ? AND skill_id = ?",
            (learner_id, sid),
        )
    }
    if all(req in have for req in REQUIRED_MASTERY_EVIDENCE):
        conn.execute(
            "UPDATE skill_state SET status = 'mastered' "
            "WHERE learner_id = ? AND skill_id = ? AND status != 'lapsed'",
            (learner_id, sid),
        )


# ---------------------------------------------------------------------------
# the compact next-session context query  (what "continue" reads)
# ---------------------------------------------------------------------------
def due_context(conn: sqlite3.Connection, learner_id: int, today, recent_days: int = 14) -> dict:
    """Return the compact context the AI uses to BUILD a lesson conversationally.

    Deterministic and small on purpose. The AI does the teaching; this only
    surfaces what is due, weak, and recently wrong, plus explanations known to
    land. Ordering is stable so the export is reproducible.
    """
    today_s = _d(today)
    cutoff = _d((today if isinstance(today, date) else date.fromisoformat(today)) - timedelta(days=recent_days))

    learner = conn.execute(
        "SELECT handle, l1, current_module FROM learners WHERE id = ?", (learner_id,)
    ).fetchone()

    due_skills = [dict(r) for r in conn.execute(
        "SELECT s.slug, ss.status, ss.strength, ss.due, ss.lapses, ss.reps "
        "FROM skill_state ss JOIN skills s ON s.id = ss.skill_id "
        "WHERE ss.learner_id = ? AND ss.due IS NOT NULL AND ss.due <= ? "
        "ORDER BY ss.due ASC, s.slug ASC",
        (learner_id, today_s),
    )]

    due_items = [dict(r) for r in conn.execute(
        "SELECT id, slug, intent_en, target_tl, due, status "
        "FROM review_items WHERE learner_id = ? AND due IS NOT NULL AND due <= ? "
        "ORDER BY due ASC, id ASC",
        (learner_id, today_s),
    )]

    weak_skills = [dict(r) for r in conn.execute(
        "SELECT s.slug, ss.status, ss.lapses, ss.due "
        "FROM skill_state ss JOIN skills s ON s.id = ss.skill_id "
        "WHERE ss.learner_id = ? AND (ss.status IN ('lapsed','leech') OR ss.lapses >= 2) "
        "ORDER BY ss.lapses DESC, s.slug ASC",
        (learner_id,),
    )]

    active_errors = [dict(r) for r in conn.execute(
        "SELECT tag, description, status, occurrences, last_seen "
        "FROM errors WHERE learner_id = ? AND status IN ('active','watch') "
        "ORDER BY occurrences DESC, tag ASC",
        (learner_id,),
    )]

    recent_errors = [dict(r) for r in conn.execute(
        "SELECT e.tag, COUNT(*) AS hits, MAX(a.occurred_on) AS last_on "
        "FROM attempt_errors ae "
        "JOIN attempts a ON a.id = ae.attempt_id "
        "JOIN errors e ON e.id = ae.error_id "
        "WHERE a.learner_id = ? AND a.occurred_on >= ? "
        "GROUP BY e.tag ORDER BY hits DESC, e.tag ASC",
        (learner_id, cutoff),
    )]

    due_slugs = [r["slug"] for r in due_skills] or [""]
    qmarks = ",".join("?" for _ in due_slugs)
    explanations = [dict(r) for r in conn.execute(
        f"SELECT s.slug, x.text, x.effectiveness FROM explanations x "
        f"JOIN skills s ON s.id = x.skill_id "
        f"WHERE x.learner_id = ? AND x.effectiveness = 'landed' AND s.slug IN ({qmarks}) "
        f"ORDER BY s.slug ASC",
        (learner_id, *due_slugs),
    )]

    return {
        "as_of": today_s,
        "learner": dict(learner) if learner else None,
        "due_skills": due_skills,
        "due_items": due_items,
        "weak_skills": weak_skills,
        "active_errors": active_errors,
        "recent_errors": recent_errors,
        "explanations_that_landed": explanations,
    }


def export_context_json(conn: sqlite3.Connection, learner_id: int, today, **kw) -> str:
    """Deterministic, AI-readable export of the context query (sorted keys)."""
    return json.dumps(due_context(conn, learner_id, today, **kw),
                      indent=2, sort_keys=True, ensure_ascii=False)


# ---------------------------------------------------------------------------
# reference seed (the skill CATALOG; in production this comes from git curriculum)
# ---------------------------------------------------------------------------
SKILL_CATALOG = [
    # slug, label_practical, label_linguistic, type, humility_flag
    ("voice.actor", "ako-track: I do the action", "actor/agent voice", "voice", 0),
    ("causative.magpa", "magpa-: have it done / get examined", "magpa- causative", "causative", 0),
    ("clitic.second_position", "akong/kong placement", "second-position clitic", "clitic", 0),
    ("lex.health", "doctor/symptom words", "health lexicon", "lexical", 0),
    ("modal.base_form", "after dapat use the base verb", "base form after modal", "modal", 1),
    ("aspect.contemplated", "future/contemplated -in-/i-", "contemplated aspect", "aspect", 0),
]

SCENE_CATALOG = [
    ("health.see_doctor", "Describe symptoms and agree to see a doctor", "health", 1),
]

GLOSSIKA_ANCHORS = [
    # corpus_line, tl, en, register, naturalness, use_as
    (282, "Tatawagan ko siya bukas.", "I'll call her tomorrow.", "neutral", "natural", "recognition"),
]


def seed_reference_data(conn: sqlite3.Connection) -> None:
    """Seed the slow-changing catalog (skills, scenes, anchors). Idempotent."""
    with conn:
        for slug, lp, ll, typ, hf in SKILL_CATALOG:
            conn.execute(
                "INSERT OR IGNORE INTO skills (slug, label_practical, label_linguistic, type, humility_flag) "
                "VALUES (?,?,?,?,?)", (slug, lp, ll, typ, hf))
        for slug, label, domain, boss in SCENE_CATALOG:
            conn.execute(
                "INSERT OR IGNORE INTO scenes (slug, label, domain, is_boss) VALUES (?,?,?,?)",
                (slug, label, domain, boss))
        for line, tl, en, reg, nat, use_as in GLOSSIKA_ANCHORS:
            conn.execute(
                "INSERT OR IGNORE INTO glossika_anchors (corpus_line, tl, en, register, naturalness, use_as) "
                "VALUES (?,?,?,?,?,?)", (line, tl, en, reg, nat, use_as))


def create_learner(conn: sqlite3.Connection, handle: str, l1: str = "German",
                   current_module: str = "62") -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO learners (handle, l1, current_module) VALUES (?,?,?)",
            (handle, l1, current_module))
    return cur.lastrowid


def open_session(conn: sqlite3.Connection, learner_id: int, kind: str = "lesson") -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO sessions (learner_id, kind) VALUES (?,?)", (learner_id, kind))
    return cur.lastrowid
