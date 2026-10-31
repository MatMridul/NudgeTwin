# NudgeTwin

A deterministic digital-twin layer for personalized health nudging — the auditable,
counterfactual, provably-safe complement to a learned nudge ranker.

## Thesis

NudgeRank (CueZen, KDD '24) proved that personalized health nudges work at scale with a
learned graph neural network. But by its own account the ranker is a **black box** (no
auditable "why this nudge for this user"), it only **scores fit** rather than projecting
behavior change, and its safety rails are **pipeline filters** rather than provable
guarantees.

NudgeTwin fills exactly that gap, without competing with the learned ranker:

- **Auditable reasoning** — every recommendation carries a traceable evidence path a
  program manager or compliance reviewer can read.
- **Counterfactual simulation** — a deterministic digital twin of a user's health-behavior
  graph projects how a candidate nudge would change behavior *before* it is sent, and ranks
  by projected benefit rather than fit alone.
- **Provable safety rails** — fatigue/annoyance constraints are enforced as structural caps
  (column / dispatch-table / state-transition guard), not as filters that "usually" run,
  each pinned to a named test.

## Relationship to ATLAS

NudgeTwin is an **instantiation of the ATLAS class** (deterministic-reasoning-first,
relationships as first-class objects, decision-record governance), applied to the digital-
health-nudging domain. Per ATLAS's own rule, instantiations live in their own repo — this
one — not inside the class repo.

The load-bearing discipline (ATLAS DR-001): the relational twin must **beat a fair
non-relational baseline that saw the same raw data** on the hardest relational case (a
shared upstream behavioral driver), and must **not** win when deficits are genuinely
independent. That asymmetry is the proof the graph earns its place.

## Status

- **Spec:** complete — see `docs/`.
- **Deterministic core:** BUILT & PROVEN. The twin, the fair baseline, and the
  DR-001 discrimination harness run green: the twin wins on the shared-driver
  scenario (delta +0.075, 90% per-user win rate) and correctly ties on the
  independent-deficit control (delta 0.000). Invariants I1/I2/I5/I6/I7 are
  enforced in code and covered by `tests/test_core.py` (6 tests green).
- **Backend (FastAPI):** BUILT & TESTED. A thin port over the core (no business
  logic in route handlers) exposing `/cohort`, `/user/{id}/twin`,
  `/user/{id}/decide`, `/eval/dr001`, `/health`. Serializers preserve every
  honesty badge (claim types, edge provenance, projected-not-realized). Covered
  by `tests/test_api.py` (6 in-process TestClient tests). Total suite: 12 green.
- **Demo frontend:** pending (build-order step 8).

Run the backend (loopback only):

```
set PYTHONPATH=src        # PowerShell: $env:PYTHONPATH="src"
uvicorn nudgetwin.api:app --host 127.0.0.1 --port 8000
# then open http://127.0.0.1:8000/docs
```

Run the proof:

```
cd NudgeTwin
set PYTHONPATH=src        # PowerShell: $env:PYTHONPATH="src"
python -m nudgetwin.dr001
python -m pytest tests/test_core.py -q
```

## Layout

```
docs/                       Frozen spec & governance
  VISION.md                 Thesis, falsifiable core claim, definition of done
  design/
    IMPLEMENTATION_SPEC.md   Frozen engineering contract (invariant -> enforcement matrix)
  decisions/
    DR-001-deterministic-core.md   Deterministic twin vs learned ranker (Proposed)
src/nudgetwin/              Deterministic engine (to be built)
tests/                      Test suite (to be built)
```
