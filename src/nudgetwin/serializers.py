"""Serializers: engine dataclasses -> JSON-safe dicts.

Keeps every honesty badge intact: claim_type on each evidence step, provenance
on each drives edge, projected (not realized) on the decision, and the labeled
assumptions. The API must never launder an assumption into a fact.
"""

from __future__ import annotations

from typing import Any

from .cohort import CohortUser
from .derive import derive_drives_edges
from .model import Decision, DrivesEdge


def edge_to_dict(e: DrivesEdge) -> dict[str, Any]:
    return {
        "source": e.source,
        "target": e.target,
        "strength": e.strength,
        "lag_days": e.lag_days,
        "provenance": e.provenance,  # honesty: 'derived-correlation', never 'causation'
    }


def twin_to_dict(user: CohortUser) -> dict[str, Any]:
    edges = derive_drives_edges(user.series)
    markers = sorted(user.series.keys())
    return {
        "user_id": user.user_id,
        "scenario": user.scenario,
        "markers": {m: round(user.latest(m), 2) for m in markers},
        "series_len": len(next(iter(user.series.values()))),
        "edges": [edge_to_dict(e) for e in edges],
        "note": "edges derived from the user's own lagged history — correlation, not causation",
    }


def decision_to_dict(d: Decision) -> dict[str, Any]:
    return {
        "user_id": d.user_id,
        "chosen_nudge_id": d.chosen_nudge_id,
        "projected_improvement": d.projected_improvement,  # projected, NOT realized
        "confidence": d.confidence,
        "claim_type": d.claim_type,
        "evidence": [
            {"kind": s.kind, "detail": s.detail, "claim_type": s.claim_type}
            for s in d.evidence
        ],
        "action": {
            "scope": d.action.scope,
            "max_impact": d.action.max_impact,
            "confidence": d.action.confidence,
            "decision_id": d.action.decision_id,
            "reversible": d.action.reversible,
            "audit_id": d.action.audit_id,
        },
        "assumptions": d.assumptions,
    }
