# NUDGE-TWIN — Implementation Spec (v1, FROZEN at gate)

> Gate discipline (per Mridul's rule): this spec is frozen once **SPEC GATE
> PASSED** is recorded below. No revision after the gate unless implementation
> *forces* it — and a forced change is recorded as a decision record, not an
> edit. Build the hardest-invariant vertical slice first; wire the demo surface
> last.

Applies the ATLAS class contract. Section references like `ATLAS §2.5` point at
`C:\Mridul\Programs\ATLAS\docs\SPEC.md`.

---

## 0. The invariant → enforcement matrix (the spine)

Every hard guarantee is pinned to a mechanism in code, never to prose intent
(Mridul's central mantra: *make the boundary a column/cap/dispatch-table, not a
sentence*). This table IS the acceptance contract.

| # | Invariant (the guarantee) | Enforcement mechanism (in code) | Test that proves it |
|---|---|---|---|
| I1 | A nudge decision is never emitted without an evidence path | `Decision` dataclass has a non-optional `evidence: list[EvidencePath]`; constructor raises if empty | `test_decision_requires_evidence` |
| I2 | Observed fact, derived fact, prediction, decision are never conflated | every reasoning value carries `claim_type: Literal["observed","derived","prediction","decision"]`; serializer refuses unknown | `test_claim_type_enforced` |
| I3 | The daily nudge budget cannot be exceeded | `budget: int` cap enforced in `ConstraintsFilter.apply()`; returns ≤ budget nudges, always | `test_budget_never_exceeded` (property test over random candidate sets) |
| I4 | A nudge rated "not useful" within the window is never re-sent | dispatch table: `(user, nudge) → last_negative_ts`; filter drops if within `negative_window_days` | `test_negative_filter` |
| I5 | The graph is load-bearing (ATLAS DR-001) | discrimination harness compares twin vs fair baseline on shared-driver case; asserts measurable decision-value delta OR reports null | `test_dr001_discrimination` |
| I6 | Every action is bounded, attributable, reversible-by-design | `ActionRecord` with `scope`, `max_impact`, `confidence`, `decision_id`, `reversible: bool`, `audit_id`; no emit path bypasses it | `test_action_record_complete` |
| I7 | Baseline fairness: baseline sees identical raw observations, lacks only the graph | both consume the SAME `ObservationBundle`; twin derives edges from it, baseline does not; a single shared fixture feeds both | `test_baseline_sees_same_raw_inputs` |

If any row cannot be answered "it's impossible through the architecture, here's
the enforcement point + test," the spec is not done.

## 1. Domain ontology (ATLAS §4.1)

Entities (nodes):
- `User` — pseudonymous id, demographic markers.
- `Marker` — a measurable behavioral/physiological signal with a value + ts:
  `steps`, `mvpa_min`, `sleep_debt`, `stress`, `resting_hr`, `goal_steps`.
- `Nudge` — a candidate template: `id`, `targets: list[MarkerType]`,
  `technique` (encouragement / goal-setting / reminder / education), `lever`
  (which marker it acts on), `cost` (fatigue weight).
- `Segment` — a dynamic cohort a user belongs to (derived, not stored raw).

Typed edges:
- `User —has_marker→ Marker` (temporal, versioned)
- `Marker —drives→ Marker` (the relational core: `sleep_debt drives steps`,
  `stress drives mvpa_min`, `sleep_debt drives stress`) with a `strength` weight
  and a `provenance` tag (literature-prior / synthetic-planted — labeled, never
  hidden).
- `Nudge —acts_on→ Marker` (the lever)
- `User —rated→ Nudge` (`useful` / `not_useful`, timestamped — feedback loop)

The `drives` edges are the *only* thing the twin has and the baseline does not.
Everything else (raw marker values, ratings, nudge catalog) is shared. This is
I7 made structural.

## 2. Observation layer (ATLAS §2.2)

- Input: `ObservationBundle` = a user's marker time series + rating history, from
  a synthetic cohort generator. Each observation retains `source` + `ts`
  provenance (ATLAS §2.2 requires it).
- Synthetic cohort generator (`data/cohort.py`) plants ground-truth `drives`
  relationships with documented strengths, then emits ONLY raw marker values —
  the relationships are *latent*, to be re-derived (twin) or ignored (baseline).
  Ground truth is retained separately for evaluation scoring, never fed to either
  reasoner.

## 3. Temporal state (ATLAS §2.3)

Markers are event-sourced: a new reading appends, never overwrites. Current state
= latest per marker; history is queryable for the `drives`-edge derivation (a
driver is inferred from lagged co-movement over the window, deterministically —
cross-correlation at lag ≥ 1, thresholded; NOT a learned model).

## 4. Reasoning engine (ATLAS §2.5) — pure deterministic

The twin's decision procedure, fully deterministic and inspectable:

1. **Build graph** from the observation bundle: nodes + derived `drives` edges
   (lagged-correlation rule above, with strength + provenance).
2. **Diagnose deficits**: markers below goal/population norm → candidate targets.
3. **Trace to root** (ATLAS §2.4 multi-hop): for each deficit, walk `drives`
   edges *upstream* to find a shared driver explaining multiple deficits. This is
   the step the baseline structurally cannot do.
4. **Counterfactual simulation** (ATLAS §8 / QUERY_MODEL Counterfactual): for each
   candidate nudge, apply a deterministic response model — nudging a marker lifts
   it by a bounded expected amount, and that lift *propagates downstream along
   `drives` edges*. Project the total expected state improvement.
5. **Rank** candidates by projected whole-person improvement per unit fatigue
   cost.
6. **Emit** a `Decision` with: chosen nudge, `claim_type="decision"`, evidence
   path (the subgraph + the readings that triggered it), projected outcome,
   confidence (from edge strengths + data sufficiency), and assumptions.

The **fair baseline** (`baseline.py`): same steps 2 + 5 + 6, but NO graph — it
scores each deficit independently (biggest single-metric gap → nudge that
metric), the strongest reasonable non-relational picker. It gets the same raw
readings and the same nudge catalog.

## 5. Constraints filter (ATLAS §2.7) — maps to NudgeRank's safety rails

Deterministic, after ranking, before emit:
- daily budget cap (I3)
- negative-rating window filter (I4)
- recently-sent diversity filter
- each surviving nudge wrapped in an `ActionRecord` (I6)

## 6. Evaluation (ATLAS §2.8, DR-001) — where the rigor lives

Two scenarios, one fair baseline, honest reporting:
- **Scenario A (shared driver):** cohort where `sleep_debt` drives both `steps`
  and `mvpa_min`. Metric: *decision value* = total projected+realized whole-person
  improvement per nudge, under the 1/day budget. Expectation: twin beats baseline
  because it nudges the root once instead of chasing two symptoms.
- **Scenario B (control / independent deficits):** cohort where low steps and low
  mvpa have *no* shared driver (genuinely independent). Expectation: twin does NOT
  beat baseline here — and that MUST be reported, not tuned away. A twin that
  "wins" even when there's no relational structure is a rigged twin (ATLAS
  honest-null requirement).
