# Statement check: txgraffiti-3

Checked 2026-11-27. `Challenge.lean` was not edited
(sha256 `305902d7187ecb96a7b7d9a3c15758764bd09407eb309f9f66eab4bd77802ebe`).

## Sources opened

- arXiv:2507.17780v1 (Davila, Brimkov, Pepper), HTML and PDF. The arXiv history lists
  only v1 (23 Jul 2025).
- google-deepmind/formal-conjectures: `FormalConjectures/Arxiv/2507.17780/3.lean` and
  `FormalConjecturesForMathlib/Combinatorics/SimpleGraph/{Domination,Matching,Saturation}.lean`,
  at `ea8e3e1` and at `main`. All four files are byte-identical between the two.

## What the source says

Section 2.3, definitions: "The independent domination number of a graph G, denoted i(G),
is the minimum cardinality of a maximal independent set [...] μ*(G), the minimum
cardinality of a maximal matching, meaning a matching that cannot be extended by adding
more edges."

Conjecture 3: "If G is an r-regular graph G with r > 0, then i(G) ≤ μ*(G), and this bound
is sharp." (The doubled "G" is in the source.)

Conventions: Section 2.3 states none. Sections 2.1 and 2.2 say "finite, simple,
undirected graph". There is no global preliminaries section.

Appendix A (Lean listing "translated into Lean 4 by TxGraffiti"):

    theorem conjecture_three (G : SimpleGraph V)
      (h1 : connected G)
      (h2 : max_degree G = min_degree G)
      (h3 : min_degree G ≥ 1)
      (h4 : order G ≥ 1) : independent_domination_number G ≤ min_maximal_matching_number G

So the appendix assumes **connected** (and nonempty); the Section 2.3 statement does not.

## Item by item

| Item | Source | Lean | Result |
|---|---|---|---|
| Objects | finite simple undirected graphs (stated in 2.1, 2.2; implicit in 2.3) | `V : Type`, `[Fintype V]`, `SimpleGraph V` | match |
| `DecidableEq V`, `DecidableRel G.Adj` | none | instance arguments only; classically always available, so no restriction | match |
| Universe | all finite graphs | `V : Type`; every finite graph is isomorphic to one on `Fin n` | match |
| Regularity | r-regular | `∀ v, G.degree v = r` | match |
| r > 0 | r > 0 | `1 ≤ r` with `r : ℕ` | match |
| Connectivity | none in Conjecture 3; present in Appendix A | none | match with 2.3; difference from App. A is immaterial (below) |
| Quantifiers | for every such G (and r) | `∀ V G r, regular → 1 ≤ r → ...` | match |
| Maximal independent set | independent, cannot be extended | `G.IsIndepSet D ∧ IsDominating G D` (Mathlib `IsIndepSet` = pairwise non-adjacent) | match (equivalence proved) |
| `IsDominating` | standard | `∀ v, v ∈ D ∨ ∃ w ∈ D, G.Adj v w` | match |
| i(G) | min cardinality of maximal independent set | `sInf` of cardinalities of such `D` | match (set proved nonempty) |
| Matching | edges of G, pairwise vertex-disjoint | `IsEdgeMatching` on `Finset (Sym2 V)`, all in `edgeSet` (so no loops) | match |
| Maximal matching | cannot be extended by adding edges | no `e ∈ edgeSet`, `e ∉ M`, with `insert e M` a matching | match (equivalent to inclusion-maximality, proved) |
| μ*(G) | min cardinality of maximal matching | `sInf` of cardinalities of maximal matchings | match (set proved nonempty) |
| Conclusion | i(G) ≤ μ*(G), non-strict | `indepDominationNumber G ≤ saturationNumber G` | match |
| "this bound is sharp" | part of the sentence | omitted | deliberate omission, immaterial (below) |

## Edge cases

- Empty vertex type: Lean includes it (regularity is vacuous for any r). Proved
  i = μ* = 0, so the inequality holds and it cannot serve as a counterexample. Appendix A
  excludes it (`order ≥ 1`).
