# Project State

Date: 2026-06-23

## Current status

The project is in pre-implementation research and architecture.

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

1. Research learning science.
2. Research current language apps and AI tutors.
3. Audit Tagalog pedagogy and linguistic explanations.
4. Define learner-model and review-item schema.
5. Design a small file-based prototype.
6. Test one end-to-end lesson cycle.
7. Review the architecture adversarially.
8. Only then expand the implementation.

## First prototype requirement

The prototype must handle one real example:

- due item: `dapat akong magpatingin`
- learner response: `dapat akong magpapatingin`
- evaluator detects future overmarking
- exact item is marked failed
- actor pronoun skill is marked successful
- modal-base-form skill is weakened
- a contrast review is scheduled
- session log is updated
