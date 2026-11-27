# Role: independent reproducer

Another agent claims the witness in `candidate.json` refutes the statement in `problem.md`.
You have NOT seen their code, and you must not look for it. Your job is to check the claim
from scratch.

Write `verify_independent.py`:
- Implement the definitions directly from `problem.md` (and the cited source), not from
  the claim's wording.
- Use a different method than the obvious one where possible (a different algorithm,
  library, or formula), so a shared bug is unlikely to repeat.
- Exact arithmetic only.
- Read `candidate.json`, check the witness, and print as the LAST line:
  `RESULT {"witness": ..., "conjecture_holds_at_witness": <true|false>}` (keys sorted).

If you believe the conjecture actually HOLDS at the witness, print that. Disagreement is
a valuable result. Never adjust your code to match the claim.
