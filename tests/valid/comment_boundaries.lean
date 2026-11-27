import Challenge

/-! Disproof: at n = 40, n^2 + n + 41 = 1681 = 41 * 41. -/
namespace/- gap -/Solution

theorem main : ¬ Challenge.Conjecture := by
  intro/- outer /- nested -/ gap -/h
  -- 41 divides 40*40 + 40 + 41, so primality forces 41 = 1 or 41 = 1681.
  have h40 := (h 40).2 41 ⟨41, by decide⟩
  rcases h40 with h1 | h2
  · exact absurd h1 (by decide)
  · exact absurd h2 (by decide)

end Solution
