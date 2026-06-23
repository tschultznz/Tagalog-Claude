CLAUDE REVIEW BRIEF — STAGE 4B v2 PATCHED
Last updated: 2026-05-09

Context:
Claude reviewed v1 and approved the core architecture: multi-file separation, root-family approach, production-first format, choice-based half-dialogues, Stage 4B bridge, and gated advancement.

This v2 incorporates Claude's suggested edge fixes.

INCORPORATED CHANGES

1. Phrasebank answer-key leakage fixed
- system_prompt_tom_tagalog_tutor.txt now contains PHRASEBANK USE RULE.
- stage4_phrasebank.txt now explicitly says it is internal selection material, not an answer key.

2. Spaced repetition date-tagging added
- progress.txt now uses last_seen, review_due D3/D7/D14, priority, and status.
- system prompt requires checking due items at session start.

3. Listening micro inserted
- system prompt requires one short written listening-recognition micro per session.
- curriculum includes listening micro in each module and dedicated modules 58 and 65.

4. Particles and po-register strengthened
- Module 55.5 added.
- core_patterns has particle micro-contrasts.
- phrasebank marks po-register/casual/neutral.

5. Numbers/money/time consolidated
- Module 53.5 added.
- core_patterns and anchor index include number/time/money frames.

6. Corpus naturalness rule added
- system prompt now tells tutor to prefer natural spoken rephrasing when corpus is stilted.
- Module 52 includes "Mainit dito sa kuwarto" vs stilted corpus line.

7. Scaffold escape hatch added
- /scaffold mode allows teach-then-drill for one cold item.

8. Taglish reality added
- curriculum, system prompt, core_patterns, phrasebank include Taglish-natural labels.

9. Verb roots expanded
- verb_system now explicitly includes dala, dating, tira, alis.
- also keeps bigay, kuha, hintay, balik, tanong, inom, kain, bukas/sara, lagay.

10. Module sequence adjusted
- Keep numbering 51-70.
- Module 52 starts next.
- Module 53.5 numbers/money/time inserted.
- Module 55.5 po-register/particles inserted before shopping if needed.
- Module 56.5 self-introduction inserted.
- Module 68 folded/reserved to reduce overlap with Module 64.

QUESTIONS FOR CLAUDE
1. Is the Module 52-70 sequence now coherent?
2. Should 55.5 be taught before or after Module 55 shopping?
3. Are the Taglish labels conservative enough?
4. Is the listening micro requirement light enough not to overwhelm?
5. Is the progress date-tagging format compact enough for repeated use?
6. Are any Stage 4B modules still too broad?
7. Should Module 68 remain reserved/folded or be replaced with a specific domain?
8. Are the naturalness notes accurate and safe?
9. Are the new verb roots sufficient for Stage 4B?
10. Does the system prompt over-constrain the tutor or preserve flexibility?

CURRENT NEXT LESSON
Module 52: Describing Things I — size, temperature, open/closed, new/old.
Start with short Module 51 maintenance review.
