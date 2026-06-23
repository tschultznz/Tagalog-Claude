# Goal

Build a file-based AI Tagalog tutor system that works inside a Codex or project workspace without requiring external API access.

## Primary outcome

Create a persistent, adaptive Tagalog tutor that:

- remembers Tom's strengths and weaknesses
- schedules delayed retrieval
- reuses the Glossika corpus
- preserves structural explanations
- includes messy speaking
- tracks exact items, underlying skills, and scene competence
- supports questions and free-form tutoring
- works without a dedicated app or GUI
- can later be migrated into a standalone application

## Success conditions

The first usable system must:

1. Read current learner state.
2. Select overdue review items mechanically.
3. Generate a production-first lesson.
4. Evaluate answers with explicit error tags.
5. Update review intervals.
6. Update skill confidence.
7. Preserve a session log.
8. Reuse earlier modules and Glossika anchors.
9. Distinguish recognition from production.
10. Work entirely through project files and chat.

## Non-goals for the first version

- No external API requirement.
- No mobile or web UI.
- No global leaderboard.
- No speech scoring until the text workflow is stable.
- No destructive migration of original files.
- No attempt to model every Tagalog verb form at once.

## Core design principle

Structure is the map. Spaced retrieval is the engine. Messy speaking is the transfer test.
