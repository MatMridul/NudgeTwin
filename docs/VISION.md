# NUDGE-TWIN — Vision

> A deterministic **digital twin** of a person's health-behavior graph that
> *simulates* candidate nudges counterfactually, ranks them by projected benefit,
> and **explains every decision with an auditable evidence path** — proving the
> relationship graph earns its place against a fair non-relational baseline.

---

## 1. Why this exists

NudgeRank (CueZen, KDD '24) proves at 1.1M-user scale that personalized health
nudges measurably raise physical activity. It is a landmark *deployment* result.
It also, in its own words, leaves two things open:

1. **The ranking is a black box.** A nudge is chosen by a dot-product of learned
   GNN embeddings. There is no auditable "*why this nudge, for this user, now*"
   that a program manager or a health-provider compliance reviewer can inspect.
   The paper flags *richer, more semantic graph reasoning* as future work.
2. **The lift is modest and uneven** (Precision@3 ≈ 0.05; the effect is weakest
   for already-active users). A learned ranker cannot answer *counterfactual*
   questions — "what would happen if we nudged the root cause instead of the
   symptom?" — which is exactly where uneven cohorts are lost.

NUDGE-TWIN is **not a NudgeRank clone.** It is the complementary layer the paper
says it lacks: a transparent, rule-grounded, *simulatable* reasoning engine. It
competes with nothing CueZen has deployed; it fills a gap they named.

## 2. What it is (one layer up)

NUDGE-TWIN is an **instantiation of the ATLAS class** for the digital-health
behavior-change domain. It inherits ATLAS's contract verbatim: relationships are
first-class computational objects; evidence precedes narrative; fact is separated
from inference; deterministic structure is preferred; action is bounded; and —
the load-bearing rule — **the graph must earn its complexity** (ATLAS DR-001):
a fair non-relational baseline receiving the *same raw observations* must be
*beaten* on the domain's hardest relational case, or the null result reported
honestly.

This is the differentiator. Any applicant can build "a graph." Few can show a
controlled experiment proving the graph produces decision value that treating
each health metric independently cannot.

## 3. The core claim (falsifiable)

> **When two or more observable health behaviors share a hidden upstream driver,
> a relational digital twin that models that driver selects a better nudge — one
> that improves more of the person's state per nudge sent — than a fair
> per-metric baseline that sees the same raw signals but not the relationships.**

The domain's hardest relational case (the ATLAS DR-001 scenario for health):
a shared upstream behavioral driver — e.g. **sleep debt / stress** sitting
upstream of *both* step count *and* active-minutes (MVPA). A per-metric nudge
picker treats low steps and low MVPA as two independent deficits and may
double-nudge or push the wrong lever; the relational twin sees the shared root
and nudges once, at the cause. Under NudgeRank's own real constraint — a **1
nudge/day budget** — picking the right single lever is the entire game.

## 4. Who it's for

- **Program managers** at a health provider: "show me why this person got this
  nudge, and what you expect it to change." NUDGE-TWIN answers with an evidence
  path, a projected outcome, and a confidence — not a score.
- **Compliance / audit** at the health provider: every nudge decision is bounded,
  attributable, and reversible-by-design (ATLAS §2.7), which maps 1:1 onto
  NudgeRank's own Constraints Filter (fatigue budget, annoyance control) — but
  made *provable* rather than procedural.

## 5. Explicit non-goals (scope discipline)

- **No learned GNN, no training on real data.** Deliberate: it invites the
  comparison we lose, and it is not where the open problem is. The twin is
  deterministic; the *evaluation* is where rigor lives.
- **No real PII / no real HPB data.** Synthetic cohort with *planted, documented*
  relational structure so the discrimination test is real, not rigged.
- **Not a production service.** A working backend engine + honest evaluation +
  one strong demo surface — finished and real, not broad and half-built.

## 6. Definition of done

1. A working deterministic engine that ingests a user's markers, builds the
   behavior graph, runs counterfactual nudge simulation, and returns a ranked
   decision **with an evidence path, projected outcome, confidence, and the
   bounded-action record**.
2. A **DR-001 discrimination harness** that runs the shared-driver scenario and a
   control scenario against a fair non-relational baseline, and reports the
   decision-value delta honestly (including if it's null).
3. A **demo-grade frontend** showing: the user's twin graph, a worked nudge
   decision with its evidence path, and the twin-vs-baseline discrimination
   result — the artifact handed to the CueZen VP.
4. Decision records for the material design choices, ATLAS two-pass governance.
