# Skill Graph Spec — v0.1

Status: planning draft. Defines how Modules 1–70 are reconstructed into a **skill graph** (the AUDIT's "reconstruct a unified skill graph from Modules 1–70" and the instruction's curriculum-reconstruction requirement). The graph is the backbone the learner model attaches state to.

Principle: **module completion ≠ skill mastery.** A module is *exposure history*; mastery is whatever `learner/skills_state.yaml` currently says.

---

## 1. Why a graph, not a concatenation
The curriculum files repeat skills across modules (e.g., *may/wala* in M1, M52, M54; modals in M6, M16, M17; clitics in M2 and again as a HIGH weak point at M61). Concatenation would double-count and lose prerequisites. A graph stores each skill **once**, with the modules that touched it and the edges to its prerequisites and confusables.

## 2. Node schema (`curriculum/skill_graph.yaml`, state in `learner/skills_state.yaml`)
Reuses `srs/item_schema.json#/$defs/skill`. Key fields:
```yaml
- id: skill.modal.base_form
  label_practical: "base verb form after dapat/kailangan/gusto/puwede"
  label_linguistic: "infinitive/basic aspect under modal predicate"
  type: modal
  prerequisites: [skill.voice.actor, skill.clitic.second_position]
  confusable_with: [skill.aspect.contemplated]
  introduced_in_modules: ["6","16","17"]
  reviewed_in_modules: ["51","61"]
  priority: HIGH
  humility_note: "Teaching rule: keep verb base after a modal. Not an absolute law (aspect can co-occur with dapat in some natural speech). Never assert the strong claim."
```

## 3. Edge types
- `prerequisite` — A must be at least `active` before B is introduced as new.
- `confusable_with` — drives **interleaving** in session selection (symmetric).
- `composes_into` — skill → scene membership (a scene's `component_skill_ids`).

## 4. Reconstruction process (Modules 1–70)
A one-time, reviewable build (proposed `curriculum/build_skill_graph.py`, Phase 2 — not implemented in this planning round):
1. Parse module headers + "Core targets/frames/Root families" blocks from `legacy/curriculum_modules_1_50.txt` and `current/curriculum_stage4b_modules_51_70.txt`.
2. Map each target to a skill id (linguistically-typed). Maintain a hand-curated `alias_map.yaml` (e.g., "ako-track" → `skill.voice.actor`).
3. Record introduced/reviewed module lists; infer prerequisites from module order + linguistic dependence (clitics before modal+clitic frames, etc.).
4. Emit `skill_graph.yaml` for human review (diffable) before any state is seeded.

This is explicitly **not** automated blindly — it is a curated migration with a human/agent review gate (matches the project's "do not simply concatenate").

## 5. The four AUDIT questions, answered structurally
| Question | Mechanism |
|---|---|
| which modules are historical only | nodes whose only module refs are legacy AND not reviewed in 51–70; still reactivatable |
| which skills remain active | nodes with `status ∈ {active, learning, lapsed}` in current state |
| which topics overlap | nodes with multiple `introduced_in_modules` |
| which skills are missing | scenes whose `component_skill_ids` include nodes with no state yet → gaps to teach |

## 6. Reactivation pool (old Glossika / old modules)
Skills not retrieved in N days (default 21) re-enter `due` **regardless of how 'done' their module was**. This operationalizes "old items should re-enter review" and "recalling older modules after long gaps" (Tom's logged weak point). Reactivation pulls a *recognition* check first; only if that passes does it schedule a *production* re-test (cheap triage before expensive production).

## 7. Seeding strategy (initial stability)
- Skills in `current/progress.txt` STABLE block → seed `status: active`, production `S ≈ 7d` (not `stable`).
- Skills only in legacy modules → seed `status: suspended`, `S` small; reactivation must *prove* them.
- HIGH weak points (e.g., clitic placement, modal base form) → `status: learning`, short `S`, `due` ≈ today.
This deliberately under-credits the past so retrieval evidence — not module completion — drives mastery. (Conservative on purpose; see `research/design_synthesis.md` §K.)

## 8. Mapping current Stage 4B + legacy into domains/scenes
Domains already align cleanly across both curricula (transport, shopping, home, food, health, errands, service, family, social, self-intro, daily-recap). Each becomes a scene cluster; legacy M37–50 (domain cleanup) and current M52–70 map onto the same domain scenes, so legacy items reactivate into the *same* scene tests Tom uses now — reuse, not duplication.

## 9. Out of scope (Phase 1)
Auto-inferring prerequisite edges by statistics; a visual graph UI; covering pre-M37 grammar exhaustively. The graph ships seeded for the *active* Stage 4B skills + the HIGH weak points first, expanding lazily.
