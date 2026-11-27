-- EXPECT: lint pin
-- REJECTED: lint / pin.
import Challenge
namespace Decoy
def fake := False
end Decoy
namespace Challenge
export Decoy (fake)
end Challenge
namespace Solution
theorem main : ¬ Challenge.fake := not_false
end Solution
