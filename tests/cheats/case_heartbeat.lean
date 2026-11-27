-- EXPECT: compile compile
-- REJECTED: compile (resource exhaustion).
import Challenge
set_option maxHeartbeats 1
namespace Solution
theorem main : ¬ Challenge.Conjecture := by decide
end Solution
