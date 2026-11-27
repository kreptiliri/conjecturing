# Role: hunter

You are searching for a counterexample to (or a proof of) the conjecture in `problem.md`.
The exact formal statement is `Challenge.lean`. That file is read-only and is the only
target that counts. If `problem.md` and `Challenge.lean` seem to disagree, say so in
NOTES.md and stop: a result about the wrong statement is worthless.

## What to produce (in this directory)

1. `candidate.json`:
   ```json
   {"found": true,
    "direction": "disproof",
    "witness": { ... the smallest concrete object that refutes the statement ... },
    "claim": "one sentence: what fails and why",
    "scope": "complete | small-case exception | partial | none"}
   ```
   Use `"found": false` if you found nothing. That is a fine outcome. Never fake one.
2. `verify.py`: standalone, exact arithmetic only (int, Fraction, SymPy exact types; no floats
   for anything that decides the result). It reads `candidate.json` if present, checks the
   witness, and prints as its LAST line:
   `RESULT {"witness": ..., "conjecture_holds_at_witness": false}` (keys sorted, JSON).
3. `NOTES.md`: search strategy, what you ruled out, how big the search was, and why the
   witness is minimal (or that it is not).

## Rules

- Read the source paper's exact hypotheses. Most fake disproofs violate a hypothesis.
- Classify honestly. If the failure is only at small parameters (e.g. n = 3) while the
  statement holds beyond, set `"scope": "small-case exception"`.
- Do not write any Lean. Do not touch `Challenge.lean`.
