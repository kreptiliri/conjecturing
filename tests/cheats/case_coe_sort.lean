-- EXPECT: pin pin
-- REJECTED: pin (coerced proposition is True).
import Challenge
namespace Solution
structure Wrapped where
  marker : Unit
instance : CoeSort Wrapped Prop where
  coe _ := True
def weak : Wrapped := ⟨()⟩
theorem main : weak := True.intro
end Solution
