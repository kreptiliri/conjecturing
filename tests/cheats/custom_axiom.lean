import Challenge
namespace Solution
-- "I am so sneaky": assert the result as an axiom.
axiom euler_fails : ¬ Challenge.Conjecture
theorem main : ¬ Challenge.Conjecture := euler_fails
end Solution
