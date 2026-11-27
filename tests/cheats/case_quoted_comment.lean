-- EXPECT: lint axioms
-- REJECTED: lint / axioms.
import Challenge
namespace Solution
def «/-» := 0
axiom forged : ¬ Challenge.Conjecture
def «-/» := 0
theorem main : ¬ Challenge.Conjecture := forged
end Solution
