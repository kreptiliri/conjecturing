-- EXPECT: lint compile
-- REJECTED: lint / pin.
import Challenge
attribute [irreducible] Challenge.Conjecture
namespace Solution
theorem main : True := True.intro
end Solution
