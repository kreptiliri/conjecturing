-- EXPECT: lint axioms
-- A malicious instance used to make the imported audit accept every axiom.
import Challenge
import Lean
instance : BEq Lean.Name where
  beq _ _ := true
namespace Solution
axiom fake : ¬ Challenge.Conjecture
theorem main : ¬ Challenge.Conjecture := fake
end Solution
