/-
Locked statement for `txgraffiti-3`.

TxGraffiti Conjecture 3 (open since 2020), as stated in
Davila, Brimkov, Pepper, "In Reverie Together: Ten Years of Mathematical Discovery
with a Machine Collaborator", arXiv:2507.17780v1, Section 2.3:

  If G is an r-regular graph with r > 0, then i(G) ≤ μ*(G).

i(G)  = independent domination number (minimum size of a maximal independent set)
μ*(G) = saturation number (minimum size of a maximal matching)

The definitions below are copied from google-deepmind/formal-conjectures
(FormalConjecturesForMathlib/Combinatorics/SimpleGraph/{Domination,Matching,Saturation}.lean,
commit ea8e3e1) and the statement from FormalConjectures/Arxiv/2507.17780/3.lean,
so this file depends on Mathlib only.
-/
import Mathlib

namespace Challenge

open SimpleGraph

variable {α : Type*}

/-- `D` dominates `G`: every vertex is in `D` or adjacent to a vertex of `D`. -/
def IsDominating (G : SimpleGraph α) (D : Set α) : Prop :=
  ∀ v, v ∈ D ∨ ∃ w ∈ D, G.Adj v w

/-- Independent dominating sets of size `n` (equivalently: maximal independent sets). -/
def IsNIndepDominatingSet (G : SimpleGraph α) (n : ℕ) (D : Finset α) : Prop :=
  G.IsIndepSet (D : Set α) ∧ IsDominating G (D : Set α) ∧ D.card = n

/-- i(G): the independent domination number. -/
noncomputable def indepDominationNumber (G : SimpleGraph α) : ℕ :=
  sInf {n | ∃ D : Finset α, IsNIndepDominatingSet G n D}

/-- A matching, as a finite set of edges of `G` that pairwise share no vertex. -/
def IsEdgeMatching (G : SimpleGraph α) (M : Finset (Sym2 α)) : Prop :=
  (∀ e ∈ M, e ∈ G.edgeSet) ∧
    ∀ e₁ ∈ M, ∀ e₂ ∈ M, e₁ = e₂ ∨ ∀ v : α, ¬ (v ∈ e₁ ∧ v ∈ e₂)

/-- A matching to which no further edge of `G` can be added. -/
def IsMaximalEdgeMatching (G : SimpleGraph α) (M : Finset (Sym2 α)) : Prop :=
  IsEdgeMatching G M ∧ ∀ e ∈ G.edgeSet, e ∉ M → ¬ IsEdgeMatching G (insert e M)

/-- μ*(G): the saturation number, the minimum size of a maximal matching. -/
noncomputable def saturationNumber (G : SimpleGraph α) : ℕ :=
  sInf {n | ∃ M : Finset (Sym2 α), IsMaximalEdgeMatching G M ∧ M.card = n}

/-- The conjecture under test. -/
def Conjecture : Prop :=
  ∀ (V : Type) [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj] (r : ℕ),
    (∀ v, G.degree v = r) → 1 ≤ r →
      indepDominationNumber G ≤ saturationNumber G

end Challenge
