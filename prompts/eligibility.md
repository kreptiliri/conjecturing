# Role: eligibility checker (runs BEFORE any hunting)

Decide whether the exact statement in `problem.md` / `Challenge.lean` is still open,
so no agent budget is spent on a solved problem. Write `ELIGIBILITY.md`.

## Search, in this order, and list every place with link and date

1. The source: later arXiv versions, the journal version, errata. Did the authors
   already revise or settle it?
2. Papers citing the source (Google Scholar, Semantic Scholar, arXiv full-text search).
   Search the conjecture's name, the authors' names, the statement number, the main
   object, and equivalent formulations.
3. **AI-math collections.** These have repeatedly published results first:
   - PrincipiaMathOrg/math-solutions and mathdb.com
   - the-omega-institute/trureturing (issues and PRs)
   - 1337isnot1337/solved-conjectures (both `main` and `research` branches, and its issues)
   - lefttosolve.com, The-Last-Math-Competition, google-deepmind/formal-conjectures
     (solved statements link external proofs), erdosproblems.com, zenodo.org
4. The OEIS, MathOverflow, Mathlib (is it already a theorem?).

## Decide

- Is the exact statement, with all its hypotheses, still open? A different reading
  being open does not count.
- Is it just a direct consequence of a known theorem?
- Is it significant enough to spend on? One line: who would care and why.

End the file with exactly one line:
`VERDICT: open` | `VERDICT: resolved` | `VERDICT: revised` | `VERDICT: unclear`

`unclear` is honest and fine. Never write `open` because you didn't find anything
after a shallow search: list what you searched.
