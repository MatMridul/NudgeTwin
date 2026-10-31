"""Acceptance tests for the NudgeTwin deterministic core.

Covers the load-bearing matrix rows reachable without the API/UI:
  I1  Decision requires a non-empty evidence path
  I2  claim_type is enforced
  I6  ActionRecord is complete
  I5  the graph is load-bearing (twin wins on shared-driver)
  I7  baseline sees the same raw inputs; twin ties on independent deficits
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nudgetwin import baseline, twin  # noqa: E402
from nudgetwin.cohort import make_cohort  # noqa: E402
from nudgetwin.dr001 import run_dr001  # noqa: E402
from nudgetwin.model import (  # noqa: E402
    ActionRecord,
    Decision,
    EvidenceStep,
)


# --- I1 ---------------------------------------------------------------------
def test_decision_requires_evidence():
    action = ActionRecord("user:x", 1.0, 0.5, "d1", True, "a1")
    with pytest.raises(ValueError, match="I1"):
        Decision("x", "nudge_sleep", 0.1, 0.5, evidence=[], action=action)


# --- I2 ---------------------------------------------------------------------
def test_claim_type_enforced():
    with pytest.raises(ValueError, match="I2"):
        EvidenceStep("observation", "bad", "not_a_claim_type")  # type: ignore[arg-type]


# --- I6 ---------------------------------------------------------------------
def test_action_record_complete():
    with pytest.raises(ValueError, match="I6"):
        ActionRecord("", 1.0, 0.5, "d1", True, "a1")  # empty scope
    with pytest.raises(ValueError, match="I6"):
        ActionRecord("user:x", 1.0, 1.5, "d1", True, "a1")  # confidence out of range


# --- I7: both reasoners consume the same raw user, differ only in the graph --
def test_baseline_and_twin_see_same_user():
    user = make_cohort("shared", n=1)[0]
    td = twin.decide(user)
    bd = baseline.decide(user)
    assert td.user_id == bd.user_id == user.user_id
    # both produce a valid, evidence-backed decision
    assert td.evidence and bd.evidence


# --- I5: the load-bearing proof -------------------------------------------
def test_dr001_discrimination():
    results = run_dr001(n=30)
    shared = results["shared"]
    indep = results["independent"]

    # twin wins where there is a shared driver to exploit
    assert shared.delta > 0.01, f"twin failed to win on shared-driver: {shared}"
    assert shared.twin_win_rate >= 0.7, f"win-rate too low: {shared.twin_win_rate}"

    # twin does NOT win where deficits are independent (honest-null requirement)
    assert abs(indep.delta) <= 0.01, f"twin wrongly won on independent case: {indep}"


def test_twin_always_picks_the_root_on_shared():
    """The twin should trace to sleep_debt (the planted root) every time."""
    for user in make_cohort("shared", n=30):
        d = twin.decide(user)
        assert d.chosen_nudge_id == "nudge_sleep", (
            f"{user.user_id}: twin picked {d.chosen_nudge_id}, expected root nudge_sleep"
        )
