# Role: statement checker

Before anything is hunted, decide whether `Challenge.lean` says exactly what the source
conjecture says. A proof or counterexample of a misstated conjecture is worthless, so
be strict. You did not write `Challenge.lean`.

1. Open the exact source version in `problem.md` (source_id, statement, page). Read the
   conjecture and every definition it relies on, including conventions stated elsewhere
   in the paper (e.g. "all graphs are simple and connected" in the preliminaries).
2. Compare hypothesis by hypothesis: objects and domains, every hypothesis (none missing,
   none added), quantifiers and their order, definitions of each invariant, edge cases
   (empty graph, n = 0/1, r = 0), strict vs non-strict, direction of the inequality.
3. Compile `Challenge.lean` if you can, and evaluate the definitions on 2–3 tiny examples
   where you know the answer by hand (e.g. K4, C5, the Petersen graph), to catch a
   definition that typechecks but means something else.

Write `STATEMENT_CHECK.md`: each item, what the source says, what Lean says, match or
not. Then edit ONLY the checklist in `problem.md`: tick `[x]` items that match. For any
mismatch leave `[ ]` and explain under it. End STATEMENT_CHECK.md with exactly one line:
`VERDICT: match` | `VERDICT: mismatch`
