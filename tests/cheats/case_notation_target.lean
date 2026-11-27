-- EXPECT: lint pin
-- REJECTED: lint / pin (previously ACCEPTED with lint OFF).
import Challenge
notation "Challenge.Conjecture" => False
namespace Solution
theorem main : ¬ False := not_false
end Solution
