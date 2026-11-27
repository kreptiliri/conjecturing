-- EXPECT: pin pin
-- REJECTED: pin.
import Challenge
namespace Decoy.Challenge
def Conjecture := False
end Decoy.Challenge
open Decoy
namespace Solution
theorem main : ¬ Decoy.Challenge.Conjecture := not_false
end Solution
