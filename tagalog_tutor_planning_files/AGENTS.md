# Agent Roles and Collaboration Protocol

All agents must read:

1. `GOAL.md`
2. `LEARNER_PROFILE_TOM.md`
3. `CURRENT_TUTOR_METHOD.md`
4. `SYSTEM_ARCHITECTURE_NOTES.md`
5. `planning/AUDIT.md`
6. `current/progress.txt`

## Agent roles

### Learning-science researcher

Research:

- retrieval practice
- spacing
- interleaving
- desirable difficulty
- generation effect
- corrective feedback
- memory models
- habit and motivation
- limitations and controversies

Output:

`research/learning_science.md`

### Current-product researcher

Research current language-learning systems, including:

- Duolingo
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

Output:

`research/current_apps.md`

### Learner-model specialist

Analyze Tom's history and define:

- learner state
- error taxonomy
- production versus recognition mastery
- review-item schema
- skill aggregation
- confidence and uncertainty

Output:

`learner/model_spec.md`
`srs/item_schema.json`

### Tagalog pedagogy and linguistics reviewer

Review:

- structural explanations
- verb-family mappings
- naturalness
- register
- Taglish
- corpus quality
- teaching simplifications versus linguistic claims

Output:

`language/linguistic_review.md`
`corpus/corpus_quality_notes.md`

### System architect

Integrate the research into:

- file structure
- schemas
- session generation
- scheduling
- grading
- state updates
- test workflows

Output:

`PROJECT_STATE.md`
`srs/scheduling_spec.md`
`tutor/session_protocol.md`

### Adversarial reviewer

Challenge:

- unsupported assumptions
- contradictions
- overengineering
- hidden API dependencies
- weak test coverage
- poor learner fit
- linguistic risk

Output:

`collaboration/secondary_review.md`

## Collaboration rules

Each claim must be labeled as one of:

- verified fact
- research inference
- design choice
- learner preference
- teaching simplification
- uncertain

Do not silently convert a teaching shortcut into a grammar fact.

## Independent proposal round

Each major model writes an independent proposal before reading the other:

- `collaboration/proposal_codex.md`
- `collaboration/proposal_secondary.md`

Each proposal must include:

- architecture
- assumptions
- risks
- unresolved questions
- file changes
- what it deliberately does not solve

## Review loop

The reviewer writes:

`collaboration/secondary_review.md`

The lead answers every point in:

`collaboration/review_response.md`

Each issue gets one status:

- ACCEPTED
- PARTIALLY ACCEPTED
- REJECTED
- DEFERRED
- NEEDS EVIDENCE

Unresolved issues go into:

`collaboration/unresolved_disagreements.md`

## Stop condition

Do not stop merely because both models say they agree.

Stop when:

- no unresolved critical issue remains
- schemas are internally consistent
- a sample lesson can be generated
- a sample answer can be graded
- a review item can be rescheduled
- learner state can be updated
- Glossika mapping has a tested sample
- the system works without external API access
