# System Architecture Notes

## Core model

The tutor should track three layers simultaneously.

### 1. Exact item

A high-value chunk or contrast.

Example:

`Dapat akong magpatingin.`

### 2. Underlying skill

The reusable structural knowledge.

Example:

`modal + actor pronoun + base verb`

### 3. Scene competence

Ability to use the language in context.

Example:

`describe symptoms and make a care plan`

A single answer should update all relevant layers.

## Example evaluation

Learner response:

`Dapat akong magpapatingin.`

Possible updates:

- exact chunk: failed
- actor pronoun: succeeded
- modal plus base form: failed
- future overmarking: active error
- health vocabulary: succeeded
- scene meaning: understandable

## Recommended project data

```text
learner/
  profile.md
  current_state.yaml
  review_items.jsonl
  attempt_log.jsonl
  session_log.jsonl
  preferences.yaml

curriculum/
  modules_1_70.yaml
  module_status.yaml
  skill_graph.yaml

language/
  patterns.yaml
  verb_families.yaml
  particles.yaml
  register.yaml
  naturalness_notes.yaml

corpus/
  tagalog_sentences.txt
  glossika_index.jsonl
  corpus_mapping.jsonl
  corpus_quality_notes.md

srs/
  scheduling_spec.md
  grading_rubric.md
  review_selection.md
  item_schema.json

tutor/
  session_protocol.md
  correction_policy.md
  prompt_generation.md
  evaluation_rubric.md
```

## Review-item model

A review item should include:

- unique ID
- prompt
- expected intent
- acceptable answers
- skill tags
- scene tags
- difficulty
- stability
- last reviewed
- due date
- hint history
- attempt history
- production or recognition mode
- source
- related Glossika anchors
- naturalness notes

## Scheduling principles

The scheduler should use a modern memory model such as FSRS or an equivalent stability/retrievability model.

It should schedule:

- exact chunks
- structural contrasts
- transfer prompts
- scene-level retrieval

It should not create a card for every sentence.

## Suggested review cycle

1. Exact production.
2. Controlled variation.
3. Contrast with a confusable form.
4. New-context transfer.
5. Messy scene.
6. Listening recognition.
7. Spontaneous production.

## Session composition

A typical session should contain:

- all overdue high-priority items
- one or two overdue medium-priority items
- one older stable item for long-term retention
- one new concept at most
- one messy scene
- one listening micro
- a concise learner-state update

New material should normally be no more than 25–35% of a session.

## Progression rules

Correct on first attempt:
- increase stability
- widen interval
- consider harder transfer

Correct with hint:
- smaller interval increase
- preserve active status

Incorrect:
- classify the error
- reset or shorten the interval
- generate a related contrast item

Mastery requires:
- production without hints
- delayed retrieval
- variation
- one scene use
- one recognition check

## Glossika integration

The raw corpus should remain immutable.

Derivative mapping should tag each useful sentence with:

- module
- domain
- skill
- verb family
- vocabulary
- register
- naturalness
- production target
- recognition status
- production status

The system should reactivate prior Glossika exposure rather than replace it.
