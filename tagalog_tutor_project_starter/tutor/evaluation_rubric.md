# Evaluation Rubric — v0.1

Status: planning draft. Defines how the tutor turns one learner production into (a) a partial-credit vector over skills, (b) error tags, (c) scheduler grades, and (d) follow-up items. This is the logic the AUDIT said must **not** live in prose — it lives here and in `srs/item_schema.json`, so any agent (Codex or Claude) grades the same way.

---

## 1. Evaluation pipeline (deterministic order)
For each attempt:
1. **Meaning check** — does the production convey the intended meaning? (`meaning_ok`). If no → top-priority error `meaning.wrong_core`; everything else is secondary.
2. **Decompose into skills exercised** — from the item's `skill_ids` (+ any extra skills the response invokes).
3. **Per-skill credit** — assign each `credit_outcome ∈ {pass, pass_hinted, fail, partial, n/a}`.
4. **Error tagging** — attach `error_tag`s for failures (taxonomy below).
5. **Register & naturalness** — `register_ok`, `naturalness ∈ {natural, understandable, awkward, unintelligible}`.
6. **Scheduler grades** — map outcomes → grades (per `scheduling_spec` §4) and apply updates.
7. **Spawn follow-ups** — active errors create contrast items.
8. **Correction message** — concise: wrong form → better form → one short reason (Tom's preferred style). Immediate in-session; a spaced re-test is scheduled for later.

## 2. Error taxonomy (with severity, correction priority, spawn behavior)
Severity drives correction order (meaning first); `spawns_contrast` says whether a failure creates a future targeted item.

| tag | severity | corr. priority | spawns_contrast |
|---|---|---|---|
| `meaning.wrong_core` | CRITICAL | 1 | yes |
| `scene.unnatural` (unusable for the scene) | HIGH | 2 | sometimes |
| `clitic.placement` | HIGH | 3 | yes |
| `voice.actor_target_mismatch` | HIGH | 3 | yes |
| `register.inappropriate` (e.g., no `po` with elder) | HIGH (social) | 4 | yes |
| `linker.error` (-ng/na) | MED | 5 | sometimes |
| `negation.error` (hindi/wala/huwag) | MED | 5 | sometimes |
| `aspect.future_overmark_after_modal` | MED | 6 | yes |
| `aspect.error` (other) | MED | 6 | sometimes |
| `particle.meaning` (na/pa/lang/na lang/naman…) | MED | 6 | sometimes |
| `lexical.substitution` | LOW–MED | 7 | if meaning-affecting |
| `spelling.only` | LOW | 9 | only if recurring |
| `signal.hesitation` (high latency) | signal | — | no (confidence signal) |
| `signal.hint_dependence` | signal | — | no (de-weights stability) |
| `signal.comprehension_without_production` | signal | — | no (keeps modality split honest) |

Correction policy mirrors the current system's order (meaning → usability → clitics → person/register → linker → negation → particles → verb family → aspect → spelling). The rubric does **not** flood Tom: correct the top 1–2 severity items, log the rest.

## 3. Partial credit — the worked PoC
Intent: *"I should go get myself looked at (see a doctor)."* Target: `Dapat akong magpatingin.`
Tom: **`Dapat akong magpapatingin.`**

```yaml
meaning_ok: true
register_ok: true            # neutral was fine
naturalness: understandable
credit_vector:
  - { skill_id: skill.causative.magpa,        outcome: pass }   # correct verb family (be examined)
  - { skill_id: skill.voice.actor,            outcome: pass }   # ako-track correct
  - { skill_id: skill.clitic.second_position, outcome: pass }   # 'akong' placement + linker correct
  - { skill_id: skill.lex.health,             outcome: pass }
  - { skill_id: skill.modal.base_form,        outcome: fail }   # base form required after dapat
  - { skill_id: skill.aspect.contemplated,    outcome: fail }   # overmarked future
error_tags: [aspect.future_overmark_after_modal]
corrected_tl: "Dapat akong magpatingin."
one_line_reason: "After dapat, keep the verb in base form — dapat already carries the 'should/future' sense."
```
Note the **humility flag**: the reason is phrased as the reliable production rule, not "aspect is illegal after dapat" (which is not absolutely true — see `research/tagalog_pedagogy.md` §2). The skill `skill.modal.base_form` carries `label_linguistic` + a humility note so the tutor never over-claims.

Scheduler effect (per `scheduling_spec` §10): `modal.base_form` and `aspect.contemplated` contract and become due tomorrow; `voice.actor`, `clitic.second_position`, `causative.magpa`, `lex.health` grow and push out. One answer, six independent updates.

## 4. Outcome → grade mapping (for the scheduler)
```
pass (hint=none)            -> good   (-> easy if latency low AND first-try AND R<0.7)
pass (hint=none, but slow)  -> good   (+ signal.hesitation)
pass_hinted                 -> hard   (w_hint applies; if scaffold_full, mark signal.hint_dependence)
fail                        -> again
partial                     -> resolved at the skill level (vector has both good and again)
```

## 5. Spawned follow-up items
A failure with `spawns_contrast: yes` creates a `review_item` with `source.kind: learner_error` and `spawned_by_attempt`. For the PoC it creates a **minimal contrast pair drill**:
```
intent: "say you should see a doctor (now) vs you will see one tomorrow"
target_tl: "Dapat akong magpatingin."          # base after modal
acceptable_tl: ["Magpapatingin ako bukas."]      # contemplated is correct WITHOUT a modal
skill_ids: [skill.modal.base_form, skill.aspect.contemplated]
hint_levels: [intent_only, contrast_label]
```
This is the mechanism by which "errors create future review items" (instruction §error model) — and it interleaves the two confusable skills by construction.

## 6. Scoring messy speaking / scenes (Busuu pattern)
During a messy-speaking scene the tutor **does not correct mid-turn** (protects flow). It logs candidate errors silently, and at the end:
1. gives a short batch summary,
2. extracts ≤3 weak points → spawns/*strengthens* skill state,
3. credits `scene_use` toward the mastery gate for skills used correctly.
This realizes the project's "messy speaking → extract 3 weak points for structured drills" rule as data.

## 7. What the rubric refuses to do
- Refuse to grade a recognition tap as production evidence.
- Refuse to mark `meaning_ok:false` when meaning was fine but form was off (the PoC is `meaning_ok:true`) — meaning and form are separate axes.
- Refuse to assert naturalness as fact; `naturalness: awkward` is a judgment, logged as such.
