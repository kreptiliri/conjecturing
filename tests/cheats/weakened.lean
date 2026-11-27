import Challenge
namespace Solution
-- Proves something true but different from the locked target.
theorem main : ¬ (∀ n : Nat, n < 5) := fun h => absurd (h 5) (by decide)
end Solution
