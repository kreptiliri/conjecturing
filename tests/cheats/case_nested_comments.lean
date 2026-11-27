-- EXPECT: lint axioms
-- REJECTED: lint / axioms.
import Challenge
/- outer /- sorry -/ still comment -/
namespace Solution
/-! /- nested -/ doc -/
theorem main : ¬ Challenge.Conjecture := by
  /- before /- nested -/ after -/ sorry
end Solution
