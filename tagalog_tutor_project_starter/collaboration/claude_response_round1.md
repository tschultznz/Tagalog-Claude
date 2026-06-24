# Claude Response Round 1

Date 2026-06-24. Author: Claude, adversarial architecture reviewer. Reviewing Codex synthesis at Tagalog-Codex `f80c672` against Claude `c969c31`. This round produces only documents. No code, migrations, or tests were changed in either repository.

## 0. How I verified

I read the five synthesis files and then the actual Codex code (`db/migrations/001_initial_schema.sql`, `db/sqlite_store.py`) and my own (`tagalog_tutor_project_starter/db/tutor_db.py`, `db/migrations/001_initial_schema.sql`). I did not rely on either model's summary. Three findings that change the discussion:

First, the Codex synthesis understates its own auto-creation defect. It flags only `ensure_skill` (`db/sqlite_store.py:72-86`), but `ensure_error` auto-creates error tags (`:89-106`) and `_upsert_schedule` auto-creates scenes mid-transaction (`:365-381`). Silent taxonomy fragmentation affects skills, errors, and scenes, not just skills.

Second, Codex has no mastery derivation anywhere. `record_attempt` writes every skill credit, including `failure` and `partial`, into `mastery_evidence` with `evidence_type = credit` (`db/sqlite_store.py:279-304`, the value written at `:300`), and nothing ever reads those rows to promote anything. So `mastery_evidence` is currently a mislabeled copy of `attempt_skill_credit`.

Third, Codex's `skill_state` is channel-keyed (`db/migrations/001_initial_schema.sql:54`) but `review_schedule` has no channel column at all (`:143-164`), and `_upsert_schedule` deduplicates open schedules without channel (`db/sqlite_store.py:389-402`). So the converged design separates production and recognition in state but silently merges them again in the schedule. This matters for several answers below.

I accept that the synthesis's critiques of my own first iteration are correct: my `skill_state` lacks a channel, my mastery gate is satisfiable from one attempt, I deferred `review_item_skills`, I have no scene state, and I store but never return Glossika anchors. I do not defend those.

## 1. Answers to the 32 questions

### Schema boundary

1. skill_state keyed by (learner, skill, channel) for production and recognition. AGREE. My single-key `skill_state` (`tagalog_tutor_project_starter/db/migrations/001_initial_schema.sql:76-86`) is a real defect: a recognition pass and a production pass collide on the same `due`/`status`. Codex's `(learner_id, skill_id, channel)` key (`db/migrations/001_initial_schema.sql:54`) is correct.

2. If not, how do you prevent recognition overwriting production. AGREE (I do not dissent). The mechanism is exactly the composite key: a recognition attempt upserts `(learner, skill, 'recognition')` and never touches the production row. Codex already demonstrates this with `ON CONFLICT(learner_id, skill_id, channel)` (`db/sqlite_store.py:260`). One required guard: the channel `CHECK` must not include `scene` (see Q3), so production and recognition stay the only writable language channels and listening stays reserved and inactive.

3. Scene competence separate from modality, not `channel = scene`. AGREE. Affected behaviour: Codex's current channel `CHECK` still allows `'scene'` and `'listening'` (`db/migrations/001_initial_schema.sql:46`, `:129`, `:183`), which contradicts the converged draft. Smallest fix: restrict the channel domain to `('production','recognition','listening')` with listening inactive, and move scene competence into its own `scene_state` projection. Consequence if left as-is: scene rows and language rows share one table and one status vocabulary, which reintroduces the conflation the draft says it is removing.

4. Smallest useful `scene_state`. AGREE_WITH_MODIFICATION. Reason: the proposed nine fields (`CONVERGED_SCHEMA_DRAFT.md:109-121`) mix latest-projection fields with cumulative aggregates, and stored aggregates are the classic source of replay divergence. Affected schema: `scene_state`. Smallest better alternative: store only fields that are latest-projection and not cheaply derivable: `learner_id, scene_id, status, due_at, support_level, notes`. Derive `last_attempted_on`, `last_success_on`, `success_count`, `blocking_error_count`, and `communication_success` from `attempts` when needed. Evidence: my own `due_context` already derives recent error counts by query rather than storing them (`tagalog_tutor_project_starter/db/tutor_db.py:358-373`), and it works. Consequence if implemented unchanged: every messy scene must write and reconcile five counters, which both invites drift and pushes messy speaking toward an app workflow, violating the rule that a scene records only a few meaningful outcomes.

