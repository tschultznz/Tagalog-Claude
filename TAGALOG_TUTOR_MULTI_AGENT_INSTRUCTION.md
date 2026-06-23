# TAGALOG TUTOR — MULTI-AGENT RESEARCH, DESIGN, AND LOOP-DEVELOPMENT INSTRUCTION

## Purpose

You are one of two independent senior AI collaborators working on the same long-term project:

**Build a file-based, persistent, adaptive AI Tagalog tutor for Tom that runs through Codex or Claude as the primary interface, without requiring external API access in the first version.**

The project must preserve and improve the current tutor system, reuse Tom’s Glossika corpus and prior modules, implement real spaced repetition, support open-ended questions, understand Tom’s strengths and weaknesses, and gradually become capable of structured drills, messy speaking, listening work, and adaptive review.

You are not being asked to follow the existing design mechanically. The project files are a starting point, not a final architecture. You have creative freedom to improve the system, simplify it, challenge assumptions, or replace weak ideas—provided that you preserve the core learner needs and explain major design decisions.

This is an independent design round. Do not coordinate with the other model yet. Do not read or infer the other model’s proposal. Produce your own best plan from first principles and from the project files.

---

# 1. Operating context

Tom will use:

- Codex or Claude as the main interface
- project files as persistent memory
- Git for version control and cross-model review
- no dedicated app or UI in the first phase
- no external language-model API in the first phase
- a future app only if the file-based system proves valuable

The AI interface must be able to:

- read learner state
- generate the next session
- ask and answer questions
- evaluate Tom’s production
- update the review queue
- update skill state
- preserve session history
- use the Glossika corpus
- work entirely from the repository and the interactive coding/chat environment

The system should be designed so that it can later migrate to an app or API-backed architecture without requiring a rewrite of the learning model.

---

# 2. Read these files first

Before planning, read all relevant project files.

Priority order:

1. `GOAL.md`
2. `LEARNER_PROFILE_TOM.md`
3. `CURRENT_TUTOR_METHOD.md`
4. `SYSTEM_ARCHITECTURE_NOTES.md`
5. `AGENTS.md`
6. `PROJECT_STATE.md`
7. `RESEARCH_PLAN.md`
8. `COLLABORATION_PROTOCOL.md`
9. `planning/AUDIT.md`
10. `current/progress.txt`
11. `current/system_prompt_tom_tagalog_tutor.txt`
12. `current/curriculum_stage4b_modules_51_70.txt`
13. `legacy/curriculum_modules_1_50.txt`
14. `corpus/tagalog_sentences.txt`
15. all other relevant language, pattern, phrasebank, and historical files

Do not treat old prompts as active instructions unless they are explicitly promoted into the new design.

Do not treat completed modules as proof of current mastery.

Do not modify the raw Glossika corpus.

---

# 3. Core learner requirements

The system is for Tom.

Tom is:

- a native German speaker
- fluent in English
- analytical and structure-oriented
- heavily exposed to Glossika Tagalog
- stronger in recognition than spontaneous production
- able to learn through root families, structural contrasts, and practical scenes
- frustrated by weak delayed review
- helped by messy speaking
- helped by production before answers
- dependent on structure when memory retrieval fails
- slowed by a two-pass process:
  1. decide intended meaning
  2. build correct Tagalog form

The system must not remove structure from the teaching method.

The long-term goal is to reduce reliance on conscious structural reconstruction by combining:

- clear structure
- repeated retrieval
- delayed review
- controlled variation
- realistic transfer
- messy speaking

Tom wants the tutor to remember:

- what he knows
- what he confuses
- when he last saw it
- whether he answered without hints
- whether he only recognized it
- whether he can use it in a realistic exchange
- which explanations help him
- which forms repeatedly collapse under pressure

---

# 4. Non-negotiable pedagogical principles

The new system must preserve or improve these principles:

## Production before answers

Tom should attempt before seeing a full answer key.

## Spaced retrieval

Review must be mechanically scheduled, not informally remembered by the tutor.

## Recognition is not mastery

Production, recognition, listening, structured variation, and scene use should be tracked separately where useful.

