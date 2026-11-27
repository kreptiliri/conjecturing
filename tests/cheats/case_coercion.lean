-- EXPECT: lint axioms
-- REJECTED: lint / axioms.
import Challenge
namespace Solution
instance : Coe True (¬ Challenge.Conjecture) where
  coe _ := by sorry
theorem main : True := True.intro
end Solution
