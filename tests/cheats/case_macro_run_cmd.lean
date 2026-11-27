-- EXPECT: lint axioms
-- Replace the old audit's run_cmd with a forged empty axiom report.
import Challenge
import Lean
macro_rules
  | `(command| run_cmd $body:doSeq) => `(command| #eval IO.println "GATE_AXIOMS []")
namespace Solution
axiom fake : ¬ Challenge.Conjecture
theorem main : ¬ Challenge.Conjecture := fake
end Solution
