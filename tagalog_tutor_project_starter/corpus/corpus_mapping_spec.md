# Corpus Mapping Spec — v0.1

Status: planning draft. Defines how Tom's Glossika corpus (`corpus/tagalog_sentences.txt`, ~1,300 EN–TL pairs) is reused **without** (a) editing the raw file, (b) annotating all of it up front, or (c) exploding into one card per sentence. Implements the instruction's Glossika-integration and migration requirements and the project's stated cautions.

---

## 1. Immutability
`corpus/tagalog_sentences.txt` is **read-only forever**. All derived data lives in separate sidecar files. Provenance: every mapping references a raw line by its number (the corpus is already numbered `1.`–`1xxx.`).

## 2. Sidecar files
```
corpus/
  tagalog_sentences.txt        # RAW, immutable
  glossika_index.jsonl         # 1 line per corpus sentence: id, en, tl, lightweight auto-tags
  corpus_mapping.jsonl         # SPARSE: only sentences actually mapped to skills/scenes
  corpus_quality_notes.md      # naturalness/register audit notes (human-readable)
```
`glossika_index.jsonl` is cheap to generate fully (just a structured copy + regex tags). `corpus_mapping.jsonl` is **demand-driven** and stays small.

## 3. Index record (cheap, can cover the whole corpus)
```json
{"id": 47, "en": "It's hot in this room.", "tl": "Mainit sa kuwarto na ito.",
 "auto_tags": {"has_po": false, "has_taglish": false, "len_tokens": 5,
               "verb_guess": null, "domain_guess": "home"},
 "familiarity": "unknown"}
```
`auto_tags` come from regex/heuristics only (no linguistic claims). `familiarity ∈ {unknown, seen, known}` supports a LingQ-style triage pass.

## 4. Mapping record (sparse, hand/agent-curated, the valuable layer)
Created only when a skill or scene needs material. Carries the linguistic + naturalness judgments:
```json
{"corpus_id": 47,
 "skill_ids": ["skill.adj.predicate", "skill.deictic.dito"],
 "scene_ids": ["scene.home.conditions"],
 "domain": "home", "register": "neutral",
 "naturalness": "stilted_corpus",
 "spoken_target": "Mainit dito sa kuwarto.",
 "use_as": ["recognition", "listening"],
 "production_target": false,
 "note": "Corpus line is grammatical but written-register; teach the spoken rephrase for production.",
 "evidence_tag": "naturalness_judgment"}
```
Field meanings:
- `naturalness ∈ {natural, neutral, stilted_corpus}` — the audit flag from `research/tagalog_pedagogy.md` §9.
- `spoken_target` — the natural rephrase used as the **production** target when the raw line is stilted.
- `use_as` — which modalities this line is allowed to feed (a stilted line may be fine for recognition/listening but barred from production).
- `production_target` — explicit gate so stilted lines never become forced production.
- `evidence_tag` — keeps naturalness calls labeled as judgments, not facts.

## 5. The ten required Glossika fields (instruction §Glossika integration) → where they live
raw sentence (`glossika_index.en/tl`) · skill tags (`mapping.skill_ids`) · root family (`mapping.skill_ids` of type lexical/verb + language/verb_families.yaml) · vocabulary (`auto_tags`/mapping) · domain (`mapping.domain`) · register (`mapping.register`) · naturalness (`mapping.naturalness`) · preferred spoken target (`mapping.spoken_target`) · recognition state + production state (in `learner/` modality_state of the skill/item the line feeds, **not** on the corpus line itself — corpus lines are not scheduled units).

Key design choice: **corpus lines are evidence/material, not schedulable cards.** They feed skills/scenes; the SRS state lives on the skill/item. This is the explosion firewall.

## 6. Lazy migration workflow (`/import` and `/map` commands)
1. **Index once:** generate `glossika_index.jsonl` for the whole corpus (cheap; auto-tags only).
2. **Triage (optional):** a session can mark lines `seen/known` to pre-rank reactivation candidates.
3. **Map on demand:** when a skill/scene needs an anchor, search the index, pick ≤ a handful of lines, write `corpus_mapping.jsonl` records with the judgments above. The existing `current/corpus_anchor_index.txt` is the seed for this (it already maps ~80 high-value anchors to modules) — migrate it first.
4. **Reactivate:** mapped lines whose skill is overdue resurface as recognition/listening material.

`current/corpus_anchor_index.txt` migration: its entries (e.g., M52 → lines 36,47,83,122,…; with the naturalness note on line 47) translate almost directly into `corpus_mapping.jsonl`, giving an immediate, non-trivial mapped set without touching the raw corpus.

## 7. Worked Glossika-linked example (required by instruction §12)
Corpus line **282**: *"I'll call her tomorrow. — Tatawagan ko siya bukas."* (from `current/corpus_anchor_index.txt`, service/repair).
```json
{"corpus_id": 282,
 "skill_ids": ["skill.voice.patient", "skill.aspect.contemplated", "skill.clitic.second_position"],
 "scene_ids": ["scene.service.followup"],
 "domain": "service", "register": "neutral", "naturalness": "natural",
 "spoken_target": "Tatawagan ko siya bukas.",
 "use_as": ["recognition", "production", "listening"], "production_target": true,
 "note": "Natural line. Good CONTRAST partner for the PoC: here contemplated 'tatawagan' is CORRECT because there is no modal. Pair with 'Dapat ko siyang tawagan' (base after modal)."}
```
This line is the perfect interleave partner for the PoC: it shows contemplated aspect is *correct* without a modal (`Tatawagan ko siya bukas`) versus base form *with* a modal (`Dapat ko siyang tawagan`). The same corpus Tom already studied becomes the contrast material that fixes his modal-base-form error — "reactivate prior exposure rather than replace it."

## 8. Out of scope (Phase 1)
Full-corpus linguistic annotation; audio; automatic naturalness scoring. Only the index is full-coverage; mappings stay sparse and curated.
