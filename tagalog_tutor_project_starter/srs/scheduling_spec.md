# Scheduling Spec — FSRS-lite v0.1

Status: planning draft. Defines the **transparent, no-API** scheduler. Every constant is named and versioned (`scheduler_version: "fsrs-lite-0.1"`); the math is deliberately simple enough to audit by hand and to run as a ~150-line deterministic script (`srs/scheduler.py`, validated in the PoC). It captures FSRS's *shape* (stability / difficulty / retrievability, desirable-difficulty bonus, lapses) without trained weights, so the design satisfies "no opaque scoring" and can later be swapped for true FSRS without re-modelling items (same stored fields).

References `srs/item_schema.json` for `srs_state`. Applies independently to each schedulable unit (exact item, skill-modality, scene) in each modality.

---

## 1. State per unit (from item_schema `srs_state`)
`stability S` (days) · `difficulty D` (1–10) · `last_review` · `due` · `reps` · `lapses` · `last_retrievability`.

## 2. Forgetting curve (retrievability)
Power-law (FSRS-6 form):

```
R(t) = (1 + FACTOR * t / S) ^ DECAY
DECAY  = -0.5
FACTOR = 19/81            # chosen so that R(S) = 0.9 exactly
```
`t` = days since `last_review`. With these constants, when `t = S`, `R = 0.9`. Lower R = more forgotten.

## 3. Interval / due date
For a target retention `r` (default `TARGET_R = 0.90`):
```
interval(S, r) = (S / FACTOR) * ( r ^ (1/DECAY) - 1 )
due = last_review + round(interval)         # min 1 day for active items
```
At `r = 0.90`, `interval = S` (clean and auditable). Raising `r` shortens intervals (more reviews, higher retention); the constant is exposed so Tom can trade review load against retention.

## 4. Grades (from the evaluator's per-unit `credit_outcome`)
The evaluator emits a per-skill `credit_outcome`; the scheduler maps it to a grade and a hint weight:

| credit_outcome | grade | note |
|---|---|---|
| `pass` (unaided) | `good` (or `easy` if fast + first-try + low R) | full stability gain |
| `pass_hinted` | `hard` | hint weight applies |
| `fail` | `again` | lapse path |
| `partial` | split per skill in the credit vector (some `good`, some `again`) | the partial-credit mechanism |
| `n/a` | — | unit not exercised |

## 5. Initial stability (first successful study), days
```
S_init(again)=0.5  S_init(hard)=1.0  S_init(good)=2.5  S_init(easy)=5.0
D_init = 5.0
```

## 6. Success update (grade ∈ {hard, good, easy})
```
S_new = S * (1 + Δ)
Δ = SC * hardness(D) * spacing(R) * w_grade * w_hint * w_modality

SC            = 2.0                      # base growth scaler
hardness(D)   = (11 - D) / 10            # easy items (low D) grow more; range (0.1 .. 1.0]
spacing(R)    = clamp(1 - R, 0.05, 1.0)  # reviewing later (low R) grows S more = desirable difficulty
w_grade       : hard 0.5 | good 1.0 | easy 1.5
w_hint        : none 1.0 | intent_only 0.9 | slot_hint 0.6 | root_family 0.5 | contrast_label 0.5 | scaffold_full 0.2
w_modality    : production 1.0 | listening 0.5 | recognition 0.3   # contribution to the production track
```
`spacing(R)` is floored at 0.05 so reviewing slightly early still yields a little gain; it is the desirable-difficulty engine (review when R is low → bigger durable gain). Hint weight prices in assistance. Modality weight enforces "recognition is not mastery."

Difficulty on success (mean-reverting toward 5):
```
D <- D + (hard:+0.0 | good:-0.5 | easy:-1.0)
D <- D + 0.05 * (5 - D)        # slow reversion
D <- clamp(D, 1, 10)
```

## 7. Failure update (grade = again)
```
S_new   = max(S_MIN, S * LAPSE_MULT)     # LAPSE_MULT=0.3, S_MIN=0.5
lapses += 1
D      <- clamp(D + 0.8 + 0.05*(5-D), 1, 10)
relearn: due = today (same-session re-ask once), then +1 day next session
status -> lapsed (if was stable) ; -> leech if lapses >= 4
```
A failed delayed retrieval of a previously-stable item is the most informative event: it shows the prior "stable" was false, contracts S sharply, and (via the evaluator) spawns a targeted contrast item.

## 8. Mastery gate ("stable")
A **skill** becomes `stable` only when ALL hold (matches the project's mastery bar; backed by retrieval + receptive≠productive evidence):
1. `unaided_delayed_production` — ≥1 `pass` with `hint=none` after an inter-session gap ≥ 7 days,
2. `scene_use` — ≥1 `pass` inside a scene/messy-speaking attempt,
3. `listening_check` — ≥1 recognition pass in the listening modality,
4. `variation_handled` — ≥1 pass on a different exact item exercising the same skill,
5. production-track `S ≥ 21` days.
Recognition/listening passes alone can raise their own modality state but **cannot** satisfy gate 1 or push production S.

## 9. Selection (what a session pulls), with load throttle
```
due_pool = units where R(today) < TARGET_R   (i.e., overdue)
rank by: priority desc, then (TARGET_R - R) desc (most overdue first), then HIGH-skill coverage
MAX_DUE_PER_SESSION = 12 production-equivalents (recognition counts 0.3, listening 0.5)
NEW_RATIO_CAP = 0.35   # new material <= 35% of the session
```
**No overdue avalanche:** items that age past due accrue **no extra penalty** for system backlog — they simply remain in `due_pool`. Lapses are only incremented by an actual failed attempt, never by the clock. After an absence, the session selects the top `MAX_DUE_PER_SESSION` by rank and lets the rest wait; nothing is punished for the gap.

**Interleaving:** when two `confusable_with` skills are both due, the selector pulls both into the same session and alternates their prompts rather than blocking.

## 10. Worked example (the proof-of-concept; full numbers in tests/)
Skill `skill.modal.base_form`, currently `S=3.0, D=6.0, last_review=2026-06-20`, reviewed `2026-06-23` (t=3, so R≈0.90). Tom fails (`Dapat akong magpapatingin`).
```
fail -> S_new = max(0.5, 3.0*0.3) = 0.9 ; lapses+1 ; D -> 6.0+0.8+0.05*(5-6.8)=6.71
due  = 2026-06-23 + interval(0.9,0.90)= +1 day -> 2026-06-24 (relearn)
```
Same attempt, skill `skill.voice.actor` `S=8,D=4` passes unaided:
```
good,unaided,production: spacing(R≈0.9)=0.10 ; Δ=2.0*(0.7)*0.10*1.0*1.0*1.0=0.14
S_new = 8*1.14 = 9.12 ; due = +9 days
```
So one answer pushes the actor-voice skill out to 9 days while pulling the modal-base-form skill back to 1 day — exactly the partial-credit behavior the project requires. Numbers reproduced by `srs/scheduler.py` in the PoC.

## 11. Constants table (versioned — change = new scheduler_version)
`TARGET_R 0.90 · DECAY -0.5 · FACTOR 19/81 · SC 2.0 · LAPSE_MULT 0.3 · S_MIN 0.5 · D_init 5.0 · leech_lapses 4 · MAX_DUE 12 · NEW_RATIO_CAP 0.35 · stable_S 21 · delayed_gap_days 7`

## 12. Deliberately out of scope (Phase 1)
Trained per-user weights, fuzz/randomized intervals, same-day multi-step learning steps beyond one relearn, post-lapse stability recovery curves. These are FSRS refinements that can be added later **without schema changes**.
