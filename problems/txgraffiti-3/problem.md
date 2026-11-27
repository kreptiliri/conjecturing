---
slug: txgraffiti-3
title: TxGraffiti Conjecture 3 (independent domination vs. saturation in regular graphs)
source: Davila, Brimkov, Pepper, In Reverie Together: Ten Years of Mathematical Discovery with a Machine Collaborator
source_id: arXiv:2507.17780v1
statement: Conjecture 3
page: Section 2.3
source_url: https://arxiv.org/abs/2507.17780v1
area: graph theory
expected: unknown (try disproof first)
---

# Statement

Conjecture 3 (TxGraffiti, open since 2020). If G is an r-regular graph with r > 0,
then i(G) ≤ μ*(G), and this bound is sharp.

- i(G): independent domination number = minimum size of a maximal independent set.
- μ*(G): saturation number = minimum size of a maximal matching
  (also called the edge domination number γ_e(G)).

Lean: `Challenge.Conjecture` in `Challenge.lean`, copied from
google-deepmind/formal-conjectures `FormalConjectures/Arxiv/2507.17780/3.lean`.

# Statement check (fill in before `harness lock`)

Compare Challenge.lean to the source, hypothesis by hypothesis. Tick each box, or
write what differs.

- [x] Every hypothesis in the source appears in Challenge.lean, none added
      (source: r-regular, r > 0. Lean: `∀ v, G.degree v = r` and `1 ≤ r`.
      No connectivity assumed in either.)
      Note: true of Conjecture 3 in Section 2.3. The paper's Appendix A Lean listing
      does add `connected G` (and `order G ≥ 1`); immaterial, since the connected and
      unrestricted versions are equivalent (see STATEMENT_CHECK.md).
- [x] Domains and objects match: finite simple graphs (Lean: `Fintype V`, `SimpleGraph`)
- [x] i(G) definition matches: Lean takes the min size of a set that is independent
      AND dominating, which is the same as a maximal independent set
- [x] μ*(G) definition matches: Lean takes the min size of a matching that no edge
      can be added to
- [x] Inequality direction and strictness match: i(G) ≤ μ*(G)
- [x] The "sharp" part is NOT in Lean (fine: refuting the inequality refutes the conjecture)

# Notes for agents

- Formal statement: `Challenge.lean`. Do not edit it.
- Both i and μ* add up over connected components, so if any counterexample exists,
  a connected one does. Search connected graphs only.
- μ*(G) = i(L(G)), the independent domination number of the line graph. So the
  conjecture says i(G) ≤ i(L(G)) for regular G.
- Evidence so far: the authors validated it on "hundreds of graphs". A sibling,
  TxGraffiti Conjecture 2, was refuted in July 2026 (arXiv:2607.23664) with a
  24-vertex subcubic graph built from gadgets: try gadget constructions too.
- Related: Baste et al. conjecture γ(G) ≤ γ_e(G) for regular graphs (weaker, since
  γ ≤ i); arXiv:2608.22498 handles degree ≥ 7. Check what it implies here.
- Suggested search: nauty `geng -c -d<r> -D<r> <n>` for all connected r-regular graphs,
  exact i and μ* via ILP or SAT; then random regular graphs and gadget constructions
  at larger n. Log the ranges searched exhaustively in NOTES.md.
- A counterexample in Lean is one explicit graph on `Fin n`: prove the regularity,
  exhibit a small maximal matching M (bounds μ* above), and show every independent
  dominating set is larger than |M|. The last part is the hard part for `decide`
  at n > ~20; consider a certificate-style proof.
