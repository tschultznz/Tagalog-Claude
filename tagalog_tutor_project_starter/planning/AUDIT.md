# Tagalog Tutor Archive Audit

Date: 2026-06-23

## Executive finding

The archive contains 29 files, but many are byte-for-byte duplicates. The important unique sources are:

1. The current Stage 4B files for Modules 51–70.
2. The complete legacy curriculum for Modules 1–50.
3. The current Stage 4B system prompt.
4. The older Stage 4 operating prompt.
5. The Glossika sentence corpus.
6. The current learner progress file.
7. Two historical rebuild archives retained only for provenance.

The legacy Modules 1–50 curriculum is not obsolete duplication. It is the only complete record of the earlier course structure and should remain available for skill reconstruction and spaced-repetition mapping.

## Canonical active files

The `current/` folder contains normalized filenames for the active Stage 4B system:

- system prompt
- current curriculum for Modules 51–70
- current progress
- core patterns
- verb system
- phrasebank
- corpus anchor index
- teacher profile/file map
- Claude review brief

The source contents are unchanged; only filenames and locations were normalized.

## Canonical legacy files

The `legacy/` folder contains unique historical material:

- `curriculum_modules_1_50.txt`
- `tutor_operating_prompt_stage4.txt`

These should be treated as historical course knowledge, not as active instructions. They can be mined to reconstruct prior skills, domains, and review targets.

## Corpus

The Glossika corpus is stored once under `corpus/tagalog_sentences.txt`.

It should remain immutable as the raw familiarity corpus. Future indexing, naturalness tagging, and skill mapping should be stored in separate derivative files rather than editing the raw corpus.

## Duplicate findings

Several loose files in `old/` are exact duplicates of current Stage 4B files:

- core patterns
- Stage 4B curriculum
- phrasebank
- teacher profile
- verb system
- corpus anchor index

The v2 nested archive also contains the same current Stage 4B prompt and content. These copies are retained only inside the historical archive, not duplicated in the active folders.

## Files not promoted

- `desktop.ini`: operating-system metadata, not course content.
- replacement-pack duplicate files: superseded by the current Stage 4B set.
- v1 rebuild contents: retained inside the original archive for provenance.
- duplicate numbered filenames such as `(3)` and `(2)`: normalized in the cleaned set.

## Important unresolved work

This package is a pre-clean, not a final migration. The next design phase should:

1. Reconstruct a unified skill graph from Modules 1–70.
2. Separate teaching policy from curriculum content.
3. Split learner state from review history.
4. Convert weak points into atomic review items.
5. Build corpus-to-skill mappings.
6. Mark corpus sentences for naturalness and register.
7. Define a mechanical review scheduler.
8. Preserve all original files in an immutable archive.
