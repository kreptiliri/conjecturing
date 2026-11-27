-- EXPECT: lint axioms
-- REJECTED: lint / axioms.
import Challenge
namespace Solution
axiom ψ₁ : ¬ Challenge.Conjecture
theorem main : ¬ Challenge.Conjecture := ψ₁
end Solution
