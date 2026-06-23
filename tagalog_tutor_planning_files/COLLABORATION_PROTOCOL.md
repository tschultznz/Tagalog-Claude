# Collaboration Protocol

## Purpose

Allow two major AI systems to design, critique, and refine the tutor without losing decisions or repeating work.

## Round 1: independent designs

Each model receives the same project files.

Each writes a complete system proposal independently.

Required sections:

- architecture
- learner model
- scheduling model
- corpus integration
- tutoring workflow
- evaluation
- gamification
- migration plan
- risks
- open questions

## Round 2: comparison

Create `collaboration/comparison.md` using these criteria:

- research quality
- learner fit
- linguistic safety
- technical simplicity
- maintainability
- SRS quality
- corpus reuse
- no-API viability
- testability

## Round 3: lead selection

Choose one lead model.

The other becomes the reviewer.

The lead should be selected for architecture quality and evidence discipline, not prose quality.

## Round 4: implementation-review loop

1. Lead proposes or implements one bounded change.
2. Reviewer checks the actual files.
3. Reviewer records issues by severity.
4. Lead responds point by point.
5. Reviewer verifies the response.
6. Decision log is updated.

## Required communication files

```text
collaboration/
  proposal_codex.md
  proposal_secondary.md
  comparison.md
  lead_questions.md
  reviewer_answers.md
  implementation_notes.md
  secondary_review.md
  review_response.md
  decision_log.md
  unresolved_disagreements.md
```

## Severity levels

- CRITICAL
- HIGH
- MEDIUM
- LOW
- NOTE

## Decision statuses

- ACCEPTED
- PARTIALLY ACCEPTED
- REJECTED
- DEFERRED
- NEEDS EVIDENCE

## Exit criteria

The first design phase is complete only when:

- the review schema works
- one attempt can be evaluated
- one item can be rescheduled
- one skill can be updated
- one scene can be generated
- one Glossika sentence can be mapped
- one lesson can be produced
- no external API is required
