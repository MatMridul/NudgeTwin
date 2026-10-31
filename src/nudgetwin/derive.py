"""Deterministic derivation of `drives` edges from a user's own history.

This is the engine's answer to 'where does the wiring come from?' (MOAT.md
three-layer model): NOT a learned model and NOT proven causation — a
deterministic, inspectable rule over the user's OWN time series:

    source --drives--> target  iff  changes in `source` are followed, at a
    positive lag, by opposite-direction changes in `target`, strongly enough
    to clear a threshold.

Positive lag (source moves first) is what lets us assert a DIRECTION honestly:
causes precede effects. We still label the result 'derived-correlation', never
'causation' — the honesty line from the moat doc.
"""

from __future__ import annotations

import numpy as np

from .model import DrivesEdge, MarkerType

# Candidate driver relationships we are willing to test for. Keeping this an
# explicit allow-list (not 'try every pair') is itself an auditable choice:
# we test hypotheses grounded in behavioral science, not fish for spurious ones.
CANDIDATE_LINKS: tuple[tuple[MarkerType, MarkerType], ...] = (
    ("sleep_debt", "steps"),
    ("sleep_debt", "mvpa_min"),
    ("sleep_debt", "stress"),
    ("stress", "mvpa_min"),
)

MAX_LAG = 4
STRENGTH_THRESHOLD = 0.45  # |correlation| below this is treated as no edge


def _best_lagged_corr(src: np.ndarray, tgt: np.ndarray) -> tuple[float, int]:
    """Strongest correlation of src(t) with tgt(t+lag) over lags 1..MAX_LAG.

    Returns (signed_corr, lag). Only positive lags are considered, so the
    source must move FIRST — the directional-evidence rule.
    """
    best_abs = 0.0
    best = (0.0, 1)
    ds = np.diff(src)  # work on changes, not levels, to avoid trend artefacts
    dt = np.diff(tgt)
    for lag in range(1, MAX_LAG + 1):
        a = ds[:-lag]
        b = dt[lag:]
        if len(a) < 5 or a.std() == 0 or b.std() == 0:
            continue
        c = float(np.corrcoef(a, b)[0, 1])
        if abs(c) > best_abs:
            best_abs = abs(c)
            best = (c, lag)
    return best


def derive_drives_edges(series: dict[MarkerType, np.ndarray]) -> list[DrivesEdge]:
    """Re-derive latent drives edges from the emitted series. Deterministic."""
    edges: list[DrivesEdge] = []
    for src, tgt in CANDIDATE_LINKS:
        if src not in series or tgt not in series:
            continue
        corr, lag = _best_lagged_corr(series[src], series[tgt])
        if abs(corr) >= STRENGTH_THRESHOLD:
            # strength = |corr|, clamped to (0,1); provenance is honest.
            edges.append(
                DrivesEdge(
                    source=src,
                    target=tgt,
                    strength=round(min(0.99, abs(corr)), 3),
                    lag_days=lag,
                    provenance="derived-correlation",
                )
            )
    return edges
