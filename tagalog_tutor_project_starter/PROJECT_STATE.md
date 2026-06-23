# Project State

Date: 2026-06-23

## Current status

Independent **Claude planning round complete** (2026-06-23). Research, architecture, schema, a runnable scheduler prototype, and a passing proof-of-concept test are in the repo. No full system implemented yet (by design). The independent proposal is `collaboration/proposal_claude.md`. The Codex independent proposal was not read during this round.

### Produced this round
- `research/`: learning_science, current_apps, tagalog_pedagogy, design_synthesis, sources (evidence-labeled, dated).
- `srs/item_schema.json` (validated), `srs/scheduling_spec.md`, `srs/scheduler.py` (FSRS-lite prototype).
- `learner/model_spec.md`, `tutor/session_protocol.md`, `tutor/evaluation_rubric.md`, `curriculum/skill_graph_spec.md`, `corpus/corpus_mapping_spec.md`.
- `tests/` fixtures + `test_poc_flow.py` — the `magpatingin` partial-credit flow; **all assertions pass**.
- `collaboration/proposal_claude.md` — full 20-section independent proposal.

### Git status
- Repository **initialized**; logical commits on branch `main` (see `GIT_RECONSTITUTE.md` for the list).
- **Not pushed** (no remote/credentials available this session; not faked).
- The project folder is a mount that cannot host a live `.git`, so history was authored in a sandbox git DB and **delivered as a verified bundle** at the repo root: `tagalog_tutor_history.bundle`, with one-command reconstruct+push steps in `GIT_RECONSTITUTE.md`. Record the remote URL/branch here once Tom pushes.

## Available source material

- current Stage 4B tutor files
- current learner progress
- Modules 51–70 curriculum
- legacy Modules 1–50 curriculum
- Glossika sentence corpus
- current phrasebank
- core patterns
- verb-family notes
- historical tutor prompts
- audit and duplicate manifest

## Confirmed design needs

- persistent learner model
- mechanical spaced repetition
- exact-item, skill, and scene tracking
- production-first lessons
- structural explanations
- messy speaking
- Glossika reuse
- concise progress updates
- no external API requirement for the first version

## Known risks

- overcomplicated schemas
- treating all corpus sentences as natural targets
- false linguistic certainty
- too many review items
- recognition inflation
- same-session repetition mistaken for retention
- agents duplicating architecture work
- hidden dependence on a GUI or API

## Immediate next phase

Done this round: research (learning science, apps, Tagalog), learner-model + schema, file-based prototype scheduler, end-to-end PoC test.

Next:
1. Hand both independent proposals (`proposal_claude.md` + Codex's) to the external evaluator (loop-development Phase 2): comparison, lead selection, merged direction.
2. Adversarial review of this architecture (`collaboration/secondary_review.md`).
3. Begin P1 implementation only after schema/skill-graph/scheduling are agreed: wire the scheduler to real `learner/` files; implement `/migrate` and one real `/start` to `/end` session.
4. Then P2 (corpus index + skill-graph build) and beyond, per `proposal_claude.md` section 18.

## First prototype requirement — SATISFIED this round

The prototype handles the required real example (see `tests/test_poc_flow.py`, all assertions pass):
- due item: `dapat akong magpatingin`
- learner response: `dapat akong magpapatingin`
- evaluator detects future overmarking (`aspect.future_overmark_after_modal`)
- exact item is marked failed
- actor-pronoun / clitic / causative / health skills marked successful
- modal-base-form skill is weakened (S 3.0 -> 0.9, due +1 day)
- a contrast review is scheduled (`item.contrast.dapat_base_vs_contemplated`)
- session/attempt log structure defined and exercised
