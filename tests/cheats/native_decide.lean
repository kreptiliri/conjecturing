import Challenge
namespace Solution
theorem main : ¬ Challenge.Conjecture := by
  intro h
  have h40 := (h 40).2 41 ⟨41, by native_decide⟩
  rcases h40 with h1 | h2
  · exact absurd h1 (by native_decide)
  · exact absurd h2 (by native_decide)
end Solution
