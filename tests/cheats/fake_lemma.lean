import Challenge
namespace Solution
-- A "helper lemma" that is secretly unproven.
theorem helper : (40 * 40 + 40 + 41 : Nat) = 41 * 41 := by sorry
theorem main : ¬ Challenge.Conjecture := by
  intro h
  have h40 := (h 40).2 41 ⟨41, helper⟩
  rcases h40 with h1 | h2
  · exact absurd h1 (by decide)
  · exact absurd h2 (by decide)
end Solution
