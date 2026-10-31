"""The relational twin: deterministic counterfactual nudge selection.

Decision procedure (spec §4):
  1. build graph  -> derived drives edges from the user's own history
  2. diagnose     -> which markers are in deficit
  3. trace-to-root-> walk drives edges upstream to a shared driver (the step the
                     baseline structurally cannot do)
  4. simulate     -> for each candidate nudge, project the whole-person
                     improvement, propagating a lever's lift DOWNSTREAM along
                     drives edges
  5. rank         -> best projected improvement per unit fatigue cost
  6. emit         -> Decision with evidence path, projected outcome, confidence,
                     assumptions (I1/I2/I6 enforced by the dataclasses)
"""

from __future__ import annotations

import uuid

from .catalog import NUDGE_CATALOG, Nudge, deficit_magnitude
from .cohort import CohortUser
from .derive import derive_drives_edges
from .model import ActionRecord, Decision, DrivesEdge, EvidenceStep, MarkerType

# A nudge is assumed to improve the deficit on its lever by this fraction of the
# remaining gap. ASSUMPTION — labeled, lifted into every Decision's assumptions.
LEVER_EFFECT = 0.30
_ASSUMPTION = (
    f"A nudge closes ~{LEVER_EFFECT:.0%} of its lever marker's deficit "
    "(assumption, not measured); downstream lift scales by derived edge strength."
)


def _downstream(edges: list[DrivesEdge], root: MarkerType) -> list[DrivesEdge]:
    return [e for e in edges if e.source == root]


def _whole_person_improvement(
    user: CohortUser,
    lever: MarkerType,
    edges: list[DrivesEdge],
) -> tuple[float, list[MarkerType]]:
    """Project total deficit reduction from nudging `lever`, propagating
    downstream along drives edges. Returns (improvement, markers_helped)."""
    helped: list[MarkerType] = []
    # direct effect on the lever's own deficit
    direct = deficit_magnitude(lever, user.latest(lever)) * LEVER_EFFECT
    total = direct
    if direct > 0:
        helped.append(lever)
    # indirect effect: lifting the lever eases its downstream markers
    for e in _downstream(edges, lever):
        down_def = deficit_magnitude(e.target, user.latest(e.target))
        indirect = down_def * LEVER_EFFECT * e.strength
        if indirect > 0:
            total += indirect
            helped.append(e.target)
    return total, helped


def decide(user: CohortUser) -> Decision:
    edges = derive_drives_edges(user.series)

    evidence: list[EvidenceStep] = []
    # (2) diagnose deficits
    deficits = {
        m: deficit_magnitude(m, user.latest(m))
        for m in ("steps", "mvpa_min", "sleep_debt", "stress")
        if deficit_magnitude(m, user.latest(m)) > 0.0
    }
    for m, d in deficits.items():
        evidence.append(
            EvidenceStep("observation", f"{m} in deficit (magnitude {d:.2f})", "observed")
        )

    # (3) trace to root: report any derived driver explaining >=2 deficits
    for e in edges:
        if e.source in deficits and e.target in deficits:
            evidence.append(
                EvidenceStep(
                    "root_trace",
                    f"{e.source} drives {e.target} (strength {e.strength}, "
                    f"lag {e.lag_days}d) — shared upstream cause",
                    "derived",
                )
            )

    # (4) + (5) counterfactual simulation + ranking over the shared catalog
    best: tuple[float, Nudge, list[MarkerType]] | None = None
    for nudge in NUDGE_CATALOG:
        improvement, helped = _whole_person_improvement(user, nudge.lever, edges)
        score = improvement / nudge.cost
        if best is None or score > best[0]:
            best = (score, nudge, helped)
    assert best is not None
    score, chosen, helped = best

    evidence.append(
        EvidenceStep(
            "counterfactual",
            f"nudging {chosen.lever} projected to help {helped} "
            f"(whole-person improvement {score:.3f}/fatigue)",
            "prediction",
        )
    )

    confidence = min(1.0, 0.4 + 0.15 * len(edges) + 0.1 * len(helped))
    decision_id = uuid.uuid4().hex[:12]
    action = ActionRecord(
        scope=f"user:{user.user_id}",
        max_impact=round(score, 3),
        confidence=round(confidence, 3),
        decision_id=decision_id,
        reversible=True,
        audit_id=uuid.uuid4().hex[:12],
    )
    return Decision(
        user_id=user.user_id,
        chosen_nudge_id=chosen.id,
        projected_improvement=round(score, 4),
        confidence=round(confidence, 3),
        evidence=evidence,
        action=action,
        assumptions=[_ASSUMPTION],
    )
