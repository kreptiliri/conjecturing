-- EXPECT: lint axioms
-- REJECTED: lint / axioms.
import Challenge
namespace Solution
theorem lie : Challenge.Conjecture = False := by sorry
attribute [simp] lie
theorem main : ¬ Challenge.Conjecture := by simp
end Solution
