"""DR-001 discrimination harness (spec §6, invariants I5 + I7).

The proof that the graph is load-bearing. Both deciders are scored on the SAME
GROUND-TRUTH realized improvement — a metric that knows the planted causal
structure (which neither reasoner is allowed to see). The question is only:
does the decision each reasoner made, scored against reality, help the person
more?

  * Shared-driver scenario  -> expect TWIN > BASELINE
      nudging the root (sleep_debt) realizes gains on steps AND mvpa; nudging a
      symptom realizes only that symptom's gain.
  * Independent scenario     -> expect TWIN ~= BASELINE (honest tie / no win)
      no shared cause to exploit, so relational reasoning buys nothing. A twin
      that 'wins' here would be rigged — and that MUST be reported, not tuned.

No post-hoc baseline nerfing: this metric and these expectations are defined
here, before any result is known.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import baseline as baseline_mod
from . import twin as twin_mod
from .catalog import NUDGE_CATALOG, deficit_magnitude
from .cohort import CohortUser, make_cohort
from .model import Decision

LEVER_EFFECT = 0.30  # same lift assumption used by both reasoners

# Planted ground-truth downstream strengths (evaluation-only; this is the
# 'reality' the engines are being judged against, NOT given to them).
GROUND_TRUTH_STRENGTH = {
    ("sleep_debt", "steps"): 0.8,
    ("sleep_debt", "mvpa_min"): 0.7,
}


def _nudge_lever(nudge_id: str):
    for n in NUDGE_CATALOG:
        if n.id == nudge_id:
            return n.lever
    raise KeyError(nudge_id)


def realized_improvement(user: CohortUser, decision: Decision) -> float:
    """Score a decision against planted ground truth.

    Direct gain on the lever, PLUS the real downstream gains the planted
    structure would produce — regardless of whether the reasoner knew about
    them. This is 'reality'; it rewards nudging the true root.

    A lever earns downstream credit only when it is a TRUE planted driver of a
    deficit marker for THIS user (read from ground_truth_drivers, which no
    reasoner sees).
    """
    lever = _nudge_lever(decision.chosen_nudge_id)
    total = deficit_magnitude(lever, user.latest(lever)) * LEVER_EFFECT
    for target, drivers in user.ground_truth_drivers.items():
        if lever in drivers:
            strength = GROUND_TRUTH_STRENGTH.get((lever, target), 0.0)
            down_def = deficit_magnitude(target, user.latest(target))
            total += down_def * LEVER_EFFECT * strength
    return total


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    n: int
    twin_mean: float
    baseline_mean: float
    delta: float
    twin_win_rate: float
    verdict: str


def run_scenario(scenario: str, n: int = 30) -> ScenarioResult:
    cohort = make_cohort(scenario, n=n)
    twin_scores, base_scores, wins = [], [], 0
    for user in cohort:
        t = realized_improvement(user, twin_mod.decide(user))
        b = realized_improvement(user, baseline_mod.decide(user))
        twin_scores.append(t)
        base_scores.append(b)
        if t > b + 1e-9:
            wins += 1
    tm = sum(twin_scores) / n
    bm = sum(base_scores) / n
    delta = tm - bm
    win_rate = wins / n
    if delta > 0.01:
        verdict = "TWIN WINS — graph is load-bearing here"
    elif delta < -0.01:
        verdict = "BASELINE WINS — relational reasoning hurt (report honestly)"
    else:
        verdict = "TIE — graph buys nothing here (expected for independent deficits)"
    return ScenarioResult(scenario, n, round(tm, 4), round(bm, 4), round(delta, 4), round(win_rate, 3), verdict)


def run_dr001(n: int = 30) -> dict[str, ScenarioResult]:
    return {
        "shared": run_scenario("shared", n),
        "independent": run_scenario("independent", n),
    }


def format_report(results: dict[str, ScenarioResult]) -> str:
    lines = [
        "=" * 70,
        "DR-001 DISCRIMINATION HARNESS — is the graph load-bearing?",
        "=" * 70,
        f"{'scenario':<14}{'twin':>10}{'baseline':>12}{'delta':>10}{'twin win%':>12}",
        "-" * 70,
    ]
    for key in ("shared", "independent"):
        r = results[key]
        lines.append(
            f"{r.scenario:<14}{r.twin_mean:>10.4f}{r.baseline_mean:>12.4f}"
            f"{r.delta:>+10.4f}{r.twin_win_rate*100:>11.1f}%"
        )
    lines.append("-" * 70)
    for key in ("shared", "independent"):
        lines.append(f"  {key:<12} {results[key].verdict}")
    lines.append("=" * 70)
    shared_ok = results["shared"].delta > 0.01
    indep_ok = abs(results["independent"].delta) <= 0.01
    if shared_ok and indep_ok:
        lines.append("ASYMMETRY HOLDS: twin wins on shared-driver, ties on independent.")
        lines.append("=> The graph earns its complexity (DR-001 satisfied).")
    else:
        lines.append("ASYMMETRY DID NOT HOLD — reporting honestly, not tuning away:")
        if not shared_ok:
            lines.append("  - twin failed to win on the shared-driver case.")
        if not indep_ok:
            lines.append("  - twin won on the independent case (possible rigging — investigate).")
    return "\n".join(lines)


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")  # Windows UTF-8
    print(format_report(run_dr001()))