## Structure plus retrieval

Do not choose between structure and chunks. Use both.

## Messy speaking

The system must regularly require free or semi-free production using due material.

## Practical scenes

Transport, shopping, home, food, health, errands, service, family, social situations, and daily recap should remain central.

## Concise correction

Correct meaning-blocking errors first. Avoid drowning the learner in low-priority detail.

## Linguistic humility

Distinguish:

- practical teaching rule
- linguistic analysis
- naturalness judgment
- uncertain claim
- verified rule

Do not present elegant but unverified explanations as facts.

## Glossika preservation

Tom’s prior Glossika investment must remain useful.

The corpus should be indexed, tagged, mapped to skills, and reused selectively.

Do not force stiff or unnatural corpus sentences as production targets.

---

# 5. Core system design problem

The system must model at least three levels:

## Exact item

Example:

`Dapat akong magpatingin.`

## Underlying skill

Example:

`modal + actor pronoun + base verb`

## Scene competence

Example:

`describe symptoms and make a care plan`

A single answer may update all three.

Example learner response:

`Dapat akong magpapatingin.`

Possible evaluation:

- exact chunk: failed
- actor pronoun: succeeded
- modal + base form: failed
- future overmarking: active error
- health vocabulary: succeeded
- scene meaning: understandable

The system should be capable of representing this kind of partial success.

---

# 6. Required first-phase research

Before finalizing architecture, conduct current research.

## Learning science

Research:

- spaced repetition
- FSRS and alternatives
- retrieval practice
- generation effect
- interleaving
- desirable difficulty
- hint dependence
- corrective feedback
- latency and confidence
- memory stability and retrievability
- overtesting
- habit formation
- gamification
- motivational design
- risks of compulsive or manipulative design
- long-term language retention
- transfer from controlled drills to spontaneous production

## Current language-learning products

Research current systems and compare observable mechanics, including:

- Duolingo
- Duolingo Max or current AI features
- Glossika
- Anki and FSRS
- SuperMemo
- Babbel
- Busuu
- Memrise
- LingQ
- Speak
- Praktika
- other current AI tutors
- any notable adaptive language-learning tools

For each product, analyze:

- what is scheduled
- what counts as mastery
- how errors are reused
- how much production is required
- how listening is tested
- how hints work
- how motivation is maintained
- whether AI remembers the learner
- whether the learner can ask open questions
- how transparent the progress model is
- what is likely pedagogically useful versus mostly engagement design

## Tagalog pedagogy and linguistics

Research or carefully audit:

- actor versus target track teaching
- aspect and potential forms
- causative and derivational forms
- pronoun and clitic placement
- natural spoken Tagalog
- register
- po-register
- Taglish
- common learner traps for English and German speakers
- how to teach Tagalog structure without paradigm overload

## Evidence standards

For all research:

- cite direct sources
- include dates
- distinguish strong evidence from design inference
- distinguish product marketing from observed behavior
- note uncertainty
- avoid unsupported claims

---

# 7. Required design work

Design the complete system.

You may improve or replace the initial file structure.

At minimum, address:

## Learner model

Define how the system stores:

- exact items
- skills
- scenes
- domains
- error types
- production status
- recognition status
- listening status
- hint dependence
- response confidence
- stability
- difficulty
- due date
- recent failures
- recent successes
- mastery evidence
- learner preferences
- explanation preferences
- fatigue or session load signals if relevant

## Scheduling model

Design how review is selected.

Address:

- FSRS or alternative model
- exact items versus skills versus scenes
- failure resets
- hint penalties
- long-term review
- overdue prioritization
- interleaving
- avoiding review overload
- avoiding card explosion
- promotion from chunk to variation to scene
- recognition versus production scheduling
- old Glossika reactivation
- review diversity
- limited new-content ratio

## Error model

Define a practical error taxonomy.

Examples:

- wrong core meaning
- unnatural for scene
- pronoun placement
- linker error
- actor/target mismatch
- aspect error
- modal + future overmarking
- negation error
- particle meaning error
- lexical substitution
- spelling only
- hesitation
- hint dependence
- comprehension without production

Define how errors create future review items.

