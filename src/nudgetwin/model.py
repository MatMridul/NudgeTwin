"""Typed domain model for NudgeTwin.

Enforces the load-bearing invariants from the frozen spec's matrix:
  I1  a Decision cannot exist without an evidence path
  I2  every reasoning value is tagged observed/derived/prediction/decision
  I6  every emitted action carries a complete, attributable ActionRecord

The enforcement lives in the constructors (raise on violation), not in prose —
per the ATLAS mantra: make the boundary a cap/guard, not a sentence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# I2: the four claim types. Nothing in the engine carries an untyped value.
# ---------------------------------------------------------------------------
ClaimType = Literal["observed", "derived", "prediction", "decision"]
_VALID_CLAIM_TYPES = frozenset({"observed", "derived", "prediction", "decision"})

MarkerType = Literal[
    "steps", "mvpa_min", "sleep_debt", "stress", "resting_hr", "goal_steps"
]

Provenance = Literal["literature-prior", "synthetic-planted", "derived-correlation"]


@dataclass(frozen=True)
class Claim:
    """A single typed value flowing through the engine (I2)."""

    name: str
    value: float
    claim_type: ClaimType

    def __post_init__(self) -> None:
        if self.claim_type not in _VALID_CLAIM_TYPES:
            raise ValueError(f"I2 violation: unknown claim_type {self.claim_type!r}")


@dataclass(frozen=True)
class DrivesEdge:
    """The relational core: one marker drives another.

    This edge is the ONLY thing the twin has and the fair baseline does not (I7).
    Its provenance is always carried, never hidden (honesty ledger).
    """

    source: MarkerType
    target: MarkerType
    strength: float  # 0..1 expected fraction of a source change passed downstream
    lag_days: int
    provenance: Provenance


@dataclass(frozen=True)
class EvidenceStep:
    """One link in the auditable reasoning chain."""

    kind: Literal["observation", "derived_edge", "root_trace", "counterfactual"]
    detail: str
    claim_type: ClaimType

    def __post_init__(self) -> None:
        if self.claim_type not in _VALID_CLAIM_TYPES:
            raise ValueError(f"I2 violation: unknown claim_type {self.claim_type!r}")


@dataclass(frozen=True)
class ActionRecord:
    """I6: every action is bounded, attributable, reversible-by-design.

    No emit path may bypass this; a Decision without one cannot be built.
    """

    scope: str
    max_impact: float
    confidence: float
    decision_id: str
    reversible: bool
    audit_id: str

    def __post_init__(self) -> None:
        missing = [
            f
            for f in ("scope", "decision_id", "audit_id")
            if not getattr(self, f)
        ]
        if missing:
            raise ValueError(f"I6 violation: ActionRecord missing {missing}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("I6 violation: confidence must be in [0, 1]")


@dataclass(frozen=True)
class Decision:
    """A ranked nudge choice with its full audit trail.

    I1: construction RAISES if the evidence path is empty. A decision without a
    traceable 'why' is structurally impossible to emit.
    """

    user_id: str
    chosen_nudge_id: str
    projected_improvement: float  # prediction, badged distinct from realized
    confidence: float
    evidence: list[EvidenceStep]
    action: ActionRecord
    assumptions: list[str] = field(default_factory=list)
    claim_type: ClaimType = "decision"

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("I1 violation: a Decision requires a non-empty evidence path")
        if self.claim_type != "decision":
            raise ValueError("I2 violation: a Decision must carry claim_type='decision'")
