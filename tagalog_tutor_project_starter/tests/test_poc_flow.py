"""End-to-end PoC: one real learner error updates six skills with PARTIAL credit.

Validates the instruction's required proof-of-concept and the numbers in
srs/scheduling_spec.md. Run:  python3 tests/test_poc_flow.py
Pure stdlib + PyYAML. Deterministic; asserts exact scheduler outputs.
"""
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "srs"))

import yaml  # PyYAML
from scheduler import SrsState, outcome_to_grade, retrievability, interval

TODAY = date(2026, 6, 23)


def load(name):
    with open(os.path.join(HERE, "fixtures", name)) as f:
        return yaml.safe_load(f)


def to_state(p):
    return SrsState(stability=p["stability"], difficulty=p["difficulty"],
                    last_review=p["last_review"], due=p["due"],
                    reps=p["reps"], lapses=p["lapses"])


def approx(a, b, tol=1e-3):
    return abs(a - b) <= tol


def main():
    skills = {s["id"]: s for s in load("skills_state.seed.yaml")["skills"]}
    attempt = load("attempt_poc.yaml")
    cv = attempt["evaluation"]["credit_vector"]
    hint = attempt["hint_level_used"]

    print("=" * 78)
    print("PoC: 'Dapat akong magpatingin.'  ->  Tom said 'Dapat akong magpapatingin.'")
    print("One attempt, hint=%s, modality=production, date=%s" % (hint, TODAY))
    print("=" * 78)
    print("%-30s %5s %16s %16s %s" % ("skill", "out", "S before->after", "due", "R@review"))
    print("-" * 78)

    results = {}
    for entry in cv:
        sid, outcome = entry["skill_id"], entry["outcome"]
        before = to_state(skills[sid]["production"])
        grade = outcome_to_grade(outcome, hint)
        after = before.review(grade, TODAY, hint=hint, modality="production")
        results[sid] = (before, after, outcome)
        arrow = "%6.3f->%6.3f" % (before.stability, after.stability)
        print("%-30s %5s %16s %16s  %.4f"
              % (sid.replace("skill.", ""), outcome, arrow,
                 after.due.isoformat(), after.last_retrievability))

    # ---- assertions: the headline partial-credit behavior ----
    b, a, _ = results["skill.modal.base_form"]
    assert a.stability == 0.9, a.stability                      # 3.0 * 0.3
    assert a.lapses == 3 and a.status == "lapsed"
    assert a.due == date(2026, 6, 24)                           # +1 relearn

    b, a, _ = results["skill.voice.actor"]
    assert approx(a.stability, 9.2376, 1e-3), a.stability       # grows on unaided pass
    assert a.due == date(2026, 7, 2)                            # pushed out ~9 days

    b, a, _ = results["skill.aspect.contemplated"]
    assert a.stability == 0.6 and a.due == date(2026, 6, 24)    # 2.0 * 0.3, relearn

    b, a, _ = results["skill.clitic.second_position"]
    assert approx(a.stability, 5.6, 1e-3) and a.due == date(2026, 6, 29)

    # one answer moved skills in BOTH directions -> partial credit works
    grew = [s for s, (b, a, o) in results.items() if a.stability > b.stability]
    shrank = [s for s, (b, a, o) in results.items() if a.stability < b.stability]
    assert len(grew) == 4 and len(shrank) == 2, (grew, shrank)

    # ---- mastery gate: a FAILED item cannot be 'stable' ----
    assert results["skill.modal.base_form"][1].status != "stable"

    # ---- desirable difficulty: later review (lower R) yields more stability gain ----
    early = SrsState(stability=10, difficulty=5, last_review=date(2026, 6, 21)).review("good", TODAY)  # t=2
    late = SrsState(stability=10, difficulty=5, last_review=date(2026, 6, 3)).review("good", TODAY)    # t=20
    assert late.stability > early.stability, (early.stability, late.stability)

    # ---- hints are priced in: scaffolded pass earns less stability than unaided ----
    base = SrsState(stability=10, difficulty=5, last_review=date(2026, 6, 13))  # t=10
    unaided = base.review("good", TODAY, hint="none")
    scaffold = base.review("good", TODAY, hint="scaffold_full")
    assert unaided.stability > scaffold.stability

    # ---- recognition cannot move production as much as production ----
    prod = base.review("good", TODAY, hint="none", modality="production")
    recog = base.review("good", TODAY, hint="none", modality="recognition")
    assert prod.stability > recog.stability

    # ---- delayed-recall WIN (the honest XP event): voice.actor recalled unaided after 9 days ----
    vb, va, _ = results["skill.voice.actor"]
    delayed_gap = (TODAY - vb.last_review).days
    xp_win = (delayed_gap >= 7 and hint == "none" and va.stability > vb.stability)
    assert xp_win, "expected a delayed-recall XP win on voice.actor"

    print("-" * 78)
    print("spawned contrast item:", attempt["spawned_items"][0],
          "(interleaves modal.base_form vs aspect.contemplated)")
    print("XP: delayed-recall WIN on voice.actor (unaided after %d days)" % delayed_gap)
    print("ALL ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
