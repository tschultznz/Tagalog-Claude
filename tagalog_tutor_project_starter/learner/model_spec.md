# Learner Model Spec — v0.1

Status: planning draft. Defines what the system stores about Tom and where. Backed by `srs/item_schema.json` (the formal schema) and the research files. Design invariant: **nothing is "known" or "mastered" except as data in these files**; the tutor reads them at session start and writes them at session end.

---

## 1. File layout (`learner/`)
```
learner/
  profile.yaml          # stable facts & preferences (rarely changes) — from LEARNER_PROFILE_TOM.md
  skills_state.yaml     # the skill graph's live state: per-skill, per-modality srs_state
  review_items.yaml     # exact items (scarce, promotion-gated)
  scenes_state.yaml     # scene/boss competence + srs_state
  attempt_log.jsonl     # append-only: every attempt (the atomic learning event)
  session_log.jsonl     # append-only: one line per session
  preferences.yaml      # explanation/format preferences, hint defaults, register goals
  gamification.yaml     # xp totals, due-review streak, personal bests, achievements
```
Structured state = YAML (human-diffable, the project's preference). Logs = JSONL (append-only, never rewritten — preserves history, enables audit and the spaced-repetition record the current system lacks). Raw corpus stays immutable under `corpus/`.

Rationale for splitting state from history (the AUDIT's "split learner state from review history"): `skills_state.yaml` is the *current* snapshot you can regenerate by replaying `attempt_log.jsonl`. If state is ever corrupted, the log is the source of truth.

## 2. What is stored, mapped to the instruction's required list

| Required (instruction §7) | Where | How |
|---|---|---|
| exact items | `review_items.yaml` | `review_item` objects |
| skills | `skills_state.yaml` | `skill` nodes |
| scenes | `scenes_state.yaml` | `scene` objects |
| domains | scene.domain + skill tags | enum |
| error types | `attempt_log` `error_tags[]` + per-skill rollup | taxonomy in evaluation_rubric |
| production / recognition / listening status | `modality_state` (3 srs_states) | independent per modality |
| hint dependence | attempt `hint_level_used`; per-skill rolling hint rate | priced in scheduling |
| response confidence / latency | attempt `latency_sec` (+ self-rated, optional) | signal, not a grade |
| stability / difficulty / due | `srs_state` | FSRS-lite |
| recent failures / successes | `attempt_log` (queryable) + skill `reps`/`lapses` | — |
| mastery evidence | skill `mastery_evidence` flags | gates "stable" |
| learner / explanation preferences | `profile.yaml`, `preferences.yaml` | drives tutor style |
| fatigue / session load | `session_log` summaries; `MAX_DUE` throttle | adaptive load |

## 3. profile.yaml (seed content, from LEARNER_PROFILE_TOM.md)
```yaml
identity: { l1: German, l2_fluent: English, target: Tagalog }
cognitive_style: [analytical, structure_first, root_family_maps, pattern_contrast]
two_pass_production: true          # decide meaning -> build form; the latency source
bridge_when_retrieval_fails: structure   # do NOT remove structure
likes: [produce_before_answer, hints_below_drill, concise_correction,
        natural_spoken, messy_speaking, actor_vs_target_explicit, write_attempt_then_correct]
dislikes: [answer_key_before_attempt, unexplained_chunks, vague_naturalness_claims,
           paradigm_dumps, midstream_explanation_changes, same_session_only_drilling,
           recognition_as_mastery, losing_glossika_investment]
real_goal: survive_messy_real_speech_in_Philippines   # incl. partner's family (register matters)
```

## 4. preferences.yaml (operational knobs Tom can edit)
```yaml
default_hint_offer: fade            # offer the lowest hint that the skill's stability still warrants
correction_style: [wrong_form, better_form, one_short_reason]
register_goals: [po_with_elders_and_vendors, casual_with_partner, taglish_where_natural]
session_length_target_min: 12
new_material_cap: 0.30
explain_depth: compact             # expand only on explicit request
show_me_the_evidence: true         # surface delayed-recall wins (interleaving trust)
```

## 5. Seeding from current state (one-time migration)
`current/progress.txt` is parsed into initial state, treating completion as **exposure, not mastery** (project rule):
- Its STABLE block → skills seeded `status: active`, modest production `S` (e.g., 7 days), **not** `stable` until the mastery gate is met by fresh evidence.
- Its WATCH block (with `last_seen`, `review_due D3/D7`, priority) maps almost 1:1 onto `review_item`/skill state — e.g., *"dapat akong magpatingin vs magpapatingin ako bukas | HIGH | D3"* becomes the PoC item plus `skill.modal.base_form` (HIGH, short S). The existing date-tags give us real `last_review`/`due` seeds.
- OVERDUE markers → `due` in the past → selected first next session.

This means migration is **lossless and faithful to his real history**, not a reset.

## 6. Confidence, uncertainty, and honesty
- Per-skill state carries `last_retrievability` and rep/lapse counts so the tutor can say *"this is genuinely fragile (3 lapses)"* vs *"this is holding (S=30d)"* with evidence, never vibes.
- The model never converts a recognition pass into a production claim (separate modality state).
- The model never asserts a teaching rule as linguistic law: skills carry both `label_practical` and `label_linguistic`, and humility-flagged rules (e.g., `dapat`+base-form) are tagged so the tutor hedges appropriately.

## 7. Privacy / footprint
All state is local plain text the learner owns and can read, diff, and delete. No account, no server, no telemetry. This is the file-based system's structural advantage over app "learner models" that live on vendor servers.
