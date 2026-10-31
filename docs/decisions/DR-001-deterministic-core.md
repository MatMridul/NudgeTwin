# DR-001 — NUDGE-TWIN core is a deterministic counterfactual twin, not a learned ranker

> **Layer: NUDGE-TWIN instantiation.** This is an application-level design
> decision, recorded in the ATLAS two-pass DR format (SPEC §2.9). Pass-1 sections
> (Question → Strongest Argument Against) are FROZEN once committed Proposed;
> Challenge/Resolution/Decision are filled only after independent challenge.

- **Status:** Proposed
- **Status history:** Proposed 2026-10-30
- **Date proposed:** 2026-10-30
- **Date resolved:** —
- **Supersedes / Superseded by:** —

## Question

Should NUDGE-TWIN's reasoning core be a **deterministic counterfactual digital
twin** (graph + rule-based response simulation), rather than a learned GNN ranker
of the kind NudgeRank uses?

## Context

NUDGE-TWIN exists to fill the gap NudgeRank's paper names: auditable, counterfactual
reasoning the deployed black-box GNN cannot provide. The build has a hard budget
(~2 days, ~598 Kiro credits) and a specific purpose (a proof artifact for a CueZen
internship conversation). A learned GNN on real data is both out of budget and
strategically wrong — it invites direct comparison with a 1.1M-user production
system NUDGE-TWIN cannot and should not try to beat.

## Evidence

- NudgeRank's own stated future work asks for *richer, more semantic graph
  reasoning* and *counterfactual* "next best action" — a learned dot-product ranker
  does not do this; a deterministic twin with a response model does.
- NudgeRank Precision@3 ≈ 0.05 and uneven cohort lift: the learned ranking is not
  the part worth reproducing; the *reasoning + constraints* layer is where
  interpretable value lives.
- ATLAS DESIGN_PRINCIPLES §5 (prefer deterministic structure), §10 (complexity must
  earn its place), §8 (build for counterfactual thinking) all point at a
  deterministic core.
- A deterministic core is the only way to satisfy I1/I2/I6 (evidence path,
  fact/inference separation, bounded auditable action) *provably* — a learned
  ranker makes those aspirational.

## Options

- **Option 1 — Deterministic counterfactual twin (recommended).** Graph +
  lagged-correlation edge derivation + rule-based response simulation. Fully
  inspectable, credit-cheap, satisfies every invariant by construction, directly
  answers the paper's open counterfactual question.
- **Option 2 — Small learned GNN on synthetic data.** Closer to NudgeRank's method,
  but reproduces the black-box property NUDGE-TWIN is meant to critique, costs
  credits on training/debug loops, and weakens the auditability story.
- **Option 3 — Hybrid (deterministic core + thin LLM explanation port).** Core
  deterministic; LLM only phrases the evidence path in natural language. Deferred as
  an optional stub, not the core.

## Proposed Decision

Adopt **Option 1**, with Option 3's LLM phrasing left as an optional, stubbed,
non-load-bearing port (mirroring NudgeRank's own "LLM as future work"). The core
reasoning — diagnosis, upstream trace, counterfactual projection, ranking — is
deterministic and carries the evidence/confidence/bounded-action guarantees.

## Strongest Argument Against

A deterministic response model is a *designed* simulation, not a learned one —
its counterfactual projections are only as credible as the hand-set `drives`
strengths and lift coefficients. A skeptic (or the VP) could say "you proved your
twin beats a baseline *in a world you yourself defined*." This is real: the
DR-001 discrimination test must therefore lean on the *structure* of the result
(twin wins on shared-driver, does NOT win on the independent control) rather than
the magnitude, and must label all coefficients as assumptions with provenance. If
the twin won on BOTH scenarios it would prove the harness is rigged, not that the
graph is load-bearing — so the control scenario is load-bearing evidence, not
decoration.

---
<!-- Pass 2 below: filled only after independent challenge. Everything ABOVE is FROZEN. -->

## External Challenge

_(pending — to be challenged by an independent model before ratification; ATLAS
rule: never ratified by a single model)_

## Resolution

_(pending)_

## Decision

_(pending)_