### Skill taxonomy

5. Unknown skills fail the transaction by default. AGREE. My write path already does this by resolving the slug inside SQL so an unknown skill becomes a `NOT NULL` failure and rolls the whole attempt back (`tagalog_tutor_project_starter/db/tutor_db.py:200-207`; test at `tests/test_attempt_transaction.py:202-222`). Codex's `INSERT OR IGNORE` auto-create (`db/sqlite_store.py:75-81`) is the defect.

6. Explicit "propose new skill" pathway vs manual catalog only. AGREE_WITH_MODIFICATION. Reason: a strict resolve-or-fail write path is right, but live teaching legitimately discovers new patterns, and forcing every new skill through a manual out-of-band edit would stall a session. Affected behaviour: the write path and a separate creation helper. Smallest better alternative: keep `record_attempt` strictly resolve-or-fail, and add a distinct, metadata-bearing `declare_skill(key, practical_label, linguistic_label, category)` call the AI invokes deliberately when it decides something new is real. The distinction that makes a typo fail while a genuine discovery succeeds is that creation requires full metadata and is a separate explicit operation, whereas a typo arrives as a bare key inside a credit row and therefore fails. Evidence: Codex conflates the two by calling `ensure_skill` from inside `record_attempt` (`db/sqlite_store.py:229-231`) and from inside `_upsert_schedule` (`:363`), so a typo silently becomes a new skill. Consequence if unchanged: the taxonomy fragments on the first misspelling and mastery and due context split across `modal.base_form` and `modal.baseform` with no error raised.

