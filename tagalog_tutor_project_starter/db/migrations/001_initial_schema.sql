-- 001_initial_schema.sql
-- Canonical mutable store for the AI Tagalog teacher's MEMORY (not a tutor engine).
--
-- Design invariant:
--   IMMUTABLE EVIDENCE  (attempts, attempt_skill_credit, attempt_errors,
--                        scheduling_events, mastery_evidence, xp_events)
--   is kept distinct from
--   PROJECTED CURRENT STATE (skill_state.due/status, review_items.due, errors.status).
--   Projected state is a cache that can be rebuilt by replaying the evidence rows.
--
-- The database stores and retrieves. It does NOT judge Tagalog, grade attempts,
-- or generate lessons. Those are the live AI teacher's job. Every column whose
-- value is a judgment (meaning_ok, outcome, naturalness, reason, due-by-AI) is
-- WRITTEN by the AI and merely PERSISTED here.
--
-- Run directly:   sqlite3 tutor.db < 001_initial_schema.sql
-- Or via helper:   db/tutor_db.py apply_migrations()  (skips if already applied)

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- migration bookkeeping
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- learner
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS learners (
    id              INTEGER PRIMARY KEY,
    handle          TEXT NOT NULL UNIQUE,
    l1              TEXT,
    current_module  TEXT,                 -- pointer only; "module done" is DERIVED from skill mastery
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- sessions  (one conversational sitting; most chat turns are NOT logged here)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id           INTEGER PRIMARY KEY,
    learner_id   INTEGER NOT NULL REFERENCES learners(id),
    started_at   TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at     TEXT,
    kind         TEXT NOT NULL DEFAULT 'lesson',
    summary      TEXT,                     -- AI-written concise progress note (the "better progress.txt")
    CHECK (kind IN ('lesson','messy','review','qa','mixed'))
);

-- ---------------------------------------------------------------------------
-- skills: CATALOG / definition layer (slow-changing, seeded from git curriculum)
-- Skill-graph EDGES (prerequisite / confusable / composes-into) deliberately
-- live in the git-tracked curriculum markdown, not here -- they are static
-- authored knowledge the AI reads directly. See SQLITE_SCHEMA_PROPOSAL.md.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
    id                INTEGER PRIMARY KEY,
    slug              TEXT NOT NULL UNIQUE,   -- e.g. 'modal.base_form'
    label_practical   TEXT NOT NULL,          -- how it is taught
    label_linguistic  TEXT,                   -- honest label
    type              TEXT,                   -- voice|aspect|clitic|causative|modal|...
    teaching_note     TEXT,
    humility_flag     INTEGER NOT NULL DEFAULT 0  -- 1 = teaching simplification; AI must hedge
);

-- ---------------------------------------------------------------------------
-- skill_state: PROJECTED mutable state, one row per (learner, skill)
-- 'strength' is a coarse days-ish memory proxy maintained by the AI (optionally
-- nudged by the suggest_due helper). It is NOT a trained FSRS weight.
-- 'status' = 'mastered' is DERIVED from mastery_evidence, never set on a whim.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skill_state (
    learner_id   INTEGER NOT NULL REFERENCES learners(id),
    skill_id     INTEGER NOT NULL REFERENCES skills(id),
    strength     REAL    NOT NULL DEFAULT 0,
    due          TEXT,                          -- next review date 'YYYY-MM-DD'
    last_review  TEXT,
    reps         INTEGER NOT NULL DEFAULT 0,
    lapses       INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'new',
    PRIMARY KEY (learner_id, skill_id),
    CHECK (status IN ('new','learning','active','lapsed','leech','mastered'))
);

-- ---------------------------------------------------------------------------
-- glossika_anchors: pointers into the IMMUTABLE raw corpus (git file).
-- The corpus line is reused, never copied wholesale into schedulable cards.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS glossika_anchors (
    id           INTEGER PRIMARY KEY,
    corpus_line  INTEGER,                  -- line no. in corpus/tagalog_sentences.txt
    tl           TEXT,
    en           TEXT,
    register     TEXT,
    naturalness  TEXT,                     -- natural|neutral|stilted_corpus
    use_as       TEXT,                     -- production|recognition|listening
    CHECK (naturalness IN ('natural','neutral','stilted_corpus') OR naturalness IS NULL)
);