## Tutor workflow

Design a normal session.

The tutor should be able to:

- inspect due items
- generate a lesson
- ask Tom to produce
- accept questions
- explain structure
- evaluate answers
- adjust difficulty
- insert messy speaking
- include listening recognition
- update state
- stop at a reasonable point
- produce a concise progress summary

## Glossika integration

Design a practical mapping system for:

- raw sentence
- skill tags
- root family
- vocabulary
- domain
- register
- naturalness
- preferred spoken target
- recognition state
- production state
- module relevance
- learner familiarity

Do not map the entire corpus manually in the first iteration.

Design a scalable tagging and migration process.

## Curriculum

Reconstruct a unified view of Modules 1–70.

Do not simply concatenate files.

Determine:

- which modules are historical only
- which skills remain active
- which topics overlap
- which skills are missing
- which old items should re-enter review
- how module completion differs from skill mastery

## Gamification

Design useful gamification.

Possible elements:

- daily streak
- due-review streak
- XP
- no-hint bonus
- delayed-recall bonus
- recovery bonus
- boss scenes
- personal bests
- mastery map
- skill stability
- weekly review
- streak freeze
- domain achievements

Do not reward trivial recognition as if it were difficult production.

Do not optimize for engagement at the expense of learning.

Avoid manipulative mechanics.

## Codex/Claude interface

The first system must be operable entirely through the coding/chat project interface.

Design commands or workflows such as:

- start session
- continue session
- ask grammar question
- review due items
- inspect weak points
- import old material
- run migration
- view mastery
- inspect one skill
- inspect one error family
- generate a messy-speaking scene
- update progress
- end session

These may be implemented through documented files, scripts, or project commands.

No dedicated UI is required.

---

# 8. File-based implementation constraints

The first implementation should be auditable and version-controlled.

Prefer:

- Markdown for human-readable principles and reports
- YAML or JSON for structured state
- JSONL for append-only attempt and session logs
- scripts for deterministic selection and updates
- tests for core flows

Avoid:

- storing all state in one giant prompt
- destructive edits
- hidden state
- opaque scoring
- unnecessary databases
- unnecessary services
- premature UI
- premature speech integration
- premature full-corpus annotation

The system should be easy for both humans and AI agents to inspect.

---

# 9. Git requirements

Initialize a Git repository in the project directory.

Create a sensible `.gitignore`.

Make an initial commit preserving the imported source files.

Then commit research, architecture, and scaffolding in logical stages.

Recommended commit sequence:

1. `chore: import and preserve source materials`
2. `docs: add research findings`
3. `docs: define learner model and tutoring architecture`
4. `feat: scaffold file-based learner state and review system`
5. `test: add end-to-end review workflow fixtures`

If remote access is available and explicitly authorized:

- create or configure the remote repository
- push the branch
- record the remote URL and branch name in `PROJECT_STATE.md`

If remote credentials are unavailable:

- initialize the repository
- commit locally
- write exact push instructions
- do not pretend the push succeeded

Do not expose secrets.

Do not commit credentials.

---

# 10. Independent planning requirement

This is an independent plan.

Do not read the other model’s proposal during this phase.

Create your own design based on:

- the project files
- your research
- first-principles reasoning
- Tom’s learner profile
- operational constraints

You are expected to improve on the starting ideas.

Do not merely restate the existing architecture notes.

Challenge them where appropriate.

---

# 11. Required planning deliverables

Create:

## `collaboration/proposal_<model>.md`

Use the appropriate filename:

- `proposal_codex.md`
- `proposal_claude.md`

The proposal must include:

1. executive summary
2. research synthesis
3. learner-model design
4. scheduling design
5. exact-item / skill / scene architecture
6. error taxonomy
7. tutor-session workflow
8. Glossika integration
9. curriculum reconstruction
10. gamification
11. Codex/Claude operating workflow
12. file and schema design
13. migration plan
14. testing strategy
15. risks
16. unresolved questions
17. what you deliberately defer
18. recommended implementation phases
19. estimated complexity by phase
20. proposed Git commit plan

## Research files

Create or update:

