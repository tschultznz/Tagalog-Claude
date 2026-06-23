# Tutor Session Protocol — v0.1

Status: planning draft. Defines how a session runs as **read state → generate → evaluate → write state**, operable entirely through chat over the project files, **no API, no UI**. Commands are documented verbs the agent (Codex or Claude) executes by reading/writing the `learner/` files per the specs.

---

## 1. The operating contract
> The tutor never decides informally what to recycle. At session start it **reads** `learner/skills_state.yaml` + `review_items.yaml` + `session_log.jsonl`, **computes** the due set via `srs/scheduling_spec`, and **selects** mechanically. At session end it **writes** updated state and appends to the logs. (This is the single biggest fix to the current method.)

## 2. Default session loop
Combines the current method's strong loop with the new mechanical scheduling:
1. **Load state** — read learner files; compute due set (R < target) and overdue ranking.
2. **Recovery check** — if gap since last session ≥ 3 days, run a short recognition-first recovery before new material (existing rule, kept).
3. **Micro review** — clear top HIGH due items first (production, hints faded).
4. **One concept hint** — root-family/structural map only if a due or new skill needs it.
5. **Pattern in several forms** — for the session's focus skill(s), interleaving confusables.
6. **Controlled drill, production-first** — intent prompt + hints *below*; Tom produces before any answer.
7. **Evaluate** (per `tutor/evaluation_rubric.md`) — partial-credit vector, concise correction, schedule updates, spawn contrasts.
8. **Choice-based half-dialogue** — applied use with English intent hints.
9. **Messy-speaking scene** (≥ M60 / weekly) — no mid-turn correction; batch feedback; extract ≤3 weak points.
10. **Listening micro** — one short written spoken-style dialogue + one recognition task.
11. **Update state + concise progress** — write files; show Tom a short, honest state delta (incl. a delayed-recall win if any, to build trust in the harder path).

Session load targets carried from the current system prompt (evidence-supported): 1 carryover weak point, 8–12 old mini-frames, 1 concept hint, 3–6 new chunks, 4–8 controlled prompts, 3–5 half-dialogues, 1 listening micro. New material ≤ 30–35%.

## 3. Commands (documented verbs; map to file ops)
Each command is something Tom can type in chat; the agent performs the file reads/writes.

| Command | Reads | Writes | Purpose |
|---|---|---|---|
| `/start` | all learner state | session_log (open) | begin a normal session (loop §2) |
| `/continue` | session_log (last) | session_log | resume mid-session |
| `/ask <question>` | language/*, skills_state | (optional note) | open grammar Q&A; answers labeled fact vs teaching-rule vs naturalness |
| `/review` | due set | — | show what's due now and why (transparency) |
| `/weak` | skills_state, attempt_log | — | list weakest skills w/ evidence (lapses, S, last R) |
| `/skill <id>` | one skill node | — | inspect one skill: state, history, confusables |
| `/errors <family>` | attempt_log | — | inspect one error family (e.g., aspect.future_overmark_after_modal) |
| `/messy [topic]` | due skills | attempt_log, spawned items | messy-speaking scene; talk-then-correct |
| `/import` | corpus_anchor_index, corpus | glossika_index, corpus_mapping | run/extend Glossika mapping (lazy) |
| `/migrate` | progress.txt, curricula | skills_state, review_items | one-time seed from current state (treats completion as exposure) |
| `/mastery` | skills_state, scenes_state | — | mastery map: per-domain, per-modality |
| `/update` | open session buffer | skills_state, review_items, scenes_state, logs | flush all state to disk |
| `/end` | — | session_log (close), gamification | finish; write concise progress + XP events |

All commands are **inspectable** — `/review`, `/weak`, `/skill`, `/errors`, `/mastery` exist specifically so Tom can audit the model that schedules him (autonomy + transparency from the research).

## 4. Hint policy at runtime (assistance-dilemma-aware)
- Offer the **lowest** hint level the skill's stability still warrants (`fade`): a skill with `S < 2` may get `root_family`; a stabilizing skill gets only `contrast_label`; a near-stable skill gets `intent_only`.
- Tom can always escalate with `/scaffold` (existing escape hatch) for one cold item — and the system **prices that in** (scaffold success earns little stability, flags `signal.hint_dependence`).
- Hints always sit **below** the prompt; never a full answer key before production (existing hard rule).

## 5. Correction at runtime
Immediate, concise, top 1–2 severity items only: *wrong form → better form → one short reason* (Tom's preferred style). The remaining errors are logged, not lectured. A **spaced re-test** of the corrected point is scheduled (immediate-now + spaced-later, resolving the feedback-timing tension).

## 6. Progress update at session end (anti-compression)
The current system's weakness was over-compressed summaries. The new end-of-session note is short but **evidence-bearing**:
```
Today: 7 attempts, 5 unaided. modal.base_form lapsed (3rd time) -> contrast drill queued for tomorrow.
voice.actor held after 9 days (delayed-recall WIN, +15 XP). Next due: 6 items, mostly clitic placement.
Module 62 not advanced (mastery gate not met on errands scene).
```
Honest, compact, and never claims mastery the data doesn't support. Dates are computed from the scheduler, never guessed (fixes the "historical dates sometimes wrong" failure).

## 7. Advancement gate (kept, made mechanical)
A module advances only when its scene's `component_skill_ids` meet the mastery gate (`scheduling_spec` §8). "Module finished" is a computed fact about skill state, not a feeling that a lesson ended.

## 8. Why this works without an API
Every step is a deterministic read/transform/write over local files plus the agent's own language ability (which Tom is already paying for via Codex/Claude). The scheduler is a local script or inline arithmetic; the content generation is the agent; the memory is the files. Nothing calls an external model API. Migrating later to an app means wrapping these same files — no relearning-model rewrite (the project's portability requirement).
