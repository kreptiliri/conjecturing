# Verifying a result (owner)

Open a **fresh** session (no memory of the run), point it at the result's pull request,
and paste:

```
You are an independent verifier. You did not produce this result, and you must not
trust anything in it that you have not checked yourself. Repo: kreptiliri/conjecturing,
PR: <link>. Result folder: results/<slug>/.

1. Statement. Open the source in problem.md (exact arXiv version and statement number).
   Read Challenge.lean line by line and say, item by item, whether it states exactly the
   source conjecture: objects, every hypothesis, quantifiers, definitions, edge cases,
   direction. This is the most important step.
2. Lean. Check out the PR branch. Run `python3 tests/run_gate_tests.py` (all expected),
   then `python3 -m harness gate <slug> results/<slug>/Solution.lean --direction <dir>
   --lake-project ~/mathproj --strict`. Report PASS/FAIL, layers and axioms. Confirm
   problems/<slug>/Challenge.lean and results/<slug>/Challenge.lean are identical and
   match the hash in challenge.lock and GATE_RECEIPT.json.
3. Computation. Run verify.py and verify_independent.py. Then write your OWN short
   checker from the definitions in the paper (not from either script) and run it on the
   witness.
4. Novelty. Search for the conjecture name, arXiv id and statement number: later
   versions of the paper, citing papers, formal-conjectures, PrincipiaMath/MathDB,
   the-omega-institute/trureturing, 1337isnot1337/solved-conjectures, lefttosolve.com.
   Is it still open? Was this witness already posted?
5. Paper. Read paper.pdf. Does it claim more than steps 1–4 support?

Verdict: VERIFIED / NOT VERIFIED, with the reason for each step.
```

If VERIFIED: run `python3 -m harness approve <slug> --name "<you>"` on the PR branch,
commit `APPROVAL.md`, and merge. If not: comment the reasons on the PR and close it.
