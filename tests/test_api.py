"""In-process API smoke test (no server process, no uvicorn).

Uses FastAPI's TestClient to hit every route and assert the honesty badges and
the DR-001 result survive the web boundary. Skipped automatically if FastAPI
is not installed, so the core test suite never depends on the web layer.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from nudgetwin.api import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_cohort_lists_both_scenarios():
    r = client.get("/cohort")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 60  # 30 shared + 30 independent
    scenarios = {u["scenario"] for u in body["users"]}
    assert scenarios == {"shared", "independent"}


def test_twin_keeps_provenance_badge():
    r = client.get("/user/S000/twin")
    assert r.status_code == 200
    edges = r.json()["edges"]
    assert edges, "expected derived drives edges for a shared-driver user"
    assert all(e["provenance"] == "derived-correlation" for e in edges)


def test_decide_returns_both_with_evidence():
    r = client.post("/user/S000/decide")
    assert r.status_code == 200
    body = r.json()
    assert body["twin"]["evidence"] and body["baseline"]["evidence"]
    assert body["twin"]["claim_type"] == "decision"
    assert body["twin"]["chosen_nudge_id"] == "nudge_sleep"  # traces to the root


def test_unknown_user_404():
    assert client.post("/user/NOPE/decide").status_code == 404


def test_dr001_asymmetry_over_api():
    r = client.get("/eval/dr001")
    assert r.status_code == 200
    s = r.json()["scenarios"]
    assert s["shared"]["delta"] > 0.01
    assert abs(s["independent"]["delta"]) <= 0.01
