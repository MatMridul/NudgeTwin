"""Thin FastAPI port over the deterministic core (spec §7).

Design rule (ATLAS core/adapter split): NO business logic in route handlers.
Each route is a thin call into the pure engine (twin / baseline / dr001) plus a
serializer. The core remains the single source of truth and stays testable
without the web layer.

Run locally (bind loopback only):
    set PYTHONPATH=src
    uvicorn nudgetwin.api:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException

from . import baseline as baseline_mod
from . import twin as twin_mod
from .cohort import CohortUser, make_cohort
from .dr001 import format_report, run_dr001
from .serializers import decision_to_dict, twin_to_dict

app = FastAPI(
    title="NudgeTwin",
    version="0.1.0",
    description="Deterministic digital-twin layer — auditable, counterfactual, provably-railed "
    "complement to a learned health-nudge ranker.",
)


@lru_cache(maxsize=1)
def _cohort_index() -> dict[str, CohortUser]:
    """Build both scenarios once; index by user id. Deterministic, so cacheable."""
    users: dict[str, CohortUser] = {}
    for scenario in ("shared", "independent"):
        for u in make_cohort(scenario, n=30):
            users[u.user_id] = u
    return users


def _get_user(user_id: str) -> CohortUser:
    user = _cohort_index().get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"unknown user {user_id!r}")
    return user


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nudgetwin"}


@app.get("/cohort")
def cohort() -> dict[str, object]:
    users = _cohort_index()
    return {
        "count": len(users),
        "users": [
            {"user_id": u.user_id, "scenario": u.scenario}
            for u in users.values()
        ],
        "note": "synthetic cohort — shaped like a wearable sync, labeled synthetic",
    }


@app.get("/user/{user_id}/twin")
def user_twin(user_id: str) -> dict[str, object]:
    return twin_to_dict(_get_user(user_id))


@app.post("/user/{user_id}/decide")
def user_decide(user_id: str) -> dict[str, object]:
    user = _get_user(user_id)
    return {
        "twin": decision_to_dict(twin_mod.decide(user)),
        "baseline": decision_to_dict(baseline_mod.decide(user)),
        "note": "twin reasons over the drives graph; baseline sees the same raw data, no graph",
    }


@app.get("/eval/dr001")
def eval_dr001() -> dict[str, object]:
    results = run_dr001(n=30)
    return {
        "scenarios": {
            k: {
                "scenario": r.scenario,
                "n": r.n,
                "twin_mean": r.twin_mean,
                "baseline_mean": r.baseline_mean,
                "delta": r.delta,
                "twin_win_rate": r.twin_win_rate,
                "verdict": r.verdict,
            }
            for k, r in results.items()
        },
        "report_text": format_report(results),
    }