7. Canonical key style: dotted vs underscore vs third. AGREE_WITH_MODIFICATION. Reason: a canonical style must be fixed before implementation, and the two repos disagree (my dotted `modal.base_form` in `tagalog_tutor_project_starter/db/tutor_db.py` `SKILL_CATALOG`, Codex's free `skill_key` with no catalog seed at all in `db/sqlite_store.py:72-86`). Affected schema: `skills.skill_key` / `skills.slug` and every foreign reference by key. Smallest better alternative: lowercase, dot-separated, ASCII hierarchical slugs `category.subtype[.detail]` (for example `modal.base_form`, `clitic.second_position`), validated by a single regex `^[a-z0-9]+(\.[a-z0-9_]+)+$`, with `category` matching the skill's `category` column. Dotted hierarchy groups and sorts naturally and lets the context query and the humility flag key off the category prefix. Consequence if left unsettled: the two implementations seed incompatible keys, the merge needs a rename migration, and replay across the rename becomes an extra hazard.

### Review items

8. Do you still defend deferring `review_item_skills`. AGREE (I retract the deferral). My deferral is stated in `tagalog_tutor_project_starter/architecture/SQLITE_SCHEMA_PROPOSAL.md:55` and enforced by the smoke-test note. Codex is right that without it the system cannot know what an exact item is meant to test before an attempt exists, which the context query needs to brief the teacher. Adopt Codex's `review_item_skills(review_item_id, skill_id, role)` (`db/migrations/001_initial_schema.sql:74-79`). One modification carried into Q9.

9. Every review item links at least one skill, or some pure lexical/pragmatic. AGREE_WITH_MODIFICATION. Reason: uniform retrieval wants a link, but forcing a contrived structural link onto a vocabulary prompt is dishonest. Affected schema: `review_item_skills` and the skill catalog. Smallest better alternative: require at least one link by default, and add lexical and pragmatic entries to the skill catalog (for example `lex.health`, which I already seed in `tagalog_tutor_project_starter/db/tutor_db.py` `SKILL_CATALOG`) so a vocabulary item links a lexical skill rather than nothing. Permit zero links only for `recognition`-mode items that exist purely for exposure. Consequence if every item is forced to link a structural skill: the AI invents fake structural targets for vocabulary drills, polluting skill state.

10. Contrast pairs: type, relation, or both. AGREE_WITH_MODIFICATION. Reason: Codex already has `item_type = 'contrast_pair'` (`db/migrations/001_initial_schema.sql:60`), which is enough to represent a contrast as one item in phase one. A first-class relation between two separate items is useful later but is not needed to teach the `dapat` base-form versus contemplated contrast now. Affected schema: `review_items.item_type` now; a deferred `review_item_relations` later. Smallest better alternative: phase one uses the `contrast_pair` type with both sides in one item's prompt and `review_item_skills` rows tagging the two confusable skills with `role = 'contrasts'`. Consequence of building the relation now: a join table and integrity rules for pair symmetry that earn nothing before real contrast scheduling exists.

### Mastery

11. Claude mastery too permissive because all labels attach to one attempt. AGREE. Confirmed in my own code: the gate is the label set `("unaided_delayed_production","scene_use","variation_handled")` (`tagalog_tutor_project_starter/db/tutor_db.py:295`) and `_maybe_promote_to_mastered` checks only distinct labels, not dates or gaps (`:298-315`); the test promotes from three labels on one attempt (`tests/test_attempt_transaction.py:186-199`). This is not delayed, multi-date mastery.

12. Minimum gap defining delayed: 1, 2, 3, or AI-supplied. AGREE_WITH_MODIFICATION. Reason: the gap is pedagogy, not a fact, so it should be a versioned policy value, not hard-coded in the schema and not supplied per attempt by the AI (which would let the model move its own goalposts). Affected behaviour: the mastery derivation helper. Smallest better alternative: 2 days as a named, versioned policy default in the derivation layer, recorded on the mastery decision so a later policy change is auditable. Revisit the number once real sessions exist. Consequence if AI-supplied per call: mastery becomes whatever gap the model felt like that day, and the audit trail cannot explain why a skill was promoted.

13. DB enforces distinct dates, or exposes facts and a helper enforces. AGREE_WITH_MODIFICATION. Reason: dated immutable attempts are facts the DB should hold, but distinct-date and gap rules are policy that should live in a derivation read, not in `CHECK` constraints. Affected schema and behaviour: this is the argument for not storing mastery at all (see section 2, mastery derivation, and Q30). Smallest better alternative: the DB stores `attempts.occurred_at` and `attempt_skill_credit.credit`; a `derive_mastery(learner, skill, channel, as_of, policy)` helper computes distinct dates, gap, variation, scene success, and recent-failure checks at read time. Evidence: every fact the gate needs is already present without a mastery table: dates on `attempts` (`db/migrations/001_initial_schema.sql:114`), per-skill unaided versus hinted in `attempt_skill_credit.credit` (`:130`), mode in `attempts.mode` (`:115`), and blocking failures via `attempt_errors.severity` (`:138`). Consequence if distinct dates are enforced by DB constraints: pedagogy is frozen into the schema and every policy tweak needs a migration.

14. Recent medium-severity failures block mastery automatically, or only when AI marks mastery-blocking. AGREE_WITH_MODIFICATION. Reason: severity itself is an AI judgment, so neither pure automatic-on-severity nor pure manual is right. Affected schema: `attempt_errors` needs a `mastery_blocking` flag in addition to `severity` (`db/migrations/001_initial_schema.sql:135-141`). Smallest better alternative: the AI sets `severity` and a `mastery_blocking` boolean per attempt error; the derivation helper then automatically enforces the policy window over AI-flagged blocking failures. So the AI judges which failures are structural and blocking; the helper applies the recency rule deterministically. Consequence if automatic on raw severity: a single AI-labeled medium error with no real bearing on the skill silently blocks mastery with no way to express "noted but not blocking."

15. Listening future-compatible but non-gating. AGREE. This was my own fix (`tagalog_tutor_project_starter/db/tutor_db.py` `REQUIRED_MASTERY_EVIDENCE` excludes listening; test at `tests/test_attempt_transaction.py` `test_mastery_promotes_only_with_full_phase1_evidence`). Keep the listening channel reserved and inactive; never let it gate.

### Glossika

16. Anchors not returned unless linked to selected due skills, errors, scenes, or items. AGREE. Codex's context returns all active anchors ordered by `corpus_id` with no relevance (`db/sqlite_store.py:578-590`); my code does not return anchors at all. Both are wrong; relevance-gated return is correct.

17. Which link tables in phase one. AGREE_WITH_MODIFICATION. Reason: the four proposed anchor link tables (`CONVERGED_SCHEMA_DRAFT.md:255-275`) are more relationship surface than phase one needs. Affected schema: the anchor link tables. Smallest better alternative: ship only `glossika_anchor_skills(anchor_id, skill_id, role)` in phase one. Due items already link skills via `review_item_skills`, scenes link skills via `scene_skills`, and errors map to skills through the AI's judgment, so all four relevance paths in `CONVERGED_SESSION_CONTEXT.md:119-124` resolve through skill. Defer `glossika_anchor_errors`, `glossika_anchor_review_items`, and `glossika_anchor_scenes` until a concrete retrieval cannot be obtained by routing through skill. Consequence if all four ship now: three relationship tables and their seeding and integrity rules exist before any query needs them, which is exactly the maintenance-cost-without-payoff the prompt warns against.

18. `recommended_use` normalized or AI text. AGREE_WITH_MODIFICATION. Reason: the context query sorts and filters on use, so the retrieval-driving dimension must be controlled, but nuance is worth keeping. Affected schema: `glossika_anchors.recommended_use`. Smallest better alternative: a controlled enum `recommended_use IN ('production_target','recognition_only','contrast_source','avoid_production')` plus a free-text `use_note`. Evidence: Codex sorts anchors by role buckets (`CONVERGED_SESSION_CONTEXT.md:136-141`), which only works on controlled values. Consequence if left as free text: the relevance sort in the context contract cannot be implemented deterministically.

19. Naturalness status so raw stays immutable but active targets can differ. AGREE_WITH_MODIFICATION. Reason: this is essentially right; I only tighten it. Affected schema: `glossika_anchors`. Smallest better alternative: keep `raw_tl` immutable, add `naturalness_status IN ('raw_natural','raw_stilted','unreviewed')` and a nullable `production_target_override`; the active production target is `COALESCE(production_target_override, raw_tl)` and is used only when `naturalness_status = 'raw_natural'` or an override exists. Evidence: my first iteration already records anchor naturalness on a controlled vocabulary (`tagalog_tutor_project_starter/db/migrations/001_initial_schema.sql` `glossika_anchors.naturalness` CHECK). Consequence if absent: stilted corpus lines get drilled as production targets, which my pedagogy notes explicitly bar.

### Context query

20. Maximum compact context size. AGREE_WITH_MODIFICATION. Reason: Codex caps with a single shared `limit = 6` across categories (`db/sqlite_store.py:463`), which lets one category crowd out others; for instance `active_weaknesses` mixes production and recognition rows under one limit (`:506-535`). Affected behaviour: the context query. Smallest better alternative: per-category caps, for example at most 8 due skills, 5 due items, 3 due scenes, 5 active errors, 5 recent attempts, 6 anchors, ranked by due date then priority, as configurable constants with a test asserting the cap. Consequence if one shared limit stays: a backlog of recognition items can hide every due production item from the teacher.

21. `recent_attempts` verbatim or only failures and summaries. AGREE_WITH_MODIFICATION. Reason: the teacher needs to see what just happened, including recent successes, but not a transcript. Affected behaviour: context query. Smallest better alternative: a short tail of the last 3 to 5 attempts with compact fields (date, prompt, learner answer, outcome, top skill credit, error tags), biased toward recent failures but including the latest successes. Evidence: Codex already returns a bounded tail of compact columns (`db/sqlite_store.py:537-556`), which is close; keep that shape, not full verbatim history. Consequence of failures-only: the teacher loses the signal that a previously weak skill just succeeded unaided, which is the delayed-recall win worth reinforcing.

22. Landed explanations now or deferred. AGREE. Defer. I concede my `explanations` table is unproven (the synthesis is fair at `codex_synthesis_round1.md:119-123`). Remove it from the next phase until real sessions show repeated reuse.

23. Due context includes resolved errors, or only active/watch plus recent counts. AGREE_WITH_MODIFICATION. Reason: resolved errors are longitudinally interesting but are noise in the compact "continue" payload. Affected behaviour: context query. Smallest better alternative: default to active and watch plus recent counts (the behaviour my code already has and tests at `tagalog_tutor_project_starter/db/tutor_db.py:358-373` and `tests/test_due_context_query.py:118-132`); expose resolved errors only as a count or behind an explicit request. Consequence if resolved errors are always included: the payload grows with history and dilutes the active picture.

### Replay and audit

24. Minimum replay proof you would accept. AGREE_WITH_MODIFICATION. Reason: replaying all four projected tables at once (`CONVERGED_SCHEMA_DRAFT.md:322-329`) is more than the next phase needs to prove the principle. Affected behaviour: the replay test. Smallest better alternative: rebuild `skill_state` only (per channel: `status`, `due_at`, `evidence_count`) from immutable `attempts`, `attempt_skill_credit`, and `scheduling_events`, and assert semantic equality with the live projection after a multi-attempt scenario that includes a manual-correction event. Consequence of attempting full four-table replay first: the proof is delayed behind scene and error projections that do not exist yet.

25. Replay exact for all projected tables, or initially skill_state, review_schedule, scene_state. AGREE_WITH_MODIFICATION. Reason: I reject `review_schedule` as a table (Q30 and section 2), and scene state arrives in a later slice. Affected behaviour: replay scope. Smallest better alternative: phase one replays `skill_state` only; `scene_state` and `learner_error_state` replay arrive with those projections. Equality should be semantic on meaningful columns, not byte-for-byte, since `updated_at` and similar audit timestamps legitimately differ. Consequence of requiring exact equality on all tables: the test fails on volatile timestamps and on tables that do not yet exist.

26. How manual corrections are represented. AGREE_WITH_MODIFICATION. Reason: corrections must be auditable and replayable, so they cannot be in-place edits. Affected schema: `scheduling_events` (and an analogous evidence row for non-schedule corrections). Smallest better alternative: represent a manual correction as an immutable event with `decided_by = 'human'`, a reason, the typed target, and previous and next values; replay applies it in timestamp order like any other event. Evidence: my `scheduling_events` already carries `decided_by` with values `ai` and `helper_default` (`tagalog_tutor_project_starter/db/migrations/001_initial_schema.sql` `scheduling_events.decided_by` CHECK); adding `human` extends it. Consequence if corrections edit projected rows directly: replay from evidence no longer reproduces live state and the audit trail has a gap.

### Progress files

27. Future role of `current/progress.txt`. AGREE_WITH_MODIFICATION. Reason: agree it is the migration source and stops being canonical, but it should become a generated export, not a human-edited journal, so the database stays the single source of truth. Affected behaviour: migration and export. Smallest better alternative: migrate from `progress.txt` once, then regenerate it read-only from SQLite as a deterministic export; if Tom wants a hand-written journal, that is a separate file, not `progress.txt`. Consequence if it stays hand-edited: two writable sources of learner state, which is the exact failure the project is replacing.

28. Session summaries SQLite only, or also git-tracked markdown. AGREE. Keep the canonical summary in `sessions.summary` and also write a deterministic git-tracked markdown export per session for human diff and audit. This matches the project's preference for auditable, diffable history alongside the live database.

### Complexity control

29. Which of your tables would you cut first. AGREE (the schema is too large; I name cuts). Cut `explanations` first (unproven; `codex_synthesis_round1.md:119-123`), then `xp_events` (not needed to prove the loop). Both are already marked defer in the converged draft (`CONVERGED_SCHEMA_DRAFT.md:279-286`), so I am agreeing and going further by cutting them from my own design now.

30. Which Codex table or behaviour do you reject as app-like or premature. DISAGREE (with keeping two items). Reason and targets:

   The first is `review_schedule` as a separate writable queue alongside per-entity `due_at`. The converged draft keeps both `skill_state.due_at` and a general `review_schedule` (`CONVERGED_SCHEMA_DRAFT.md:59-71` and `:187-212`), and Codex's code writes due in both places in one attempt: `skill_state.due_at` from the credit row (`db/sqlite_store.py:274`) and a `review_schedule` row in the schedule loop (`:321-336`). That is two writable sources of truth for one fact, which the prompt says to reject. Smallest better alternative: keep `due_at` on each typed projected-state table and `scheduling_events` for audit, and make the open queue a query (a union of due rows across `skill_state`, `review_items`, `scene_state`, `learner_error_state`). Evidence it works: my `due_context` already builds the queue this way from per-entity due fields (`tagalog_tutor_project_starter/db/tutor_db.py:330-394`) and is tested (`tests/test_due_context_query.py`). Consequence if `review_schedule` stays: `skill_state.due_at` and `review_schedule.due_at` drift, and the polymorphic target has no integrity (the `CHECK` at `db/migrations/001_initial_schema.sql:158-163` requires at least one target id but not exactly one, does not enforce that `target_type` matches the populated foreign key, and has no channel, so the dedup at `db/sqlite_store.py:389-402` collapses production and recognition schedules for the same skill).

   The second is the `mastery_evidence` table. It duplicates facts already in the attempt model and Codex currently misuses it as a copy of skill credit including failures (`db/sqlite_store.py:279-304`). Smallest better alternative: derive mastery at read time from `attempts`, `attempt_skill_credit`, and `attempt_errors`; do not store it. See section 2.

   I do not reject Codex's channel-specific state, `review_item_skills`, scene catalog, or scheduling-event history; those are good.

31. Defer XP entirely for the next phase. AGREE. XP is not needed to prove the AI-teacher loop; `xp_events` waits until the loop shows value (`DECISION_MATRIX_ROUND1.md:30`).

32. Is `explanations` worth keeping in phase one. AGREE. Defer it. Concede my own table is premature; revisit only with evidence that Tom benefits from repeated phrasing memory.

## 2. Cross-cutting positions on the ten challenge areas

Phase size. The proposed next phase has ten work items in one migration (`codex_synthesis_round1.md:309-326`). That is not bounded; it is a small rewrite. See `CLAUDE_PHASE_SLICING.md` for three narrow slices, each independently testable, with phase one the smallest that materially improves the live teacher.

Duplicate scheduling state. Reject option C as written and the draft's current both-and. Adopt option A: `due_at` on each typed projected-state table plus immutable `scheduling_events`; no separate writable `review_schedule`. The open queue is a query. If a materialized queue is ever needed for performance (not at n equals one), it returns as an explicitly derived, read-only cache rebuilt from entity due fields, never written directly. Detail in `CLAUDE_CONVERGENCE_DELTAS.md`.

Mastery duplication. Mastery is derivable entirely from `attempts` plus `attempt_skill_credit` plus `attempt_errors`. Every fact the gate needs is present there (dates, per-skill unaided versus hinted credit, mode, blocking-failure recency). A separate `mastery_evidence` table stores nothing the attempt model cannot, so remove it and derive mastery at read time. Database verifies facts; AI judgment is captured in the credit value, the attempt mode, and the error severity and blocking flag it supplied at attempt time.

Raw JSON versus normalized evidence. Normalized rows are authoritative for replay and querying. Retain `attempts.evaluation_json` (`db/migrations/001_initial_schema.sql:122`) as write-once audit of the raw AI verdict only; replay and context never parse it. Validate and extract normalized rows in the same transaction so you never get JSON without matching rows; if extraction fails, the attempt fails. One canonical replay source: the normalized evidence.

Glossika over-normalization. Phase one ships `glossika_anchor_skills` only; the other three anchor link tables are deferred because item, scene, and error relevance all resolve through skill.

Taxonomy strictness versus live teaching. Predeclared and strict at attempt time: skills, errors, scenes (resolve-or-fail). Created only through explicit, metadata-bearing pathways, never silently during credit or schedule resolution: review items always, and new skills, errors, or scenes through a separate deliberate `declare_*` call. A bare key with no metadata always fails, so a typo fails and a real discovery does not.

Polymorphic schedule integrity. Removing `review_schedule` removes the polymorphic-target problem. For `scheduling_events`, use typed nullable foreign keys (`skill_id`, `review_item_id`, `scene_id`, `learner_error_id`) with a one-hot `CHECK` that exactly one is set, plus `source_attempt_id` and `decided_by`. This beats both my earlier generic `unit_type + unit_id` (which sacrificed foreign-key integrity) and Codex's dependence on a `review_schedule_id` whose own target is ambiguous.

Scene-state semantics. Smallest useful set is `status`, `due_at`, `support_level`, `notes`; derive the rest. See Q4.

Mastery thresholds. Versioned policy in the derivation layer, not hard-coded schema rules and not per-attempt AI values. Defaults 2-day gap and 7-day window, labeled as policy version one, recorded on each mastery decision.

Replay scope. Minimum useful proof is `skill_state` replay with a manual-correction event, semantic equality. See Q24 and Q25.

## 3. Codex decisions I accept without change

Channel-specific projected skill state for production and recognition (`DECISION_MATRIX_ROUND1.md:19`). Adopt `review_item_skills` (`:22`). Canonical error taxonomy plus learner-specific `learner_error_state` (`:24`). Immutable scheduling-event history with previous due, next due, reason, decided-by (`:28`). Version-aware migration execution and no-op reapplication tests, which is my own behaviour (`:31`). Defer XP and landed explanations (`:25`, `:30`). Production and recognition must not share projected state, listening must not gate, unknown skills must not be silently created, arbitrary anchors must not appear, mastery cannot be three labels on one attempt (`:38-48`). Scene competence is its own projection, not a language modality.

## 4. Decisions that still require negotiation

Schedule source of truth: I require option A (no writable `review_schedule`); Codex's draft keeps both. This is the main open schema question.

Mastery storage: I require deriving mastery from the attempt model with no `mastery_evidence` table; the draft keeps the table. Open.

Canonical skill key style: dotted hierarchical slugs with a validation regex versus Codex underscore keys. Needs a single decision before migration `002`.

Mastery policy numbers: 2-day gap and 7-day window as policy defaults are acceptable to me, but the exact values should be revisited after real sessions rather than fixed now.

Whether `scheduling_events` carries typed foreign keys (my position) or stays tied to a `review_schedule_id`. Resolved automatically if option A is adopted.

## 5. Defects found in the synthesis and the Codex code

The synthesis understates auto-creation: errors (`db/sqlite_store.py:89-106`) and scenes (`:365-381`) are auto-created too, not only skills.

The converged draft and Codex code carry two writable sources of due (`skill_state.due_at` and `review_schedule`), written together in one attempt (`db/sqlite_store.py:274` and `:321-336`).

`mastery_evidence` is written for every credit including failures and is never read for derivation (`db/sqlite_store.py:279-304`), so it is currently a mislabeled duplicate of `attempt_skill_credit`.

`skill_state` is channel-keyed but `review_schedule` is channel-blind (`db/migrations/001_initial_schema.sql:54` versus `:143-164`), and the dedup ignores channel (`db/sqlite_store.py:389-402`), so the schedule re-merges what state separates.

The channel domain still includes `scene` and `listening` (`db/migrations/001_initial_schema.sql:46`), contradicting the converged decision that scene is not a channel and listening is inactive.

`attempts` stores both `evaluation_json` and normalized outcome columns (`db/migrations/001_initial_schema.sql:119-122`) with no statement of which is authoritative for replay.

## 6. Final verdict

READY_FOR_CODEX_REVISION.

There is no architectural blocker. The disagreements are simplifications that reduce surface and risk, not conflicts about the product. The two changes I require before implementation, both of which shrink the schema, are: one writable schedule source (option A, remove `review_schedule`), and mastery derived from the attempt model (remove `mastery_evidence`). With those and a fixed key style, migration `002` can proceed on the sliced plan in `CLAUDE_PHASE_SLICING.md`.
