# DR-002 — Drop networkx; hand-roll graph traversal

**Status:** Accepted (implementation-forced)
**Date:** 2026-11-01

## Context

The frozen IMPLEMENTATION_SPEC §8 named `networkx` for graph traversal. The gate
rule allows a post-gate change only when implementation *forces* it, recorded as
a decision record rather than a silent edit. This is that record.

## What forced it

`networkx` is not installed in the build environment, and the host was under
memory pressure during the build window — installing a dependency was both
unnecessary risk and avoidable. The NudgeTwin graph is tiny (a handful of marker
nodes, an explicit allow-list of candidate `drives` edges), so a full graph
library is complexity that does not earn its place (ATLAS §10).

## Decision

Represent the graph as plain Python: a list of `DrivesEdge` dataclasses, with
upstream/downstream traversal as simple list comprehensions over edges
(`twin._downstream`). No third-party graph dependency.

## Strongest argument against

If the domain later needs multi-hop paths, cycles, or large graphs, a hand-rolled
structure will not scale and networkx (or a graph DB) becomes justified. Revisit
then — this decision is scoped to the current single-hop, few-node reasoning.

## Consequence

Spec §8 tech list is amended: `networkx` removed. `numpy` (lagged-correlation
derivation + response simulation) and the stdlib carry the engine. No other spec
row changes.