- n ≥ 1 with `1 ≤ r` forces every vertex to have a neighbour; no edgeless graph qualifies.
- r = 0 is excluded in both.
- `sInf ∅ = 0` in `ℕ` is never reached: both sets are nonempty for every finite graph.
- r = 1, 2: the paper calls r = 2 clearly true and says only r ≥ 3 is open. Lean states
  all r ≥ 1, as the source does.

## Connectivity (Appendix A vs. Section 2.3 / Lean)

Not material. i and μ* both add over connected components and each component of an
r-regular graph is r-regular, so a disconnected counterexample has a connected component
that is a counterexample. Checked in Lean in a scratch file: with `ConnectedConjecture`
defined as `Conjecture` plus the hypothesis `G.Connected`,
`ConnectedConjecture ↔ Conjecture` compiles with axioms
`propext, Classical.choice, Quot.sound` only. (`G.Connected` in Mathlib includes
nonemptiness, so this also covers `order ≥ 1`.)

## Sharpness clause

`Challenge.Conjecture` is only the inequality. The clause "this bound is sharp" does not
change the truth value: K_{r,r} has i = μ* = r for every r ≥ 1 (the maximal independent
sets are the two sides; a maximal matching leaving a vertex unmatched on one side leaves
one on the other, and those two are adjacent, so every maximal matching is perfect). So a
proof of the Lean statement plus this example gives the full sentence, and a Lean
counterexample refutes it. Only the r = 3 instance (K_{3,3}) was checked in Lean.

## Comparison with upstream

- Statement: same binders, hypotheses and conclusion as `tx_graffiti_conjecture_3`.
- `IsDominating`, `IsEdgeMatching`, `IsMaximalEdgeMatching`, `indepDominationNumber`,
  `saturationNumber`: same bodies.
- `IsNIndepDominatingSet`: upstream is a structure with fields `isIndep`, `isDominating`,
  `card_eq` and takes `G` through a variable; Challenge is the conjunction of the same three,
  with `G` explicit. Equivalent.
- Upstream's decidability instances, computable companions and unused definitions are not
  copied; they do not affect the statement.

## Compilation and examples

`lake env lean` on a copy of `Challenge.lean` in `~/mathproj` (Lean v4.35.0): exit 0, no
messages. `#print` confirmed that `Conjecture` refers to `Challenge.indepDominationNumber`
and `Challenge.saturationNumber`, and that `IsIndepSet` is Mathlib's pairwise
non-adjacency. Temporary files were removed.

General lemmas proved in scratch files against these definitions (standard axioms):

- `G.IsIndepSet D ∧ IsDominating G D ↔ Maximal G.IsIndepSet D`
- `IsMaximalEdgeMatching G M ↔ Maximal (IsEdgeMatching G) M`
- both `sInf` sets are nonempty for every finite graph

Exact values (upper bound by witness, lower bound by exhaustive check; these use
`native_decide`, so they also trust the Lean compiler). All graphs verified regular.

| Graph | r | i(G) expected / Lean | μ*(G) expected / Lean |
|---|---|---|---|
| K4 | 3 | 1 / 1 | 2 / 2 |
| C5 | 2 | 2 / 2 | 2 / 2 |
| K_{3,3} | 3 | 3 / 3 | 3 / 3 |
| Petersen | 3 | 3 / 3 | 3 / 3 |

Rejections checked by kernel `decide`: in K4, `{01}` and `∅` are not maximal matchings,
`{01, 12}` and `{00}` are not matchings; in C5, `{0}` and `{0,1}` are not independent
dominating sets.

## Remarks (none affects the verdict)

- The checklist note in `problem.md` said no connectivity is assumed "in either". That is
  true of Conjecture 3 itself but not of the paper's Appendix A; a note was added there.
- The name γ_e(G) for μ*(G) in `problem.md` is not used in Section 2.3. The paper's
  Section 2.4 calls μ* the saturation number and notes μ*(G) = i(L(G)).

VERDICT: match
