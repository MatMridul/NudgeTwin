"""Shared, non-relational facts: the nudge catalog and marker norms.

Both the twin and the fair baseline consume these identically (I7). Nothing
here encodes a relationship between markers — the relationships live only in
the twin's derived `drives` edges.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import MarkerType


@dataclass(frozen=True)
class Nudge:
    id: str
    lever: MarkerType          # the marker this nudge acts on
    technique: str             # encouragement / goal-setting / reminder / education
    cost: float                # fatigue weight (>0)


# One lever per actionable marker. Deliberately simple and auditable.
NUDGE_CATALOG: tuple[Nudge, ...] = (
    Nudge("nudge_steps", "steps", "goal-setting", cost=1.0),
    Nudge("nudge_mvpa", "mvpa_min", "encouragement", cost=1.0),
    Nudge("nudge_sleep", "sleep_debt", "education", cost=1.0),
    Nudge("nudge_stress", "stress", "education", cost=1.0),
)

# Population norms: a marker below (or, for debts, above) its norm is a deficit.
# "higher_is_better" says which direction counts as healthy.
@dataclass(frozen=True)
class Norm:
    marker: MarkerType
    norm: float
    higher_is_better: bool


NORMS: dict[MarkerType, Norm] = {
    "steps": Norm("steps", 8000.0, higher_is_better=True),
    "mvpa_min": Norm("mvpa_min", 150.0, higher_is_better=True),
    "sleep_debt": Norm("sleep_debt", 0.0, higher_is_better=False),   # hours of debt
    "stress": Norm("stress", 0.3, higher_is_better=False),           # 0..1 index
}


def deficit_magnitude(marker: MarkerType, value: float) -> float:
    """How far below healthy this reading is, as a non-negative number.

    0.0 means at/above the norm (no deficit). Normalised to the norm so
    markers on different scales compare fairly.
    """
    n = NORMS.get(marker)
    if n is None:
        return 0.0
    if n.higher_is_better:
        gap = max(0.0, n.norm - value)
        return gap / n.norm if n.norm else gap
    else:
        gap = max(0.0, value - n.norm)
        # scale debts/stress by a reference span so they're comparable to ratios
        ref = 8.0 if marker == "sleep_debt" else 1.0
        return gap / ref
