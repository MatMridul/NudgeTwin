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
- **Build:** pending.

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
