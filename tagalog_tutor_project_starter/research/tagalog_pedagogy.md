# Research / Audit: Tagalog Pedagogy and Linguistics

Compiled 2026-06-23. This file audits the linguistic claims in Tom's existing materials and grounds the structures the tutor teaches, observing the project's **linguistic-humility** rule. Every claim is tagged:

- **[VERIFIED]** standard in reference grammars (Schachter & Otanes; Kroeger; Wikipedia "Tagalog grammar" as tertiary pointer)
- **[TEACHING-RULE]** a deliberate simplification that is *useful and safe* for Tom's level, even if not the full linguistic truth
- **[NATURALNESS]** a judgment about what sounds natural in spoken PH Tagalog/Taglish, inherently softer
- **[UNCERTAIN]** I am not confident; flag before asserting to Tom

Sources + retrieval dates in `research/sources.md`.

---

## 1. Voice / focus / "trigger" — the actor vs target track

**[VERIFIED]** Tagalog's defining feature is the **voice/trigger system**: the verb's affix marks which argument is the grammatical pivot (marked by *ang*/*si*), and that argument's thematic role — agent, patient, location, beneficiary, instrument — is what the affix selects. Actor/agent trigger affixes: **-um-, mag-, ma-, mang-**. Patient/object trigger: **-in (‑in/‑an), i-**, etc.

**[VERIFIED]** It is **not** simply active vs passive. Patient-trigger clauses are extremely common and *unmarked* in everyday speech (Tagalog often prefers patient trigger where English uses active voice), so calling it "passive" misleads English/German learners into under-using it.

**[TEACHING-RULE]** The project's **"ako-track vs ko-track"** framing (actor: *Puwede ba akong maghintay?* / target: *Hintayin ko na lang ba ito?*) is an excellent, safe simplification. It teaches the *choice* via the pronoun the learner reaches for (*ako* vs *ko*) and the natural frame, deferring the word "trigger." **Audit verdict: keep it.** Recommend only that internal skill tags use precise labels (`voice.actor` / `voice.patient`) so the data model stays linguistically honest even while the *teaching surface* stays practical.

**[NATURALNESS]** For German/English speakers the hard part is not forming each voice but *choosing* it under time pressure — exactly Tom's logged weak point ("switching between actor and target tracks"). This is an **interleaving** target, not a paradigm to memorize.

## 2. Aspect (not tense) — and the proof-of-concept error

**[VERIFIED]** Tagalog verbs inflect for **aspect**, not tense. Three finite aspects plus the basic/infinitive form:
- **Infinitive / basic** — no aspect marking (e.g., *magpatingin*, *kumain*, *bumili*).
- **Contemplated** (unstarted, irrealis): CV-**reduplication**, no *-in-* infix (e.g., *magpapatingin*, *kakain*, *bibili*). Often maps to English future.
- **Imperfective** (ongoing/habitual): reduplication **+** realized marking (e.g., *kumakain*, *bumibili*).
- **Perfective** (completed): realized marking, no reduplication (e.g., *kumain*, *bumili*).

**[VERIFIED]** **`magpa-` is the causative** ("have something done to/for oneself; get someone to do"). **`magpatingin`** = *pa-* causative on root *tingin* ("look/examine") = literally "have someone look at you" → **"have oneself examined (by a doctor)."** Its contemplated form is **`magpapatingin`** ("will have oneself examined"), via reduplication of the *pa-* syllable (pa → papa).

### The PoC, precisely
- Target: **`Dapat akong magpatingin.`** = "I should have myself looked at / see a doctor."
- Tom produced: **`Dapat akong magpapatingin.`**
- **What's right:** the *causative* choice (`magpa-`, correct — he wants *to be examined*, not to examine), the *actor track* (`ako`), and the second-position clitic with linker (`akong`). Health vocabulary fine. Meaning fully understandable.
- **What's wrong:** he marked **contemplated aspect** (`magpapa-`) where the **base form** belongs.

**[TEACHING-RULE]** After a modal like **`dapat` / `kailangan` / `gusto` / `puwede`**, the lexical verb takes the **infinitive/base form** (*Dapat akong magpatingin*, *Gusto kong kumain*, *Kailangan kong bumalik*). The modal already carries the unrealized meaning, so reduplicating the main verb double-marks the future. This is the reliable rule to teach Tom, and it generalizes across his verb families.

**[UNCERTAIN / HUMILITY]** The full truth is softer than the teaching rule. In natural speech aspect *can* co-occur with `dapat` in some constructions (corpus example surfaced in research: *"Magluluto dapat si Maria ng manok kahapon"*), and `dapat` has uses where it floats. **Do not** tell Tom "aspect is always illegal after dapat as an absolute law of the language." Tell him the *practical production rule* ("after dapat, keep the verb in base form") and label it as the reliable default, which is exactly how his profile wants explanations delivered (stable, structural, not over-claimed). The data model should tag this error as `aspect.future_overmark_after_modal` so it is scored as a *form* error, not a meaning error.

**Audit of `verb_system.txt`:** its aspect micro-contrasts (*Kukunin ko ito bukas* vs *Kunin ko na lang ba ito bukas?*; *Umalis siya* vs *Aalis siya*) are **[VERIFIED]** correct and well-chosen. The file wisely teaches aspect "only through practical scene contrasts." Keep.

## 3. Potential / abilitative (`maka-`, `ma-`) and the `makarating` family

**[VERIFIED]** `maka-`/`ma-` mark ability/possibility/involuntary action ("manage to", "be able to"). *makarating* = "manage to arrive/reach"; *natawagan* = "managed to call (and reached)". The contrast *darating* (will arrive) vs *makakarating* (will be able to arrive) in `progress.txt` ("makarating / makakarating / darating") is a real and useful one. **[VERIFIED]** correct.

**[NATURALNESS]** This family is genuinely hard because it overlaps semantically with plain actor verbs; treat as a confusable cluster for interleaving, not a one-shot lesson.

## 4. Clitic / pronoun placement

**[VERIFIED]** Tagalog has **second-position (Wackernagel) enclitics**: pronouns (*ako, ka, ko, mo, siya, niya…*) and particles (*na, pa, lang, ba, daw, po…*) cluster right after the **first** full constituent of the clause. After a one-word predicate or modal, they pile up there, with a fixed internal order among them (monosyllabic particles before pronouns in many cases; *po* early; *ba* after the cluster's start, etc.).

**[VERIFIED]** The **linker** surfaces as *-ng/na* binding the cluster: *dapat* + *ako* → **`dapat akong`** + verb. *Gusto* + *ko* → **`gusto kong`** + verb.

**[TEACHING-RULE]** Tom's logged weak point "pronoun/clitic placement after hindi / dapat" is the highest-value structural target in his current state (HIGH priority, appears 3×). Teach it as **fixed frames** ("after *dapat*, the *ako/ko* comes next and links with -ng") rather than as the full second-position theory. The full theory is **[VERIFIED]** but paradigm-heavy and would violate his "no paradigm dumps" preference.

**Audit of `core_patterns.txt` §3–4 (ako-track/ko-track, na lang):** frames are **[VERIFIED]** well-formed and natural. Keep as canonical production frames.

## 5. `bigyan` vs `ibigay`, and the locative/benefactive `-an`

**[VERIFIED]** *bigyan* (locative/benefactive trigger: *bigyan + person + ng thing*) vs *ibigay* (instrumental/theme trigger: *ibigay + ang thing + sa person*). The rule stated in `verb_system.txt` and `core_patterns.txt` §9 is **[VERIFIED]** accurate and is one of the cleaner explanations in the materials. Keep verbatim.

## 6. Register and `po`

**[VERIFIED]** *po/opo* (and *ho/oho*, softer) are politeness markers, second-position clitics, used to signal respect to elders, strangers, customers/vendors, in-laws, service contexts. Omitting *po* with elders/strangers reads as rude; over-using it among peers reads as stiff.

**[NATURALNESS]** The system-prompt list of *po*-contexts (drivers, vendors, elders, partner's family, service staff) is accurate and practically scoped. **[VERIFIED/NATURALNESS]** Keep. Register should be a **scored dimension** (did Tom select appropriate register for the scene?), because for his real goal — partner's family in the Philippines — register errors are socially costly even when grammatically fine.

## 7. Taglish

**[NATURALNESS]** Code-switching (Taglish) is the unmarked register of urban/everyday PH speech for many domains (tech, shopping, work): *I-text mo ako*, *Nag-grocery ako*, *Paki-order nito*. These are natural, not "broken." The materials' three-way labeling — **[TAGLISH-NATURAL] / [PURE TAGALOG OPTION] / [AVOID: broken mix]** — is a sound pedagogical stance. **[NATURALNESS]** verdict: keep, and store a `register: taglish` tag so the tutor can *teach toward* natural code-switching rather than penalizing it.

**[UNCERTAIN]** Exactly *which* items are "natural Taglish" vs "lazy mix" is a judgment that varies by speaker and region. Flag such calls as naturalness judgments, never as grammar facts (the project's rule). When in doubt the tutor should say so.

## 8. Learner traps specific to English/German speakers (Tom)

- **[VERIFIED/NATURALNESS]** Over-using actor trigger ("active") where patient trigger is idiomatic — German/English voice habits. → interleave tracks.
- **[TEACHING-RULE]** Future-overmarking after modals (the PoC) — English "should see" + German tense instincts push toward marking the main verb. → the `dapat` + base-form frame.
- **[VERIFIED]** Clitic second-position order — no German/English analog; *ako/ko/na/pa/po* ordering must be drilled as frames.
- **[NATURALNESS]** *ng* vs *sa* vs *ang* marking of objects/locations; *nasa/sa* with transport (*nakasakay sa, not ng* — already in his WATCH list).
- **[NATURALNESS]** German speakers sometimes transfer V2 word order; Tagalog is predicate-initial. Usually self-corrects with frames; low priority.
- **[VERIFIED]** Aspect ≠ tense: there is no clean past/present/future; mapping must go through *completed / ongoing / unstarted*. Teach via scene contrasts (the materials already do this well).

## 9. Corpus-naturalness audit (Glossika lines)

**[NATURALNESS]** The materials are right that some corpus lines are grammatical but stilted/literary for speech (e.g., *"Mainit sa kuwarto na ito"* → natural *"Mainit dito sa kuwarto."*; *"Malamig ang aking kamay"* → spoken *"Malamig ang kamay ko."*). The possessive *aking/iyong* pre-nominal forms are more formal/written; spoken Tagalog prefers post-nominal *ko/mo/niya*. **Design consequence:** every mapped corpus item needs a **naturalness flag** and an optional **spoken_target** rewrite, so stilted lines are used for *recognition/listening* but a natural rephrase is the *production* target. (Specified in `corpus/corpus_mapping_spec.md`.)

---

## Audit summary

- The existing linguistic content is **largely accurate and unusually disciplined** about not over-claiming. The *bigyan/ibigay*, aspect-contrast, and ako/ko-track explanations are correct and should be promoted verbatim into the new `language/` specs.
- The materials' **biggest pedagogical strength** — teaching structure through practical frames and contrasts rather than paradigms — matches both Tom's profile and the learning-science evidence (frames = retrieval scaffolds that fade).
- The **one linguistic-humility risk** to encode mechanically: the `dapat` + base-form rule must be tagged as a *teaching rule / reliable default*, not an absolute law, so the tutor never asserts the strong version. The error taxonomy gets a dedicated `aspect.future_overmark_after_modal` tag for exactly this.
- Internal skill labels should be **linguistically precise** (`voice.actor`, `voice.patient`, `aspect.contemplated`, `clitic.second_position`, `causative.magpa`, `register.po`, `register.taglish`) even where the **teaching surface** stays practical (ako-track/ko-track). This keeps the data model honest and future-proof while protecting Tom from paradigm overload.
