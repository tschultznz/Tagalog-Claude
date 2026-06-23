# Research → Design Synthesis

Compiled 2026-06-23. This file converts the three research streams into the specific design commitments that the architecture specs implement. It is the bridge from *evidence* to *schema*.

---

## A. The central reframing

The current system's failure is **not** weak content — the curriculum and explanations are strong. It is that **memory is managed by prose, not mechanism**. The tutor "remembers" weak points informally, re-drills them within a session (massing — the worst case for retention), and treats recognition as mastery. Every high-value research finding points to the same fix: **move scheduling, scoring, and learner memory out of the prose and into auditable files with explicit rules.**

So the architecture is organized around one invariant:

> **Every learning event is logged as data; every session is generated from that data; no mastery claim exists outside the data.**

## B. The grain problem (and its resolution)

Glossika scheduled **sentences**; Anki schedules **cards**; both explode if you make one unit per sentence (the project's stated fear: "card explosion"). But scheduling only **skills** loses the concrete chunks Tom actually needs in a shop or clinic.

**Decision — three coupled grains, scheduled independently but updated together:**
1. **Exact item** — a high-value chunk/contrast (e.g., `Dapat akong magpatingin.`). Few, hand-promoted, scheduled.
2. **Skill** — reusable structure (e.g., `modal + actor pronoun + base verb`). The aggregation layer; carries the durable mastery signal.
3. **Scene** — applied competence (e.g., `clinic: describe symptoms + make a care plan`). The transfer test.

A single attempt updates all three via a **credit-assignment vector** (Section D). This is the project's own exact/skill/scene model — the research validates it (Speak's pattern→automatize→free-use; Bjork's storage strength accrues at the skill level; transfer must be tested at the scene level) and the synthesis adds the *mechanics* that were missing.

**Card-explosion control:** only skills and scenes are created freely; **exact items are scarce and promoted on evidence** (a chunk becomes a scheduled exact item only when it's high-value AND has failed at least once, or is a designated module anchor). Corpus sentences are *never* auto-promoted to scheduled items — they live in a separate mapping pool and are pulled in as recognition/listening material or as evidence toward a skill. This is what stops the explosion.

## C. Scheduling: FSRS-lite (transparent, no-API)

From the learning-science file: adopt FSRS's *shape*, not its trained weights.

- Each scheduled unit stores **stability** (S, days), **difficulty** (D, 1–10), **last_review**, **due**, and per-modality state.
- **Retrievability** R(t) = (1 + t/(c·S))^(−k) — a power-law forgetting curve (FSRS-6 shape), evaluated at review time to prioritize.
- **Update rules** are explicit, versioned constants (in `srs/scheduling_spec.md`), not a black box:
  - clean unaided success → S grows by a difficulty-scaled multiplier;
  - hinted success → much smaller growth (hints priced in);
  - failure → S contracts, item re-enters short interval, D mean-reverts upward slightly;
  - recognition-only success → updates the recognition modality, contributes little to production stability.
- **Target retention** 0.90 default; **load throttle** caps due items per session and ages overflow gracefully (no overdue avalanche after an absence).

This is implementable as a ~150-line deterministic Python script (validated in the PoC) and is fully inspectable — satisfying "no opaque scoring."

## D. Partial credit (the magpatingin requirement)

The instruction's hard test: one answer must update many layers with **partial** success. Implemented as a **credit vector** the evaluator emits per attempt:

```
attempt → { skill_id: outcome }   where outcome ∈ {pass, pass_hinted, fail, n/a}
```

For `Dapat akong magpapatingin`:
`voice.actor: pass`, `clitic.second_position: pass`, `causative.magpa: pass`, `modal+base_form: fail`, `aspect.future_overmark_after_modal: fail(active_error)`, `vocab.health: pass`, `scene.clinic: partial(understandable)`.

The exact item fails; the skills move independently; the active error becomes a **scheduled contrast item**. No existing app does this because none carries a skill-indexed learner memory — it is our differentiator (current_apps §synthesis).

## E. Hints, modalities, correction timing

- **Hints priced + fading:** every prompt records `hint_level_used`; stability gain scales down with it; the *offered* hint level for an item decays as its skill stabilizes (assistance-dilemma evidence).
- **Three modalities** (recognition / production / listening) tracked separately; **stability can reach "stable" only on unaided, delayed production + ≥1 scene + ≥1 listening** (matches the project's mastery bar; backed by retrieval-practice + receptive≠productive evidence).
- **Immediate correction now + spaced re-test later:** in-session concise correction (good for Tom, good for meaning-blocking errors) PLUS a scheduled delayed contrast (captures the spacing benefit). Resolves the corrective-feedback-timing dispute instead of picking a side.

## F. Interleaving and session composition

- Sessions **interleave confusable families** (actor/target; aspect contrasts; `kunin`/`kumuha`) rather than blocking — directly targets Tom's logged track-switching weakness.
- Composition (from SYSTEM_ARCHITECTURE_NOTES, kept because evidence supports it): all overdue HIGH items, 1–2 MED, one old stable item (long-term retention), ≤1 new concept, one messy scene, one listening micro, concise state update. New material ≤25–35%.
- Because interleaving *feels worse*, the tutor surfaces delayed-recall wins in the progress summary so Tom trusts the harder path (metacognition evidence).

## G. Gamification that rewards learning, not engagement

Reward only science-aligned events (current_apps + learning_science §7):
- **no-hint production**, **delayed-recall success** (item recalled after a long gap), **recovery** (re-mastering a lapsed item), **scene/boss clears**, **skill-stability milestones**, **register-appropriateness**.
- Prefer a **due-review streak** (cleared what was due) over a raw daily streak; include a **streak-freeze/recovery** so a missed day doesn't punish.
- **Never** reward recognition as production, app-opening, or volume alone. No countdown/loss-aversion pressure. Transparent: Tom can read his XP rules and state.

This is the rare case where Tom's stated motivators ("gamification tied to actual learning quality") and the ethics evidence point the same way.

## H. Glossika migration (staged, not bulk)

Do **not** annotate ~1,300 lines up front (project caution). Instead: a **lazy, on-demand mapping** — when a skill/scene needs material, map only the handful of corpus lines it needs, tagging skill/domain/register/naturalness/spoken_target, and append to `corpus/corpus_mapping.jsonl`. A small **triage pass** (LingQ-style known/unknown) can pre-rank lines by Tom's familiarity, but full annotation is demand-driven. This reuses his investment without the upfront cost or the explosion.

## I. Curriculum reconstruction (skill graph, not file concat)

Modules 1–70 are **coverage history, not mastery proof** (project rule). Reconstruct a **skill graph**: nodes = skills, edges = prerequisites; each node records which modules introduced/reviewed it and its current per-modality state. "Module 61 finished" becomes "these skills were *exposed*," and their *mastery* is whatever the data says now. Legacy modules become a **reactivation pool**: skills not retrieved in N days resurface regardless of how "done" their module was. (Spec: `curriculum/skill_graph_spec.md`.)

## J. What the evidence tells us to deliberately NOT do (Phase 1)

- No trained ML scheduler, no embeddings, no API (no-API rule; FSRS-lite suffices).
- No speech scoring yet (text workflow first; listening = written spoken-style dialogue, as now).
- No full-corpus annotation (lazy mapping).
- No raw daily streak / leaderboard (engagement-dark-pattern risk; Tom dislikes anyway).
- No one-card-per-sentence (explosion).

## K. Open tensions carried into the proposal

1. **Modality bookkeeping cost vs. value** — three modalities per skill is more state to maintain by hand/agent. Mitigation: the agent updates it, not Tom; sample fixtures prove it's tractable.
2. **Who runs the scheduler** — a deterministic script (reproducible, testable) vs. the agent computing inline (no runtime dependency, but less auditable). Recommendation: ship the script *and* document the math so either can run it; PoC validates the script.
3. **`dapat`+aspect humility** — the teaching rule is reliable but not absolute; encoded as a tagged form-error, never an absolute claim.
4. **How much to trust legacy "completed" modules** — resolved by treating completion as exposure only, but the *initial* stability seeding of legacy skills is a judgment call (proposed: seed low, let retrieval prove them).
