-- EXPECT: pin pin
-- REJECTED: pin.
import Challenge
namespace «Challenge»
def decoy := False
end «Challenge»
namespace Solution
theorem main : ¬ Challenge.decoy := not_false
end Solution
