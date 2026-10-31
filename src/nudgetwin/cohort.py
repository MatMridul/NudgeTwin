"""Synthetic cohort generator with planted, documented ground truth.

Per the spec (§2, §6) and the three-layer data model in MOAT.md:

  * STATE  -> the raw daily marker time series we emit (stands in for a
             Google Fit / Apple Health sync; synthetic, labeled synthetic).
  * WIRING -> planted `drives` relationships, expressed ONLY as time-lagged
             co-movement in the emitted series. The relationships themselves are
             LATENT: never handed to either reasoner. The twin must re-derive
             them from the trend; the baseline ignores them.

Ground truth is retained separately (CohortUser.ground_truth_drivers) for
evaluation scoring — never fed to the twin or the baseline.

Two scenarios (DR-001):
  * "shared"       sleep_debt drives BOTH steps and mvpa_min  -> twin should win
  * "independent"  steps and mvpa_min low for unrelated reasons -> twin should tie
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .model import MarkerType

WINDOW_DAYS = 56  # ~8 weeks of history, per the "study the trend" design


@dataclass(frozen=True)
class CohortUser:
    user_id: str
    scenario: str
    # STATE: raw daily series per marker (what a wearable feed would give us)
    series: dict[MarkerType, np.ndarray]
    # GROUND TRUTH (evaluation only — never shown to a reasoner)
    ground_truth_drivers: dict[MarkerType, list[MarkerType]] = field(default_factory=dict)

    def latest(self, marker: MarkerType) -> float:
        return float(self.series[marker][-1])


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _shared_driver_user(uid: str, seed: int) -> CohortUser:
    """sleep_debt is the hidden root; it drags steps and mvpa down with a lag."""
    r = _rng(seed)
    t = WINDOW_DAYS

    # Root cause: MODERATE, fluctuating sleep debt. Deliberately not the biggest
    # visible deficit — the realistic relational case is one where the SYMPTOMS
    # look worst and a per-metric picker is drawn to them, while the true root is
    # only moderately elevated. The twin must trace to the root anyway.
    sleep_debt = np.clip(1.6 + 0.8 * np.sin(np.linspace(0, 6, t)) + r.normal(0, 0.25, t), 0, 8)

    # Downstream markers respond to sleep_debt with a 2-day lag (causes precede
    # effects — the directional signal the twin keys on). The pull is strong, so
    # steps and mvpa are the dominant VISIBLE deficits.
    lag = 2
    debt_lagged = np.concatenate([np.full(lag, sleep_debt[0]), sleep_debt[:-lag]])

    steps = np.clip(8200 - 1900 * debt_lagged + r.normal(0, 250, t), 500, 14000)
    mvpa = np.clip(165 - 42 * debt_lagged + r.normal(0, 8, t), 0, 320)
    stress = np.clip(0.22 + 0.04 * debt_lagged + r.normal(0, 0.03, t), 0, 1)

    return CohortUser(
        user_id=uid,
        scenario="shared",
        series={
            "sleep_debt": sleep_debt,
            "steps": steps,
            "mvpa_min": mvpa,
            "stress": stress,
        },
        ground_truth_drivers={"steps": ["sleep_debt"], "mvpa_min": ["sleep_debt"]},
    )


def _independent_user(uid: str, seed: int) -> CohortUser:
    """Low steps and low mvpa, but NO shared cause — genuinely independent."""
    r = _rng(seed)
    t = WINDOW_DAYS

    # sleep_debt here is LOW and does not drive anything (no relational structure).
    sleep_debt = np.clip(0.4 + r.normal(0, 0.2, t), 0, 8)

    # Two independent low series with their own unrelated wobble.
    steps = np.clip(4200 + 600 * np.sin(np.linspace(0, 5, t)) + r.normal(0, 300, t), 500, 14000)
    mvpa = np.clip(70 + 20 * np.cos(np.linspace(0, 4, t)) + r.normal(0, 10, t), 0, 320)
    stress = np.clip(0.28 + r.normal(0, 0.03, t), 0, 1)

    return CohortUser(
        user_id=uid,
        scenario="independent",
        series={
            "sleep_debt": sleep_debt,
            "steps": steps,
            "mvpa_min": mvpa,
            "stress": stress,
        },
        ground_truth_drivers={},  # no relational structure, by construction
    )


def make_cohort(scenario: str, n: int = 30, base_seed: int = 1000) -> list[CohortUser]:
    """Generate `n` synthetic users for a scenario ('shared' or 'independent')."""
    if scenario == "shared":
        gen = _shared_driver_user
        prefix = "S"
    elif scenario == "independent":
        gen = _independent_user
        prefix = "I"
    else:
        raise ValueError(f"unknown scenario {scenario!r}")
    return [gen(f"{prefix}{i:03d}", base_seed + i) for i in range(n)]