-- ---------------------------------------------------------------------------
-- review_items: exact items (scarce, promotion-gated to avoid card explosion)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_items (
    id            INTEGER PRIMARY KEY,
    learner_id    INTEGER NOT NULL REFERENCES learners(id),
    slug          TEXT,
    intent_en     TEXT NOT NULL,           -- the production-first prompt
    target_tl     TEXT,
    acceptable_tl TEXT,                     -- JSON array text (AI-authored variants)
    modality      TEXT NOT NULL DEFAULT 'production',
    strength      REAL NOT NULL DEFAULT 0,
    due           TEXT,
    last_review   TEXT,
    reps          INTEGER NOT NULL DEFAULT 0,
    lapses        INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'new',
    source_kind   TEXT,                     -- module_anchor|corpus|learner_error|tutor_authored
    source_anchor_id   INTEGER REFERENCES glossika_anchors(id),
    spawned_by_attempt INTEGER REFERENCES attempts(id),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (modality IN ('production','recognition','listening')),
    CHECK (status IN ('new','learning','active','lapsed','leech','mastered'))
);

-- ---------------------------------------------------------------------------
-- scenes: applied-competence / transfer tests
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scenes (
    id       INTEGER PRIMARY KEY,
    slug     TEXT NOT NULL UNIQUE,
    label    TEXT,
    domain   TEXT,
    is_boss  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS scene_skills (
    scene_id  INTEGER NOT NULL REFERENCES scenes(id),
    skill_id  INTEGER NOT NULL REFERENCES skills(id),
    PRIMARY KEY (scene_id, skill_id)
);

-- ---------------------------------------------------------------------------
-- attempts: IMMUTABLE evidence. The atomic learning event.
-- Only meaningful learner PRODUCTIONS the AI decides to record become rows.
-- Casual conversation, questions, and explanations are NOT attempts.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attempts (
    id            INTEGER PRIMARY KEY,
    session_id    INTEGER NOT NULL REFERENCES sessions(id),
    learner_id    INTEGER NOT NULL REFERENCES learners(id),
    item_id       INTEGER REFERENCES review_items(id),
    scene_id      INTEGER REFERENCES scenes(id),
    occurred_on   TEXT NOT NULL,            -- date 'YYYY-MM-DD' used for scheduling math
    occurred_at   TEXT NOT NULL DEFAULT (datetime('now')),
    modality      TEXT NOT NULL DEFAULT 'production',
    mode          TEXT NOT NULL DEFAULT 'drill',     -- drill | messy | recovery
    prompt_shown  TEXT,
    response_tl   TEXT NOT NULL,            -- verbatim learner production (kept raw)
    hint_level    TEXT NOT NULL DEFAULT 'none',
    meaning_ok    INTEGER,                  -- AI judgment (0/1)
    register_ok   INTEGER,                  -- AI judgment (0/1)
    naturalness   TEXT,                     -- AI judgment label
    corrected_tl  TEXT,                     -- AI-authored correction
    reason        TEXT,                     -- AI one-line reason
    CHECK (modality IN ('production','recognition','listening')),
    CHECK (mode IN ('drill','messy','recovery')),
    CHECK (hint_level IN ('none','intent_only','slot_hint','root_family','contrast_label','scaffold_full'))
);

-- ---------------------------------------------------------------------------
-- attempt_skill_credit: the PARTIAL-CREDIT VECTOR. IMMUTABLE.
-- One learner production -> many per-skill outcomes (the core requirement).
-- 'outcome' is supplied by the AI; the DB never derives it.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attempt_skill_credit (
    attempt_id  INTEGER NOT NULL REFERENCES attempts(id),
    skill_id    INTEGER NOT NULL REFERENCES skills(id),
    outcome     TEXT NOT NULL,
    PRIMARY KEY (attempt_id, skill_id),
    CHECK (outcome IN ('pass','pass_hinted','fail','partial','n/a'))
);

-- ---------------------------------------------------------------------------
-- errors: recurring error-PATTERN registry (projected; status is mutable)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS errors (
    id           INTEGER PRIMARY KEY,
    learner_id   INTEGER NOT NULL REFERENCES learners(id),
    tag          TEXT NOT NULL,            -- e.g. aspect.future_overmark_after_modal
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'active',
    occurrences  INTEGER NOT NULL DEFAULT 0,
    first_seen   TEXT,
    last_seen    TEXT,
    UNIQUE (learner_id, tag),
    CHECK (status IN ('active','watch','resolved'))
);

-- ---------------------------------------------------------------------------
-- attempt_errors: which error patterns one attempt exhibited. IMMUTABLE.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attempt_errors (
    attempt_id  INTEGER NOT NULL REFERENCES attempts(id),
    error_id    INTEGER NOT NULL REFERENCES errors(id),
    PRIMARY KEY (attempt_id, error_id)
);

-- ---------------------------------------------------------------------------
-- scheduling_events: IMMUTABLE log of every due change. Enables replay + audit.
-- review dates "work without a scheduler service" because each attempt writes
-- the next_due here and onto the projected state; the next session just QUERIES
-- due <= today. 'decided_by' records whether the AI set it or the default helper.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scheduling_events (
    id            INTEGER PRIMARY KEY,
    attempt_id    INTEGER REFERENCES attempts(id),
    unit_type     TEXT NOT NULL,           -- skill | item | scene
    unit_id       INTEGER NOT NULL,
    prev_due      TEXT,
    next_due      TEXT,
    interval_days INTEGER,
    reason        TEXT,
    decided_by    TEXT NOT NULL DEFAULT 'ai',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (unit_type IN ('skill','item','scene')),
    CHECK (decided_by IN ('ai','helper_default'))
);

-- ---------------------------------------------------------------------------
-- mastery_evidence: IMMUTABLE evidence rows. Mastery is DERIVED from these.
-- PHASE-1 GATE = { unaided_delayed_production, scene_use, variation_handled }.
-- listening_check is RECORDED if it ever happens but is NEVER required in
-- phase 1 -- listening must not block mastery.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mastery_evidence (
    id             INTEGER PRIMARY KEY,
    learner_id     INTEGER NOT NULL REFERENCES learners(id),
    skill_id       INTEGER NOT NULL REFERENCES skills(id),
    evidence_type  TEXT NOT NULL,
    attempt_id     INTEGER REFERENCES attempts(id),
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (evidence_type IN ('unaided_delayed_production','scene_use','variation_handled','listening_check'))
);

-- ---------------------------------------------------------------------------
-- explanations: phrasings that worked for THIS learner (retrieval memory).
-- Lets the AI reuse an explanation it already knows landed for Tom.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS explanations (
    id            INTEGER PRIMARY KEY,
    learner_id    INTEGER NOT NULL REFERENCES learners(id),
    skill_id      INTEGER REFERENCES skills(id),
    text          TEXT NOT NULL,
    effectiveness TEXT,                     -- AI judgment: landed | partial | confused
    last_used     TEXT,
    CHECK (effectiveness IN ('landed','partial','confused') OR effectiveness IS NULL)
);

-- ---------------------------------------------------------------------------
-- xp_events: OPTIONAL honest gamification log. IMMUTABLE.
-- Rewards only science-aligned events (delayed recall, recovery, scene clear).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS xp_events (
    id          INTEGER PRIMARY KEY,
    learner_id  INTEGER NOT NULL REFERENCES learners(id),
    attempt_id  INTEGER REFERENCES attempts(id),
    kind        TEXT NOT NULL,             -- delayed_recall_win|recovery|scene_clear|mastery_milestone
    points      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- indexes for the next-session context query
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_skill_state_due  ON skill_state(learner_id, due);
CREATE INDEX IF NOT EXISTS idx_review_items_due ON review_items(learner_id, due);
CREATE INDEX IF NOT EXISTS idx_errors_status    ON errors(learner_id, status);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_mastery_skill    ON mastery_evidence(learner_id, skill_id);

-- record this migration (idempotent)
INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (1, '001_initial_schema');
