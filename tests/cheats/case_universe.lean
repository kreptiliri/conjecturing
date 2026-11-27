-- EXPECT: pin pin
-- REJECTED: pin (polymorphic proposition proves a different statement).
import Challenge
universe u
namespace Solution
theorem main : ∀ α : Sort u, True := fun _ => True.intro
end Solution
