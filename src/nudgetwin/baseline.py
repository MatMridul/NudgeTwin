"""The fair non-relational baseline (spec §4, I7).

Sees the SAME raw readings and the SAME nudge catalog as the twin. The ONLY
thing it lacks is the drives graph — so it treats every deficit as independent
and nudges the single biggest gap. This is the strongest reasonable
non-relational picker, not a strawman (the honesty requirement from MOAT.md §4).

Its 'improvement' is scored on the SAME metric as the twin, but WITHOUT
downstream propagation — because it has no edges to propagate along. That
asymmetry is the whole point: identical data, minus the relationships.
"""

from __future__ import annotations

import uuid

from .catalog import NUDGE_CATALOG, deficit_magnitude
from .cohort import CohortUser
from .model import ActionRecord, Decision, EvidenceStep

LEVER_EFFECT = 0.30  # same assumption as the twin, applied without propagation
_ASSUMPTION = (
    f"A nudge closes ~{LEVER_EFFECT:.0%} of its lever marker's deficit "
    "(assumption). Baseline models no downstream effects — it has no graph."
)


def decide(user: CohortUser) -> Decision:
    evidence: list[EvidenceStep] = []
    # score each candidate nudge by its DIRECT effect on its lever only
    best = None
    for nudge in NUDGE_CATALOG:
        direct = deficit_magnitude(nudge.lever, user.latest(nudge.lever)) * LEVER_EFFECT
        score = direct / nudge.cost
        evidence_note = f"{nudge.lever} deficit-reduction {direct:.3f} (no relational reasoning)"
        if best is None or score > best[0]:
            best = (score, nudge, evidence_note)
    assert best is not None
    score, chosen, note = best

    evidence.append(EvidenceStep("observation", note, "observed"))
    evidence.append(
        EvidenceStep(
            "counterfactual",
            f"nudging {chosen.lever} (biggest single-metric gap, direct effect only)",
            "prediction",
        )
    )

    decision_id = uuid.uuid4().hex[:12]
    action = ActionRecord(
        scope=f"user:{user.user_id}",
        max_impact=round(score, 3),
        confidence=0.5,
        decision_id=decision_id,
        reversible=True,
        audit_id=uuid.uuid4().hex[:12],
    )
    return Decision(
        user_id=user.user_id,
        chosen_nudge_id=chosen.id,
        projected_improvement=round(score, 4),
        confidence=0.5,
        evidence=evidence,
        action=action,
        assumptions=[_ASSUMPTION],
    )
