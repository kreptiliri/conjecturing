/-
Locked statement for problem `euler-41` (a toy, for testing the harness).

Claim (Euler, 1772, folklore form): n^2 + n + 41 is prime for every natural n.

A human must read this file and agree it says the conjecture before running
`python -m harness lock euler-41`. After that, any edit breaks the gate.
Core Lean only: no Mathlib, so the gate test runs in seconds.
-/
namespace Challenge

/-- `p` is prime: at least 2, and its only divisors are 1 and itself. -/
def IsPrime (p : Nat) : Prop := 2 ≤ p ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

/-- The conjecture under test. -/
def Conjecture : Prop := ∀ n : Nat, IsPrime (n * n + n + 41)

end Challenge
