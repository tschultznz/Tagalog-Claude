"""FSRS-lite v0.1 -- transparent, no-API scheduler prototype.

Planning-round PROTOTYPE. Its only job is to validate the design math in
srs/scheduling_spec.md (esp. the partial-credit proof-of-concept). It is NOT the
full system. Pure stdlib, deterministic, ~150 lines, auditable by hand.

Every constant matches srs/scheduling_spec.md section 11. Changing any constant
means bumping SCHEDULER_VERSION.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta

SCHEDULER_VERSION = "fsrs-lite-0.1"

# --- constants (scheduling_spec section 11) ---
TARGET_R = 0.90
DECAY = -0.5
FACTOR = 19 / 81          # so that R(S) == 0.90 exactly
SC = 2.0
LAPSE_MULT = 0.3
S_MIN = 0.5
D_INIT = 5.0
LEECH_LAPSES = 4
STABLE_S = 21.0

W_GRADE = {"hard": 0.5, "good": 1.0, "easy": 1.5}
W_HINT = {"none": 1.0, "intent_only": 0.9, "slot_hint": 0.6,
          "root_family": 0.5, "contrast_label": 0.5, "scaffold_full": 0.2}
W_MODALITY = {"production": 1.0, "listening": 0.5, "recognition": 0.3}
S_INIT = {"again": 0.5, "hard": 1.0, "good": 2.5, "easy": 5.0}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def retrievability(S: float, t_days: float) -> float:
    """Power-law forgetting curve (FSRS-6 form). R(S) == 0.90."""
    if S <= 0:
        return 0.0
    return (1 + FACTOR * t_days / S) ** DECAY


def interval(S: float, r: float = TARGET_R) -> float:
    """Days until retrievability decays to r. At r=0.90, interval == S."""
    return (S / FACTOR) * (r ** (1 / DECAY) - 1)


@dataclass
class SrsState:
    stability: float
    difficulty: float = D_INIT
    last_review: date | None = None
    due: date | None = None
    reps: int = 0
    lapses: int = 0
    last_retrievability: float | None = None
    status: str = "active"
    scheduler_version: str = SCHEDULER_VERSION

    def review(self, grade: str, today: date, hint: str = "none",
               modality: str = "production") -> "SrsState":
        """Return a NEW state after a review. grade in {again,hard,good,easy}."""
        t = (today - self.last_review).days if self.last_review else 0
        R = retrievability(self.stability, t) if self.last_review else 1.0
        S, D = self.stability, self.difficulty

        if grade == "again":                       # failure / lapse path
            S_new = max(S_MIN, S * LAPSE_MULT)
            D_new = clamp(D + 0.8 + 0.05 * (5 - D), 1, 10)
            lapses = self.lapses + 1
            status = "leech" if lapses >= LEECH_LAPSES else "lapsed"
        else:                                       # success path
            hardness = (11 - D) / 10                # easy items grow more
            spacing = clamp(1 - R, 0.05, 1.0)       # desirable difficulty
            delta = (SC * hardness * spacing
                     * W_GRADE[grade] * W_HINT[hint] * W_MODALITY[modality])
            S_new = S * (1 + delta)
            dd = {"hard": 0.0, "good": -0.5, "easy": -1.0}[grade]
            D_new = clamp(D + dd + 0.05 * (5 - (D + dd)), 1, 10)
            lapses = self.lapses
            status = "stable" if S_new >= STABLE_S else "active"

        due = today + timedelta(days=max(1, round(interval(S_new))))
        return SrsState(
            stability=round(S_new, 4), difficulty=round(D_new, 4),
            last_review=today, due=due, reps=self.reps + 1, lapses=lapses,
            last_retrievability=round(R, 4), status=status,
            scheduler_version=SCHEDULER_VERSION,
        )


# grade mapping from the evaluator's per-skill credit_outcome (evaluation_rubric section 4)
def outcome_to_grade(outcome: str, hint: str = "none") -> str:
    return {"pass": "good", "pass_hinted": "hard", "fail": "again"}[outcome]


if __name__ == "__main__":
    # smoke check: at t==S, R==0.90; interval(S)==S at target 0.90
    assert abs(retrievability(10, 10) - 0.90) < 1e-9
    assert abs(interval(10) - 10) < 1e-9
    print("scheduler self-check OK:", SCHEDULER_VERSION)
