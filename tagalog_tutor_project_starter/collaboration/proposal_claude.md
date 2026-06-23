# Proposal — Claude (independent planning round)

Date: 2026-06-23 · Author: independent Claude planning agent · Status: Phase-1 independent design (the other model's proposal was **not** read).

This proposal is deliberately backed by working artifacts, not prose alone: a formal schema (`srs/item_schema.json`), seven design specs, a runnable scheduler (`srs/scheduler.py`), and a passing end-to-end test of the required proof-of-concept (`tests/test_poc_flow.py`). Where a claim rests on evidence, it is cited in `research/`. Section numbers below match the instruction's required-deliverable list (§11).

---

## 1. Executive summary

Tom's existing tutor has **strong content and a broken memory**. The curriculum (Modules 1–70), the root-family explanations, the production-first method, and the Glossika corpus are good and should be preserved. The failure is that scheduling, scoring, and learner memory live in prose: weak points are "remembered" informally, re-drilled within a session (massing — near-worst for retention), and recognition is mistaken for mastery.

My design moves memory out of prose and into **auditable files governed by explicit rules**, organized around one invariant:

> Every learning event is logged as data; every session is generated from that data; no mastery claim exists outside the data.

Concretely:
- A **three-grain model** — exact item, skill, scene — updated together from one answer via a **partial-credit vector** (the `magpatingin` requirement, validated in code).
- A **transparent FSRS-lite scheduler** (stability/difficulty/retrievability, no API, ~120 lines, fully inspectable) that prices in hints, separates production/recognition/listening, and throttles load.
- A **lazy Glossika mapping** that reuses Tom's investment without annotating 1,300 lines or exploding into one-card-per-sentence.
- **Honest gamification** that rewards only science-aligned events (unaided production, delayed recall, recovery, scene transfer), never recognition or app-opening.
- Operated entirely through **chat over version-controlled files** — no API, no UI — and portable to an app later without re-modelling.

The single most important change is mechanical: **sessions are built from a computed review queue, and stability only rises on the right evidence.**

## 2. Research synthesis

Full detail in `research/`; the eight rules the evidence imposes (`research/learning_science.md`):
1. Schedule by **stability**, lengthen multiplicatively, decay over real time (FSRS; Cepeda 2008 spacing ridgeline).
2. **Produce before the answer**; log verbatim attempts; errorful generation is valuable (generation effect, 300+ studies).
3. Score **production > recognition**; stability can't rise on recognition alone (testing effect; receptive≠productive).
4. **Interleave** confusables; show Tom the delayed-recall payoff so he trusts the harder path (Bjork desirable difficulties).
5. **Price hints in**; fade them (assistance dilemma).
6. **Immediate** in-session correction **plus** a **spaced** delayed re-test (corrective-feedback-timing dispute resolved by doing both).
7. **Throttle** load; cap new items; no overdue avalanche.
8. Gamify **learning quality** only; transparency over loss-aversion (SDT + dark-pattern critique).

Market read (`research/current_apps.md`): no existing product is a transparent, skill-indexed learner memory the user owns. Borrow Anki's FSRS, Speak's pattern→automatize→free-use staging, Busuu's talk-now/correct-after; avoid recognition inflation, unpriced hints, opacity, and engagement dark patterns. Glossika gave Tom broad *recognition* at the *sentence* grain; our job is to convert it to *production* at the *skill* grain.

Linguistics (`research/tagalog_pedagogy.md`): existing materials are accurate and unusually disciplined. Keep the ako-track/ko-track teaching surface but tag skills with precise linguistic labels. Encode the `dapat`+base-form rule as a **teaching rule, not absolute law** (humility), because aspect can co-occur with `dapat` in some natural speech.

## 3. Learner-model design

Spec: `learner/model_spec.md`. Files under `learner/`: `profile.yaml`, `skills_state.yaml`, `review_items.yaml`, `scenes_state.yaml`, `attempt_log.jsonl`, `session_log.jsonl`, `preferences.yaml`, `gamification.yaml`. Structured state = YAML (diffable); history = append-only JSONL. **State is a snapshot regenerable by replaying the attempt log** — the log is the source of truth (the AUDIT's "split learner state from review history").

Every required field (exact items, skills, scenes, domains, error types, production/recognition/listening status, hint dependence, latency/confidence, stability, difficulty, due, recent fail/success, mastery evidence, preferences, fatigue/load) maps to a concrete location — table in `model_spec.md` §2. Seeding from `current/progress.txt` is **faithful**: STABLE items become `active` (not `stable`) with modest stability; WATCH items map near 1:1 (their `D3/D7` tags seed real due dates); completion = exposure, never mastery.

## 4. Scheduling design

Spec: `srs/scheduling_spec.md`; implementation `srs/scheduler.py`. **FSRS-lite v0.1**: power-law forgetting `R(t)=(1+FACTOR·t/S)^DECAY` with `DECAY=-0.5, FACTOR=19/81` so `R(S)=0.90` and, at target 0.90, `interval=S`. Success grows S by `Δ = SC·hardness(D)·spacing(R)·w_grade·w_hint·w_modality` — where `spacing(R)=1-R` is the desirable-difficulty engine (review later → bigger durable gain), `w_hint` prices assistance, `w_modality` enforces recognition≠mastery. Failure contracts S (`×0.3`, floor 0.5), increments lapses, mean-reverts D upward; ≥4 lapses → `leech` (stop tightening, flag for redesign). Mastery gate for `stable`: unaided delayed (≥7d) production + scene use + listening check + variation + production S≥21. Load throttle caps due items and **never** penalizes a unit for calendar backlog (no overdue avalanche). Every constant is versioned (`fsrs-lite-0.1`); the math is swappable for true FSRS later without schema change.

## 5. Exact-item / skill / scene architecture (with the proof-of-concept)

Three coupled grains, scheduled independently, updated together (`research/design_synthesis.md` §B):
- **Exact item** — scarce, promotion-gated (a chunk becomes a scheduled item only if high-value AND has failed, or is a module anchor) → stops card explosion.
- **Skill** — the durable mastery layer; carries per-modality state; linguistically typed.
- **Scene** — the transfer test; "boss" scenes are graded milestones.

**Partial credit** is the linchpin: the evaluator emits `{skill_id: outcome}` per attempt. Validated PoC (`tests/test_poc_flow.py`, all assertions pass):

Prompt `Dapat akong magpatingin.` → Tom: **`Dapat akong magpapatingin.`** (today 2026-06-23):

| skill | outcome | S before→after | due |
|---|---|---|---|
| voice.actor | pass | 8.000 → 9.238 | 2026-07-02 |
| causative.magpa | pass | 6.000 → 7.008 | 2026-06-30 |
| clitic.second_position | pass | 5.000 → 5.600 | 2026-06-29 |
| lex.health | pass | 4.000 → 4.374 | 2026-06-27 |
| modal.base_form | **fail** | 3.000 → 0.900 | 2026-06-24 |
| aspect.contemplated | **fail** | 2.000 → 0.600 | 2026-06-24 |

How the instruction's PoC checklist is satisfied: the attempt is **logged** verbatim (`attempt_log.jsonl`); the **exact item** `item.health.dapat_magpatingin` is marked failed; **skills succeed** (actor, clitic, causative, health) and **one skill fails** (`modal.base_form`); the **error tag** is `aspect.future_overmark_after_modal`; the **next review** is rescheduled (modal back to +1 day, others pushed out); the **follow-up prompt** is the spawned contrast item (below); **later messy-speaking** reuses the distinction because `modal.base_form` and `aspect.contemplated` are `confusable_with` each other and get interleaved; the **skill becomes stable** only when the mastery gate is met (unaided delayed production + scene + listening + variation + S≥21).

**Spawned follow-up** (`tutor/evaluation_rubric.md` §5): `item.contrast.dapat_base_vs_contemplated` — "should see a doctor (now)" `Dapat akong magpatingin.` vs "will see one tomorrow" `Magpapatingin ako bukas.` — interleaving the two confusables by construction.

## 6. Error taxonomy

Spec: `tutor/evaluation_rubric.md` §2; enum in `srs/item_schema.json#/$defs/error_tag`. 15 tags with severity + correction priority + `spawns_contrast`, e.g. `meaning.wrong_core` (CRITICAL), `clitic.placement` / `voice.actor_target_mismatch` / `register.inappropriate` (HIGH), `aspect.future_overmark_after_modal` (MED, dedicated tag for the PoC class), down to `spelling.only` (LOW) and three non-error **signals** (`hesitation`, `hint_dependence`, `comprehension_without_production`). Correction is concise and capped at the top 1–2 severity items (no flooding); the rest are logged. Failures with `spawns_contrast: yes` create targeted future items — this is the mechanism by which "errors create future review."

## 7. Tutor-session workflow

Spec: `tutor/session_protocol.md`. Loop = **read state → recovery check → micro review → concept hint → pattern → production drill (hints below) → evaluate (partial credit, concise correction, schedule, spawn) → choice half-dialogue → messy scene (talk-now/correct-after) → listening micro → write state + honest progress note**. Documented chat commands map to file ops: `/start /continue /ask /review /weak /skill /errors /messy /import /migrate /mastery /update /end`. The inspection commands (`/review /weak /skill /errors /mastery`) exist so Tom can audit the model that schedules him. Hints fade to the lowest level a skill's stability warrants; `/scaffold` remains the cold-item escape hatch but is priced in. End-of-session note is short but **evidence-bearing** and dates are computed (fixes the "historical dates wrong" + "over-compressed summary" failures).

## 8. Glossika integration

Spec: `corpus/corpus_mapping_spec.md`. Raw `corpus/tagalog_sentences.txt` is **immutable**. Sidecars: `glossika_index.jsonl` (cheap, full-coverage, auto-tags only) and `corpus_mapping.jsonl` (sparse, hand/agent-curated — skill/domain/register/naturalness/`spoken_target`/`use_as`). **Corpus lines are evidence/material, not schedulable cards** (the explosion firewall); SRS state lives on the skill/item the line feeds. Stilted lines (e.g., `Mainit sa kuwarto na ito` → `Mainit dito sa kuwarto`) are barred from production but fine for recognition/listening. Mapping is **demand-driven**; `current/corpus_anchor_index.txt` (~80 anchors) migrates first.

**Glossika-linked example** (required, `corpus_mapping_spec.md` §7, in fixtures): corpus line **282** *"I'll call her tomorrow. — Tatawagan ko siya bukas."* Here contemplated `tatawagan` is **correct** (no modal); paired with `Dapat ko siyang tawagan` (base after modal), the same line Tom already studied becomes the contrast material that fixes his PoC error — reactivating prior exposure rather than replacing it.

## 9. Curriculum reconstruction

Spec: `curriculum/skill_graph_spec.md`. Modules 1–70 → a **skill graph** (nodes = skills stored once; edges = prerequisite / confusable / composes-into), not a concatenation. Each node records introduced/reviewed modules and current per-modality state. The AUDIT's four questions are answered structurally (historical-only, still-active, overlapping, missing). Legacy modules become a **reactivation pool**: a skill not retrieved in 21 days resurfaces regardless of its module's "done" status, with a cheap recognition triage before expensive production. Build is a curated, reviewable step (`build_skill_graph.py`, Phase 2) with a human/agent gate — not blind automation.

## 10. Gamification

Spec basis: `research/design_synthesis.md` §G + `learning_science.md` §7. Reward **only** science-aligned events: no-hint production, delayed-recall success, recovery of a lapsed item, scene/boss clears, skill-stability milestones, register-appropriateness, mastery-map growth. Prefer a **due-review streak** (cleared what was due) over a raw daily streak, with a **streak-freeze/recovery** so a missed day doesn't punish. **Never** reward recognition-as-production, app-opening, or volume; no countdown/loss-aversion pressure. XP rules and state are plain text Tom can read. This is the rare case where Tom's stated motivators and the ethics evidence align. In the PoC, the failed attempt earns **zero** XP while the unaided 9-day recall of `voice.actor` earns a delayed-recall win — exactly the right incentive.

## 11. Codex/Claude operating workflow

No API, no UI. Each command is a deterministic read/transform/write over `learner/` files plus the agent's own language ability (which Tom already pays for via Codex/Claude). The scheduler runs as `srs/scheduler.py` **or** as inline arithmetic the agent performs and logs — both documented, so either model produces identical state. Because evaluation and scheduling logic live in specs + schema (not prose), Codex and Claude grade and schedule the same way, which is what makes the two-model loop convergent rather than divergent.

## 12. File and schema design

Single source of truth: `srs/item_schema.json` (JSON Schema 2020-12; validated, all `$ref`s resolve) with `$defs` for `srs_state`, `modality_state`, `skill`, `review_item`, `scene`, `credit_outcome`, `error_tag`, `attempt`, `session`. On disk: YAML for state, JSONL for logs, Markdown for human-readable specs, Python for deterministic scheduling — matching the project's "prefer Markdown/YAML/JSONL/scripts/tests" constraint and avoiding databases/services/UI. Proposed tree is the SYSTEM_ARCHITECTURE_NOTES layout, now populated under `tagalog_tutor_project_starter/`.

## 13. Migration plan

1. **Index** the corpus (cheap, full) → `glossika_index.jsonl`.
2. **Seed** skills/items from `current/progress.txt` (faithful, completion=exposure) → `skills_state.yaml`, `review_items.yaml`.
3. **Migrate anchors** from `current/corpus_anchor_index.txt` → `corpus_mapping.jsonl`.
4. **Build skill graph** from Modules 1–70 (curated, gated) → `skill_graph.yaml`.
5. **Reactivation** turns legacy coverage into due recognition checks.
All steps are reversible, version-controlled, and never touch the raw corpus or original prompts (preserved in the initial commit + `archive/`).

## 14. Testing strategy

`tests/test_poc_flow.py` already proves the critical path end-to-end (partial credit, exact S/due, mastery gate, desirable difficulty, priced hints, modality weighting, delayed-recall XP) — deterministic, stdlib+PyYAML. Planned additions (Phase 2): scheduler property tests (monotonicity: lower R → larger gain; hinted ≤ unaided; recognition ≤ production), a schema-validation test (every fixture validates against `item_schema.json`), a migration round-trip test (replay attempt_log → reproduce skills_state), and a "no overdue avalanche" load test. The exit criteria from `COLLABORATION_PROTOCOL.md` are individually testable and most are already green.

## 15. Risks

- **Hand-maintained modality bookkeeping** could be tedious — mitigated by the agent (not Tom) doing updates; fixtures show it's tractable.
- **Skill-graph reconstruction is judgment-heavy** — mitigated by a curated, reviewable build with an alias map and a human gate, not blind parsing.
- **Linguistic over-claiming** — mitigated by dual practical/linguistic labels + humility notes + the `aspect.*` tags; the rubric refuses to assert naturalness as fact.
- **FSRS-lite constants are hand-tuned, not learned** — acceptable for n=1 and transparency; the schema stores exactly what true FSRS needs, so upgrading later is non-breaking.
- **Scope creep toward an app/API** — fenced by the Phase-1 no-API/no-UI rule and the deferral list (§17).
- **Two-model divergence** — mitigated by logic living in shared schema/specs so both agents compute identically.

## 16. Unresolved questions

1. Target retention default — 0.90 (more reviews, safer) vs 0.85 (lighter load)? Proposed 0.90; expose the knob.
2. Who runs the scheduler in production — script vs inline agent arithmetic? Proposed: ship both; PoC uses the script.
3. Initial stability seeding for legacy skills — how low? Proposed: seed low, let retrieval prove them; needs a few real sessions to calibrate.
4. Latency capture without a UI — self-reported or omitted? Proposed: optional, treated as a soft signal only.
5. How aggressively to interleave before it frustrates Tom — needs his feedback after ~5 sessions.
6. Messy-speaking evaluation depth — how many weak points to extract without overwhelming? Proposed cap 3.

## 17. What I deliberately defer

Trained ML scheduler / embeddings / any API; speech recognition + pronunciation scoring; full-corpus linguistic annotation; a GUI/app; auto-inferred prerequisite edges; same-day multi-step learning steps; post-lapse stability-recovery curves; global leaderboards. None require schema changes to add later (`scheduling_spec` §12, `corpus_mapping_spec` §8, `skill_graph_spec` §9).

## 18. Recommended implementation phases

- **P0 (done, this round):** schema, specs, scheduler prototype, PoC test, provenance + Git.
- **P1 — Minimum usable loop:** implement `/migrate` (seed from progress.txt), `/start`→`/end` with the scheduler wired to real `learner/` files, evaluation rubric applied by the agent, one real session writing state. Exit: one session generated, one answer graded, one item rescheduled, one skill updated — from files, no API.
- **P2 — Corpus + curriculum:** `glossika_index.jsonl`, anchor migration, `build_skill_graph.py`, reactivation pool, `/import` `/mastery` `/weak`.
- **P3 — Robustness + gamification:** property/schema/migration tests, gamification.yaml + honest XP, streak-freeze, messy-speaking batch evaluation.
- **P4 — Optional future:** app/API wrapper, speech, learned scheduler — only if the file system proves valuable.

## 19. Estimated complexity by phase

- P0: complete.
- **P1: Medium.** Mostly wiring + careful migration; the hard design is done. Main effort = faithful `progress.txt` seeding + agent-applied rubric. ~1–2 focused sessions.
- **P2: Medium-High.** Skill-graph reconstruction is the labor (curation of Modules 1–70). ~2–4 sessions, parallelizable across the two models.
- **P3: Medium.** Test scaffolding is straightforward; gamification is small but needs taste.
- **P4: High** and out of current scope.

## 20. Proposed Git commit plan

Executed this round (history in the repo / delivered bundle):
1. `chore: import and preserve source materials`
2. `docs: add research findings`
3. `docs: define learner model, scheduling, evaluation, and tutoring architecture`
4. `feat: scaffold transparent FSRS-lite scheduler prototype`
5. `test: add end-to-end review workflow fixtures (magpatingin PoC)`
6. `docs: add independent proposal + project-state/push handoff` (this file)

Proposed next (P1+, when implementation begins): `feat: implement /migrate seeding from progress.txt` → `feat: wire scheduler to learner state for /start.../end` → `test: schema-validation + migration round-trip` → `feat: glossika index + anchor mapping` → `feat: skill-graph build from Modules 1-70`. Each bounded change follows the loop-development protocol (lead implements → secondary reviews actual files → point-by-point response → decision log → commit).

---

### Appendix — claim-labeling discipline
Per `AGENTS.md`, claims here are tagged in the underlying research files as verified fact / research inference / design choice / learner preference / teaching simplification / uncertain. The headline design choices (three grains, FSRS-lite, partial credit, lazy mapping, honest gamification) are **design choices** justified by **research inference**; the linguistic rules are **verified facts** except the `dapat`+base-form rule, which is a **teaching simplification** and tagged as such everywhere it appears.
