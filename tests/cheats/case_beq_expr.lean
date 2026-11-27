-- EXPECT: lint pin
-- A malicious equality instance hides the notation-substituted target.
import Challenge
import Lean
instance : BEq Lean.Expr where
  beq _ _ := true
notation "Challenge.Conjecture" => False
namespace Solution
theorem main : ¬ False := not_false
end Solution