- `research/learning_science.md`
- `research/current_apps.md`
- `research/tagalog_pedagogy.md`
- `research/design_synthesis.md`
- `research/sources.md`

## Architecture files

Create proposed versions of:

- `learner/model_spec.md`
- `srs/scheduling_spec.md`
- `srs/item_schema.json`
- `tutor/session_protocol.md`
- `tutor/evaluation_rubric.md`
- `curriculum/skill_graph_spec.md`
- `corpus/corpus_mapping_spec.md`

These are design artifacts in the planning round.

Do not yet implement the entire system unless needed to test a critical design assumption.

---

# 12. Required proof-of-concept example

Your plan must demonstrate one complete sample flow.

Use this real learner error:

Expected:

`Dapat akong magpatingin.`

Learner produced:

`Dapat akong magpapatingin.`

Show:

- how the attempt is logged
- which exact item is affected
- which skills succeed
- which skill fails
- which error tag is assigned
- how the next review is scheduled
- what follow-up prompt is generated
- how a later messy-speaking scene reuses the same distinction
- how the system decides when the skill becomes stable

Also include one Glossika-linked example from the corpus.

---

# 13. Loop-development protocol

This project will use loop development across two models.

## Phase 1: independent plans

Each model independently produces its full plan.

No cross-reading.

## Phase 2: external comparison

Tom will provide both plans to a third evaluator.

The evaluator will:

- compare architectures
- identify strengths
- identify contradictions
- recommend a lead
- propose a merged direction

## Phase 3: second planning round

Both models may receive:

- the other proposal
- the comparison
- questions
- proposed merged principles

Each model then writes:

- `collaboration/review_of_other_model.md`
- `collaboration/revised_proposal_<model>.md`

## Phase 4: lead selection

One model becomes lead.

The other becomes secondary reviewer.

## Phase 5: implementation loop

For each bounded change:

1. lead proposes or implements
2. secondary reviews actual files
3. secondary writes findings
4. lead responds point by point
5. secondary verifies
6. decision log is updated
7. commit is made
8. push occurs if authorized and possible

## Issue statuses

Use:

- ACCEPTED
- PARTIALLY ACCEPTED
- REJECTED
- DEFERRED
- NEEDS EVIDENCE

## Severity

Use:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- NOTE

## Stop condition

Do not stop because both models say “looks good.”

A phase is complete only when:

- no unresolved critical issue remains
- schemas are consistent
- the proof-of-concept flow works
- one session can be generated
- one answer can be evaluated
- one item can be rescheduled
- one skill can be updated
- one scene can be updated
- one Glossika item can be mapped
- the workflow works without an external API

Residual disagreements must be recorded.

---

# 14. Creative freedom

You are encouraged to:

- simplify the design
- replace weak schemas
- propose better scheduling
- improve the multi-agent loop
- invent useful commands
- propose better gamification
- challenge the exact-item / skill / scene model if you have a stronger alternative
- propose a graph, Bayesian, FSRS, or hybrid learner model
- identify hidden assumptions
- create small prototypes to validate design choices

You are not required to preserve every existing filename or concept.

You are required to preserve:

- source provenance
- learner history
- Glossika corpus
- production-first teaching
- structural explanations
- messy speaking
- adaptive review
- no-API first phase
- project-file operability

---

# 15. Important cautions

Do not:

- overfit the system to one recent module
- assume previous completion equals current mastery
- create one card per sentence
- make the entire corpus active at once
- use recognition as the main mastery signal
- rely on the AI to “remember” without files
- hide evaluation logic in prose
- conflate linguistic theory with teaching shortcuts
- build a UI before the learning engine works
- require an API before Tom chooses to pay for one
- claim a Git push succeeded if it did not
- read the other model’s independent proposal before completing yours

---

# 16. Final response format

At the end of the planning run, report:

1. what you researched
2. what you designed
3. what files you created or changed
4. what assumptions you challenged
5. what remains uncertain
6. whether Git was initialized
7. whether commits were created
8. whether a remote push succeeded
9. what Tom should review first
10. the exact path to your independent proposal

Keep the final chat summary concise.

The repository files are the primary deliverable.