- Report: a results table with the delta, significance over N synthetic users,
  and a plain-English verdict. Null/negative is a valid outcome (DR-001).

The eval is defined HERE, before any result is known. No post-hoc baseline
nerfing.

## 7. Interfaces (so the frontend is clean)

Backend exposes a small typed API (FastAPI):
- `GET /cohort` → list synthetic users
- `GET /user/{id}/twin` → the graph (nodes, edges, markers, provenance)
- `POST /user/{id}/decide` → run twin + baseline, return both decisions + evidence
- `GET /eval/dr001` → run the discrimination harness, return the results table

Pure functions underneath; the API is a thin port. No business logic in the route
handlers (keeps the core testable and the boundary clean per ATLAS core/adapter
split).

## 8. Tech choices (minimal — complexity must earn its place, ATLAS §10)

- **Python 3.11**, `dataclasses` for the typed model, `networkx` for graph
  traversal (standard, not a graph DB — the domain doesn't need one yet).
- `numpy` for the lagged-correlation derivation + response simulation.
- `pytest` + `hypothesis` (property tests for I3).
- `FastAPI` + `uvicorn` for the thin API.
- **No LLM, no DB, no vector store, no training.** (ATLAS §10 / §6 anti-patterns.)
- Frontend: Kiro's call — a single strong interactive page (graph + decision +
  DR-001 result). Decided at frontend-design phase, not here.

## 9. Build order (hardest-invariant-first — Mridul's rule)

1. Typed domain model + I1/I2/I6 enforcement + their tests. (deterministic heart)
2. Synthetic cohort generator with planted ground truth.
3. Graph build + upstream trace + counterfactual sim (the twin).
4. Fair baseline.
5. Constraints filter (I3/I4) + property tests.
6. **DR-001 harness (I5/I7) green on A, honest on B.** ← the proof.
7. FastAPI port.
8. Frontend design spec → build → Playwright visual QA → human QA.

Each step ends green before the next starts. The whole-system loop is proven at
step 6 — *before* any UI exists.

## 10. Honesty ledger (carried from Mridul's past builds)

- Synthetic data is labeled synthetic everywhere it surfaces.
- `drives` edge provenance (literature-prior vs planted) is shown, never hidden.
- If the DR-001 delta is null, the demo SAYS SO. A portfolio piece that lies about
  its own evaluation is worse than one that honestly reports a modest result.
- "Projected" outcomes are badged distinct from "realized" (simulated) outcomes.

---

## SPEC GATE

- [ ] Vision reviewed
- [ ] Invariant→enforcement matrix complete and each row has a named test
- [ ] DR for the one material decision (deterministic-vs-learned core) recorded
- [ ] **SPEC GATE PASSED** — (date / signoff) — frozen after this line
